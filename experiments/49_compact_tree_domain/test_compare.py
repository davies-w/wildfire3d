"""Regression checks for paired diagnostic decisions, not solver execution."""
import unittest,numpy as np,tempfile
from pathlib import Path
from scipy.io import FortranFile
from compare import scalar_compare,field_compare
class ComparisonTests(unittest.TestCase):
 def setUp(self):
  self.x={'Time':np.array([0.,20.,180.]),'HRR':np.array([0.,10.,0.])};self.d={'Time':self.x['Time'],'fuel mass':np.array([100.,90.,80.])}
 def test_identity(self):
  self.assertEqual(scalar_compare(self.x,self.x,self.d,self.d,100)['major_metric_flags'],[])
 def test_major_heat_difference(self):
  y=dict(self.x,HRR=self.x['HRR']*2);self.assertIn('total_energy_relative_difference',scalar_compare(self.x,y,self.d,self.d,100)['major_metric_flags'])
 def test_mass_loss_difference(self):
  d=dict(self.d);d['fuel mass']=np.array([100.,90.,70.]);self.assertIn('wet_mass_loss_difference_percentage_points',scalar_compare(self.x,self.x,self.d,d,100)['major_metric_flags'])
class FieldTests(unittest.TestCase):
 def synthetic(self,path,old,delta=0):
  shape=(3,5 if old else 3,3)
  with FortranFile(path,'w') as f:
   for text in ['TEMPERATURE','temp','C']:f.write_record(np.frombuffer(text.encode().ljust(30),dtype='u1'))
   f.write_record(np.array([0,shape[0]-1,0,shape[1]-1,0,shape[2]-1],dtype='i4'))
   for t in (range(0,181,2) if old else range(1,180,2)):
    i,j,k=np.indices(shape);a=(100+i+10*(j-(2 if old else 0))+k+t+delta).astype('f4')
    f.write_record(np.array([t],dtype='f4'));f.write_record(a.flatten(order='F'))
 def test_translated_and_interpolated_field(self):
  with tempfile.TemporaryDirectory() as td:
   a,b=Path(td)/'old.sf',Path(td)/'new.sf';self.synthetic(a,True);self.synthetic(b,False)
   c={'domain':[1,1,1],'original_domain':[1,18,1]};m=field_compare(a,b,c)
   self.assertEqual(m['common_region_hot_temperature_mae_C'],0);self.assertEqual(m['peak_temperature_history_mae_C'],0)
   self.synthetic(b,False,150);m=field_compare(a,b,c);self.assertAlmostEqual(m['common_region_hot_temperature_mae_C'],150)
if __name__=='__main__':unittest.main()
