import os
from flask import render_template, request, Response, send_file, jsonify, current_app
from werkzeug.wsgi import FileWrapper
from . import default_blueprint
from webapp.app.models.fields_definitions import field_definitions
from webapp.app.utils import fake_row, create_sd_file, upload_schema_file_to_gcs, get_file_from_cloud


def extract_data(data_form):
    field_data = []

    rows = data_form.get('rows')
    file_name = data_form.get('file_name')

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

    return file_name, int(rows), field_data


@default_blueprint.route('/')
def default_sdg():
    return render_template('default_sdg.html', field_definitions=field_definitions, field_data=[], rows=None,
                           file_name=None)


@default_blueprint.route('/preview', methods=['POST'])
def preview_data():
    (file_name, rows, field_data) = extract_data(request.form)
    faker_methods = [field_definitions[field[0]].faker_method for field in field_data]
    fake_data = [fake_row(faker_methods) for i in range(0, 10)]
    return render_template('preview.html', fake_data=fake_data, file_name=file_name, rows=rows, field_data=field_data,
                           field_definitions=field_definitions)


@default_blueprint.route('/documentation')
def documentation():
    return render_template('documentation.html')


@default_blueprint.route('/download-data', methods=['POST'])
def download_file():
    (file_name, rows, field_data) = extract_data(request.form)
    local_file_path = create_sd_file(file_name, rows, field_data, field_definitions)

    file_handle = open(local_file_path, 'rb')
    wrapper = FileWrapper(file_handle)\

    response = Response(wrapper, mimetype='text/csv', direct_passthrough=True)
    response.headers['Content-Disposition'] = f'attachment; filename="{file_name}"'

    # Register a function to be called when the response has finished being sent
    def cleanup():
        file_handle.close()  # Close the file
        try:
            os.remove(local_file_path)  # Delete the file
        except Exception as error:
            current_app.logger.error(f"Error removing file: {error}")

    response.call_on_close(cleanup)

    return response


@default_blueprint.route('/upload-data-to-cloud', methods=['POST'])
def upload_data_to_cloud():
    (file_name, rows, field_data) = extract_data(request.json)
    file_name = upload_schema_file_to_gcs(file_name, rows, field_data)

    return jsonify({"status": "success", "message": "File uploaded successfully", "filename": file_name})

