# -*- coding: utf-8 -*-

import requests
import urllib3
from . import logger

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def __retry_on_503(core, request, response, retry=True):
    if not retry:
        return None

    if response.status_code == 503:
        core.time.sleep(2)
        request['validate'] = lambda response: __retry_on_503(core, request, response, retry=False)
        return request

def execute(core, request, session=None):
    if not session:
        session = requests

    request.setdefault('timeout', 10)

    validate = request.pop('validate', None)
    next = request.pop('next', None)

    if not validate:
        validate = lambda response: __retry_on_503(core, request, response)

    if next:
        request.pop('stream', None)

    logger.debug(f"{request['method']} ^ - {request['url']}")
    try:
        response = session.request(verify=False, **request)
        exc = ''
    except:
        exc = core.traceback.format_exc()
        response = lambda: None
        response.text = ''
        response.content = ''
        response.status_code = 500
    logger.debug(
        f"{request['method']} $ - {request['url']} - {response.status_code}, {exc}"
    )


    if alt_request := validate(response):
        return execute(core, alt_request)

    if next and response.status_code == 200:
        if next_request := next(response):
            return execute(core, next_request)
        else:
            return None

    return response
