"""No network/solver tests: execute the generated epoch with simulated cloud APIs."""
import copy
import json
import math
import re
import unittest
from types import SimpleNamespace
from urllib.parse import unquote
from pathlib import Path
import yaml
from build import build
from pool import Pool

class Obj(dict):
    def __getattr__(self,k):
        try: return self[k]
        except KeyError: raise AttributeError(k) from None
    def __setattr__(self,k,v): self[k]=v

def wrap(v):
    if isinstance(v,dict): return Obj({k:wrap(x) for k,x in v.items()})
    if isinstance(v,list): return [wrap(x) for x in v]
    return v

def lookup(m,k):
    for key in k if isinstance(k,list) else [k]:
        if not isinstance(m,dict): return None
        m=m.get(key)
    return m

class Jump(Exception): pass
class Done(Exception): pass

class Cloud:
    def __init__(self, durations, allowance=100000000, failures=(), ordinary=()):
        self.durations=durations; self.limit=allowance; self.failures=set(failures); self.ordinary=set(ordinary)
        self.now=0; self.jobs={}; self.objects={}; self.submissions=[]; self.peak=0
        self.ambiguous=False; self.canary_approved=True
    def call(self,name,args):
        if name=='sys.sleep': self.now+=args['seconds']; return None
        url=args['url']; query=args.get('query',{})
        if name=='http.post' and 'storage.googleapis' in url:
            key=query['name']
            if key in self.objects: raise RuntimeError('Immutable claim conflict')
            self.objects[key]=copy.deepcopy(args['body']); return {'body':{}}
        if name=='http.post':
            a=json.loads(args['body']['argument']); i=a['index']; n='execution/'+str(i)
            if n in self.jobs: raise AssertionError('duplicate paid submission')
            self.jobs[n]={'i':i,'end':self.now+self.durations[i]}
            self.submissions.append((i,self.now))
            self.peak=max(self.peak,sum(j['end']>self.now for j in self.jobs.values()))
            if self.ambiguous: raise RuntimeError('POST response lost after acceptance')
            return {'body':{'name':n}}
        if 'workflowexecutions' in url:
            j=self.jobs[url.split('/v1/')[1]]; i=j['i']
            if self.now<j['end']: return {'body':{'state':'ACTIVE'}}
            return {'body':{'state':'SUCCEEDED','result':json.dumps({'passed':i not in self.failures,'count':1,'wave':'wave-'+str(i),'cleanup_verified':True,'compute_charge_upper_usd':.01,'spot':i in self.failures and i not in self.ordinary,'started':True})}}
        path=unquote(url.split('/o/')[1])
        if path.endswith('admission-v4.json'): body={'passed':True,'compute_limit_usd':self.limit/1000000}
        elif '/inputs/items/' in path:
            i=int(path.rsplit('/',1)[1].split('.')[0]); body={'index':i,'id':'wave-'+str(i),'count':1}
        elif path.endswith('canary-approved.json'): body={'passed':self.canary_approved,'case':'case0','archive_verified':True,'batch_succeeded':True,'cleanup_verified':True}
        elif '/started/' in path: body={'started':True}
        else: raise AssertionError(url)
        return {'body':body}

class Engine:
    """Small test interpreter for the emitted epoch's control-flow subset.
    Does not claim to replace Google Cloud's compiler/readiness validation.
    """
    def __init__(self,cloud,state):
        self.cloud=cloud
        self.env={'args':wrap({'state':copy.deepcopy(state)}),'true':True,'false':False,'null':None,
          'int':int,'string':str,'len':len,'keys':lambda d:list(sorted(d)),
          'default':lambda v,d:d if v is None else v,
          'map':SimpleNamespace(get=lookup,delete=lambda d,k:wrap({x:v for x,v in d.items() if x!=k})),
          'math':math,'json':SimpleNamespace(decode=lambda s:wrap(json.loads(s)),encode_to_string=json.dumps),
          'text':SimpleNamespace(url_encode=lambda s:s),
          'sys':SimpleNamespace(get_env=lambda s:'test-execution')}
        self.steps=0
    def val(self,x):
        if isinstance(x,str) and x.startswith('${'):
            return wrap(eval(x[2:-1],{'__builtins__':{}},self.env))
        if isinstance(x,dict): return wrap({k:self.val(v) for k,v in x.items()})
        if isinstance(x,list): return [self.val(v) for v in x]
        return x
    def block(self,steps):
        labels={next(iter(s)):i for i,s in enumerate(steps)}; i=0
        while i<len(steps):
            try: self.node(next(iter(steps[i].values())))
            except Jump as e:
                dest=e.args[0]
                if dest not in labels: raise
                i=labels[dest]; continue
            i+=1
    def node(self,n):
        self.steps+=1
        if self.steps>90000: raise AssertionError('step budget exceeded')
        if 'assign' in n:
            for a in n['assign']:
                k,x=next(iter(a.items())); self.env['_value']=self.val(x)
                exec(k+' = _value',{'__builtins__':{}},self.env)
        if 'call' in n:
            result=self.cloud.call(n['call'],self.val(n.get('args',{})))
            if 'result' in n: self.env[n['result']]=wrap(result)
        if 'try' in n: self.node(n['try'])  # tests use no GET failures/retries
        if 'steps' in n: self.block(n['steps'])
        if 'switch' in n:
            for branch in n['switch']:
                if self.val(branch['condition']): self.node(branch); break
        if 'for' in n:
            f=n['for']
            for v in self.val(f['in']):
                self.env[f['value']]=v
                try: self.block(f['steps'])
                except Jump as e:
                    if e.args[0]=='continue': continue
                    if e.args[0]=='break': break
                    raise
        if 'raise' in n: raise RuntimeError(self.val(n['raise']))
        if 'return' in n: raise Done(self.val(n['return']))
        if 'next' in n: raise Jump(n['next'])
    def run(self):
        try: self.block(build()['epoch.yaml']['main']['steps'])
        except Done as d: return d.args[0]
        raise AssertionError('missing return')

def state(n,limit=100000000):
    return dict(epoch=0,cursor=0,total=n,active={},spent=0,limit=limit,reserve=525000,started=0,evicted=0,policy=480,completed=0,interrupted=0,canary_approved=True,canary_case="case0",stopped=False,audit_required=False)

class GeneratedControllerTests(unittest.TestCase):
    def test_fast_cases_refill_while_first_case_still_running(self):
        c=Cloud([1800]+[30]*53); s=Engine(c,state(54)).run()
        while s.active: s=Engine(c,s).run()
        self.assertEqual(s.completed,54)
        self.assertLess(dict(c.submissions)[18],1800)
        self.assertEqual(dict(c.submissions)[18],30)
        self.assertLessEqual(c.peak,18)
    def test_epoch_handoff_keeps_running_cases_and_no_duplicate(self):
        c=Cloud([4000]*18+[30]*18); s=state(36)
        s=Engine(c,s).run(); self.assertEqual(len(s.active),18)
        self.assertEqual(len(c.submissions),18)
        while s.active or s.cursor<s.total: s=Engine(c,s).run()
        self.assertEqual(len(c.submissions),36); self.assertEqual(s.completed,36)
    def test_large_instant_queue_bounded_steps_per_epoch(self):
        c=Cloud([0]*2000); s=wrap(state(2000))
        while s.active or s.cursor<s.total:
            e=Engine(c,s); s=e.run()
            self.assertLess(e.steps,60000)
        self.assertEqual(s.completed,2000)
        self.assertEqual(len(c.submissions),2000)
    def test_policy_markers_match_worker_contract(self):
        import sys
        sys.path.append(str(Path(__file__).resolve().parents[1]))
        from checkpoint_control import CheckpointControl
        markers={480:{'run_id':'fds-tree51-campaign01','checkpoint_seconds':480},
                 300:{'run_id':'fds-tree51-campaign01','checkpoint_seconds':300}}
        control=CheckpointControl(read=markers.get)
        control.preflight(); self.assertEqual(control.interval(),300)
        text=yaml.safe_dump(build()['parent.yaml'])
        self.assertIn('control/480.json',text); self.assertIn('run_id: __RUN__',text)
    def test_budget_stops_without_claiming_unfunded_work(self):
        c=Cloud([30]*100,allowance=550000); s=Engine(c,state(100,550000)).run()
        self.assertEqual(len(c.submissions),3)
        self.assertEqual(s.spent,30000); self.assertFalse(s.active)
    def test_lost_post_reply_is_never_retried(self):
        c=Cloud([30]*2); c.ambiguous=True; s=state(2)
        with self.assertRaisesRegex(RuntimeError,'response lost'): Engine(c,s).run()
        self.assertEqual(len(c.submissions),1)
        with self.assertRaisesRegex(RuntimeError,'claim conflict'): Engine(c,s).run()
        self.assertEqual(len(c.submissions),1)
    def test_spot_failure_preserved_and_other_cases_continue_without_retry(self):
        c=Cloud([30]*40,failures=(1,2,3,4)); s=Engine(c,state(40)).run()
        self.assertFalse(s.stopped); self.assertFalse(s.active)
        self.assertEqual(len(c.submissions),40)
        self.assertEqual(s.completed,36); self.assertEqual(s.interrupted,4); self.assertEqual(s.policy,180)
    def test_ordinary_failure_stops_admission_and_drains(self):
        c=Cloud([30]*40,failures=(0,),ordinary=(0,)); s=Engine(c,state(40)).run()
        self.assertTrue(s.stopped); self.assertFalse(s.active)
        self.assertEqual(len(c.submissions),18); self.assertEqual(s.completed,17)
        self.assertEqual(s.policy,480); self.assertEqual(s.interrupted,0)
    def test_canary_blocks_bulk_until_independent_gate(self):
        c=Cloud([30]*40); c.canary_approved=False; initial=state(40); initial['canary_approved']=False
        s=Engine(c,initial).run(); self.assertEqual(len(c.submissions),1); self.assertEqual(s.completed,1)
        c.canary_approved=True
        while s.active or s.cursor<s.total: s=Engine(c,s).run()
        self.assertEqual(len(c.submissions),40)
    def test_generated_files_equal_builder_and_expression_bounds(self):
        for filename,doc in build().items():
            self.assertEqual(yaml.safe_load((Path(__file__).parent/filename).read_text()),doc)
            def walk(x):
                if isinstance(x,dict):
                    for v in x.values(): walk(v)
                elif isinstance(x,list):
                    for v in x: walk(v)
                elif isinstance(x,str) and x.startswith('${'): self.assertLessEqual(len(x)-3,400,x)
            walk(doc)
    def test_step_names_unique_within_each_routine(self):
        for doc in build().values():
            for routine in doc.values():
                seen=set()
                def walk(x):
                    if isinstance(x,dict):
                        for k,v in x.items():
                            if k=='steps':
                                for step in v:
                                    name=next(iter(step)); self.assertNotIn(name,seen); seen.add(name)
                            walk(v)
                    elif isinstance(x,list):
                        for v in x: walk(v)
                walk(routine)
    def test_claim_before_post_and_cleanup_isolation(self):
        docs=build(); epoch=docs['epoch.yaml']['main']['steps']
        names=[next(iter(s)) for s in epoch]
        self.assertLess(names.index('intent'),names.index('submit'))
        case=docs['case.yaml']; txt=yaml.safe_dump(case)
        self.assertNotIn('fds-tree51-campa.*',txt)
        self.assertIn('labels.trial_id = ',txt)
        self.assertIn('Foreign resource',txt)
        def walk(x):
            if isinstance(x,dict):
                if x.get('call')=='http.post': self.assertNotIn('retry',x)
                if isinstance(x.get('try'),dict) and x['try'].get('call')=='http.post':
                    args=x['try']['args']
                    self.assertEqual(args['url'],'https://storage.googleapis.com/upload/storage/v1/b/tmrw-wildfire-20261015-trial/o')
                    self.assertIn('/job-status.json',args['query']['name'])
                    self.assertEqual(args['query']['ifGenerationMatch'],0)
                    self.assertEqual(args['body'],'${state.body}')
                for v in x.values(): walk(v)
            elif isinstance(x,list):
                for v in x: walk(v)
        walk(docs)

class PackagingTests(unittest.TestCase):
    def test_exact_deck_singleton_and_recovery_rejection(self):
        from prepare_rolling import singleton
        import hashlib
        deck='&HEAD CHID="case" /'
        payload={'groups.json':json.dumps({'wave':[{'pilot_case':'a','deck_sha256':hashlib.sha256(deck.encode()).hexdigest()}]}),'decks/a.fds':deck,'decks/b.fds':'other','worker.py':'untouched'}
        out=singleton(payload,'a','t51r05')
        self.assertEqual(out['decks/a.fds'],deck); self.assertNotIn('decks/b.fds',out)
        self.assertEqual(out['worker.py'],'untouched')
        with self.assertRaises(ValueError): singleton(dict(payload,**{'recovery.json':'{}'}),'a','t51r05')
    def test_rendered_bootstrap_has_only_future_namespace(self):
        from prepare_rolling import render
        import base64
        rendered=render('t51r05')
        for text in rendered.values():
            self.assertNotIn('__RUN__',text); self.assertNotIn('campaign04',text)
        encoded=re.search("b64decode\\('([^']+)'",rendered['case.yaml']).group(1)
        boot=base64.b64decode(encoded).decode()
        self.assertNotIn('__RUN__',boot); self.assertIn('tree51/t51r05/',boot)
        with self.assertRaises(ValueError): render('fds-tree51-campaign04')

class AccountingTests(unittest.TestCase):
    def test_cleanup_unverified_retains_slot_and_money(self):
        p=Pool(['a','b'],525000); p.admit()
        with self.assertRaises(ValueError): p.finish('a',charge=1,cleanup=False,passed=True,started=True)
        self.assertIn('a',p.active); self.assertEqual(p.admit(),[])
    def test_double_settlement_rejected(self):
        p=Pool(['a'],525000); p.admit(); p.finish('a',charge=1,cleanup=True,passed=True,started=True)
        with self.assertRaises(ValueError): p.finish('a',charge=1,cleanup=True,passed=True,started=True)
    def test_ordinary_failure_not_eviction(self):
        p=Pool(['a'],525000); p.admit(); p.finish('a',charge=1,cleanup=True,passed=False,started=True)
        self.assertEqual(p.checkpoint_seconds,480); self.assertEqual(p.evictions,0)
    def test_duplicate_manifest_rejected(self):
        with self.assertRaises(ValueError): Pool(['a','a'],525000)

if __name__=='__main__': unittest.main(verbosity=2)
