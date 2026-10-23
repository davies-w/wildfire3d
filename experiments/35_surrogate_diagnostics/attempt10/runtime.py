"""Immutable, content-verified cloud output upload; transport retry is not a job retry."""
import json,urllib.request,urllib.parse,urllib.error,time,hashlib,base64
PREFIX='diagnostics35/attempt10/';BUCKET='tmrw-wildfire-20261015-trial'
def token():
 r=urllib.request.Request('http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/token',headers={'Metadata-Flavor':'Google'})
 return json.load(urllib.request.urlopen(r,timeout=20))['access_token']
def upload(name,data):
 object_name=PREFIX+name;md5=base64.b64encode(hashlib.md5(data).digest()).decode()
 for attempt in range(3):
  auth={'Authorization':'Bearer '+token()};url='https://storage.googleapis.com/upload/storage/v1/b/'+BUCKET+'/o?uploadType=media&ifGenerationMatch=0&name='+urllib.parse.quote(object_name,safe='')
  try:
   result=json.load(urllib.request.urlopen(urllib.request.Request(url,data=data,headers={**auth,'Content-Type':'application/octet-stream'},method='POST'),timeout=180));assert result['md5Hash']==md5;return
  except Exception as original:
   # Investigate an uncertain upload result before retrying; never overwrite existing evidence.
   meta='https://storage.googleapis.com/storage/v1/b/'+BUCKET+'/o/'+urllib.parse.quote(object_name,safe='')
   try:
    found=json.load(urllib.request.urlopen(urllib.request.Request(meta,headers=auth),timeout=30))
    if found['md5Hash']==md5 and int(found['size'])==len(data):return
    raise RuntimeError('Immutable cloud object has different content: '+object_name) from original
   except urllib.error.HTTPError as missing:
    if missing.code!=404:raise
   if attempt==2:raise original
   time.sleep(2**attempt)
