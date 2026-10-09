"""Check S3 access to a Hugging Face Storage Bucket.

Reads HF-generated S3 credentials from ~/.hf_s3_cred (never from argv, so the
secret stays out of shell history and chat), points boto3 at the HF S3 gateway
with the settings its docs require -- path-style addressing and checksums only
"when_required", since the gateway does not parse the trailing CRC32 checksums
recent boto3 sends by default.

Lists the buckets visible to the key.  That alone proves the endpoint, the
region, the addressing style and the credential pair are all correct.
"""
import os, sys

import boto3
from botocore.config import Config

NAMESPACE = "wdavies"
CRED = os.path.expanduser("~/.hf_s3_cred")


def load_creds(path):
    if not os.path.exists(path):
        sys.exit("missing %s -- see the setup steps" % path)
    creds = {}
    for line in open(path):
        line = line.strip()
        if "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            creds[k.strip()] = v.strip().strip('"').strip("'")
    return creds


creds = load_creds(CRED)
key = creds.get("AWS_ACCESS_KEY_ID")
secret = creds.get("AWS_SECRET_ACCESS_KEY")
if not key or not secret:
    sys.exit("need AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY in %s" % CRED)

print("access key: %s...%s" % (key[:6], key[-4:]))

s3 = boto3.client(
    "s3",
    endpoint_url="https://s3.hf.co/%s" % NAMESPACE,
    region_name="us-east-1",
    aws_access_key_id=key,
    aws_secret_access_key=secret,
    config=Config(
        s3={"addressing_style": "path"},
        request_checksum_calculation="when_required",
        response_checksum_validation="when_required",
    ),
)

try:
    r = s3.list_buckets()
except Exception as e:
    sys.exit("FAILED: %s" % e)

names = [b["Name"] for b in r.get("Buckets", [])]
print("buckets visible: %s" % (names or "(none)"))
print("OK")
