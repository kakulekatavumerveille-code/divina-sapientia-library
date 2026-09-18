import os
import json
import boto3
from datetime import datetime

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

def get_type(filename):
    ext = filename.lower().split(".")[-1] if "." in filename else ""

    if ext in ["jpg", "jpeg", "png", "gif", "webp", "svg"]:
        return "image"

    if ext == "pdf":
        return "pdf"

    if ext in ["mp3", "wav", "ogg", "m4a", "aac", "flac"]:
        return "audio"

    if ext in ["mp4", "webm", "mov", "mkv", "avi", "m4v"]:
        return "video"

    if ext in ["doc", "docx", "odt"]:
        return "document"

    if ext in ["xls", "xlsx", "ods", "csv"]:
        return "spreadsheet"

    if ext in ["ppt", "pptx", "odp"]:
        return "presentation"

    if ext in ["zip", "rar", "7z"]:
        return "archive"

    return "file"


objects = []
continuation_token = None

while True:
    params = {
        "Bucket": bucket,
        "MaxKeys": 1000
    }

    if continuation_token:
        params["ContinuationToken"] = continuation_token

    response = s3.list_objects_v2(**params)

    for obj in response.get("Contents", []):
        key = obj["Key"]

        # Les clés terminant par / représentent des dossiers vides
        if key.endswith("/"):
            continue

        filename = key.rstrip("/").split("/")[-1]
        folder = "/".join(key.rstrip("/").split("/")[:-1])

        objects.append({
            "name": filename,
            "key": key,
            "folder": folder,
            "type": get_type(filename),
            "extension": filename.rsplit(".", 1)[-1].lower()
                if "." in filename else "",
            "size": obj["Size"],
            "last_modified": obj["LastModified"].isoformat()
        })

    if not response.get("IsTruncated"):
        break

    continuation_token = response.get("NextContinuationToken")


# Construction de la liste des dossiers
folders = set()

for item in objects:
    parts = item["key"].split("/")[:-1]

    for i in range(1, len(parts) + 1):
        folders.add("/".join(parts[:i]))


library = {
    "generated_at": datetime.utcnow().isoformat() + "Z",
    "bucket": bucket,
    "folders": sorted(folders),
    "files": objects
}


with open("bibliotheque.json", "w", encoding="utf-8") as f:
    json.dump(library, f, ensure_ascii=False, indent=2)


print("===================================")
print("Synchronisation R2 terminée")
print(f"Dossiers : {len(folders)}")
print(f"Fichiers : {len(objects)}")
print("===================================")
