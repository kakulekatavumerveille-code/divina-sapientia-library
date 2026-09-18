import os
import json
import boto3


# ============================================================
# CONFIGURATION
# ============================================================

account_id = os.environ["CLOUDFLARE_ACCOUNT_ID"]
access_key = os.environ["R2_ACCESS_KEY_ID"]
secret_key = os.environ["R2_SECRET_ACCESS_KEY"]
bucket = os.environ["R2_BUCKET"]

endpoint = f"https://{account_id}.r2.cloudflarestorage.com"


# ============================================================
# CONNEXION À CLOUDFLARE R2
# ============================================================

s3 = boto3.client(
    "s3",
    endpoint_url=endpoint,
    aws_access_key_id=access_key,
    aws_secret_access_key=secret_key,
    region_name="auto",
)


# ============================================================
# DÉTERMINER LE TYPE DU FICHIER
# ============================================================

def get_type(filename):
    ext = filename.lower().split(".")[-1] if "." in filename else ""

    if ext in [
        "jpg", "jpeg", "png", "gif", "webp", "svg", "bmp", "ico"
    ]:
        return "image"

    if ext == "pdf":
        return "pdf"

    if ext in [
        "mp3", "wav", "ogg", "m4a", "aac", "flac"
    ]:
        return "audio"

    if ext in [
        "mp4", "webm", "mov", "mkv", "avi", "m4v"
    ]:
        return "video"

    if ext in [
        "doc", "docx", "odt", "rtf", "txt"
    ]:
        return "document"

    if ext in [
        "xls", "xlsx", "ods", "csv"
    ]:
        return "spreadsheet"

    if ext in [
        "ppt", "pptx", "odp"
    ]:
        return "presentation"

    if ext in [
        "zip", "rar", "7z", "tar", "gz"
    ]:
        return "archive"

    return "file"


# ============================================================
# RÉCUPÉRER TOUS LES OBJETS DE R2
# ============================================================

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

        # Ignorer les objets utilisés uniquement comme dossiers vides
        if key.endswith("/"):
            continue

        # Nom du fichier
        filename = key.rstrip("/").split("/")[-1]

        # Dossier contenant le fichier
        folder = "/".join(
            key.rstrip("/").split("/")[:-1]
        )

        # Extension
        extension = (
            filename.rsplit(".", 1)[-1].lower()
            if "." in filename
            else ""
        )

        # Ajouter le fichier à la bibliothèque
        objects.append({
            "name": filename,
            "key": key,
            "folder": folder,
            "type": get_type(filename),
            "extension": extension,
            "size": obj["Size"],
            "last_modified": obj["LastModified"].isoformat()
        })

    # Vérifier s'il existe encore d'autres pages
    if not response.get("IsTruncated"):
        break

    continuation_token = response.get(
        "NextContinuationToken"
    )


# ============================================================
# RECONSTRUIRE AUTOMATIQUEMENT LES DOSSIERS
# ============================================================

folders = set()

for item in objects:

    parts = item["key"].split("/")[:-1]

    for i in range(1, len(parts) + 1):

        folder_path = "/".join(parts[:i])

        folders.add(folder_path)


# ============================================================
# CRÉER LA BIBLIOTHÈQUE
# ============================================================

library = {
    "bucket": bucket,
    "folders": sorted(folders),
    "files": objects
}


# ============================================================
# ÉCRIRE bibliotheque.json
# ============================================================

with open(
    "bibliotheque.json",
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        library,
        f,
        ensure_ascii=False,
        indent=2
    )


# ============================================================
# RAPPORT
# ============================================================

print("===================================")
print("Synchronisation R2 terminée")
print(f"Dossiers : {len(folders)}")
print(f"Fichiers : {len(objects)}")
print("===================================")
