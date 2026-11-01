# SPDX-License-Identifier: MPL-2.0
"""Development import of the same package used by the verified runtime."""
from pathlib import Path
__path__ = [str(Path(__file__).resolve().parents[1] / "src/smb3x")]
