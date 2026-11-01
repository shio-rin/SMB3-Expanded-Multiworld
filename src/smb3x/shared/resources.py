# SPDX-License-Identifier: MPL-2.0
"""All runtime data is contained by this verified package root."""
from pathlib import Path
RESOURCE_ROOT = Path(__file__).resolve().parents[1]
PACKAGE_ROOT = RESOURCE_ROOT
DATA = RESOURCE_ROOT / "planning/data"
