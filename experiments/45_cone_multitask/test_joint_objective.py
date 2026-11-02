import unittest,torch
from joint_objective import cone_terms,SCALES
class LossTests(unittest.TestCase):
 def test_perfect_parameters(self):
  y=torch.ones(2,3,5);p,a=cone_terms(y,torch.zeros(2,3),y,torch.ones(2,3,dtype=torch.bool),torch.ones(2,3));self.assertTrue(torch.equal(p,torch.zeros(2)));self.assertTrue(torch.allclose(a,torch.full((2,),.69314718)))
 def test_inactive_nan_mask(self):
  y=torch.full((1,2,5),float('nan'));p,a=cone_terms(torch.ones_like(y),torch.zeros(1,2),y,torch.zeros(1,2,dtype=torch.bool),torch.ones(1,2));self.assertEqual(p.item(),0);self.assertTrue(torch.isfinite(a).all())
 def test_presence_cannot_hide_parameter_error(self):
  y=torch.zeros(1,2,5);pred=torch.tensor(SCALES).expand_as(y)*.1;active=torch.ones(1,2,dtype=torch.bool);dt=torch.ones(1,2)
  p1,_=cone_terms(pred,torch.full((1,2),-100.),y,active,dt);p2,_=cone_terms(pred,torch.full((1,2),100.),y,active,dt)
  self.assertTrue(torch.equal(p1,p2));self.assertAlmostEqual(p1.item(),.05,places=6)
 def test_elapsed_time_weight(self):
  y=torch.zeros(1,2,5);pred=y.clone();pred[:,1]=torch.tensor(SCALES)*.2
  p,_=cone_terms(pred,torch.zeros(1,2),y,torch.ones(1,2,dtype=torch.bool),torch.tensor([[1.,3.]]));self.assertAlmostEqual(p.item(),.15*.75,places=6)
if __name__=='__main__':unittest.main()
