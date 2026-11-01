# SPDX-License-Identifier: MPL-2.0
"""Failure injection at Hybrid storage boundaries. Native State is mocked here."""
from copy import deepcopy
import unittest
from unittest.mock import patch
from smb3x.client.effects import EffectDelivery, EffectStore, empty, validate, extends, recovered
from smb3x.client.persistence.checkpoints import read, save_json, validate_prefix
from tests.test_checkpoints import AutoCheckpointTests


class EffectPersistenceTests(AutoCheckpointTests):
    def setUp(self):
        super().setUp()
        self.binding['effects']={'contract':'m25-effects-1'}
        self.store.binding=deepcopy(self.binding)
        # The base fixture has already created an epoch. Recreate its binding
        # only in this explicitly mocked, never-native test setup.
        from smb3x.client.persistence.checkpoints import fingerprint
        e=read(self.store.epochs);e['binding']=fingerprint(self.binding);save_json(self.store.epochs,e)
        self.effects=empty()

    def candidate(self):
        candidate,verification=super().candidate()
        from pathlib import Path
        folder=Path(candidate['path']);d=read(folder/'deliveries.json');c=read(folder/'controller.json')
        state=EffectDelivery(self.identity,registry=self.binding['registry']);state.overlay(self.effects)
        d=state.as_dict();c.update(schema=2,effects=deepcopy(self.effects),deathlink=deepcopy(getattr(self,'deaths',{'contract':'m25-deathlink-2','records':{}})))
        c['delivery']={k:d[k] for k in ('items','handled','pending')}
        save_json(folder/'deliveries.json',d);save_json(folder/'controller.json',c)
        save_json(folder/'server.json',dict(schema=1,received=self.effects['prefix']))
        return candidate,verification

    def test_previous_namespace_is_not_a_migration(self):
        from tests.test_controlled_checkpoint_fixture import CheckpointTests
        c,v=CheckpointTests.candidate(self)
        with self.assertRaises(ValueError):self.store.publish(c,v)

    def active(self):
        p=self.publish();self.store.activate_checkpoint(self.run,p['generation'])
        state=EffectDelivery(self.identity,registry=self.binding['registry'])
        state.receive([[0x534D3402,111,1,4],[0x534D3383,112,2,0],[0x534D3411,113,2,2]])
        self.store.persist_effects(self.run,state.effects)
        return state

    def test_old_map_new_completion_complete_extension_and_no_replay(self):
        state=self.active();state.schedule(2,1);state.commit(2,1,self.run,'room')
        self.store.persist_effects(self.run,state.effects)
        r=state.effects['records']['2']
        state.outcome(2,1,r['token'],'completed_noop','powered suit preserved')
        self.store.persist_effects(self.run,state.effects)
        run,derived,folder,m,c=self.store.resume()
        self.assertEqual(c['deliveries']['items'],{}) # immutable checkpoint untouched
        restored=EffectStore(derived/'deliveries').load(self.identity)
        restored.overlay(self.store.resume_effects)
        self.assertEqual(restored.pending,[1]) # ordinary intervening reward unissued
        self.assertEqual(restored.effects['records']['0']['state'],'queued')
        self.assertEqual(restored.effects['records']['2']['state'],'completed_noop')
        self.assertFalse(restored.receive(state.effects['prefix']))
        with self.assertRaises(ValueError):restored.schedule(2,2)

    def test_crashes_on_each_side_of_activation_commit(self):
        for stage in ('custody','scheduled','committed','activated','completed'):
            with self.subTest(stage=stage):
                state=self.active() if stage=='custody' else EffectDelivery(self.identity,registry=self.binding['registry'])
                if stage!='custody':state.receive([[0x534D3402,111,1,4]])
                if stage!='custody':state.schedule(0,1)
                if stage in ('committed','activated','completed'):state.commit(0,1,self.run,'room')
                if stage in ('activated','completed'):
                    r=state.effects['records']['0'];state.outcome(0,1,r['token'],stage,'native result')
                got=recovered(state.effects)['records']['0']['state']
                self.assertEqual(got,'queued' if stage in ('custody','scheduled') else 'completed' if stage=='completed' else 'disposed_interrupted')

    def test_commit_durability_failure_never_returns_permission(self):
        state=self.active();state.schedule(0,1);self.store.persist_effects(self.run,state.effects)
        before=self.store.epochs.read_bytes();state.commit(0,1,self.run,'room')
        with patch('smb3x.client.persistence.checkpoints.save_json',side_effect=OSError('injected disk failure')):
            with self.assertRaises(OSError):self.store.persist_effects(self.run,state.effects)
        self.assertEqual(before,self.store.epochs.read_bytes())
        self.store.resume();self.assertEqual(self.store.resume_effects['records']['0']['state'],'queued')

    def test_publication_cannot_drop_tail_and_atomic_fold(self):
        state=self.active();state.schedule(0,1);state.commit(0,1,self.run,'room')
        r=state.effects['records']['0'];state.outcome(0,1,r['token'],'completed','expired')
        self.store.persist_effects(self.run,state.effects)
        c,v=self.candidate()
        with self.assertRaises(ValueError):self.store.publish(c,v)
        self.effects=state.effects;c,v=self.candidate();original=save_json
        def fail_epoch(path,data):
            if path==self.store.epochs:raise OSError('injected epoch replacement')
            return original(path,data)
        with patch('smb3x.client.persistence.checkpoints.save_json',side_effect=fail_epoch):
            with self.assertRaises(OSError):self.store.publish(c,v)
        self.store.resume()
        self.assertEqual(self.store.resume_effects['records']['0']['state'],'completed')

    def test_foreign_tail_prefix_and_terminal_mutation_refuse(self):
        state=self.active();state.schedule(0,1);state.commit(0,1,self.run,'room')
        r=state.effects['records']['0'];state.outcome(0,1,r['token'],'completed','expired')
        self.store.persist_effects(self.run,state.effects)
        for field in ('item','location','player','flags'):
            bad=deepcopy(state.effects['prefix']);bad[0][('item','location','player','flags').index(field)]+=1
            with self.assertRaises(ValueError):validate_prefix(state.effects['prefix'],bad)
        bad=deepcopy(state.effects);bad['records']['0']['reason']='rewritten'
        with self.assertRaises(ValueError):self.store.persist_effects(self.run,bad)
        e=self.store.epoch();e['effects']['ancestor']['generation']='a'*32;save_json(self.store.epochs,e)
        with self.assertRaises(ValueError):self.store.resume()

    def test_death_origin_tail_survives_old_checkpoint_and_new_lifetime(self):
        from smb3x.client.deathlink import empty
        from tests.test_deathlink import record
        self.active()
        value=empty();value['records']['a'*64]=record('applied');value['records']['b'*64]=dict(record('committed'),network_id='b'*64)
        self.store.persist_deathlink(self.run,value)
        run,derived,folder,manifest,components=self.store.resume()
        self.assertEqual(components['controller']['deathlink']['records'],{})
        self.assertEqual(self.store.resume_deathlink['records']['a'*64]['state'],'applied')
        self.assertEqual(self.store.resume_deathlink['records']['b'*64]['state'],'disposed_interrupted')
        bad=deepcopy(value);bad['records']['a'*64]['state']='queued'
        with self.assertRaises(ValueError):self.store.persist_deathlink(run,bad)

    def test_burst_and_progression_do_not_wait_for_effect_activation(self):
        state=EffectDelivery(self.identity)
        rows=[[0x534D3403,100+i,1,4] for i in range(100)]+[[0x534D3382,201,2,1]]
        state.receive(rows)
        self.assertEqual(state.pending,[100]);self.assertEqual(state.unlock_mask,3)
        self.assertEqual(len(state.effects['records']),100)
        state.schedule(7,1);state.outcome(7,1,None,'queued','entry ended before commitment')
        self.assertEqual(len(state.effects['records']),100)
        with self.assertRaises(ValueError):state.schedule(8,1)

    def test_failure_before_custody_replays_complete_authoritative_prefix(self):
        p=self.publish();self.store.activate_checkpoint(self.run,p['generation'])
        rows=[[0x534D3402,111,1,4],[0x534D3382,112,2,1]]
        state=EffectDelivery(self.identity);state.receive(rows)
        before=self.store.epochs.read_bytes()
        with patch('smb3x.client.persistence.checkpoints.save_json',side_effect=OSError('before custody replacement')):
            with self.assertRaises(OSError):self.store.persist_effects(self.run,state.effects)
        self.assertEqual(before,self.store.epochs.read_bytes())
        self.store.resume();self.assertEqual(self.store.resume_effects['prefix'],[])
        restored=EffectDelivery(self.identity);restored.overlay(self.store.resume_effects);restored.receive(rows)
        self.assertEqual(restored.effects['records']['0']['state'],'queued')
        self.assertEqual(restored.pending,[1]);self.assertEqual(restored.unlock_mask,3)

    def test_ready_durability_failure_never_sends_bridge_permission(self):
        import asyncio
        from types import SimpleNamespace
        from unittest.mock import AsyncMock,Mock
        from smb3x.client.persistence.coordinator import Coordinator
        state=self.active();state.schedule(0,1);self.store.persist_effects(self.run,state.effects)
        bridge=SimpleNamespace(control=AsyncMock(return_value={'event':dict(type='ready',index=0,entry=1,area='1:1',sequence=7)}))
        projection=Mock();ctx=SimpleNamespace(store=projection)
        coordinator=Coordinator(self.store,self.run)
        with patch('smb3x.client.persistence.checkpoints.save_json',side_effect=OSError('ready commit failure')):
            with self.assertRaises(OSError):asyncio.run(coordinator.service_effects(ctx,bridge,state))
        self.assertEqual(bridge.control.await_count,1)
        self.assertNotIn('acknowledgement',bridge.control.await_args.kwargs)
        projection.save.assert_not_called()
        self.store.resume();self.assertEqual(self.store.resume_effects['records']['0']['state'],'queued')

    def test_cold_controller_contradiction_never_releases_input(self):
        import asyncio
        from types import SimpleNamespace
        from unittest.mock import AsyncMock,Mock
        from smb3x.client.persistence.coordinator import Coordinator
        state=self.active()
        run,derived,folder,manifest,components=self.store.resume()
        restored=EffectStore(derived/'deliveries').load(self.identity)
        ctx=SimpleNamespace(identity=self.identity,delivery=restored,connection_generation=1,validation_error=None,
            replay_ready=True,items_received=state.effects['prefix'],checked_locations=set(),store=Mock())
        bridge=SimpleNamespace(state_dir=derived,build={'session':'fixture','output':{'sha256':'fixture'},'progression':{'hammer_mode':'regional'}},
            control=AsyncMock(side_effect=[{'witness':components['witness'],'bridge_instance':'fresh'}, {'effects':empty()}]))
        coordinator=Coordinator(self.store,run,components)
        journal=Mock();journal.state={}
        with patch('smb3x.client.persistence.coordinator.NativeJournal',return_value=journal):
            with self.assertRaisesRegex(ValueError,'reconciliation mismatch'):asyncio.run(coordinator.before_poll(ctx,bridge))
        self.assertEqual([c.args[0]for c in bridge.control.await_args_list],['RESUME_READY','RECONCILE_EFFECTS'])
        self.assertEqual(self.store.epoch()['state'],'restoring')


if __name__=='__main__':unittest.main()
