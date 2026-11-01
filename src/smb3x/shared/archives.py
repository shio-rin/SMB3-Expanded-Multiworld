# SPDX-License-Identifier: MPL-2.0
"""Deterministic owned patch archives."""
from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED

def write_zip(path, files):
    with ZipFile(path, 'x', compression=ZIP_DEFLATED, compresslevel=9) as archive:
        for name, data in sorted(files.items()):
            info = ZipInfo(name, (2026, 10, 27, 0, 0, 0))
            info.compress_type = ZIP_DEFLATED
            info.external_attr = 33188 << 16
            archive.writestr(info, data, compresslevel=9)
