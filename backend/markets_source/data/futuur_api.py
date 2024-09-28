import requests
import json
import os
from event_models import StandardizedEvent
from dotenv import load_dotenv
import hashlib
import hmac
import datetime
import requests
from collections import OrderedDict
from urllib.parse import urlencode

load_dotenv()
PUBLIC_KEY = os.getenv("FUTUUR_PUBLIC_KEY")
PRIVATE_KEY = os.getenv("FUTUUR_PRIVATE_KEY")
print(PUBLIC_KEY, PRIVATE_KEY)
BASE_URL = "https://api.futuur.com/api/v1/"

def build_signature(params: dict):
    params_to_sign = OrderedDict(sorted(list(params.items())))

    params_to_sign = urlencode(params_to_sign)

    encoded_params = params_to_sign.encode('utf-8')
    encoded_private_key = PRIVATE_KEY.encode('utf-8')

    data = {
        'hmac': hmac.new(encoded_private_key, encoded_params, hashlib.sha512).hexdigest(),
        'Timestamp': params['Timestamp']
    }

    return data


def build_headers(params: dict):
    signature = build_signature(params)
    headers = {
        'Key': PUBLIC_KEY,
        'Timestamp': str(signature.get('Timestamp')),
        'HMAC': signature.get('hmac')
    }
    return headers


signature = build_signature({
    'Key': PUBLIC_KEY,
    'Timestamp': int(datetime.datetime.utcnow().timestamp()),
    'category': 5
})


headers = build_headers({
    'Key': PUBLIC_KEY,
    'Timestamp': int(datetime.datetime.utcnow().timestamp()),
    'category': 5
})

def call_api(endpoint: str, params: dict = None, payload: dict = None, method: str = 'GET') -> dict:
    url_params = '?' + urlencode(params) if params else ''
    headers = build_headers(params or payload)
    url = BASE_URL + endpoint + url_params

    request_kwargs = {
        'method': method,
        'url': url,
        'headers': headers,
    }
    if method.upper() == 'POST' and payload is not None:
        request_kwargs['json'] = payload

    response = requests.request(**request_kwargs)
    return response.json()

response = call_api(
    endpoint='markets/',
    params={
        'Key': PUBLIC_KEY,
        'Timestamp': int(datetime.datetime.utcnow().timestamp()),
        'currency_mode': 'real_money',
        'hide_my_bets': 'true',
        'limit': 1000,
        'live': 'false',

    },
    method='GET'
)
# print with indent

print(json.dumps(response, indent=4))