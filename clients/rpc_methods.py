from jsonrpcserver import method


def custom_method(prop, _method):
    return method(_method(prop))
