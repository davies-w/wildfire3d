"""Resolve FDS samples with its exact ELF/DWARF; keep stripped libraries at module level.
Format: https://gperftools.github.io/gperftools/cpuprofile-fileformat.html
"""
import struct,re,json,bisect,collections,hashlib
from pathlib import Path
from elftools.elf.elffile import ELFFile
ROOT=Path(__file__).resolve().parent

def read_profile(path):
 b=path.read_bytes();header=struct.unpack_from('<5Q',b);assert header[0]==0 and header[1]>=3 and header[2]==0
 pos=(2+header[1])*8;records=[]
 while True:
  count,depth=struct.unpack_from('<2Q',b,pos);pos+=16
  pcs=struct.unpack_from('<'+'Q'*depth,b,pos);pos+=8*depth
  if count==0 and depth==1 and pcs[0]==0:break
  assert count>0 and 0<depth<1000;records.append((count,pcs))
 maps=[]
 for line in b[pos:].decode(errors='replace').splitlines():
  m=re.match(r'([0-9a-f]+)-([0-9a-f]+)\s+(\S+)\s+([0-9a-f]+)\s+\S+\s+\S+\s*(.*)',line)
  if m:maps.append((int(m[1],16),int(m[2],16),int(m[4],16),m[5]))
 return header[3],records,maps

class Resolver:
 def __init__(self,path):
  self.f=path.open('rb');self.elf=ELFFile(self.f);self.dwarf=self.elf.get_dwarf_info();self.aranges=self.dwarf.get_aranges();self.lines={}
  self.symbols=sorted((int(s['st_value']),int(s['st_size']),s.name) for s in self.elf.get_section_by_name('.symtab').iter_symbols() if s['st_info']['type']=='STT_FUNC' and s['st_size']>0)
  self.starts=[x[0] for x in self.symbols]
 def function(self,pc):
  ix=bisect.bisect_right(self.starts,pc)-1
  if ix>=0:
   start,size,name=self.symbols[ix]
   if pc<start+size:return name
  return 'FDS unresolved'
 def line(self,pc):
  offset=self.aranges.cu_offset_at_addr(pc)
  if offset is None:return '?'
  if offset not in self.lines:
   cu=self.dwarf.get_CU_at(offset);lp=self.dwarf.line_program_for_CU(cu);segments=[];previous=None
   for entry in lp.get_entries():
    s=entry.state
    if s is None:continue
    if previous is not None and s.address>previous.address:
     idx=previous.file if lp.header.version>=5 else previous.file-1
     try:name=lp.header.file_entry[idx].name.decode()
     except (IndexError,AttributeError):name='?'
     segments.append((previous.address,s.address,f'{name}:{previous.line}'))
    previous=None if s.end_sequence else s
   segments.sort();self.lines[offset]=([s[0] for s in segments],segments)
  starts,segments=self.lines[offset];i=bisect.bisect_right(starts,pc)-1
  return segments[i][2] if i>=0 and pc<segments[i][1] else '?'

def main():
 (ROOT/'results/profiles').mkdir(parents=True,exist_ok=True)
 binary=ROOT/'data/binary/fds';resolver=Resolver(binary);digest=hashlib.sha256(binary.read_bytes()).hexdigest()
 for path in sorted((ROOT/'data/cloud').glob('*/cpu.prof')):
  case=path.parent.name;metadata=json.loads((path.parent/'result.json').read_text());assert metadata['binary_sha256']==digest
  period,records,maps=read_profile(path);starts=[m[0] for m in maps]
  def resolve(pc):
   i=bisect.bisect_right(starts,pc)-1
   if i<0 or pc>=maps[i][1]:return 'unmapped',None
   start,end,offset,name=maps[i]
   return ('FDS',pc-start+offset) if name=='/usr/local/bin/fds' else (Path(name).name or 'anonymous',None)
  total=sum(n for n,_ in records);modules=collections.Counter();flat=collections.Counter();cumulative=collections.Counter();lines=collections.Counter();openmp_context=collections.Counter()
  for n,pcs in records:
   module,pc=resolve(pcs[0]);modules[module]+=n
   if module=='FDS':flat[resolver.function(pc)]+=n;lines[resolver.line(pc)]+=n
   if 'libgomp' in module:
    caller='OpenMP runtime with no FDS caller in captured stack'
    for address in pcs[1:]:
     cm,cp=resolve(address-1)
     if cm=='FDS':caller=resolver.function(cp)+' @ '+resolver.line(cp);break
    openmp_context[caller]+=n
   seen=set()
   for frame_index,address in enumerate(pcs):
    module,pc=resolve(address-(frame_index>0))
    if module=='FDS':seen.add(resolver.function(pc))
   for name in seen:cumulative[name]+=n
  def table(counter):return [{'name':name,'samples':n,'percent_all_cpu_samples':100*n/total} for name,n in counter.most_common(50)]
  result=dict(case=case,total_samples=total,sample_period_us=period,sampled_cpu_s=total*period/1e6,os_cpu_s=metadata['cpu_user_s']+metadata['cpu_system_s'],modules=table(modules),openmp_context=table(openmp_context),fds_flat=table(flat),fds_cumulative=table(cumulative),fds_lines=table(lines),caveat='Library attribution only for stripped shared objects. Flat samples are exclusive; cumulative rows overlap. Optimized source-line attribution includes inlining.')
  (ROOT/'results/profiles'/f'symbolized-{case}.json').write_text(json.dumps(result,indent=2)+'\n')
  print(case,'samples',total,'modules',table(modules)[:4],'lines',table(lines)[:4])
if __name__=='__main__':main()
