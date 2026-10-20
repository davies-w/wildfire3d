"""One-time six-test launch; every submission independently reserves full allowance."""
from cloud import launch,read
for g in read('groups.json'):
 assert g['id'] not in read('budget.json')['reservations'],'Reserved attempt may never be resubmitted'
 launch(g['id'],5.)
