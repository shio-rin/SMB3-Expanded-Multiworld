# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations
import argparse
import asyncio
from hashlib import sha1
import json
import logging
import os
from pathlib import Path
import sys
import time
from .notifications import Notifications
from .presentation import snapshot as presentation_snapshot
from .transport import BridgeUnavailable, LuaBridge

ITEM_ID = 0x534D3381
from .persistence.receipts import DeliveryState, Identity, StateStore, new_location_checks
from ..shared import location_signals
from ..shared.items import ITEMS, ITEM_REGISTRY_SHA256, ITEM_SIGNATURE
import Utils
import warnings
from CommonClient import CommonContext, server_loop
from NetUtils import ClientStatus
from .network import SMB3Context

LOG = logging.getLogger('SMB3X')


async def watcher(ctx: SMB3Context, bridge: LuaBridge) -> None:
    """Serialize receipt persistence, native polling, checkpointing and AP publication.

    Ownership is rechecked after awaits: reconnect can change the owner while the
    native operation is outstanding. Never infer permission from an earlier poll.
    """
    bridge_up = False
    bridge_problem_reported = False
    warned_blocked = False
    while not ctx.exit_event.is_set():
        if ctx.persistence and await ctx.persistence.before_poll(ctx, bridge):
            await asyncio.sleep(0.1)
            continue
        identity, state, generation = (ctx.identity, ctx.delivery, ctx.connection_generation)
        if identity is not None and state is not None:
            incoming = [(index, item.item) for index, item in enumerate(ctx.items_received)]
            try:
                if ctx.bridge_protocol in (35,):
                    changed = (
                        state.receive([list(item) for item in ctx.items_received])
                        if hasattr(state, 'effects')
                        else state.observe_items(incoming)
                    )
                else:
                    changed = state.observe_indices([i for i, item in incoming if item == ITEM_ID])
            except ValueError as exc:
                LOG.error('Server item history rejected: %s', exc)
                ctx.exit_event.set()
                break
            # Persist pending receipt ownership before bridge.poll can request a grant.
            if changed:
                if hasattr(state, 'effects'):
                    ctx.persistence.store.persist_effects(ctx.persistence.run, state.effects)
                ctx.store.save(state)
                LOG.info('Queued server item indices: %s', state.pending)
            try:
                if ctx.bridge_protocol in (35,):
                    if state.observe_checks([], ctx.checked_locations, ctx.location_ids):
                        ctx.store.save(state)
                    cosmetic_batch = (
                        ctx.cosmetic(lambda: ctx.notifications.batch(bridge.instance)) or []
                    )
                    response = await bridge.poll(
                        identity.key,
                        state.commands(),
                        protocol=ctx.bridge_protocol,
                        goal=ctx.goal,
                        presentation=presentation_snapshot(
                            state,
                            ctx.progression_config,
                            ctx.goal,
                            ctx.server is not None and ctx.slot is not None,
                        ),
                        hazards=ctx.hazards,
                        audiovisual=ctx.audiovisual,
                        level_shuffle=ctx.level_shuffle,
                        cosmetics=ctx.cosmetics,
                        progression_config=ctx.progression_config,
                        progression={**state.progression, 'checks': state.check_counts()},
                        developer_connected=ctx.server is not None and ctx.slot is not None,
                        notifications=cosmetic_batch,
                        unlock_mask=state.unlock_mask,
                        handled=state.handled,
                        checkpoint=state.travel,
                        item_hash=ITEM_REGISTRY_SHA256,
                        item_signature=ITEM_SIGNATURE,
                        location_hash=(
                            location_signals.REGISTRY_SHA256 if ctx.bridge_protocol == 35 else None
                        ),
                        location_signature=(
                            location_signals.SIGNATURE if ctx.bridge_protocol == 35 else None
                        ),
                        location_ids=(
                            sorted(ctx.location_ids) if ctx.bridge_protocol == 35 else None
                        ),
                    )
                else:
                    response = await bridge.poll(identity.key, state.pending)
                if ctx.identity != identity or ctx.delivery is not state or ctx.validation_error:
                    raise ValueError(
                        'AP owner changed during native poll; no stale acknowledgement may be persisted'
                    )
                if ctx.connection_generation != generation or not ctx.replay_ready:
                    await bridge.control('WAIT_SERVER')
                    while not ctx.replay_ready and (not ctx.exit_event.is_set()):
                        await bridge.control('STATUS')
                        await asyncio.sleep(0.1)
                    if ctx.exit_event.is_set():
                        return
                    if (
                        ctx.identity != identity
                        or ctx.delivery is not state
                        or ctx.validation_error
                    ):
                        raise ValueError('AP owner changed while waiting for server replay')
                    from .persistence.checkpoints import validate_prefix

                    validate_prefix(
                        ctx.persistence.known_received, [list(item) for item in ctx.items_received]
                    )
                    generation = ctx.connection_generation
                if response.get('cosmetic_accepted'):
                    ctx.cosmetic(lambda: ctx.notifications.acknowledge(cosmetic_batch))
                if not bridge_up:
                    LOG.info('BizHawk Lua bridge connected on 127.0.0.1:%d', bridge.port)
                    if response.get('read_only'):
                        LOG.warning(
                            'Read-only SMB3 observer: genuine checks only; custom travel and RAM item delivery disabled. Items remain pending.'
                        )
                    bridge_up = True
                bridge_problem_reported = False
                for acknowledgement in response.get('acks', []):
                    index = acknowledgement['index']
                    result = acknowledgement['result']
                    if state.acknowledge(index, result):
                        ctx.store.save(state)
                        ctx.cosmetic(
                            lambda: ctx.notifications.applied(
                                index, ITEMS[state.items[index]]['name'], result
                            )
                        )
                        LOG.info(
                            '%s delivery index=%d %s; remaining=%s',
                            ITEMS.get(state.items.get(index), {'name': '1-Up'})['name'],
                            index,
                            result,
                            state.pending,
                        )
                checkpoint = response.get('checkpoint')
                if checkpoint is not None and checkpoint != state.travel:
                    if (
                        not isinstance(checkpoint, dict)
                        or checkpoint.get('session') != identity.key
                    ):
                        raise ValueError('Travel checkpoint identity mismatch')
                    previous_checkpoint = state.travel
                    state.travel = checkpoint
                    ctx.store.save(state)
                    if previous_checkpoint is None or previous_checkpoint.get(
                        'active'
                    ) != checkpoint.get('active'):
                        LOG.info(
                            'TRAVEL CHECKPOINT saved: World %d; seed/slot bound',
                            checkpoint['active'] + 1,
                        )
                if response.get('blocked') and (not warned_blocked):
                    LOG.error('Lua delivery blocked; inspect BizHawk Lua Console')
                    warned_blocked = True
                connected = ctx.server is not None and ctx.slot is not None
                if connected and (not ctx.goal_status_requested):
                    key = f'_read_client_status_{ctx.team}_{ctx.slot}'
                    await ctx.send_msgs(
                        [{'cmd': 'SetNotify', 'keys': [key]}, {'cmd': 'Get', 'keys': [key]}]
                    )
                    if (
                        ctx.identity != identity
                        or ctx.delivery is not state
                        or ctx.connection_generation != generation
                        or ctx.validation_error
                    ):
                        raise ValueError('AP owner changed during status query')
                    ctx.goal_status_requested = True
                reported = response.get('checks')
                if not isinstance(reported, list) or any(
                    (type(value) is not int for value in reported)
                ):
                    raise ValueError('Bridge checks must be an array of location IDs')
                if state.observe_checks(reported, ctx.checked_locations, ctx.location_ids):
                    ctx.store.save(state)
                if ctx.persistence:
                    await ctx.persistence.after_poll(ctx, bridge, identity, state, response)
                if (
                    ctx.identity != identity
                    or ctx.delivery is not state
                    or ctx.connection_generation != generation
                    or ctx.validation_error
                ):
                    raise ValueError('AP owner changed during checkpoint barrier')
                # Observations alone are insufficient: the coordinator must have saved them.
                if connected and (not ctx.persistence.closed):
                    publishable = ctx.persistence.publication_checks(
                        state, ctx.missing_locations, ctx.location_ids
                    )
                    due = new_location_checks(publishable, ctx.missing_locations, ctx.location_ids)
                    sent = await ctx.check_locations(due)
                    if (
                        ctx.identity != identity
                        or ctx.delivery is not state
                        or ctx.connection_generation != generation
                        or ctx.validation_error
                    ):
                        raise ValueError('AP owner changed during check publication')
                    if sent:
                        for location in sorted(sent):
                            LOG.info(
                                'Sent LocationChecks: %s (%d)',
                                ctx.smb3_location_names[location],
                                location,
                            )
                from ..shared.victory import satisfied

                airships = {
                    i
                    for i, r in location_signals.BY_ID.items()
                    if r['stage'] == 'airship' and r['world'] <= 7
                }
                if (
                    connected
                    and (not ctx.persistence.closed)
                    and (ctx.persistence.saved_physical >= set(state.physical_checks))
                    and (not ctx.finished_game)
                    and (not ctx.goal_confirmed)
                    and bridge.authorized
                    and bridge.journal
                    and satisfied(
                        ctx.goal,
                        ctx.persistence.goal_ending(bridge),
                        ctx.checked_locations,
                        ctx.location_ids,
                        airships,
                    )
                ):
                    ctx.persistence.store.authorize_publication(
                        ctx.persistence.run, ctx.persistence.saved_physical
                    )
                    LOG.info(
                        'AP GOAL CONDITIONS SATISFIED: %s; native ending and server checked locations',
                        ctx.goal,
                    )
                    if await ctx.send_goal(identity, state, generation):
                        ctx.finished_game = True
                        LOG.info('AP GOAL SUBMITTED; awaiting server confirmation')
            except BridgeUnavailable as exc:
                if bridge_up or not bridge_problem_reported:
                    LOG.warning('BizHawk Lua bridge unavailable; waiting to retry: %s', exc)
                    bridge_problem_reported = True
                bridge_up = False
            except (KeyError, TypeError, ValueError) as exc:
                LOG.error('Invalid bridge acknowledgement: %s', exc)
                await bridge.close()
                bridge_up = False
                ctx.exit_event.set()
        await asyncio.sleep(effect_poll_interval(ctx))


def effect_poll_interval(ctx):
    """Use the existing watcher more promptly while an indexed effect owns service.

    The same serialized watcher/epoch remains authority; no worker or durability
    ordering changes. Ordinary idle/queued-only games retain the accepted cadence.
    """
    delivery = getattr(ctx, 'delivery', None)
    records = getattr(delivery, 'effects', {}).get('records', {})
    return (
        0.01
        if any((r['state'] in ('scheduled', 'committed', 'activated') for r in records.values()))
        else 0.25
    )
