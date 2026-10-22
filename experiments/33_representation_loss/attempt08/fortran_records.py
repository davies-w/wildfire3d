"""Little-endian 4-byte Fortran records used by the pinned FDS Linux build."""
import struct
import numpy as np
class FortranEOFError(EOFError):pass
class FortranFile:
 def __init__(self,path):self.f=open(path,'rb')
 def read_record(self,dtype):
  head=self.f.read(4)
  if not head:raise FortranEOFError()
  assert len(head)==4
  n=struct.unpack('<I',head)[0];data=self.f.read(n);tail=self.f.read(4)
  assert len(data)==n and len(tail)==4 and struct.unpack('<I',tail)[0]==n
  return np.frombuffer(data,dtype=np.dtype(dtype).newbyteorder('<')).copy()
 def read_ints(self,dtype='i4'):return self.read_record(dtype)
 def read_reals(self,dtype='f4'):return self.read_record(dtype)
 def __del__(self):self.f.close()
