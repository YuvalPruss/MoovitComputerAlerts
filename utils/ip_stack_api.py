import json
import requests
from typing import Dict

IP_STACK_API_URL = 'http://api.ipstack.com/'
ACCESS_KEY = '71ef224880f350c823f8136aa18be783'


def get_location_by_ip(ip_address: str) -> Dict:
    url = IP_STACK_API_URL + '/' + ip_address
    api_key = {'access_key': ACCESS_KEY}

    response = requests.get(url, params=api_key)
    return response.json()
