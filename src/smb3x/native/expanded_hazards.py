# SPDX-License-Identifier: MPL-2.0
from ..planning import hazards as hazard_plan
'Apply the certified expanded hazard sources after stage and palette construction.'
from pathlib import Path
from .patches.expanded_poison import install
from .bps import make_bps, apply_bps
from .rom import digest
from ..shared.resources import RESOURCE_ROOT as ROOT
PATCH_VERSION = 'm243-native-1'

def expanded_hazards(source, identity, original, base, *args, **kwargs):
    poison = kwargs.get('poison_mushrooms', 'off')
    kwargs['poison_mushrooms'] = 'off'
    hazards = hazard_plan._expanded_plan(identity.seed, base['level_shuffle'], poison, kwargs.get('angry_sun', 'off'))
    if hazards['suns'] != base['hazards']['suns']:
        raise ValueError('Sun independence')
    target = bytearray(original)
    extension = install(target, source, base, hazards)
    target = bytes(target)
    config = {k: v for k, v in base.items() if k not in ('source', 'output', 'bps', 'prg_sha256', 'chr_sha256')}
    config.update(patch_version=PATCH_VERSION, hazards=hazards, m243_hazard_extension=extension, m243_sources={__file__.replace('\\', '/').rsplit('/', 1)[-1]: digest(Path(__file__).read_bytes())['sha256']})
    return (target, config)
