# SPDX-License-Identifier: MPL-2.0
"""Bounded Windows replacement retry; no replay of native commands or receipts."""

from pathlib import Path
import json
import logging
import os
import tempfile
import time


def publish_directory(source, target):
    """Publish a verified sibling under the session lock; never rebuild or replace.

    Windows scanners can briefly hold files inside a preparation directory.
    Retry only this rename. Exhaustion retains the complete verified candidate.
    """
    source, target = Path(source), Path(target)
    if source.parent.resolve() != target.parent.resolve():
        raise ValueError('Prepared publication must use sibling directories')
    for attempt in range(5):
        if target.exists():
            raise FileExistsError('Prepared game already exists; it was not replaced')
        try:
            source.rename(target)
            return
        except OSError as exc:
            if getattr(exc, 'winerror', None) not in (5, 32, 33) or attempt == 4:
                raise OSError(
                    'Prepared game publication failed; the verified candidate was retained. Close software holding this new session, then reopen its player file.'
                ) from exc
            time.sleep((attempt + 1) * 0.03)


def save_json(target, value):
    """Flush a short sibling, then atomically replace; retain evidence on failure.

    Retry only replacement, never serialization or any native side effect.
    """
    target = Path(target)
    from ...shared.path_limits import validate_file_path

    validate_file_path(target)
    validate_file_path(target.parent / ('j-' + 'x' * 8 + '.pending'))
    target.parent.mkdir(parents=True, exist_ok=True)
    descriptor, name = tempfile.mkstemp(prefix='j-', suffix='.pending', dir=target.parent)
    with os.fdopen(descriptor, 'w', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, indent=2, sort_keys=True)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())
    for attempt in range(5):
        try:
            os.replace(name, target)
            return
        except OSError as exc:
            if getattr(exc, 'winerror', None) not in (5, 32, 33) or attempt == 4:
                raise OSError(
                    'Journal replacement failed; preserve runtime and the .pending file. No native operation was retried.'
                ) from exc
            logging.getLogger('SMB3.JOURNAL').warning(
                'Windows replacement blocked (code %s); retry %d/4', exc.winerror, attempt + 1
            )
            time.sleep((attempt + 1) * 0.03)
