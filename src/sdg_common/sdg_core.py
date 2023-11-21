import json
from datetime import date
from decimal import Decimal
from faker import Faker


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


def row_to_json(faker_methods, headers):
    row_data = fake_row(faker_methods)
    row_dict = dict(zip(headers, row_data))
    return json.dumps(row_dict, ensure_ascii=False, cls=CustomJSONEncoder)
