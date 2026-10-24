#!/usr/bin/env python3
"""Read posted wildfire costs; never treat an absent export as zero spend."""
import argparse
import datetime
import json
import os
from pathlib import Path
import shutil
import subprocess

PROJECT = 'tmrw-wildfire-20261015'
DATASET = 'billing_export'
TABLE = 'gcp_billing_export_resource_v1_0136FB_EBB956_005416'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--start', default='2026-10-01')
    parser.add_argument('--end', default=datetime.date.today().isoformat(), help='Exclusive usage-date bound (UTC)')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    for value in (args.start, args.end):
        datetime.date.fromisoformat(value)
    sdk = Path.home() / '.local/google-cloud-sdk/bin'
    env = dict(os.environ, PATH=str(sdk) + os.pathsep + os.environ.get('PATH', ''))
    bq = shutil.which('bq', path=env['PATH'])
    if not bq:
        raise SystemExit('Google Cloud bq CLI is required')
    def run(*options):
        return subprocess.check_output([bq, '--project_id=' + PROJECT, '--location=US', '--format=json', *options], env=env, text=True)
    tables = json.loads(run('ls', '--max_results=1000', PROJECT + ':' + DATASET) or '[]')
    result = {'fetched_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'project': PROJECT, 'source': f'{PROJECT}.{DATASET}.{TABLE}', 'start_inclusive': args.start, 'end_exclusive': args.end}
    if TABLE not in [t['tableReference']['tableId'] for t in tables]:
        result.update(status='awaiting_first_export', costs=None)
    else:
        query = f'''SELECT DATE(usage_start_time) AS usage_date, invoice.month AS invoice_month,
          service.description AS service, sku.id AS sku_id, sku.description AS sku,
          resource.name AS resource_name, currency, cost_type,
          SUM(cost) AS gross_cost,
          SUM(IFNULL((SELECT SUM(c.amount) FROM UNNEST(credits) c),0)) AS credits,
          SUM(cost + IFNULL((SELECT SUM(c.amount) FROM UNNEST(credits) c),0)) AS net_cost,
          MAX(export_time) AS latest_export_time
        FROM `{PROJECT}.{DATASET}.{TABLE}`
        WHERE project.id = '{PROJECT}' AND usage_start_time >= TIMESTAMP('{args.start}')
          AND usage_start_time < TIMESTAMP('{args.end}')
        GROUP BY 1,2,3,4,5,6,7,8 ORDER BY 1,3,4,6'''
        rows = json.loads(run('query', '--use_legacy_sql=false', '--maximum_bytes_billed=1000000000', '--max_rows=1000000', query))
        result.update(status='posted_costs_subject_to_adjustment', costs=rows)
    output = json.dumps(result, indent=2) + '\n'
    if args.output:
        args.output.write_text(output)
    else:
        print(output, end='')

if __name__ == '__main__':
    main()
