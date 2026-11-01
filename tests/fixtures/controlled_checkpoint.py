# SPDX-License-Identifier: MPL-2.0
"""M23.2 immutable coordinated checkpoints. No ROM writes or historical migration.

All methods require the caller's exclusive session_lock. A clean closed epoch is
required for Tier 1 resume; active/dirty tails are deliberately unsupported.
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
from smb3x.client.persistence.atomic import save_json
from smb3x.client.persistence.receipts import Identity, StateStore
from smb3x.client.persistence.world_journal import NativeJournal, unseal, occupied
from smb3x.client.inventory import validate as inventory_validate
SCHEMA = 1
MEMBERS = ('native.State', 'worlds.json', 'deliveries.json', 'controller.json', 'witness.json', 'server.json')

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
    if not isinstance(value, str) or len(value) != 32 or any((c not in '0123456789abcdef' for c in value)):
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
    if len(received) < len(saved) or received[:len(saved)] != saved:
        raise ValueError('Authoritative server item prefix changed/truncated; preserve both histories')

def validate_state_container(path, marker):
    try:
        with ZipFile(path) as z:
            if z.testzip() is not None:
                raise ValueError('State container CRC mismatch')
            names = z.namelist()
            if len(names) != len(set(names)) or not {'Core.bin', 'BizVersion.txt', 'UserData.txt'} <= set(names):
                raise ValueError('State container members missing/duplicated')
            data = json.loads(z.read('UserData.txt'))
            if data.get('o', {}).get('smb3.m232.generation') != marker:
                raise ValueError('Native State lacks exact namespaced generation marker')
            if z.read('BizVersion.txt').decode().strip() != 'Version 2.10':
                raise ValueError('Native State emulator version mismatch')
            if not z.read('Core.bin'):
                raise ValueError('Empty native core State')
            return {n: dict(size=len(z.read(n)), sha256=digest(z.read(n))) for n in names}
    except BadZipFile as exc:
        raise ValueError('Invalid native State container') from exc

def validate_components(folder, binding):
    """Validate unchanged schema9 journals plus schema1 controller/witness records."""
    folder = Path(folder)
    worlds = read(folder / 'worlds.json')
    deliveries = read(folder / 'deliveries.json')
    controller = read(folder / 'controller.json')
    witness = read(folder / 'witness.json')
    server = read(folder / 'server.json')
    identity = Identity(**binding['identity'])
    session = identity.key
    journal = NativeJournal(folder / 'unused-validation', session, binding['rom_sha256'], binding['registry'], hammer_mode=binding['progression']['hammer_mode'])
    journal.validate(worlds)
    if worlds['pending'] is not None:
        raise ValueError('Checkpoint contains pending native transaction')
    if deliveries.get('schema') != 9 or deliveries.get('identity') != identity.as_dict() or deliveries.get('registry') != binding['registry']:
        raise ValueError('Checkpoint delivery binding mismatch')
    items = deliveries.get('items', {})
    pending = deliveries.get('pending')
    handled = deliveries.get('handled', {})
    from smb3x.shared.items import ITEMS
    if not isinstance(pending, list) or any((type(i) is not int or i < 0 for i in pending)) or pending != sorted(set(pending)) or any((not str(k).isdigit() or str(int(k)) != k or type(v) is not int or (v not in ITEMS) for k, v in items.items())) or any((k not in items or v not in ('applied', 'capped') for k, v in handled.items())) or set(map(str, pending)) & set(handled) or (set(map(str, pending)) | set(handled) != set(items)) or (set(items) != set(map(str, range(len(items))))):
        raise ValueError('Invalid checkpoint delivery partition/history')
    physical = deliveries.get('physical_checks')
    confirmed = deliveries.get('confirmed_physical')
    if any((not isinstance(v, list) or v != sorted(set(v)) or any((type(i) is not int for i in v)) for v in (physical, confirmed))):
        raise ValueError('Malformed physical check sets')
    if not set(confirmed) <= set(physical) <= set(binding['location_ids']):
        raise ValueError('Physical provenance mismatch')
    if controller.get('schema') != 1 or witness.get('schema') != 1 or server.get('schema') != 1:
        raise ValueError('Unknown checkpoint component schema')
    if controller.get('session') != session or witness.get('session') != session:
        raise ValueError('Controller/witness session mismatch')
    if set(witness) != {'schema', 'session', 'frame', 'native', 'inventory', 'ram', 'prg', 'chr', 'frozen', 'publication'}:
        raise ValueError('Incomplete native checkpoint witness')
    if type(witness['frame']) is not int or witness['frame'] < 0 or witness['frozen'] is not True or (witness['publication'] != {'mailbox': 0, 'stack': 0, 'pending': 0, 'write': 0}) or (witness['prg'] != binding['prg_sha256']) or (witness['chr'] != binding['chr_sha256']) or (not isinstance(witness['ram'], list)) or (len(witness['ram']) != 2) or any((not isinstance(x, str) or len(x) != 64 or any((c not in '0123456789abcdef' for c in x)) for x in witness['ram'])):
        raise ValueError('Native freeze/publication/ROM/RAM witness invalid')
    n = witness['native']
    if n['phase'] != 2 or n['bound'] != 1 or n['error'] != 0 or (n['session'] != session) or (n['active'] != worlds['active']) or (n['world'] != worlds['active']) or (n['sequence'] != n['seen']) or (n['sequence'] != worlds['sequence']) or (n['transaction'] != worlds['committed']):
        raise ValueError('Native checkpoint witness differs from external world authority')
    if n['ending_phase'] != worlds['ending']['phase'] or n['ending_version'] != (1 if n['ending_phase'] else 0):
        raise ValueError('Native ending witness differs from world authority')
    if n['snapshot'] != unseal(worlds['worlds'][str(worlds['active'])]) or occupied(n['snapshot']['data'], n['snapshot']['point']):
        raise ValueError('Active checkpoint snapshot mismatch/occupied')
    if witness['inventory'] != worlds['inventory']['snapshot'] or witness['inventory']['pending'] != 0:
        raise ValueError('Inventory witness differs or native grant pending')
    inventory_validate(witness['inventory'], binding['progression']['inventory_mode'], regional=binding['progression']['hammer_mode'] == 'regional')
    if controller['delivery']['handled'] != handled or controller['delivery']['items'] != items or controller['delivery']['pending'] != pending:
        raise ValueError('Lua/Python delivery histories disagree')
    if controller['physical_checks'] != physical:
        raise ValueError('Lua/Python physical histories disagree')
    t = controller.get('travel', {})
    if controller.get('flight') is not False or controller.get('unissued') is not True or t.get('schema') != 1 or (t.get('session') != session) or (t.get('active') != n['active']) or (t.get('want_mask') != n['unlock']) or (not isinstance(t.get('progression'), dict)) or (set(t['progression']) != {'hammers', 'stars', 'pending', 'checks'}):
        raise ValueError('Incomplete/unsettled Lua controller witness')
    prefix = server.get('received')
    if not isinstance(prefix, list) or len(prefix) != len(items) or any((not isinstance(x, list) or len(x) != 4 or x[0] != items[str(i)] for i, x in enumerate(prefix))):
        raise ValueError('Full NetworkItem prefix missing/different')
    return dict(worlds=worlds, deliveries=deliveries, controller=controller, witness=witness, server=server)

class CheckpointStore:

    def __init__(self, root, binding):
        self.root = Path(root)
        self.binding = deepcopy(binding)
        self.epochs = self.root / 'EPOCH.json'
        self.pointer = self.root / 'LATEST.json'

    def epoch(self):
        e = read(self.epochs)
        if e.get('schema') != 1 or e.get('binding') != fingerprint(self.binding) or e.get('state') not in ('active', 'restoring', 'closed'):
            raise ValueError('Unknown/mismatched run epoch')
        identifier(e['run'])
        return e

    def new_run(self):
        if self.epochs.exists() or self.pointer.exists():
            raise ValueError('Existing session cannot be started as new; preserve history')
        run = unique()
        folder = self.root / 'runs' / run
        folder.mkdir(parents=True, exist_ok=False)
        save_json(self.epochs, dict(schema=1, binding=fingerprint(self.binding), run=run, state='active', parent=None, created=time.time()))
        return (run, folder)

    def candidate(self, run):
        e = self.epoch()
        if e['state'] != 'active' or e['run'] != run:
            raise ValueError('Save requires the active run owner')
        generation = unique()
        folder = self.root / 'candidates' / generation
        folder.mkdir(parents=True, exist_ok=False)
        marker = 'm232:1:' + Identity(**self.binding['identity']).key + ':' + generation + ':' + unique()
        return dict(generation=generation, path=str(folder), marker=marker, run=run, parent=e['parent'])

    def publish(self, candidate, verification):
        e = self.epoch()
        folder = Path(candidate['path'])
        if e['state'] != 'active' or e['run'] != candidate['run'] or folder != self.root / 'candidates' / identifier(candidate['generation']):
            raise ValueError('Candidate ownership mismatch')
        components = validate_components(folder, self.binding)
        w = components['witness']
        if verification != {'verified': True, 'marker': candidate['marker'], 'witness_sha256': fingerprint(w), 'frame': w['frame']}:
            raise ValueError('Native actual-load verification does not match candidate')
        container = validate_state_container(folder / 'native.State', candidate['marker'])
        members = {}
        for name in MEMBERS:
            flush_file(folder / name)
            data = (folder / name).read_bytes()
            members[name] = dict(size=len(data), sha256=digest(data))
        manifest = dict(schema=1, version='m232-tier1-1', generation=candidate['generation'], run=e['run'], parent=e['parent'], binding=self.binding, marker=candidate['marker'], created=time.time(), members=members, container=container, prefix_sha256=fingerprint(components['server']['received']), verified=verification)
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
        pointer = dict(schema=1, generation=candidate['generation'], manifest_sha256=digest((committed / 'manifest.json').read_bytes()))
        save_json(self.pointer, pointer)
        save_json(self.epochs, {**e, 'state': 'closed', 'generation': pointer['generation'], 'manifest_sha256': pointer['manifest_sha256'], 'closed': time.time()})
        return pointer

    def verify(self):
        p = read(self.pointer)
        if p.get('schema') != 1:
            raise ValueError('Unknown checkpoint pointer schema')
        folder = self.root / 'checkpoints' / identifier(p['generation'])
        m = read(folder / 'manifest.json')
        if digest((folder / 'manifest.json').read_bytes()) != p['manifest_sha256'] or m.get('schema') != 1 or m.get('version') != 'm232-tier1-1':
            raise ValueError('Checkpoint manifest mismatch/version')
        if m['generation'] != p['generation'] or m['binding'] != self.binding or set(m['members']) != set(MEMBERS):
            raise ValueError('Checkpoint binding/member mismatch')
        for name, expected in m['members'].items():
            data = (folder / name).read_bytes()
            if dict(size=len(data), sha256=digest(data)) != expected:
                raise ValueError('Checkpoint member missing/changed: ' + name)
        if validate_state_container(folder / 'native.State', m['marker']) != m['container']:
            raise ValueError('Checkpoint state-container mismatch')
        components = validate_components(folder, self.binding)
        if fingerprint(components['server']['received']) != m['prefix_sha256']:
            raise ValueError('Item prefix digest mismatch')
        w = components['witness']
        if m['verified'] != {'verified': True, 'marker': m['marker'], 'witness_sha256': fingerprint(w), 'frame': w['frame']}:
            raise ValueError('Native verification certificate mismatch')
        seen = {m['generation']}
        parent = m['parent']
        while parent is not None:
            if set(parent) != {'generation', 'manifest_sha256'} or identifier(parent['generation']) in seen:
                raise ValueError('Checkpoint ancestry loop/mismatch')
            seen.add(parent['generation'])
            ancestor = self.root / 'checkpoints' / parent['generation'] / 'manifest.json'
            if digest(ancestor.read_bytes()) != parent['manifest_sha256']:
                raise ValueError('Checkpoint ancestor missing/changed')
            previous = read(ancestor)
            if previous.get('binding') != self.binding or previous.get('generation') != parent['generation']:
                raise ValueError('Checkpoint ancestor binding mismatch')
            parent = previous['parent']
        return (folder, m, components)

    def resume(self):
        folder, m, components = self.verify()
        e = self.epoch()
        if e['state'] not in ('closed', 'restoring') or e.get('generation') != m['generation'] or e.get('manifest_sha256') != digest((folder / 'manifest.json').read_bytes()):
            raise ValueError('No clean Save & Quit: active/dirty run cannot use Tier 1 Resume')
        run = unique()
        derived = self.root / 'runs' / run
        derived.mkdir(parents=True, exist_ok=False)
        key = Identity(**self.binding['identity']).key
        for name, sub in (('worlds', 'worlds'), ('deliveries', 'deliveries')):
            target = derived / sub
            target.mkdir()
            write_new(target / (key + '.json'), components[name])
        save_json(self.epochs, {**e, 'state': 'restoring', 'run': run, 'parent': dict(generation=m['generation'], manifest_sha256=e['manifest_sha256'])})
        return (run, derived, folder, m, components)

    def activate(self, run):
        e = self.epoch()
        if e['state'] != 'restoring' or e['run'] != run:
            raise ValueError('Resume token is stale/already consumed')
        save_json(self.epochs, {**e, 'state': 'active', 'activated': time.time()})
