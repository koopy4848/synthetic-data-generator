import csv
import os
from faker import Faker
from flask import current_app, Response
import json
from google.cloud import storage
from ..config import config
from werkzeug.wsgi import FileWrapper
from decimal import Decimal
from datetime import date


class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return str(obj)  # Convert Decimal to string
        elif isinstance(obj, date):
            return obj.isoformat()  # Convert date to ISO string format
        return json.JSONEncoder.default(self, obj)


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
    except Exception as error:
        current_app.logger.error(f"Error removing file: {error}")


def respond_with_file(file_name, local_file_path):

    file_handle = open(local_file_path, 'rb')
    wrapper = FileWrapper(file_handle)\

    response = Response(wrapper, mimetype='text/csv', direct_passthrough=True)
    response.headers['Content-Disposition'] = f'attachment; filename="{file_name}"'

    # Register a function to be called when the response has finished being sent
    response.call_on_close(lambda: cleanup_file(file_handle, local_file_path))

    return response


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


def create_file(file_name):
    # Define the full path for the new file
    temp_directory = os.path.join(current_app.root_path, 'temp')
    full_path = os.path.join(temp_directory, file_name)

    # Ensure the '/temp/' directory exists
    os.makedirs(temp_directory, exist_ok=True)

    return full_path


def create_data_csv(full_path, field_definitions, field_data, faker_methods, rows):
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


def row_to_json(faker_methods, headers):
    row_data = fake_row(faker_methods)
    row_dict = dict(zip(headers, row_data))
    return json.dumps(row_dict, ensure_ascii=False, cls=CustomJSONEncoder)


def create_data_json(full_path, field_definitions, field_data, faker_methods, rows):
    # Create the headers
    headers = [field[1] if field[1] else field_definitions[field[0]].display for field in field_data]

    with open(full_path, mode='w', encoding='utf-8') as file:
        file.write('[')  # Start of JSON array

        for i in range(rows):
            json_string = row_to_json(faker_methods, headers)

            if i > 0:
                file.write(',\n')  # Add a comma before the next item, except for the first item

            file.write(json_string)  # Write the JSON string

        file.write(']')  # End of JSON array


def create_data_ndjson(full_path, field_definitions, field_data, faker_methods, rows):
    # Create the headers
    headers = [field[1] if field[1] else field_definitions[field[0]].display for field in field_data]

    # Write to an NDJSON file
    with open(full_path, mode='w', encoding='utf-8') as file:
        for i in range(rows):
            json_string = row_to_json(faker_methods, headers)

            file.write(json_string + '\n')


def create_data_file(file_name, file_format, rows, field_data, field_definitions):
    faker_methods = [field_definitions[field[0]].faker_method for field in field_data]

    new_file_name = change_file_extension(file_name, file_format)
    print(new_file_name)
    print(file_format)
    full_path = create_file(new_file_name)

    if file_format == 'csv':
        create_data_csv(full_path, field_definitions, field_data, faker_methods, rows)
    elif file_format == 'json':
        create_data_json(full_path, field_definitions, field_data, faker_methods, rows)
    elif file_format == 'ndjson':
        create_data_ndjson(full_path, field_definitions, field_data, faker_methods, rows)

    return full_path, new_file_name


def create_schema_file(file_name, file_format, rows, field_data):
    # Parse the file_name to remove the extension and add .schema.json
    base = os.path.splitext(file_name)[0]  # This removes the extension
    schema_file_name = f"{base}.schema.json"  # This adds .schema.json

    # Convert the data to a JSON string
    json_data = json.dumps({"file_name": file_name, "file_format": file_format, "rows": rows, "field_data": field_data},
                           indent=4)

    local_file_path = create_file(schema_file_name)

    # Write json data to schema file
    with open(local_file_path, 'w') as schema_file:
        schema_file.write(json_data)

    # Return the schema file name for reference if needed
    return {"filename": schema_file_name, "local_file_path": local_file_path}


def upload_schema_file_to_gcs(file_name, file_format, rows, field_data):
    bucket_name = config.BUCKET_NAME

    # Create the schema file
    schema_file_name, _ = create_schema_file(file_name, file_format, rows, field_data)

    # Initialize Google Cloud Storage client
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)

    # Check if the schema file exists in GCS
    blob = bucket.blob(schema_file_name)
    if blob.exists():
        return {"status": "error", "message": "File already exists in the bucket"}

    # Read the schema file data
    with open(schema_file_name, 'r') as file:
        schema_data = file.read()

    # Upload the schema file
    blob.upload_from_string(schema_data, content_type='application/json')

    os.remove(schema_file_name)

    return {"status": "success", "message": "File uploaded successfully", "filename": schema_file_name}
