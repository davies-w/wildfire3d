"""Regression checks for paired diagnostic decisions, not solver execution."""
import unittest,numpy as np
from compare import scalar_compare
class ComparisonTests(unittest.TestCase):
 def setUp(self):
  self.x={'Time':np.array([0.,20.,180.]),'HRR':np.array([0.,10.,0.])};self.d={'Time':self.x['Time'],'fuel mass':np.array([100.,90.,80.])}
 def test_identity(self):
  self.assertEqual(scalar_compare(self.x,self.x,self.d,self.d,100)['major_metric_flags'],[])
 def test_major_heat_difference(self):
  y=dict(self.x,HRR=self.x['HRR']*2);self.assertIn('total_energy_relative_difference',scalar_compare(self.x,y,self.d,self.d,100)['major_metric_flags'])
 def test_mass_loss_difference(self):
  d=dict(self.d);d['fuel mass']=np.array([100.,90.,70.]);self.assertIn('wet_mass_loss_difference_percentage_points',scalar_compare(self.x,self.x,self.d,d,100)['major_metric_flags'])
if __name__=='__main__':unittest.main()
