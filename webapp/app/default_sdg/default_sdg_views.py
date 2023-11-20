import json

from flask import render_template, request
from . import default_blueprint
from webapp.app.models.fields_definitions import field_definitions
from webapp.app.utils import fake_row, create_data_file, upload_schema_file_to_gcs, respond_with_file, \
    create_schema_file


def extract_data(data_form, enforce_rows_int=False):
    field_data = []

    rows = data_form.get('rows')
    file_name = data_form.get('file_name')
    file_format = data_form.get('file_format')

    for key in data_form:
        if key.startswith('field_type_'):
            index = key.split('_')[-1]  # Get the index from the field name
            field_type = data_form.get(f'field_type_{index}')
            custom_name = data_form.get(f'custom_name_{index}')
            field_data.append((field_type, custom_name))
        elif key == "field_type":
            field_type = data_form.get(f'field_type')
            custom_name = data_form.get(f'custom_name')
            field_data.append((field_type, custom_name))

    return file_name, file_format, int(rows), field_data


@default_blueprint.route('/')
def default_sdg():
    return render_template('default_sdg.html', field_definitions=field_definitions, field_data=[], rows=None,
                           file_name=None)


@default_blueprint.route('/preview', methods=['POST'])
def preview_data():
    (file_name, file_format, rows, field_data) = extract_data(request.form)
    faker_methods = [field_definitions[field[0]].faker_method for field in field_data]
    fake_data = [fake_row(faker_methods) for _ in range(0, 10)]
    return render_template('preview.html', fake_data=fake_data, file_name=file_name, rows=rows, field_data=field_data,
                           field_definitions=field_definitions, file_format=file_format)


@default_blueprint.route('/documentation')
def documentation():
    return render_template('documentation.html')


@default_blueprint.route('/download-data', methods=['POST'])
def download_file():
    (file_name, file_format, rows, field_data) = extract_data(request.form)
    local_file_path, new_file_name = create_data_file(file_name, file_format, rows, field_data, field_definitions)

    return respond_with_file(new_file_name, local_file_path)


@default_blueprint.route('/download-schema', methods=['POST'])
def download_schema():
    (file_name, file_format, rows, field_data) = extract_data(request.form)

    result = create_schema_file(file_name, file_format, rows, field_data)
    return respond_with_file(result["filename"], result["local_file_path"])


@default_blueprint.route('/start-sdg', methods=['POST'])
def start_sdg():
    (file_name, file_format, rows, field_data) = extract_data(request.json)
    result = upload_schema_file_to_gcs(file_name, file_format, rows, field_data)

    return result


@default_blueprint.route('/upload-schema', methods=['POST'])
def upload_schema():
    # Default values
    message = ''
    field_data = []
    rows = 0
    file_name = ''
    file_format = ''

    # Check if the post request has the file part
    if 'schema' not in request.files:
        message = 'No file part'
    else:
        file = request.files['schema']

        # If a file is present
        if file and file.filename:
            try:
                # Read the file contents
                file_contents = file.read()
                data = json.loads(file_contents)

                field_data = data.get("field_data", [])
                rows = data.get("rows", 0)
                file_name = data.get("file_name", "")
                file_format = data.get("file_format", "")
            except json.JSONDecodeError as e:
                message = f"Invalid JSON file: {e}"
            except Exception as e:
                message = f"Error processing file: {e}"
        else:
            message = 'No selected file' if file.filename == '' else "Unexpected error when reading the file"

    # Render template with the processed data or error message
    return render_template('default_sdg.html', field_definitions=field_definitions, field_data=field_data,
                           rows=rows, file_name=file_name, file_format=file_format, message=message)
