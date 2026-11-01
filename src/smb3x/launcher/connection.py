# SPDX-License-Identifier: MPL-2.0
"""launcher / connection implementation for managed SMB3X sessions."""
import asyncio
from ..shared.resources import RESOURCE_ROOT as ROOT

async def connected(store, run, live, control, components, build, session, server, password, port, process):
    from ..client.network import SMB3Context, server_loop
    from ..client.service import watcher
    from ..client.effects import EffectStore as StateStore
    from ..client.native_session import NativeBridge
    from ..client.persistence.coordinator import Coordinator
    from ..client.transport import BridgeUnavailable
    ctx = SMB3Context(server, password, session['slot_name'], session['seed_name'], StateStore(live / 'deliveries'))
    ctx.expected_palette_selection = build.get('m242_palettes', build.get('m241_palettes'))
    ctx.expected_r3_music = build.get('r3_music')
    ctx.expected_special_palettes = build.get('special_palette_selection')
    ctx.expected_placement = [build.get('world_pass_placement'), build.get('placement_policy')]
    ctx.expected_effects = build.get('effects')
    ctx.expected_trap_warning = build.get('trap_warning')
    ctx.expected_release = 'm27-1'
    bridge = NativeBridge(build, live / 'worlds', port=port, fatal=ctx.exit_event.set, run=run, token=control['token'])
    bridge.recovery_validator = store.epoch
    ctx.persistence = Coordinator(store, run, components)

    async def owned_process():
        while process.poll() is None and (not ctx.exit_event.is_set()):
            await asyncio.sleep(0.25)
        ctx.exit_event.set()
    monitor = asyncio.create_task(owned_process())
    tasks = [monitor]
    try:
        if components:
            for attempt in range(150):
                if process.poll() is not None:
                    raise ValueError('Emulator closed during restoration; latest checkpoint retained')
                try:
                    ready = await bridge.control('RESUME_READY')
                    if ready['witness'] != components['witness']:
                        raise ValueError('Restored native witness mismatch')
                    break
                except BridgeUnavailable:
                    await asyncio.sleep(0.2)
            else:
                raise ValueError('Paused emulator did not finish verified restoration; latest checkpoint retained')
        server_task = asyncio.create_task(server_loop(ctx))
        ctx.server_task = server_task
        watch = asyncio.create_task(watcher(ctx, bridge))
        exit_wait = asyncio.create_task(ctx.exit_event.wait())
        tasks.extend((server_task, watch, exit_wait))
        done, _ = await asyncio.wait((watch, exit_wait), return_when=asyncio.FIRST_COMPLETED)
        if watch in done:
            await watch
        if ctx.validation_error:
            raise ValueError(ctx.validation_error)
        return ctx.persistence.closed
    finally:
        ctx.server_address = ''
        ctx.disconnected_intentionally = True
        for task in (ctx.server_task, ctx.autoreconnect_task):
            if task is not None and task not in tasks:
                tasks.append(task)
        ctx.cancel_autoreconnect()
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
        ctx.server_task = None
        await bridge.close()
        await ctx.shutdown()
