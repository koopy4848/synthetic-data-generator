import csv
import os
from faker import Faker
from flask import current_app
import json
from google.cloud import storage
from ..config import config


def invoke_method(obj, method_name):
    # Check if the method exists in the object
    if hasattr(obj, method_name):
        method = getattr(obj, method_name)
        if callable(method):
            return method()  # Call the method and return its result
    else:
        return None  # or raise an error if the method does not exist


def fake_row(faker_methods):
    fake = Faker()
    return [invoke_method(fake, method_name) for method_name in faker_methods]


def create_sd_file(file_name, rows, field_data, field_definitions):
    faker_methods = [field_definitions[field[0]].faker_method for field in field_data]

    # Define the full path for the new file
    temp_directory = os.path.join(current_app.root_path, 'temp')
    full_path = os.path.join(temp_directory, file_name)

    # Ensure the '/temp/' directory exists
    os.makedirs(temp_directory, exist_ok=True)

    # Open a new CSV file
    with open(full_path, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)

        # Write header
        # Custom names as headers
        headers = [field[1] if field[1] else field_definitions[field[0]].display for field in field_data]
        writer.writerow(headers)

        # Write rows
        for i in range(rows):
            row = fake_row(faker_methods)
            writer.writerow(row)

    return full_path


def upload_schema_file_to_gcs(file_name, rows, field_data):
    bucket_name = config.BUCKET_NAME

    # Convert the data to a JSON string
    json_data = json.dumps({"file_name": file_name, "rows": rows, "field_data": field_data})

    # Upload to Google Cloud Storage
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    # Check if the file exists and modify the filename if it does
    base_name, ext = os.path.splitext(file_name)
    new_file_name = file_name
    counter = 1
    while bucket.blob(new_file_name).exists():
        new_file_name = f"{base_name}_{counter}{ext}"
        counter += 1

    # Upload the file
    blob = bucket.blob(new_file_name)
    blob.upload_from_string(json_data, content_type='application/json')

    return new_file_name


def get_file_from_cloud(file_name):
    return ""
