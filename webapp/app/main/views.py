from flask import render_template, request, redirect, url_for
from . import main
from ..models.fields_definitions import field_definitions
from ..utils import fake_row


def extract_data():
    field_data = []

    rows = request.form.get('rows')
    file_name = request.form.get('file_name')

    for key in request.form:
        if key.startswith('field_type_'):
            index = key.split('_')[-1]  # Get the index from the field name
            field_type = request.form.get(f'field_type_{index}')
            custom_name = request.form.get(f'custom_name_{index}')
            field_data.append((field_type, custom_name))
        elif key == "field_type":
            field_type = request.form.get(f'field_type')
            custom_name = request.form.get(f'custom_name')
            field_data.append((field_type, custom_name))

    return file_name, int(rows), field_data


@main.route('/')
def home():
    return render_template('home.html', field_definitions=field_definitions, field_data=[], rows=None,
                           file_name=None)


@main.route('/preview', methods=['POST'])
def preview():
    (file_name, rows, field_data) = extract_data()
    faker_methods = [field_definitions[field[0]].faker_method for field in field_data]
    fake_data = [fake_row(faker_methods) for i in range(0, 10)]
    return render_template('preview.html', fake_data=fake_data, file_name=file_name, rows=rows, field_data=field_data,
                           field_definitions=field_definitions)


@main.route('/documentation')
def documentation():
    return render_template('home.html')


@main.route('/custom_generator')
def custom_generator():
    return render_template('generate.html')

