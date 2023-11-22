import logging
import apache_beam as beam
from apache_beam import window
from apache_beam.options.pipeline_options import PipelineOptions, SetupOptions
import json
from datetime import date
from decimal import Decimal
from faker import Faker
import os
from google.cloud import bigquery
from google.api_core.exceptions import GoogleAPIError


class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return str(obj)  # Convert Decimal to string
        elif isinstance(obj, date):
            return obj.isoformat()  # Convert date to ISO string format
        return json.JSONEncoder.default(self, obj)


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


def row_to_dict(faker_methods, headers):
    row_data = fake_row(faker_methods)
    row_dict = dict(zip(headers, row_data))

    # Convert any non-serializable types
    for key, value in row_dict.items():
        if isinstance(value, Decimal):
            row_dict[key] = str(value)  # Convert Decimal to string
        elif isinstance(value, date):
            row_dict[key] = value.isoformat()  # Convert date to ISO string format

    return row_dict


class Field:
    def __init__(self, field_id, faker_method, display, data_type, example):
        self.field_id = field_id
        self.faker_method = faker_method
        self.display = display
        self.data_type = data_type
        self.example = example


class ProcessMessage(beam.DoFn):
    def __init__(self, field_defs):
        self.field_definitions = field_defs

    def process(self, element):
        message = json.loads(element)
        bq_table = message['bq_table']
        field_data = message['field_data']
        rows = message['rows']

        faker_methods = [self.field_definitions[field[0]].faker_method for field in field_data]
        headers = [field[1] if field[1] else self.field_definitions[field[0]].display for field in field_data]
        schema = generate_bigquery_schema_from_message(field_data, self.field_definitions)
        for _ in range(rows):
            row_data = row_to_dict(faker_methods, headers)
            key = (bq_table, json.dumps(schema))  # Use JSON string as the schema can be a complex object
            yield key, row_data


def generate_bigquery_schema_from_message(field_data, field_definitions):
    """
    Generates a BigQuery schema from field data contained in a Pub/Sub message.

    :param field_data: A list of tuples representing field data.
    :param field_definitions: A dictionary of Field objects.
    :return: A list of dictionaries representing the BigQuery schema.
    """
    schema = []
    for field in field_data:
        field_id = field[0]
        field_info = field_definitions[field_id]
        field_schema = {
            'name': field[1] if field[1] else field_info.display,
            'type': 'STRING' if field_info.data_type in [str, 'str'] else
            'INTEGER' if field_info.data_type in [int, 'int'] else
            'FLOAT' if field_info.data_type in [float, 'float'] else
            'DATE' if field_info.data_type in ['date'] else
            'STRING',  # Default type
            'mode': 'NULLABLE'  # Assuming all fields are nullable
        }
        schema.append(field_schema)
    return schema


class WriteGroupedDataToBigQueryFn(beam.DoFn):
    def start_bundle(self):
        self.bq_dataset = os.getenv('BQ_DATASET', 'default_dataset')  # Fallback to 'default_dataset' if not set
        self.gcp_project_id = os.getenv('GCP_PROJECT_ID', 'default_dataset')  # Fallback to 'default_dataset' if not set
        self.client = bigquery.Client()

    def process(self, element, *args, **kwargs):
        table, schema_json = element[0]
        rows = list(element[1])
        schema = json.loads(schema_json)

        dataset_ref = self.client.dataset(self.bq_dataset)
        table_ref = dataset_ref.table(table)

        try:
            # Create or get the table with the specified schema
            table = bigquery.Table(table_ref, schema=schema)
            table = self.client.create_table(table, exists_ok=True)

            # Insert rows
            errors = self.client.insert_rows_json(table, rows)
            if errors:
                # Log or handle errors here
                logging.error(f"Errors occurred while inserting rows to bigQuery:{errors}", exc_info=True)
        except GoogleAPIError as e:
            logging.error("An error occurred", exc_info=True)


def run(argv=None):
    pipeline_options = PipelineOptions(argv)
    subscription = os.getenv("BQ_SUB")

    field_definitions = {
        "first_name": Field('first_name', 'first_name', 'First Name', str, 'Vasile'),
        "last_name": Field('last_name', 'last_name', 'Last Name', str, 'Popescu'),
        "personal_number": Field('personal_number', 'ssn', 'Social Personal Number', int, '8240804276204'),
        "birthdate": Field('birthdate', 'date_of_birth', 'Date', 'date', '2023-04-19'),
        "address": Field('address', 'address', 'Address with Postcode', str, 'Intrarea Nr. 167 Nicolau Mare, 197205'),
        "county": Field('county', 'state', 'County Name', str, 'Hunedoara'),
        "phone_number": Field('phone_number', 'phone_number', 'Phone Number', str, '0248 455 730'),
        "mac_address": Field('mac_address', 'mac_address', 'MAC Address', str, 'd4:a3:82:98:85:a6'),
        "ip_address": Field('ip_address', 'ipv4', 'IP Address', str, '172.25.185.30'),
        "job": Field('job', 'job', 'Job Title', str, 'Pictor'),
        "iban": Field('iban', 'iban', 'Bank Account Number', str, 'RO83YUNU3862659030037214'),
        "currency": Field('currency', 'currency_code', 'Currency Code', str, 'XAF'),
        "balance": Field('balance', 'random_number', 'Random Number', int, '75564642'),
        "latitude": Field('latitude', 'latitude', 'Latitude Value', float, '27.6863225'),
        "longitude": Field('longitude', 'longitude', 'Longitude Value', float, '44.431989')
    }

    with beam.Pipeline(options=pipeline_options) as p:
        (p
         | "Read from Pub/Sub" >> beam.io.ReadFromPubSub(subscription=subscription)
         | "Process Messages" >> beam.ParDo(ProcessMessage())
         | "Apply Windowing" >> beam.WindowInto(window.FixedWindows(10))  # 10 seconds windows
         | "Group by Table and Schema" >> beam.GroupByKey()
         | "Write Grouped Data to BigQuery" >> beam.ParDo(WriteGroupedDataToBigQueryFn())
         )


if __name__ == "__main__":
    run()
