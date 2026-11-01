# SPDX-License-Identifier: MPL-2.0
"""Sequenced loopback transport. Retried requests retain the original run, token and sequence."""

from __future__ import annotations
import asyncio
import json
import logging
from copy import deepcopy

LOG = logging.getLogger(__name__)


class BridgeUnavailable(ConnectionError):
    pass


class LuaBridge:

    def __init__(self, build, *, run, token, host='127.0.0.1', port=43210):
        self.host, self.port = (host, port)
        self.reader = self.writer = None
        self.build = build
        self.run, self.token = (run, token)
        self.last_response = None
        self.sequence = 0
        self.transport_instance = None
        self.wire = 40 if 'effects' in build else 39
        self.exchange_lock = asyncio.Lock()
        self.recovery_validator = None

    async def close(self) -> None:
        writer, self.writer = (self.writer, None)
        self.reader = None
        if writer is not None:
            writer.close()
            try:
                await asyncio.shield(writer.wait_closed())
            except OSError:
                pass

    response_notice_seconds = 3

    async def receive(self):
        pending = asyncio.create_task(self.reader.readline())
        try:
            try:
                line = await asyncio.wait_for(asyncio.shield(pending), self.response_notice_seconds)
            except asyncio.TimeoutError:
                LOG.info('Waiting for BizHawk Lua servicing; exact outstanding request retained')
                line = await pending
                LOG.info('BizHawk Lua servicing resumed; original response received')
        finally:
            if not pending.done():
                pending.cancel()
                await asyncio.gather(pending, return_exceptions=True)
        if not line:
            raise ConnectionError('Local Lua socket closed')
        if len(line) > 1048576:
            raise ValueError('Oversized Lua response')
        return json.loads(line)

    async def exchange(self, request):
        async with self.exchange_lock:
            epoch = deepcopy(self.recovery_validator()) if self.recovery_validator else None
            self.sequence += 1
            request = {
                **request,
                'protocol': self.wire,
                'run': self.run,
                'token': self.token,
                'sequence': self.sequence,
            }
            attempted = False
            reported = False
            refused = 0
            try:
                while True:
                    try:
                        if self.writer is None:
                            self.reader, self.writer = await asyncio.wait_for(
                                asyncio.open_connection(self.host, self.port, limit=1048576), 1
                            )
                        refused = 0
                        attempted = True
                        self.writer.write(
                            json.dumps(request, separators=(',', ':')).encode() + b'\n'
                        )
                        await self.writer.drain()
                        result = await self.receive()
                        if (
                            result.get('protocol') != self.wire
                            or result.get('session') != request['session']
                        ):
                            raise ValueError('wire/session mismatch')
                        if result.get('error') or result.get('blocked'):
                            raise ValueError(result.get('error') or 'Managed Lua bridge blocked')
                        instance = result.get('bridge_instance')
                        if not isinstance(instance, str) or not 1 <= len(instance) <= 512:
                            raise ValueError('Missing/invalid Lua lifetime identity')
                        if (
                            self.transport_instance is not None
                            and instance != self.transport_instance
                        ):
                            raise ValueError(
                                'Lua lifetime changed; retained transport recovery forbidden'
                            )
                        self.transport_instance = instance
                        if result.get('suspension'):
                            if (
                                epoch is None
                                or self.recovery_validator() != epoch
                                or epoch.get('run') != self.run
                            ):
                                raise ValueError(
                                    'Retained transport recovery lost durable run/epoch ownership'
                                )
                            request['resume_transport'] = result['suspension']['challenge']
                            continue
                        if result.get('sequence') != self.sequence:
                            raise ValueError('Stale/out-of-order Lua response')
                        self.last_response = result
                        return result
                    except (OSError, asyncio.TimeoutError) as exc:
                        request.pop('resume_transport', None)
                        await self.close()
                        if not attempted:
                            self.sequence -= 1
                            raise BridgeUnavailable(str(exc)) from exc
                        if isinstance(exc, ConnectionRefusedError):
                            refused += 1
                            if refused >= 20:
                                raise ValueError(
                                    'Lua listener stopped; retained emulator is paused. Reopen the player file for verified checkpoint recovery.'
                                ) from exc
                        if not reported:
                            LOG.warning(
                                'Local bridge suspended; retaining request %s for same-lifetime reconciliation: %s',
                                self.sequence,
                                exc,
                            )
                            reported = True
                        await asyncio.sleep(0.25)
            except asyncio.CancelledError:
                await self.close()
                raise

    async def control(self, op, **values):
        return await self.exchange(
            dict(type='CHECKPOINT', session=self.build['session'], op=op, **values)
        )
