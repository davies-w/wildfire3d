import unittest
import numpy as np
from cones import membership,fit,metrics
class GeometryTests(unittest.TestCase):
    def test_upright_cap_and_radius(self):
        xyz=np.array([[8,8,0],[8,8,4],[9.9,8,4],[10.1,8,4],[8,8,4.1],[8,8,-.1]])
        np.testing.assert_array_equal(membership(xyz,0,0,4,2),[1,1,1,0,0,0])
    def test_downwind(self):
        xyz=np.array([[10,8,2],[7,8,2],[12,9.9,2],[12,10.1,2]])
        np.testing.assert_array_equal(membership(xyz,2,90,4,2),[1,0,1,0])
    def test_fit_and_empty(self):
        self.assertIsNone(fit(np.empty((0,3)),4))
        xyz=np.array([[8+x,8+y,z] for x in [-1,0,1] for y in [-1,0,1] for z in [2.5,3.5,5.5]])
        _,h,t,l,r=fit(xyz,4)
        self.assertGreaterEqual(membership(xyz,h,t,l,r).mean(),.95)
    def test_counts(self):
        m=metrics(np.array([1,1,0],bool),np.array([1,0,1],bool))
        self.assertEqual(m['hot_recall'],.5);self.assertEqual(m['hot_precision'],.5);self.assertEqual(m['iou'],1/3)
if __name__=='__main__':unittest.main()
