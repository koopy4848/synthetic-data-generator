class PostData:
    def __init__(self, rows=10, file_name="synthetic_data", file_format="ndjson", field_data=[], rows_per_worker=1000,
                 workers=10, bq_table="synthetic_data", rows_per_part=1000, gcs_file_suffix="synthetic_data",
                 gcs_file_format="ndjson", parts=10):
        self.rows = rows
        self.file_name = file_name
        self.file_format = file_format
        self.field_data = field_data
        self.rows_per_worker = rows_per_worker
        self.workers = workers
        self.bq_table = bq_table
        self.rows_per_part = rows_per_part
        self.gcs_file_suffix = gcs_file_suffix
        self.gcs_file_format = gcs_file_format
        self.parts = parts

    @staticmethod
    def __extract_field_data(data_form):
        field_data = []

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

        return field_data

    @staticmethod
    def extract_post_data(data_form):
        field_data = PostData.__extract_field_data(data_form)

        post_data = PostData(
            rows=int(data_form.get('rows')),
            file_name=data_form.get('file_name'),
            file_format=data_form.get('file_format'),
            field_data=field_data,
            rows_per_worker=int(data_form.get("rows_per_worker")),
            workers=int(data_form.get("workers")),
            bq_table=data_form.get("bq_table"),
            rows_per_part=int(data_form.get("rows_per_part")),
            gcs_file_suffix=data_form.get("gcs_file_suffix"),
            gcs_file_format=data_form.get("gcs_file_format"),
            parts=int(data_form.get("parts"))
        )

        return post_data
