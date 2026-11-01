# SPDX-License-Identifier: MPL-2.0
"""shared / serialization implementation for managed SMB3X sessions."""
from pathlib import Path
from zipfile import ZipFile
import asyncio, hashlib, json, logging, os, socket, subprocess, sys, time, uuid
from copy import deepcopy
from contextlib import contextmanager

def canonical(v):
    return json.dumps(v, sort_keys=True, separators=(',', ':')).encode()

def fingerprint(v):
    return hashlib.sha256(canonical(v)).hexdigest()

def read(p):
    return json.loads(Path(p).read_text(encoding='utf-8'))

def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()
