from . import test_blueprint


@test_blueprint.route('/test')
def test():
    return "This is a test blueprint!"
