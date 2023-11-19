# config.py
import os


class Config:
    BUCKET_NAME = os.environ.get('BUCKET_NAME', 'default-bucket-name')
    # other config variables


# Create a global config object
config = Config()
