import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions
import json
from datetime import date
from decimal import Decimal
import os


class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return str(obj)  # Convert Decimal to string
        elif isinstance(obj, date):
            return obj.isoformat()  # Convert date to ISO string format
        return json.JSONEncoder.default(self, obj)


#class Field:
 #   def __init__(self, field_id, faker_method, display, data_type, example):
 #       self.field_id = field_id
 #       self.faker_method = faker_method
 #       self.display = display
 #       self.data_type = data_type
 #       self.example = example


def invoke_method(obj, method_name):
    # Check if the method exists in the object
    if hasattr(obj, method_name):
        method = getattr(obj, method_name)
        if callable(method):
            return method()  # Call the method and return its result
    else:
        return None  # or raise an error if the method does not exist


class WriteDataToCloudStorageFn(beam.DoFn):
    def start_bundle(self):
        from google.cloud import storage
        self.gcs_bucket = os.getenv('BUCKET_NAME', 'default_bucket')
        self.client = storage.Client()
        self.field_definitions = {
            "first_name": ('first_name', 'first_name', 'First Name', str, 'Vasile'),
            "last_name": ('last_name', 'last_name', 'Last Name', str, 'Popescu'),
            "personal_number": ('personal_number', 'ssn', 'Social Personal Number', int, '8240804276204'),
            "birthdate": ('birthdate', 'date_of_birth', 'Date', 'date', '2023-04-19'),
            "address": ('address', 'address', 'Address with Postcode', str, 'Intrarea Nr. 167 Nicolau Mare, 197205'),
            "county": ('county', 'state', 'County Name', str, 'Hunedoara'),
            "phone_number": ('phone_number', 'phone_number', 'Phone Number', str, '0248 455 730'),
            "mac_address": ('mac_address', 'mac_address', 'MAC Address', str, 'd4:a3:82:98:85:a6'),
            "ip_address": ('ip_address', 'ipv4', 'IP Address', str, '172.25.185.30'),
            "job": ('job', 'job', 'Job Title', str, 'Pictor'),
            "iban": ('iban', 'iban', 'Bank Account Number', str, 'RO83YUNU3862659030037214'),
            "currency": ('currency', 'currency_code', 'Currency Code', str, 'XAF'),
            "balance": ('balance', 'random_number', 'Random Number', int, '75564642'),
            "latitude": ('latitude', 'latitude', 'Latitude Value', float, '27.6863225'),
            "longitude": ('longitude', 'longitude', 'Longitude Value', float, '44.431989')
        }

    def process(self, element):
        message = json.loads(element)
        file_name = message['file_name']
        file_format = message['file_format']
        field_data = message['field_data']
        rows = message['rows']

        faker_methods = [self.field_definitions[field[0]][1] for field in field_data]
        headers = [field[1] if field[1] else self.field_definitions[field[0]][2] for field in field_data]

        bucket = self.client.bucket(self.gcs_bucket)
        blob = bucket.blob(file_name)

        import io
        output = io.StringIO()

        from faker import Faker
        faker = Faker()

        import csv
        if file_format == 'csv':
            content_type = 'text/csv'
            writer = csv.DictWriter(output, fieldnames=headers)
            writer.writeheader()
            for _ in range(rows):
                row_data = [invoke_method(faker, method_name) for method_name in faker_methods]
                row_dict = dict(zip(headers, row_data))
                writer.writerow(row_dict)

        elif file_format in ["json", "ndjson"]:
            content_type = 'application/json'
            json_rows = []
            for _ in range(rows):
                row_data = [invoke_method(faker, method_name) for method_name in faker_methods]
                row_dict = dict(zip(headers, row_data))
                json_row = json.dumps(row_dict, ensure_ascii=False, cls=CustomJSONEncoder)
                if file_format == "ndjson":
                    output.write(json_row + "\n")
                else:
                    json_rows.append(json_row)
            if file_format == "json":
                output.write(json.dumps(json_rows, ensure_ascii=False, cls=CustomJSONEncoder))

        blob.upload_from_string(output.getvalue(), content_type=content_type)


def run(argv=None):
    pipeline_options = PipelineOptions(argv)
    subscription = os.getenv("GCS_SUB")

    with beam.Pipeline(options=pipeline_options) as p:
        (p
         | "Read from Pub/Sub" >> beam.io.ReadFromPubSub(subscription=subscription)
         | "Process Messages" >> beam.ParDo(WriteDataToCloudStorageFn())
         )


if __name__ == "__main__":
    run()
