# SPDX-License-Identifier: MPL-2.0
"""Pool conservation, determinism and published effect identities."""
import runpy, unittest
from pathlib import Path
from collections import Counter
C=vars(__import__('smb3x.shared.effects',fromlist=['pool']))


class PoolTests(unittest.TestCase):
    def test_combined_budget_and_progression(self):
        names=['World 2 Pass']*11+['Super Mushroom']*26+['Super Leaf']*21+['1-Up']*67
        for seed in range(100):
            for mode in C['PERCENT']:
                for blessings in (False,True):
                    plan, audit=C['replacement_plan'](names,set(range(11)),mode,blessings,seed,1)
                    self.assertEqual(audit['traps'],47*C['PERCENT'][mode]//100)
                    self.assertEqual(audit['blessings'],2*blessings)
                    self.assertEqual(sum(audit['after'].values()),125)
                    for name in ('World 2 Pass','1-Up','Super Leaf'):
                        self.assertEqual(audit['before'][name],audit['after'][name])
                    self.assertEqual((plan,audit),C['replacement_plan'](names,set(range(11)),mode,blessings,seed,1))

    def test_registry_and_delay(self):
        from smb3x.shared.items import ITEMS
        self.assertEqual(len(ITEMS),28)
        self.assertFalse(C['RESERVED'] & ITEMS.keys())
        self.assertEqual(sum(v[2] for v in C['SPECS'].values()),4)
        values={C['delay_frames']('test',0,1,i,e) for i in range(125) for e in range(10)}
        self.assertEqual(values,set(range(240,1081,60)))

    def test_constrained_pool_never_replaces_other_filler(self):
        names=['Super Leaf']*8+['1-Up']*117
        _, audit=C['replacement_plan'](names,set(),'chaos',True,'x',1)
        self.assertEqual(audit['traps'],0)
        self.assertEqual(audit['after']['Super Leaf'],6)
        self.assertEqual(audit['after']['1-Up'],117)
        with self.assertRaises(ValueError):C['replacement_plan'](['1-Up']*125,set(),'chaos',True,'x',1)
