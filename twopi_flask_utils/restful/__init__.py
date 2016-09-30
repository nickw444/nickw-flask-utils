from flask import jsonify

def format_error(*errors):
    return {
        '_errors': errors
    }

def output_json(data, code, headers=None):
    if type(data) is str:
        # Handle view returning a string
        message = data
        if code != 200:
            data = format_error(message)
        else:
            data = {'message': message}

    elif code == 405 and type(data) is dict and 'message' in data:
        # handle flask-restful default
        data = format_error(data.get('message'))

    resp = jsonify(data)

    if code:
        resp.status_code = code

    resp.headers.extend(headers)
    return resp

def handle_bad_request(err):
    data = getattr(err, 'data')
    if data:
        # Get validations from the ValidationError object
        messages = data['exc'].messages
    else:
        messages = ['Invalid request']

    # Handle flat responses and give it a generic key.
    if type(messages) == list:
        messages = {
            '_errors': messages
        }

    return jsonify(messages), 422

