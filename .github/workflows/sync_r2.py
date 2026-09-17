import os
import json
import boto3

account_id = os.environ["CLOUDFLARE_ACCOUNT_ID"]
access_key = os.environ["R2_ACCESS_KEY_ID"]
secret_key = os.environ["R2_SECRET_ACCESS_KEY"]
bucket = os.environ["R2_BUCKET"]

endpoint = f"https://{account_id}.r2.cloudflarestorage.com"

s3 = boto3.client(
    "s3",
    endpoint_url=endpoint,
    aws_access_key_id=access_key,
    aws_secret_access_key=secret_key,
    region_name="auto",
)

objects = []
continuation_token = None

while True:
    params = {
        "Bucket": bucket,
        "MaxKeys": 1000,
    }

    if continuation_token:
        params["ContinuationToken"] = continuation_token

    response = s3.list_objects_v2(**params)

    for obj in response.get("Contents", []):
        objects.append({
            "key": obj["Key"],
            "size": obj["Size"],
            "last_modified": obj["LastModified"].isoformat(),
        })

    if not response.get("IsTruncated"):
        break

    continuation_token = response.get("NextContinuationToken")

with open("bibliotheque.json", "w", encoding="utf-8") as f:
    json.dump(objects, f, ensure_ascii=False, indent=2)

print(f"{len(objects)} fichiers récupérés depuis R2.")
