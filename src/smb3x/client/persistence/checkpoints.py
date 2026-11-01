# SPDX-License-Identifier: MPL-2.0
"""immutable automatic checkpoints and bounded fresh-process recovery.

All methods require the caller's exclusive session_lock. Dirty runs are retained;
only a complete verified generation may replace an entire fresh native lifetime.
"""

from __future__ import annotations
from copy import deepcopy
from hashlib import sha256
from pathlib import Path
import json
import os
import time
import uuid
from zipfile import ZipFile, BadZipFile
from .atomic import save_json
from .receipts import Identity, StateStore
from .world_journal import NativeJournal, unseal, occupied
from ..inventory import validate as inventory_validate
from ...shared.emulators import bound_profile

SCHEMA = 3
# Persisted inside BizHawk State; historical spelling is a save contract.
CHECKPOINT_GENERATION_KEY = 'smb3.m233.generation'
MEMBERS = (
    'native.State',
    'worlds.json',
    'deliveries.json',
    'controller.json',
    'witness.json',
    'server.json',
)


def digest(data):
    return sha256(data).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True).encode()


def fingerprint(value):
    return digest(canonical(value))


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def unique():
    return uuid.uuid4().hex


def identifier(value):
    if (
        not isinstance(value, str)
        or len(value) != 32
        or any((c not in '0123456789abcdef' for c in value))
    ):
        raise ValueError('Invalid checkpoint/run identifier')
    return value


def flush_file(path):
    with Path(path).open('r+b') as f:
        f.flush()
        os.fsync(f.fileno())


def write_new(path, value):
    with Path(path).open('xb') as f:
        f.write(canonical(value) + b'\n')
        f.flush()
        os.fsync(f.fileno())


def validate_prefix(saved, received):
    """Call only after an explicit complete index-0 ReceivedItems replay."""
    if not isinstance(saved, list) or not isinstance(received, list):
        raise ValueError('Invalid received history')
    if len(received) < len(saved) or received[: len(saved)] != saved:
        raise ValueError(
            'Authoritative server item prefix changed/truncated; preserve both histories'
        )


def validate_state_container(path, marker, emulator):
    selected = bound_profile(emulator)
    core_member = selected['state_core']
    try:
        with ZipFile(path) as z:
            if z.testzip() is not None:
                raise ValueError('State container CRC mismatch')
            names = z.namelist()
            if len(names) != len(set(names)) or not {
                core_member,
                'BizVersion.txt',
                'UserData.txt',
            } <= set(names):
                raise ValueError('State container members missing/duplicated')
            data = json.loads(z.read('UserData.txt'))
            if data.get('o', {}).get(CHECKPOINT_GENERATION_KEY) != marker:
                raise ValueError('Native State lacks exact namespaced generation marker')
            if z.read('BizVersion.txt').decode().strip() != selected['state_version']:
                raise ValueError('Native State emulator version mismatch')
            if set(names) & {'Core.bin', 'Core.bin.zst'} != {core_member}:
                raise ValueError('Native State core member differs from its emulator profile')
            if selected['state_sync']:
                if 'SyncSettings.json' not in names:
                    raise ValueError('Native State sync settings missing')
                if fingerprint(json.loads(z.read('SyncSettings.json'))) != selected['state_sync_sha256']:
                    raise ValueError('Native State sync settings differ from the verified emulator profile')
                if not z.read(core_member).startswith(bytes.fromhex('28b52ffd')):
                    raise ValueError('Native State compressed core header is invalid')
            if not z.read(core_member):
                raise ValueError('Empty native core State')
            return {n: dict(size=len(z.read(n)), sha256=digest(z.read(n))) for n in names}
    except BadZipFile as exc:
        raise ValueError('Invalid native State container') from exc


def validate_components(folder, binding):
    """Cross-check State witnesses, typed receipts and controller/server histories.

    Effect-aware bindings select their own existing schemas. Checks stay ordered:
    malformed input must fail before later fields are indexed or native work begins.
    """
    folder = Path(folder)
    worlds = read(folder / 'worlds.json')
    deliveries = read(folder / 'deliveries.json')
    controller = read(folder / 'controller.json')
    witness = read(folder / 'witness.json')
    server = read(folder / 'server.json')
    identity = Identity(**binding['identity'])
    session = identity.key
    journal = NativeJournal(
        folder / 'unused-validation',
        session,
        binding['rom_sha256'],
        binding['registry'],
        hammer_mode=binding['progression']['hammer_mode'],
    )
    journal.validate(worlds)
    if worlds['pending'] is not None:
        raise ValueError('Checkpoint contains pending native transaction')
    if (
        deliveries.get('schema') != (10 if 'effects' in binding else 9)
        or deliveries.get('identity') != identity.as_dict()
        or deliveries.get('registry') != binding['registry']
    ):
        raise ValueError('Checkpoint delivery binding mismatch')
    items = deliveries.get('items', {})
    pending = deliveries.get('pending')
    handled = deliveries.get('handled', {})
    from ...shared.items import ITEMS

    # Validate types before set/range operations; preserve this short-circuit order.
    if (
        not isinstance(pending, list)
        or any((type(i) is not int or i < 0 for i in pending))
        or pending != sorted(set(pending))
        or any(
            (
                not str(k).isdigit() or str(int(k)) != k or type(v) is not int or (v not in ITEMS)
                for k, v in items.items()
            )
        )
        or any((k not in items or v not in ('applied', 'capped') for k, v in handled.items()))
        or set(map(str, pending)) & set(handled)
        or (set(map(str, pending)) | set(handled) != set(items))
        or (set(items) != set(map(str, range(len(items)))))
    ):
        raise ValueError('Invalid checkpoint delivery partition/history')
    physical = deliveries.get('physical_checks')
    confirmed = deliveries.get('confirmed_physical')
    if any(
        (
            not isinstance(v, list) or v != sorted(set(v)) or any((type(i) is not int for i in v))
            for v in (physical, confirmed)
        )
    ):
        raise ValueError('Malformed physical check sets')
    if not set(confirmed) <= set(physical) <= set(binding['location_ids']):
        raise ValueError('Physical provenance mismatch')
    if (
        controller.get('schema') != (2 if 'effects' in binding else 1)
        or witness.get('schema') != 1
        or server.get('schema') != 1
    ):
        raise ValueError('Unknown checkpoint component schema')
    if controller.get('session') != session or witness.get('session') != session:
        raise ValueError('Controller/witness session mismatch')
    if set(witness) != {
        'schema',
        'session',
        'frame',
        'native',
        'inventory',
        'ram',
        'prg',
        'chr',
        'frozen',
        'publication',
    }:
        raise ValueError('Incomplete native checkpoint witness')
    if (
        type(witness['frame']) is not int
        or witness['frame'] < 0
        or witness['frozen'] is not True
        or (witness['publication'] != {'mailbox': 0, 'stack': 0, 'pending': 0, 'write': 0})
        or (witness['prg'] != binding['prg_sha256'])
        or (witness['chr'] != binding['chr_sha256'])
        or (not isinstance(witness['ram'], list))
        or (len(witness['ram']) != 2)
        or any(
            (
                not isinstance(x, str)
                or len(x) != 64
                or any((c not in '0123456789abcdef' for c in x))
                for x in witness['ram']
            )
        )
    ):
        raise ValueError('Native freeze/publication/ROM/RAM witness invalid')
    native = witness['native']
    if (
        native['phase'] != 2
        or native['bound'] != 1
        or native['error'] != 0
        or (native['session'] != session)
        or (native['active'] != worlds['active'])
        or (native['world'] != worlds['active'])
        or (native['sequence'] != native['seen'])
        or (native['sequence'] != worlds['sequence'])
        or (native['transaction'] != worlds['committed'])
    ):
        raise ValueError('Native checkpoint witness differs from external world authority')
    if native['ending_phase'] != worlds['ending']['phase'] or native['ending_version'] != (
        1 if native['ending_phase'] else 0
    ):
        raise ValueError('Native ending witness differs from world authority')
    if native['snapshot'] != unseal(worlds['worlds'][str(worlds['active'])]) or occupied(
        native['snapshot']['data'], native['snapshot']['point']
    ):
        raise ValueError('Active checkpoint snapshot mismatch/occupied')
    if (
        witness['inventory'] != worlds['inventory']['snapshot']
        or witness['inventory']['pending'] != 0
    ):
        raise ValueError('Inventory witness differs or native grant pending')
    inventory_validate(
        witness['inventory'],
        binding['progression']['inventory_mode'],
        regional=binding['progression']['hammer_mode'] == 'regional',
    )
    if (
        controller['delivery']['handled'] != handled
        or controller['delivery']['items'] != items
        or controller['delivery']['pending'] != pending
    ):
        raise ValueError('Lua/Python delivery histories disagree')
    if controller['physical_checks'] != physical:
        raise ValueError('Lua/Python physical histories disagree')
    travel = controller.get('travel', {})
    if (
        controller.get('flight') is not False
        or controller.get('unissued') is not True
        or travel.get('schema') != 1
        or (travel.get('session') != session)
        or (travel.get('active') != native['active'])
        or (travel.get('want_mask') != native['unlock'])
        or (not isinstance(travel.get('progression'), dict))
        or (set(travel['progression']) != {'hammers', 'stars', 'pending', 'checks'})
    ):
        raise ValueError('Incomplete/unsettled Lua controller witness')
    prefix = server.get('received')
    if (
        not isinstance(prefix, list)
        or len(prefix) != len(items)
        or any(
            (
                not isinstance(x, list) or len(x) != 4 or x[0] != items[str(i)]
                for i, x in enumerate(prefix)
            )
        )
    ):
        raise ValueError('Full NetworkItem prefix missing/different')
    if 'effects' in binding:
        from ..deathlink import validate as validate_deaths

        validate_deaths(controller.get('deathlink'))
        from ..effects import validate_delivery

        validate_delivery(deliveries)
        if (
            controller.get('effects') != deliveries['effects']
            or server['received'] != deliveries['effects']['prefix']
        ):
            raise ValueError('Lua/Python effect controller or receipt prefix mismatch')
        if any(
            (
                r['state'] in ('committed', 'activated')
                for r in deliveries['effects']['records'].values()
            )
        ):
            raise ValueError('Unsettled effect cannot enter a map checkpoint')
    return dict(
        worlds=worlds, deliveries=deliveries, controller=controller, witness=witness, server=server
    )


class RecoveryConfirmationNeeded(ValueError):

    def __init__(self, summary):
        self.summary = summary
        super().__init__(
            'Restore the last verified checkpoint and discard the preserved unsaved tail? '
            + summary['reason']
        )


class CheckpointStore:

    def __init__(self, root, binding):
        self.root = Path(root)
        self.binding = deepcopy(binding)
        self.epochs = self.root / 'EPOCH.json'
        self.pointer = self.root / 'LATEST.json'
        self.recovery = None

    def epoch(self):
        e = read(self.epochs)
        if (
            e.get('schema') != SCHEMA
            or e.get('binding') != fingerprint(self.binding)
            or e.get('state') not in ('active', 'restoring', 'closed', 'sealed')
        ):
            raise ValueError('Unknown/mismatched run epoch')
        identifier(e['run'])
        return e

    def new_run(self):
        if self.epochs.exists() or self.pointer.exists():
            raise ValueError('Existing session cannot be started as new; preserve history')
        run = unique()
        folder = self.root / 'runs' / run
        folder.mkdir(parents=True, exist_ok=False)
        save_json(
            self.epochs,
            dict(
                schema=SCHEMA,
                binding=fingerprint(self.binding),
                run=run,
                state='active',
                parent=None,
                created=time.time(),
                epoch_token=unique(),
                published=[],
                tail=None,
            ),
        )
        return (run, folder)

    def restart_unstarted(self):
        """Restart only a proven pre-native lifetime; never infer from no LATEST."""
        if self.pointer.exists():
            raise ValueError('A verified checkpoint exists; use Resume')
        e = self.epoch()
        old = self.root / 'runs' / e['run']
        key = Identity(**self.binding['identity']).key
        if (
            e['state'] != 'active'
            or e.get('parent')
            or e.get('generation')
            or e.get('tail')
            or e.get('published')
            or any((self.root / 'candidates').glob('*'))
            or any((self.root / 'checkpoints').glob('*'))
            or any((old / 'worlds').glob('*'))
        ):
            raise ValueError(
                'Initial checkpoint was not completed and native activity cannot be excluded. Preserve this same session and its logs for recovery; no new room is required.'
            )
        path = old / 'deliveries' / (key + '.json')
        state = None
        if path.exists():
            parser = StateStore
            if 'effects' in self.binding:
                from ..effects import EffectStore

                parser = EffectStore
            state = parser(path.parent).load(Identity(**self.binding['identity']))
            if (
                state.handled
                or state.physical_checks
                or state.confirmed_physical
                or state.travel
                or (state.registry not in (None, self.binding.get('registry')))
                or (
                    'effects' in self.binding
                    and (state.effects['records'] or state.effects['last_entry'])
                )
            ):
                raise ValueError(
                    'Initial native outcome exists without a checkpoint; preserve this session for recovery'
                )
        if 'effects' in self.binding:
            effects = self.validate_effect_tail(e)
            deaths = self.validate_death_tail(e)
            if (
                effects
                and (
                    state is None
                    or effects['value'] != state.effects
                    or effects['value']['records']
                    or effects['value']['last_entry']
                )
                or (deaths and deaths['value']['records'])
            ):
                raise ValueError(
                    'Initial effect/death custody cannot be restarted without a checkpoint; preserve this session for recovery'
                )
        history = self.root / 'epoch-history'
        history.mkdir(exist_ok=True)
        write_new(history / (unique() + '.json'), e)
        run = unique()
        folder = self.root / 'runs' / run
        folder.mkdir(parents=True, exist_ok=False)
        save_json(
            self.epochs,
            dict(
                schema=SCHEMA,
                binding=fingerprint(self.binding),
                run=run,
                state='active',
                parent=None,
                created=time.time(),
                epoch_token=unique(),
                published=[],
                tail=None,
                unstarted_predecessor=e['run'],
            ),
        )
        return (run, folder)

    def candidate(self, run):
        e = self.epoch()
        if e['state'] != 'active' or e['run'] != run:
            raise ValueError('Save requires the active run owner')
        generation = unique()
        folder = self.root / 'candidates' / generation
        folder.mkdir(parents=True, exist_ok=False)
        marker = (
            'm233:3:' + Identity(**self.binding['identity']).key + ':' + generation + ':' + unique()
        )
        return dict(
            generation=generation, path=str(folder), marker=marker, run=run, parent=e['parent']
        )

    def publish(self, candidate, verification, close=False):
        timing = {}
        step = time.perf_counter()
        e = self.epoch()
        folder = Path(candidate['path'])
        if (
            e['state'] != 'active'
            or e['run'] != candidate['run']
            or candidate.get('parent') != e['parent']
            or (folder != self.root / 'candidates' / identifier(candidate['generation']))
        ):
            raise ValueError('Candidate ownership mismatch')
        components = validate_components(folder, self.binding)
        if 'effects' in self.binding:
            from ..effects import extends
            from ..deathlink import extends as death_extends

            death_tail = self.validate_death_tail(e)
            if death_tail:
                death_extends(death_tail['value'], components['controller']['deathlink'])
            tail = e.get('effects')
            if tail:
                self.validate_effect_tail(e)
                extends(tail['value'], components['deliveries']['effects'])
        w = components['witness']
        if verification != {
            'verified': True,
            'marker': candidate['marker'],
            'witness_sha256': fingerprint(w),
            'frame': w['frame'],
        }:
            raise ValueError('Native actual-load verification does not match candidate')
        container = validate_state_container(folder / 'native.State', candidate['marker'], self.binding['emulator'])
        timing['component_container_validation_seconds'] = time.perf_counter() - step
        timing['component_flush_seconds'] = 0.0
        timing['component_read_hash_seconds'] = 0.0
        members = {}
        for name in MEMBERS:
            step = time.perf_counter()
            flush_file(folder / name)
            timing['component_flush_seconds'] += time.perf_counter() - step
            step = time.perf_counter()
            data = (folder / name).read_bytes()
            members[name] = dict(size=len(data), sha256=digest(data))
            timing['component_read_hash_seconds'] += time.perf_counter() - step
        step = time.perf_counter()
        manifest = dict(
            schema=SCHEMA,
            version='m25-hybrid-1',
            generation=candidate['generation'],
            run=e['run'],
            parent=e['parent'],
            binding=self.binding,
            marker=candidate['marker'],
            created=time.time(),
            members=members,
            container=container,
            prefix_sha256=fingerprint(components['server']['received']),
            verified=verification,
        )
        write_new(folder / 'manifest.json', manifest)
        committed = self.root / 'checkpoints' / candidate['generation']
        committed.parent.mkdir(exist_ok=True)
        for attempt in range(5):
            try:
                os.rename(folder, committed)
                break
            except OSError as exc:
                if getattr(exc, 'winerror', None) not in (5, 32, 33) or attempt == 4:
                    raise
                time.sleep(0.03 * (attempt + 1))
        pointer = dict(
            schema=SCHEMA,
            generation=candidate['generation'],
            manifest_sha256=digest((committed / 'manifest.json').read_bytes()),
        )
        save_json(self.pointer, pointer)
        parent = {k: pointer[k] for k in ('generation', 'manifest_sha256')}
        published_at = time.time()
        folded = {}
        if 'effects' in self.binding:
            folded['effects'] = dict(ancestor=parent, value=components['deliveries']['effects'])
            folded['deathlink'] = dict(ancestor=parent, value=components['controller']['deathlink'])
        save_json(
            self.epochs,
            {
                **e,
                'state': 'closed' if close else 'sealed',
                **parent,
                'parent': parent,
                'saved': published_at,
                'tail': None,
                **folded,
            },
        )
        self.published_at = published_at
        timing['manifest_publish_epoch_seconds'] = time.perf_counter() - step
        self.publish_timing = timing
        return pointer

    def verify(self):
        p = read(self.pointer)
        if p.get('schema') != SCHEMA:
            raise ValueError('Unknown checkpoint pointer schema')
        folder = self.root / 'checkpoints' / identifier(p['generation'])
        m = read(folder / 'manifest.json')
        if (
            digest((folder / 'manifest.json').read_bytes()) != p['manifest_sha256']
            or m.get('schema') != SCHEMA
            or m.get('version') != 'm25-hybrid-1'
        ):
            raise ValueError('Checkpoint manifest mismatch/version')
        if (
            m['generation'] != p['generation']
            or m['binding'] != self.binding
            or set(m['members']) != set(MEMBERS)
        ):
            raise ValueError('Checkpoint binding/member mismatch')
        for name, expected in m['members'].items():
            data = (folder / name).read_bytes()
            if dict(size=len(data), sha256=digest(data)) != expected:
                raise ValueError('Checkpoint member missing/changed: ' + name)
        if validate_state_container(folder / 'native.State', m['marker'], self.binding['emulator']) != m['container']:
            raise ValueError('Checkpoint state-container mismatch')
        components = validate_components(folder, self.binding)
        if fingerprint(components['server']['received']) != m['prefix_sha256']:
            raise ValueError('Item prefix digest mismatch')
        w = components['witness']
        if m['verified'] != {
            'verified': True,
            'marker': m['marker'],
            'witness_sha256': fingerprint(w),
            'frame': w['frame'],
        }:
            raise ValueError('Native verification certificate mismatch')
        seen = {m['generation']}
        parent = m['parent']
        while parent is not None:
            if (
                set(parent) != {'generation', 'manifest_sha256'}
                or identifier(parent['generation']) in seen
            ):
                raise ValueError('Checkpoint ancestry loop/mismatch')
            seen.add(parent['generation'])
            ancestor = self.root / 'checkpoints' / parent['generation'] / 'manifest.json'
            if digest(ancestor.read_bytes()) != parent['manifest_sha256']:
                raise ValueError('Checkpoint ancestor missing/changed')
            previous = read(ancestor)
            if (
                previous.get('binding') != self.binding
                or previous.get('generation') != parent['generation']
            ):
                raise ValueError('Checkpoint ancestor binding mismatch')
            parent = previous['parent']
        return (folder, m, components)

    def resume(self, allow_loss=False):
        """Restore a verified generation into a fresh run; retain the old run as evidence."""
        folder, m, components = self.verify()
        e = self.epoch()
        if not set(e.get('published', [])) <= set(components['deliveries']['physical_checks']):
            raise ValueError(
                'Server publication exceeds verified native checkpoint; ambiguous recovery refused'
            )
        prior = e.get('generation')
        ancestor = m
        if not prior and m['run'] != e['run']:
            raise ValueError('Initial checkpoint belongs to a different native lifetime')
        while prior and ancestor['generation'] != prior and ancestor['parent']:
            ancestor = read(
                self.root / 'checkpoints' / ancestor['parent']['generation'] / 'manifest.json'
            )
        if prior and ancestor['generation'] != prior:
            raise ValueError('Dirty epoch is not an ancestor of the latest checkpoint')
        self.resume_deathlink = None
        self.resume_effects = None
        if 'effects' in self.binding:
            from ..effects import recovered, extends

            effect_tail = self.validate_effect_tail(e)
            baseline = components['deliveries']['effects']
            if effect_tail:
                if (
                    effect_tail['ancestor'] == e.get('parent')
                    and e.get('generation') == m['generation']
                ):
                    extends(baseline, effect_tail['value'])
                    baseline = effect_tail['value']
                else:
                    extends(effect_tail['value'], baseline)
            self.resume_effects = recovered(baseline)
            from ..deathlink import recovered as death_recovered, extends as death_extends

            dt = self.validate_death_tail(e)
            baseline = components['controller']['deathlink']
            if dt:
                if e.get('generation') == m['generation']:
                    death_extends(baseline, dt['value'])
                    baseline = dt['value']
                else:
                    death_extends(dt['value'], baseline)
            self.resume_deathlink = death_recovered(baseline)
        tail = e.get('tail') if e.get('generation') == m['generation'] else None
        self.recovery = dict(
            kind='clean' if e['state'] == 'closed' else 'automatic',
            generation=m['generation'],
            saved=m['created'],
            discarded_run=e['run'],
            reason=tail['reason'] if tail else 'No durably observed meaningful unsaved progress',
        )
        if tail and (not allow_loss):
            raise RecoveryConfirmationNeeded(self.recovery)
        run = unique()
        derived = self.root / 'runs' / run
        derived.mkdir(parents=True, exist_ok=False)
        key = Identity(**self.binding['identity']).key
        for name, sub in (('worlds', 'worlds'), ('deliveries', 'deliveries')):
            target = derived / sub
            target.mkdir()
            write_new(target / (key + '.json'), components[name])
        previous = self.root / 'epoch-history'
        previous.mkdir(exist_ok=True)
        write_new(previous / (unique() + '.json'), e)
        parent = dict(
            generation=m['generation'],
            manifest_sha256=digest((folder / 'manifest.json').read_bytes()),
        )
        reconciled = {}
        if self.resume_effects is not None:
            reconciled['effects'] = dict(ancestor=parent, value=self.resume_effects)
            reconciled['deathlink'] = dict(ancestor=parent, value=self.resume_deathlink)
        save_json(
            self.epochs,
            {
                **e,
                'state': 'restoring',
                'run': run,
                **parent,
                'parent': parent,
                'tail': None,
                'recovery': self.recovery,
                **reconciled,
            },
        )
        return (run, derived, folder, m, components)

    def activate(self, run):
        e = self.epoch()
        if e['state'] != 'restoring' or e['run'] != run:
            raise ValueError('Resume token is stale/already consumed')
        save_json(
            self.epochs, {**e, 'state': 'active', 'activated': time.time(), 'epoch_token': unique()}
        )

    def activate_checkpoint(self, run, generation):
        e = self.epoch()
        if e['state'] != 'sealed' or e['run'] != run or e.get('generation') != generation:
            raise ValueError('Autosave release token is stale')
        token = unique()
        history = self.root / 'epoch-history'
        history.mkdir(exist_ok=True)
        write_new(history / (token + '.json'), e)
        save_json(
            self.epochs, {**e, 'state': 'active', 'epoch_token': token, 'activated': time.time()}
        )
        return token

    def mark_exposed(self, run, reason, frame=None):
        e = self.epoch()
        if e['run'] != run or e['state'] != 'active':
            raise ValueError('Tail observation lost active ownership')
        if not e.get('tail'):
            save_json(
                self.epochs,
                {**e, 'tail': dict(reason=str(reason), frame=frame, observed=time.time())},
            )

    def authorize_publication(self, run, checks):
        folder, m, c = self.verify()
        e = self.epoch()
        if e['run'] != run or e['state'] not in ('active', 'closed', 'sealed'):
            raise ValueError('Check publication lost run ownership')
        if not set(checks) <= set(c['deliveries']['physical_checks']):
            raise ValueError('Unsaved physical checks cannot be published')
        published = sorted(set(e.get('published', [])) | set(checks))
        if published != e.get('published', []):
            save_json(self.epochs, {**e, 'published': published})
        return set(checks)

    def validate_effect_tail(self, e):
        from ..effects import validate

        tail = e.get('effects')
        if tail is None:
            return None
        if (
            not isinstance(tail, dict)
            or set(tail) != {'ancestor', 'value'}
            or tail['ancestor'] != e.get('parent')
        ):
            raise ValueError('Effect disposition checkpoint ancestry mismatch')
        validate(tail['value'])
        if tail['ancestor'] is None and any(
            (r['state'] != 'queued' for r in tail['value']['records'].values())
        ):
            raise ValueError('Effect activation before initial verified checkpoint')
        return tail

    def persist_effects(self, run, value):
        from ..effects import validate, extends

        validate(value)
        e = self.epoch()
        if (
            e['run'] != run
            or e['state'] not in ('active', 'restoring')
            or 'effects' not in self.binding
        ):
            raise ValueError('Effect disposition lost managed run authority')
        tail = self.validate_effect_tail(e)
        if tail:
            extends(tail['value'], value)
        if e.get('parent') is None and any(
            (r['state'] != 'queued' for r in value['records'].values())
        ):
            raise ValueError('No effect activation before initial checkpoint')
        updated = dict(ancestor=e.get('parent'), value=deepcopy(value))
        if tail != updated:
            save_json(self.epochs, {**e, 'effects': updated})

    def validate_death_tail(self, e):
        from ..deathlink import validate

        tail = e.get('deathlink')
        if tail is None:
            return None
        if (
            not isinstance(tail, dict)
            or set(tail) != {'ancestor', 'value'}
            or tail['ancestor'] != e.get('parent')
        ):
            raise ValueError('DeathLink disposition checkpoint ancestry mismatch')
        validate(tail['value'])
        return tail

    def persist_deathlink(self, run, value):
        from ..deathlink import validate, extends

        validate(value)
        e = self.epoch()
        if (
            e['run'] != run
            or e['state'] not in ('active', 'restoring')
            or 'effects' not in self.binding
        ):
            raise ValueError('DeathLink lost managed run authority')
        tail = self.validate_death_tail(e)
        if tail:
            extends(tail['value'], value)
        updated = dict(ancestor=e.get('parent'), value=deepcopy(value))
        if tail != updated:
            save_json(self.epochs, {**e, 'deathlink': updated})
