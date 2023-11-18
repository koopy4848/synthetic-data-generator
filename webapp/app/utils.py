from faker import Faker


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


