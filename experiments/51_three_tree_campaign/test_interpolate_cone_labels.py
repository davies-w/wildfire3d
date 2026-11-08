import unittest
import numpy as np
from interpolate_cone_labels import interpolate_cones

class InterpolationEvidence(unittest.TestCase):
    def setUp(self):
        self.time = np.array([0,36.0094,72.006,108.0015,144.0042,180.])
        self.values = np.array([[0,0,0,0,0,0], [1,2,10,8,3,400],
                                [1,4,20,12,5,800], [1,3,15,10,4,600],
                                [1,1,5,4,2,200], [0,0,0,0,0,0]],float)
    def test_actual_saved_rows_preserved(self):
        out=interpolate_cones(self.time,self.values,self.time)
        np.testing.assert_array_equal(out['cones'], self.values)
        self.assertTrue(out['observed'].all())
    def test_nominal_times_are_not_fabricated_observations(self):
        out=interpolate_cones(self.time,self.values,np.arange(0,181,2.))
        self.assertEqual(out['observed'].sum(),2)
        self.assertTrue(out['interpolated'][18])
        np.testing.assert_array_equal(out['source_time_s'],self.time)
    def test_onset_midpoint_is_explicitly_synthetic(self):
        out=interpolate_cones(self.time,self.values,[0,self.time[1]/2,180])
        np.testing.assert_allclose(out['cones'][1],self.values[1]/2)
        self.assertTrue(out['interpolated'][1])
        self.assertEqual(out['cones'][1,0],.5)
    def test_extrapolation_and_invalid_sources_rejected(self):
        with self.assertRaises(ValueError):interpolate_cones(self.time,self.values,[-1,180])
        with self.assertRaises(ValueError):interpolate_cones(self.time[::-1],self.values,[0,180])
        bad=self.values.copy();bad[0,1]=2
        with self.assertRaises(ValueError):interpolate_cones(self.time,bad,[0,180])
if __name__=='__main__':unittest.main()
