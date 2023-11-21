import json

from flask import render_template, request
from . import main
from webapp.app.models.fields_definitions import field_definitions
from webapp.app.models.PostData import PostData
from webapp.app.utils import fake_row, create_data_file, start_sdg_in_gcs, start_sdg_in_bq, create_schema_file,\
    respond_with_file


@main.route('/')
def home():
    return render_template('main.html', field_definitions=field_definitions, post_data=PostData(), rows=None,
                           file_name=None)


@main.route('/preview', methods=['POST'])
def preview_data():
    post_data = PostData.extract_data(request.form)
    faker_methods = [field_definitions[field[0]].faker_method for field in post_data.field_data]
    fake_data = [fake_row(faker_methods) for _ in range(0, 10)]
    return render_template('preview.html', fake_data=fake_data, data=post_data)


@main.route('/documentation')
def documentation():
    return render_template('documentation.html')


@main.route('/download-data', methods=['POST'])
def download_file():
    post_data = PostData.extract_data(request.form)
    local_file_path, new_file_name = create_data_file(post_data.file_name, post_data.file_format, post_data.rows,
                                                      post_data.field_data, field_definitions)

    return respond_with_file(new_file_name, local_file_path)


@main.route('/download-schema', methods=['POST'])
def download_schema():
    post_data = PostData.extract_post_data(request.form)

    schema_file_name, local_file_path = create_schema_file(post_data.file_name, post_data.file_format, post_data.rows,
                                                           post_data.field_data)
    return respond_with_file(schema_file_name, local_file_path)


@main.route('/upload-schema', methods=['POST'])
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
    return render_template('main.html', field_definitions=field_definitions, field_data=field_data,
                           rows=rows, file_name=file_name, file_format=file_format, message=message)


@main.route('/start-sdg-gcs', methods=['POST'])
def start_sdg_gcs():
    post_data = PostData.extract_post_data(request.json)

    result = start_sdg_in_gcs(post_data.field_data, post_data.rows_per_part, post_data.parts, post_data.gcs_file_suffix,
                              post_data.gcs_file_format)

    return result


@main.route('/start-sdg-bq', methods=['POST'])
def start_sdg_bq():
    post_data = PostData.extract_post_data(request.json)

    result = start_sdg_in_bq(post_data.field_data, post_data.rows_per_worker, post_data.workers, post_data.bq_table)

    return result
