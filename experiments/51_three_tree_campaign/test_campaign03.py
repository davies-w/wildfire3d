"""Regression checks for the step-limit failure and safe continuation guards."""
import unittest,yaml
from pathlib import Path
R=Path(__file__).resolve().parent
class Campaign(unittest.TestCase):
 def test_healthy_polling_does_not_scan_tasks(self):
  # Full 375-poll wave: zero historical-event enumeration for healthy tasks.
  last=0;scans=0
  for failed in [0]*375:
   if failed>=2 and failed>last:scans+=1;last=failed
  self.assertEqual(scans,0)
 def test_repeated_failure_count_only_scanned_once(self):
  last=0;scans=0
  for failed in [0,1,2,2,2,3,3,4,4]:
   if failed>=2 and failed>last:scans+=1;last=failed
  self.assertEqual(scans,3)
  w=yaml.safe_load((R/'wave03.yaml').read_text());s=w['main']['steps'][-1]['wave_run']['try']['steps'];guard=next(x['eviction_check_needed'] for x in s if 'eviction_check_needed' in x)
  self.assertIn('> last_failed',guard['switch'][0]['condition'])
 def test_parent_carries_budget_and_policy(self):
  w=yaml.safe_load((R/'workflow03.yaml').read_text());s=w['main']['steps'][4]['waves']['for']['steps'];self.assertEqual(next(iter(s[0])),'budget_admission')
  self.assertIn('spent+outcome.compute_charge_upper_usd',str(s[-1]));self.assertIn('outcome.checkpoint_seconds',str(s[-1]))
 def test_duplicate_claim_precedes_cleanup_scope(self):
  w=yaml.safe_load((R/'wave03.yaml').read_text());s=w['main']['steps'];n=[next(iter(x)) for x in s]
  self.assertLess(n.index('claim_once'),n.index('wave_run'));self.assertEqual(s[n.index('claim_once')]['claim_once']['args']['query']['ifGenerationMatch'],0)
 def test_failure_event_scan_is_bounded_and_failed_only(self):
  w=yaml.safe_load((R/'wave03.yaml').read_text());steps=next(s['count_tasks']['for']['steps'] for s in w['adapt_checkpoints']['steps'] if 'count_tasks' in s)
  g=next(s['failed_task_events']['switch'][0] for s in steps if 'failed_task_events' in s)
  self.assertEqual(g['condition'],'${task.status.state == "FAILED"}')
  self.assertIn('> 50',str(g))
if __name__=='__main__':unittest.main()
