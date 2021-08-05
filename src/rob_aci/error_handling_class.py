import json


class Error(Exception):
    pass


class APICError(Error):

    def __init__(self, message):
        self.message = message


def check_error(request):
    if request.status_code == 503:
        raise APICError("Error Code 503: APIC Temporarily Unavailable - Cannot Login")
    elif request.status_code == 401:
        raise APICError("Error Code 401: APIC User Credentials Incorrect - Failed Authentication")
    elif request.status_code == 400:
        error_message = json.loads(request.text)
        error_message = error_message['imdata'][0]['error']['attributes']['text']
        raise APICError("Error Code 400: Bad Request - %s" % error_message)
    elif request.status_code == 403:
        error_message = json.loads(request.text)
        error_message = error_message['imdata'][0]['error']['attributes']['text']
        raise APICError("Error Code 403: Forbidden - %s" % error_message)
    elif request.status_code == 502:
        raise APICError("Error Code 502: Error Communicating with APIC - Bad Gateway")
    elif request.status_code == 301:
        error_message = json.loads(request.text)
        error_message = error_message['imdata'][0]['error']['attributes']['text']
        raise APICError("Error Code 301: %s" % error_message)
    else:
        error_message = json.loads(request.text)
        error_message = error_message['imdata'][0]['error']['attributes']['text']
        raise APICError("General Error: Code %s. %s" % (request.status_code, error_message))


def build_exception(exception):
    raise APICError(exception)
