import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions, SetupOptions
import json
from sdg_common.sdg_core import fake_row


class ProcessMessage(beam.DoFn):
    def to_runner_api_parameter(self, unused_context):
        pass

    def process_batch(self, batch, *args, **kwargs):
        pass

    def process(self, element):
        message = json.loads(element)
        bq_table = message['bq_table']
        field_data = message['field_data']
        rows = message['rows']

        data = [fake_row(field_data) for _ in range(rows)]
        return [{'table': bq_table, 'data': row} for row in data]


def run(argv=None):
    pipeline_options = PipelineOptions(argv)

    # Use setup.py to install additional dependencies in the workers.
    setup_options = pipeline_options.view_as(SetupOptions)
    setup_options.setup_file = './setup.py'

    with beam.Pipeline(options=pipeline_options) as p:
        (p
         | "Read from Pub/Sub" >> beam.io.ReadFromPubSub(topic="your-pubsub-topic")
         | "Process Messages" >> beam.ParDo(ProcessMessage())
         | "Write to BigQuery" >> beam.io.WriteToBigQuery(
             table=lambda element: element['table'],
             schema='SCHEMA_DEFINITION',  # Define your schema
             create_disposition=beam.io.BigQueryDisposition.CREATE_IF_NEEDED,
             write_disposition=beam.io.BigQueryDisposition.WRITE_APPEND)
        )


if __name__ == "__main__":
    run()
