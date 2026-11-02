import io,struct,unittest
import numpy as np
from extract_training import record,read_temperature

def rec(b):return struct.pack('<I',len(b))+b+struct.pack('<I',len(b))
class DecoderTests(unittest.TestCase):
    def test_temperature_grid_and_times(self):
        shape=(49,33,33);a=np.arange(np.prod(shape),dtype='<f4').reshape(shape)
        data=b''.join(rec(x) for x in [b'TEMPERATURE',b'TEMP',b'C',np.array([0,48,0,32,0,32],dtype='<i4').tobytes()])
        for t in [0.,2.125]:data+=rec(np.array([t],dtype='<f4').tobytes())+rec(a.tobytes(order='F'))
        rows=list(read_temperature(io.BytesIO(data),[0,0,0]));self.assertEqual([x[0] for x in rows],[0,2.125]);np.testing.assert_array_equal(rows[0][1],a[1:,1:,1:].reshape(-1))
    def test_bad_record_rejected(self):
        with self.assertRaises(AssertionError):record(io.BytesIO(struct.pack('<I',4)+b'abcd'+struct.pack('<I',3)))
    def test_wrong_quantity_rejected(self):
        with self.assertRaises(AssertionError):list(read_temperature(io.BytesIO(rec(b'HRRPUV')),[0,0,0]))
if __name__=='__main__':unittest.main()
