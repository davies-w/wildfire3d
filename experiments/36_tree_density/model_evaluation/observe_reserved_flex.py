"""Read the exact reserved Flex execution; never resume/cancel/reallocate it."""
from pathlib import Path
import datetime,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from cloud import gc,read,save
reservation=read('../33_representation_loss/budget.json')['reservations']['density36-flex-queue01'];parts=reservation['execution'].split('/');workflow=parts[-3]
status=gc('workflows','executions','describe',parts[-1],'--workflow='+workflow,'--location=us-central1');executions=gc('workflows','executions','list',workflow,'--location=us-central1')
proof=dict(checked_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),reserved_execution=reservation['execution'],allowance_usd_unchanged=reservation['allowance_usd'],execution=status,same_workflow_execution_states=[dict(name=v['name'],state=v['state'],startTime=v.get('startTime'),endTime=v.get('endTime')) for v in executions],mutation_performed=False,scope='Read-only status of the execution named by the existing40USDreservation and other executions of that same workflow. Cancellation actor/cause not established; this does not inventory every possible differently named workflow. No queue, job, grant or budget entry changed.')
save('results/flex-reserved-execution-observation.json',proof);print(dict(state=status['state'],endTime=status.get('endTime'),same_workflow_states=[v['state'] for v in executions],reservation_unchanged=reservation['allowance_usd']))
