"""Immutable upload with verified uncertain outcomes and bounded transient retries."""
import json,urllib.request,urllib.parse,urllib.error,time,hashlib,base64
PREFIX='diagnostics35/attempt17/';BUCKET='tmrw-wildfire-20261015-trial'
TRANSIENT={408,429,500,502,503,504}
def token():
 r=urllib.request.Request('http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/token',headers={'Metadata-Flavor':'Google'})
 return json.load(urllib.request.urlopen(r,timeout=20))['access_token']
def object_metadata(name):
 url='https://storage.googleapis.com/storage/v1/b/'+BUCKET+'/o/'+urllib.parse.quote(PREFIX+name,safe='')
 for attempt in range(5):
  try:
   return json.load(urllib.request.urlopen(urllib.request.Request(url,headers={'Authorization':'Bearer '+token()}),timeout=30))
  except urllib.error.HTTPError as e:
   if e.code==404:return None
   if e.code not in TRANSIENT or attempt==4:raise
  except (TimeoutError,urllib.error.URLError):
   if attempt==4:raise
  time.sleep(min(2**attempt,16))
def matches(found,data):return found is not None and found.get('md5Hash')==base64.b64encode(hashlib.md5(data).digest()).decode() and int(found['size'])==len(data)
def upload(name,data):
 url='https://storage.googleapis.com/upload/storage/v1/b/'+BUCKET+'/o?uploadType=media&ifGenerationMatch=0&name='+urllib.parse.quote(PREFIX+name,safe='')
 for attempt in range(5):
  try:
   result=json.load(urllib.request.urlopen(urllib.request.Request(url,data=data,headers={'Authorization':'Bearer '+token(),'Content-Type':'application/octet-stream'},method='POST'),timeout=180))
   assert matches(result,data),'Upload digest mismatch';return
  except (urllib.error.URLError,TimeoutError) as error:
   # Do not issue another upload while the outcome is unknown. GET itself retries
   # transient errors. Missing permission or exhausted verification stops safely.
   found=object_metadata(name)
   if found is not None:
    if matches(found,data):return
    raise RuntimeError('Immutable object contains different bytes: '+name) from error
   if isinstance(error,urllib.error.HTTPError) and error.code not in TRANSIENT|{412}:raise
   if attempt==4:raise
   time.sleep(min(2**attempt,16))
