# SPDX-License-Identifier: MPL-2.0
"""Physical observations become publishable only after a coherent native State and
matching journals are durable. This coordinator owns that barrier, not the server."""

from copy import deepcopy
import asyncio
import logging
import time
from pathlib import Path
from .checkpoints import write_new, fingerprint, validate_prefix
from .world_journal import NativeJournal
from ..inventory import reconcile as reconcile_inventory
from ..transport import BridgeUnavailable

LOG = logging.getLogger('SMB3')


def received(ctx):
    return [list(item) for item in ctx.items_received]


class Coordinator:

    def __init__(self, store, run, components=None):
        self.store, self.run, self.components = (store, run, components)
        self.busy = False
        self.resuming = components is not None
        self.initial = True
        self.ready = False
        self.closed = False
        self.saved_physical = (
            set(components['deliveries']['physical_checks']) if components else set()
        )
        self.known_received = components['server']['received'] if components else []
        self.saved_ending = deepcopy(components['worlds']['ending']) if components else None
        self.checkpoint_metrics = []
        from ..deathlink import empty

        tail = store.epoch().get('deathlink')
        self.deathlink = deepcopy(tail['value']) if tail else empty()

    async def before_poll(self, ctx, bridge):
        """Return True while server replay or cold-restore ownership still blocks polling."""
        bridge.recovery_validator = self.store.epoch
        if self.closed:
            return True
        if ctx.identity is None or not ctx.replay_ready:
            try:
                await bridge.control('STATUS')
            except BridgeUnavailable:
                pass
            return True
        current = received(ctx)
        validate_prefix(self.known_received, current)
        self.known_received = deepcopy(current)
        if self.initial:
            if self.resuming:
                owner = (ctx.identity, ctx.delivery, ctx.connection_generation)
                validate_prefix(self.components['server']['received'], received(ctx))
                if not set(self.components['deliveries']['confirmed_physical']) <= set(
                    ctx.checked_locations
                ):
                    raise ValueError(
                        'Server lost checkpoint-confirmed physical checks; preserve server and local saves'
                    )
                ready = await bridge.control('RESUME_READY')
                if (
                    ctx.identity != owner[0]
                    or ctx.delivery is not owner[1]
                    or ctx.connection_generation != owner[2]
                    or ctx.validation_error
                ):
                    raise ValueError('AP owner changed during local restore validation')
                if not ctx.replay_ready:
                    return True
                current = received(ctx)
                validate_prefix(self.known_received, current)
                self.known_received = deepcopy(current)
                if ready['witness'] != self.components['witness']:
                    raise ValueError('Cold native witness changed before network validation')
                bridge.journal = NativeJournal(
                    bridge.state_dir,
                    bridge.build['session'],
                    bridge.build['output']['sha256'],
                    self.store.binding['registry'],
                    hammer_mode=bridge.build['progression']['hammer_mode'],
                )
                state = deepcopy(bridge.journal.state)
                state['bridge_instance'] = ready['bridge_instance']
                bridge.journal.save(state)
                bridge.instance = ready['bridge_instance']
                bridge.authorized = True
                if 'effects' in self.store.binding:
                    overlay = self.store.resume_effects
                    validate_prefix(overlay['prefix'], received(ctx))
                    ctx.delivery.overlay(overlay)
                    self.store.persist_effects(self.run, ctx.delivery.effects)
                    ctx.store.save(ctx.delivery)
                    self.deathlink = deepcopy(self.store.resume_deathlink)
                    self.store.persist_deathlink(self.run, self.deathlink)
                    reconciled = await bridge.control(
                        'RECONCILE_EFFECTS',
                        effects=ctx.delivery.effects,
                        delivery=ctx.delivery.as_dict(),
                        deathlink=self.deathlink,
                    )
                    if normalize_effects(reconciled['effects']) != ctx.delivery.effects:
                        raise ValueError('Cold effect reconciliation mismatch')
                self.store.activate(self.run)
                await bridge.control('ACTIVATE')
                if (
                    ctx.identity != owner[0]
                    or ctx.delivery is not owner[1]
                    or ctx.connection_generation != owner[2]
                    or ctx.validation_error
                ):
                    raise ValueError('AP owner changed during neutral restore activation')
            self.initial = False
        if not ctx.replay_ready:
            return True
        current = received(ctx)
        validate_prefix(self.known_received, current)
        self.known_received = deepcopy(current)
        return False

    async def after_poll(self, ctx, bridge, identity, state, response):
        """Reconcile a safe native capture before authorizing any new check publication."""
        if ctx.identity != identity or ctx.delivery is not state:
            raise ValueError('AP identity/delivery owner changed while native poll was outstanding')
        if 'effects' in self.store.binding:
            await self.service_effects(ctx, bridge, state)
            await self.service_deathlink(ctx, bridge)
        if (
            response.get('checkpoint_dirty')
            and response.get('checkpoint_exposed')
            and self.store.pointer.exists()
        ):
            self.store.mark_exposed(
                self.run,
                response.get('checkpoint_reason', 'unsaved native progress'),
                response.get('frame'),
            )
        if response.get('checkpoint_awaiting_ack'):
            generation = ctx.connection_generation
            await bridge.control('ACK_RESULTS', delivery=state.as_dict())
            if (
                ctx.identity != identity
                or ctx.delivery is not state
                or ctx.connection_generation != generation
                or ctx.validation_error
            ):
                raise ValueError('AP owner changed during durable batch acknowledgement')
            return
        if not response.get('save_requested') or response.get('save_stable', 0) < 30:
            return
        if bridge.action or not bridge.journal or bridge.journal.state['pending'] is not None:
            return
        captured_prefix = deepcopy(self.known_received[: len(state.items)])
        self.busy = True
        generation = ctx.connection_generation
        freeze_started = time.perf_counter()
        owns_freeze = False
        try:
            frozen = await bridge.control('FREEZE')
            if (
                ctx.connection_generation != generation
                or ctx.identity != identity
                or ctx.delivery is not state
                or ctx.validation_error
            ):
                raise ValueError('AP owner changed while freezing; no stale state may be persisted')
            if frozen.get('waiting'):
                return
            owns_freeze = True
            timing = dict(frozen.get('timing', {}))
            timing['freeze_rpc_seconds'] = time.perf_counter() - freeze_started
            step = time.perf_counter()
            witness = frozen['witness']
            if bridge.journal.reconcile(witness['native']) is not None:
                raise ValueError('Frozen checkpoint requires a native action')
            worlds = deepcopy(bridge.journal.state)
            worlds['inventory'] = reconcile_inventory(
                worlds.get('inventory'),
                witness['inventory'],
                bridge.build['progression']['inventory_mode'],
                regional=bridge.build['progression']['hammer_mode'] == 'regional',
            )
            bridge.journal.save(worlds)
            for acknowledgement in frozen['acks']:
                state.acknowledge(acknowledgement['index'], acknowledgement['result'])
            state.observe_checks(frozen['checks'], ctx.checked_locations, ctx.location_ids)
            ctx.store.save(state)
            prefix = captured_prefix
            if len(prefix) != len(state.items) or any(
                (x[0] != state.items[i] for i, x in enumerate(prefix))
            ):
                raise ValueError('Capture lacks matching complete typed received prefix')
            candidate = self.store.candidate(self.run)
            folder = Path(candidate['path'])
            timing['external_reconciliation_seconds'] = time.perf_counter() - step
            step = time.perf_counter()
            capture = await bridge.control(
                'CAPTURE',
                path=(folder / 'native.State').as_posix(),
                marker=candidate['marker'],
                delivery=state.as_dict(),
                physical_checks=sorted(state.physical_checks),
            )
            timing['capture_rpc_seconds'] = time.perf_counter() - step
            timing.update(capture.get('timing', {}))
            step = time.perf_counter()
            if (
                ctx.connection_generation != generation
                or ctx.identity != identity
                or ctx.delivery is not state
                or ctx.validation_error
            ):
                raise ValueError(
                    'AP owner changed during capture; candidate remains frozen and preserved'
                )
            if (
                not capture['verified']
                or capture['witness'] != witness
                or capture['marker'] != candidate['marker']
            ):
                raise ValueError('Actual native self-load verification mismatch')
            for field in ('items', 'handled'):
                if capture['controller']['delivery'][field] == [] and (not state.as_dict()[field]):
                    capture['controller']['delivery'][field] = {}
            if 'effects' in self.store.binding:
                capture['controller']['effects'] = normalize_effects(
                    capture['controller']['effects']
                )
                capture['controller']['deathlink'] = normalize_deaths(
                    capture['controller']['deathlink']
                )
            for name, value in dict(
                worlds=worlds,
                deliveries=state.as_dict(),
                controller=capture['controller'],
                witness=witness,
                server=dict(schema=1, received=prefix),
            ).items():
                write_new(folder / (name + '.json'), value)
            timing['external_record_write_flush_seconds'] = time.perf_counter() - step
            step = time.perf_counter()
            closing = response.get('checkpoint_quit', False)
            # Publication commits the matching State and journals before ACTIVATE/thaw.
            pointer = self.store.publish(
                candidate,
                dict(
                    verified=True,
                    marker=candidate['marker'],
                    witness_sha256=fingerprint(witness),
                    frame=witness['frame'],
                ),
                close=closing,
            )
            published_at = getattr(self.store, 'published_at', None)
            timing['publish_total_seconds'] = time.perf_counter() - step
            timing.update(getattr(self.store, 'publish_timing', {}))
            step = time.perf_counter()
            self.saved_physical = set(state.physical_checks)
            self.saved_ending = deepcopy(worlds['ending'])
            if closing:
                await ctx.disconnect()
                await bridge.control('CLOSE', marker=candidate['marker'], published_at=published_at)
                self.closed = True
                LOG.info('Saved successfully — safe to exit. Checkpoint %s', pointer['generation'])
                ctx.exit_event.set()
            else:
                token = self.store.activate_checkpoint(self.run, pointer['generation'])
                released = await bridge.control(
                    'THAW', marker=candidate['marker'], epoch_token=token, published_at=published_at
                )
                timing.update(released.get('timing', {}))
                self.resuming = False
                LOG.info(
                    'Autosaved coherent checkpoint %s; pending unissued items=%d',
                    pointer['generation'],
                    len(state.pending),
                )
            metric = dict(
                generation=pointer['generation'],
                frame=witness['frame'],
                closed=closing,
                timing=timing,
                return_epoch_rpc_seconds=time.perf_counter() - step,
                freeze_to_release_seconds=time.perf_counter() - freeze_started,
                native_bytes=(
                    self.store.root / 'checkpoints' / pointer['generation'] / 'native.State'
                )
                .stat()
                .st_size,
                handled=len(state.handled),
                pending=len(state.pending),
            )
            self.checkpoint_metrics.append(metric)
            LOG.info('CHECKPOINT METRICS %s', metric)
        except Exception:
            ctx.exit_event.set()
            writer = getattr(bridge, 'writer', None)
            if owns_freeze and writer is not None and (not writer.is_closing()):
                try:
                    await asyncio.wait_for(bridge.control('SAVE_FAILED'), 0.5)
                except Exception:
                    pass
            raise
        finally:
            self.busy = False

    def publication_checks(self, state, missing=None, supported=None):
        checks = set(state.physical_checks) & self.saved_physical
        if missing is not None:
            from .receipts import new_location_checks

            checks = new_location_checks(checks, set(missing), set(supported))
        if not checks:
            return set()
        return self.store.authorize_publication(self.run, checks)

    async def service_effects(self, ctx, bridge, state):
        result = await bridge.control('EFFECTS', effects=state.effects)
        event = result.get('event')
        if not event:
            return
        old = deepcopy(state.effects)
        if event['type'] == 'select':
            eligible = event['eligible']
            index = event['index']
            if eligible != sorted(set(eligible)) or any(
                (
                    state.effects['records'].get(str(i), {}).get('state') != 'queued'
                    for i in eligible
                )
            ):
                raise ValueError('Invalid native entry compatibility snapshot')
            if index != (eligible[0] if eligible else False):
                raise ValueError('Native effect skipped oldest compatible receipt')
            state.schedule(None if index is False else index, event['entry'])
        elif event['type'] == 'ready':
            state.commit(event['index'], event['entry'], self.run, event['area'])
        elif event['type'] == 'outcome':
            state.outcome(
                event['index'], event['entry'], event.get('token'), event['state'], event['reason']
            )
        else:
            raise ValueError('Unknown native effect event')
        self.store.persist_effects(self.run, state.effects)
        ctx.store.save(state)
        result = await bridge.control(
            'EFFECTS', effects=state.effects, acknowledgement=event['sequence']
        )
        if normalize_effects(result['effects']) != state.effects:
            raise ValueError('Native effect mirror acknowledgement mismatch')
        LOG.info('EFFECT %s', event)
        index = event.get('index')
        if index is not False and index is not None:
            from ...shared.items import ITEMS

            name = ITEMS[state.items[index]]['name']
            disposition = event.get('state')
            text = (
                'Scheduled: ' + name
                if event['type'] == 'select'
                else (
                    name + ': already powered; no change'
                    if disposition == 'completed_noop'
                    and state.effects['records'][str(index)]['kind'] == 'mushroom'
                    else (
                        name + ': already Small; no change'
                        if disposition == 'completed_noop'
                        else (
                            'Activated: ' + name
                            if disposition == 'activated'
                            or (
                                disposition == 'completed'
                                and old['records'][str(index)]['state'] == 'committed'
                            )
                            else (
                                'Ended: ' + name
                                if disposition in ('completed', 'disposed_interrupted')
                                else None
                            )
                        )
                    )
                )
            )
            if getattr(ctx.notifications, 'trap_warning', 'show') == 'hide':
                from ..effects import SPECS

                before_activation = event['type'] == 'select' or (
                    disposition == 'disposed_interrupted'
                    and old['records'][str(index)]['state'] != 'activated'
                )
                if SPECS[state.items[index]][2] and before_activation:
                    text = None
            if text:
                ctx.cosmetic(
                    lambda: ctx.notifications.emit_event(
                        'effect:' + self.run + ':' + str(event['sequence']), text
                    )
                )

    async def service_deathlink(self, ctx, bridge):
        from ..deathlink import payload, event_id, FINAL
        from ..effects import digest

        now = time.time()
        now_ms = int(now * 1000)
        enabled = self.store.binding['effects']['death_link']
        records = self.deathlink['records']
        while ctx.death_inbox:
            data, received, monotonic = ctx.death_inbox.pop(0)
            key = event_id(data)
            if key in records or any((r['network_id'] == key for r in records.values())):
                continue
            expired = time.monotonic() - monotonic >= 20 or not received <= now <= received + 20
            records[key] = dict(
                direction='incoming',
                state='expired' if expired or not enabled else 'queued',
                received=int(received * 1000),
                deadline=int(received * 1000) + 20000,
                network_id=key,
                run=self.run,
                reason=(
                    'original receipt expired/disabled'
                    if expired or not enabled
                    else 'validated remote receipt; source is unauthenticated'
                ),
            )
        for r in records.values():
            if (
                r['direction'] == 'incoming'
                and r['state'] == 'queued'
                and (not r['received'] <= now_ms < r['deadline'])
            ):
                r.update(
                    state='expired',
                    reason='original network receipt deadline elapsed or local clock reversed',
                )
        self.store.persist_deathlink(self.run, self.deathlink)
        status = await bridge.control('DEATH_STATUS', deathlink=self.deathlink)
        for e in status.get('events', []):
            if e['kind'] == 'native-local-death':
                key = digest([self.run, 'native-local-death', e['sequence']])
                if key not in records:
                    records[key] = dict(
                        direction='outgoing',
                        state='send_intent',
                        received=now_ms,
                        deadline=now_ms,
                        network_id=None,
                        run=self.run,
                        reason='genuine native Player_Die producer',
                    )
                    self.store.persist_deathlink(self.run, self.deathlink)
                    if (
                        enabled
                        and ctx.server is not None
                        and (getattr(ctx.server, 'socket', None) is not None)
                    ):
                        ctx.death_send_key = key
                        try:
                            await ctx.send_death('SMB3 native death')
                            records[key].update(
                                state='published', reason='socket send completed; no retry'
                            )
                        except Exception:
                            records[key].update(
                                state='send_uncertain',
                                reason='socket outcome ambiguous; never retry',
                            )
                        finally:
                            ctx.death_send_key = None
                    else:
                        records[key].update(
                            state='send_uncertain',
                            reason='DeathLink disabled or disconnected; not published',
                        )
            elif e.get('remote_id') in records and records[e['remote_id']]['state'] == 'committed':
                r = records[e['remote_id']]
                r.update(
                    state='applied' if e['kind'] == 'remote-death-observed' else 'expired',
                    reason=e['reason'],
                )
            self.store.persist_deathlink(self.run, self.deathlink)
            await bridge.control(
                'DEATH_ACK', event_sequence=e['sequence'], deathlink=self.deathlink
            )
        queued = sorted(
            (
                (r['received'], key)
                for key, r in records.items()
                if r['direction'] == 'incoming' and r['state'] == 'queued'
            )
        )
        if enabled and queued:
            _, key = queued[0]
            r = records[key]
            if status['dying']:
                r.update(state='coalesced', reason='already dying')
                self.store.persist_deathlink(self.run, self.deathlink)
            elif status['ready']:
                r.update(
                    state='committed', reason='durable remote native request; no automatic retry'
                )
                self.store.persist_deathlink(self.run, self.deathlink)
                result = await bridge.control(
                    'DEATH_APPLY',
                    id=key,
                    received=r['received'],
                    deadline=r['deadline'],
                    deathlink=self.deathlink,
                )
                if not result['accepted']:
                    r.update(
                        state='expired',
                        reason='native request expired or already dying before consumption',
                    )
                    self.store.persist_deathlink(self.run, self.deathlink)
        await bridge.control('DEATH_STATUS', deathlink=self.deathlink)

    def outgoing_packet(self, key, data):
        from ..deathlink import event_id

        r = self.deathlink['records'][key]
        if r['state'] != 'send_intent' or r['network_id'] is not None:
            raise ValueError('DeathLink send intent already used')
        r['network_id'] = event_id(data)
        self.store.persist_deathlink(self.run, self.deathlink)


def normalize_deaths(value):
    value = deepcopy(value)
    if value.get('records') == []:
        value['records'] = {}
    for r in value['records'].values():
        r.setdefault('network_id', None)
    return value


def normalize_effects(value):
    value = deepcopy(value)
    if value.get('records') == []:
        value['records'] = {}
    for r in value['records'].values():
        for k in ('entry', 'token', 'delay_frames'):
            r.setdefault(k, None)
    return value
