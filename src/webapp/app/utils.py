import csv
import tempfile
from flask import current_app
from google.cloud import storage
from ..config import config
from werkzeug.wsgi import FileWrapper
from google.cloud import pubsub_v1
from flask import Response
import os
import json
from src.sdg_common.sdg_core import fake_row, row_to_json


def change_file_extension(file_name, file_format):
    # Split the file name into the name and current extension
    name, _ = os.path.splitext(file_name)

    # Add the new extension
    new_file_name = f"{name}.{file_format}"

    return new_file_name


def cleanup_file(file_handle, local_file_path):
    file_handle.close()  # Close the file
    try:
        os.remove(local_file_path)  # Delete the file
        print(f'Removed {local_file_path}')
    except Exception as error:

        current_app.logger.error(f"Error removing file: {error}")


def respond_with_file(file_name, local_file_path):
    file_handle = open(local_file_path, 'rb')
    wrapper = FileWrapper(file_handle)
    response = Response(wrapper, mimetype='text/csv', direct_passthrough=True)
    response.headers['Content-Disposition'] = f'attachment; filename="{file_name}"'

    # Register a function to be called when the response has finished being sent
    response.call_on_close(lambda: cleanup_file(file_handle, local_file_path))

    return response



def create_file(file_name):
    # Define the full path for the new file
    temp_directory = os.path.join(current_app.root_path, 'temp')
    full_path = os.path.join(temp_directory, file_name)

    # Ensure the '/temp/' directory exists
    os.makedirs(temp_directory, exist_ok=True)

    return full_path


def create_data_csv(field_definitions, field_data, faker_methods, rows):
    with tempfile.NamedTemporaryFile(mode='w+', delete=False) as temp_file:
        writer = csv.writer(temp_file)

        # Write header
        # Custom names as headers
        headers = [field[1] if field[1] else field_definitions[field[0]].display for field in field_data]
        writer.writerow(headers)

        # Write rows
        for i in range(rows):
            row = fake_row(faker_methods)
            writer.writerow(row)

        temp_file_path = temp_file.name

    return temp_file_path


def create_data_json(field_definitions, field_data, faker_methods, rows):
    # Create the headers
    headers = [field[1] if field[1] else field_definitions[field[0]].display for field in field_data]

    with tempfile.NamedTemporaryFile(mode='w+', delete=False, encoding='utf-8') as temp_file:
        temp_file.write('[')  # Start of JSON array

        for i in range(rows):
            json_string = row_to_json(faker_methods, headers)

            if i > 0:
                temp_file.write(',\n')  # Add a comma before the next item, except for the first item

            temp_file.write(json_string)  # Write the JSON string

        temp_file.write(']')  # End of JSON array
        temp_file_path = temp_file.name

    return temp_file_path


def create_data_ndjson(field_definitions, field_data, faker_methods, rows):
    # Create the headers
    headers = [field[1] if field[1] else field_definitions[field[0]].display for field in field_data]

    # Write to an NDJSON file
    with tempfile.NamedTemporaryFile(mode='w+', delete=False, encoding='utf-8') as temp_file:
        temp_file.write('[')  # Start of JSON array
        for i in range(rows):
            json_string = row_to_json(faker_methods, headers)

            temp_file.write(json_string + '\n')
        temp_file_path = temp_file.name

    return temp_file_path


def create_data_file(file_name, file_format, rows, field_data, field_definitions):
    faker_methods = [field_definitions[field[0]].faker_method for field in field_data]

    new_file_name = change_file_extension(file_name, file_format)

    outfile = ""
    if file_format == 'csv':
        outfile = create_data_csv(field_definitions, field_data, faker_methods, rows)
    elif file_format == 'json':
        outfile = create_data_json(field_definitions, field_data, faker_methods, rows)
    elif file_format == 'ndjson':
        outfile = create_data_ndjson(field_definitions, field_data, faker_methods, rows)

    return outfile, new_file_name


def create_schema_file(file_name, file_format, rows, field_data):
    # Parse the file_name to remove the extension and add .schema.json
    base = os.path.splitext(file_name)[0]  # This removes the extension
    schema_file_name = f"{base}.schema.json"  # This adds .schema.json

    # Convert the data to a JSON string
    json_data = json.dumps({"file_name": file_name, "file_format": file_format, "rows": rows, "field_data": field_data},
                           indent=4)

    with tempfile.NamedTemporaryFile(mode='w+', delete=False) as temp_file:
        temp_file.write(json_data)
        temp_file_path = temp_file.name

    # Return the schema file name for reference if needed
    return schema_file_name, temp_file_path


def start_sdg_in_gcs(field_data, rows_per_part, parts, gcs_file_suffix, gcs_file_format):
    publisher = pubsub_v1.PublisherClient()
    topic_path = publisher.topic_path(config.PROJECT_ID, config.GCS_TOPIC_ID)
    messages = []

    for i in range(0, parts):
        file_name = f"{gcs_file_suffix}_{i:000}.{gcs_file_format}"

        data = json.dumps({"file_name": file_name, "file_format": gcs_file_format, "rows": rows_per_part,
                           "field_data": field_data}, indent=4)

        try:
            # Data must be a bytestring
            data = data.encode("utf-8")

            # Publishes a message
            future = publisher.publish(topic_path, data)
            messages.append(future.result())
        except Exception as e:
            return {"status": "error", "message": f'An error occurred: {e}'}

    return {"status": "success", "message": f'Message published. Message ID: {".".join(messages)}'}


def start_sdg_in_bq(field_data, rows_per_worker, workers, bq_table):
    publisher = pubsub_v1.PublisherClient()
    topic_path = publisher.topic_path(config.PROJECT_ID, config.BQ_TOPIC_ID)
    messages = []

    for i in range(0, workers):
        data = json.dumps({"bq_table": bq_table, "rows": rows_per_worker, "field_data": field_data},
                          indent=4)

        try:
            # Data must be a bytestring
            data = data.encode("utf-8")

            # Publishes a message
            future = publisher.publish(topic_path, data)
            messages.append(future.result())
        except Exception as e:
            return {"status": "error", "message": f'An error occurred: {e}'}

    return {"status": "success", "message": f'Message published. Message ID: {".".join(messages)}'}


def save_schema_to_gcs(schema_file_name, schema_data):
    bucket_name = config.BUCKET_NAME

    # Initialize Google Cloud Storage client
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)

    # Check if the schema file exists in GCS
    blob = bucket.blob(schema_file_name)
    if blob.exists():
        return {"status": "error", "message": "File already exists in the bucket"}

    # Upload the schema file
    blob.upload_from_string(schema_data, content_type='application/json')
