import os
from flask import render_template, request, Response, send_file, jsonify, current_app
from werkzeug.wsgi import FileWrapper
from . import schema_blueprint
from ..models.fields_definitions import field_definitions
from ..utils import fake_row, create_sd_file, upload_schema_file_to_gcs, get_file_from_cloud


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


@schema_blueprint.route('/schema_sdg')
def schema_sdg():
    return render_template('schema_sdg.html', field_definitions=field_definitions, field_data=[], rows=None,
                           file_name=None)


@schema_blueprint.route('/schema-preview', methods=['POST'])
def preview_data():
    (file_name, rows, field_data) = extract_data(request.form)
    faker_methods = [field_definitions[field[0]].faker_method for field in field_data]
    fake_data = [fake_row(faker_methods) for i in range(0, 10)]
    return render_template('schema_preview.html', fake_data=fake_data, file_name=file_name, rows=rows, field_data=field_data,
                           field_definitions=field_definitions)


@schema_blueprint.route('/upload-schema-to-cloud', methods=['POST'])
def upload_schema_to_cloud():
    (file_name, rows, field_data) = extract_data(request.json)
    file_name = upload_schema_file_to_gcs(file_name, rows, field_data)

    return jsonify({"status": "success", "message": "File uploaded successfully", "filename": file_name})


@schema_blueprint.route('/download-schema-from-cloud', methods=['POST'])
def download_schema_from_cloud():
    (file_name, rows, field_data) = extract_data(request.form)
    local_file_path = get_file_from_cloud(file_name)
    return send_file(local_file_path, as_attachment=True)
