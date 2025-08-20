from app.gcp_config import gcp_config
import os
import datetime

BUCKET_NAME = "ttsinfo"
AUDIO_DIR = gcp_config.get_audio_directory()


def generate_signed_url(storage_client, bucket_name: str, blob_name: str, expiration_hours: int = 1):
    try:
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(blob_name)
        try:
            return blob.generate_signed_url(expiration=datetime.timedelta(hours=expiration_hours), version="v4", method="GET")
        except Exception:
            try:
                return blob.public_url
            except Exception:
                return f"https://storage.googleapis.com/{bucket_name}/{blob_name}"
    except Exception as e:
        return None


def main():
    storage_client = gcp_config.get_storage_client()
    if not os.path.exists(AUDIO_DIR):
        print(f"Audio directory does not exist: {AUDIO_DIR}")
        return

    files = sorted(os.listdir(AUDIO_DIR))
    if not files:
        print(f"No files found in {AUDIO_DIR}")
        return

    urls = []
    for f in files:
        url = generate_signed_url(storage_client, BUCKET_NAME, f)
        urls.append((f, url))

    # Print results
    for filename, url in urls:
        print(f"{filename}\t{url}")


if __name__ == '__main__':
    main()
