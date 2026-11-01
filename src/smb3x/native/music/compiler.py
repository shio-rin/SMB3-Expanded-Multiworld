# SPDX-License-Identifier: MPL-2.0
"""Bind the immutable accepted compiler to this resource-owned package.

The external private catalogue pins the complete original compiler source hash.
Do not change that file, its hash, musical logic or pack validation. These two
imports are its only absolute project imports; bind exactly their four symbols
here and execute the identical definitions. This is not a general import hook.
"""
from pathlib import Path
import hashlib
from .score.arrangement import compile_arrangement as compile_legacy
from .score.score import DURATIONS, CHANNELS, require

_path=Path(__file__).with_name('certified_compiler.py')
_source=_path.read_bytes().replace(b'\r\n',b'\n')
if hashlib.sha256(_source).hexdigest()!='a4cf514ca98ee3510ba9bf9972672d7fe0c03e1f3e51f9e911760ee026c48065':
    raise ValueError('Private music compiler identity mismatch')
for _statement in (b'from tools.music_m20.arrangement import compile_arrangement as compile_legacy',b'from tools.music_m20.score import DURATIONS, CHANNELS, require'):
    if _source.count(_statement)!=1:raise ValueError('Private compiler import binding changed')
    _source=_source.replace(_statement,b'# Symbols bound by the SMB3X package adapter above')
exec(compile(_source,str(_path),'exec'),globals())
