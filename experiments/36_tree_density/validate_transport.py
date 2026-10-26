"""Offline failure injection: no network, no compute, no fitting."""
from pathlib import Path
import io,json,base64,hashlib,urllib.error
from unittest.mock import patch
with patch.object(Path,'read_text',return_value=' {"id":"test"}'):
 import transport as runtime
R=Path(__file__).resolve().parent;data=b'fixed evidence';good={'size':str(len(data)),'md5Hash':base64.b64encode(hashlib.md5(data).digest()).decode()}
def response(x):return io.BytesIO(json.dumps(x).encode())
def error(code):return urllib.error.HTTPError('https://example.invalid',code,'injected',{},None)
def check(events,expected_calls,raises=None):
 with patch.object(runtime,'token',return_value='fake'),patch.object(runtime.time,'sleep'),patch.object(runtime.urllib.request,'urlopen',side_effect=events) as op:
  if raises:
   try:runtime.upload('probe',data)
   except raises:pass
   else:raise AssertionError('Expected failure')
  else:runtime.upload('probe',data)
  assert op.call_count==expected_calls
check([response(good)],1)
check([error(503),response(good)],2) # lost success response
check([error(503),error(503),response(good)],3) # metadata transient
check([error(503),error(404),response(good)],3) # confirmed missing; retry create
check([error(412),response(good)],2) # existing identical object
check([error(503),error(403)],2,urllib.error.HTTPError) # do not blindly retry
check([error(503),response({'size':'2','md5Hash':'different'})],2,RuntimeError)
check([error(503)]+[error(503)]*5,6,urllib.error.HTTPError)
(R/'results/transport-preflight.json').write_text(json.dumps({'passed':True,'network_used':False,'cases':8,'checks':['success','uncertain success verified','transient metadata retried','confirmed missing then create','idempotent existing match','403 stops without retry','content mismatch stops','verification retries exhausted stops']},indent=2));print('TRANSPORT PREFLIGHT PASSED')
