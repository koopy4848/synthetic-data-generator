# config.py
import os


class Config:
    BUCKET_NAME = os.environ.get('BUCKET_NAME', 'default-bucket-name')
    PROJECT_ID = os.environ.get("GCP_PROJECT_ID")
    BQ_TOPIC_ID = os.environ.get("BQ_TOPIC_ID")
    GCS_TOPIC_ID = os.environ.get("GCS_TOPIC_ID")


# Create a global config object
config = Config()
