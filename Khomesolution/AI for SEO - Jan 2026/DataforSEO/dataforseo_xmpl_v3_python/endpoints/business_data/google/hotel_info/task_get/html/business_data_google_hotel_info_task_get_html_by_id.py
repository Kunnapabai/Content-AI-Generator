"""
Method: GET
Endpoint: https://api.dataforseo.com/v3/business_data/google/hotel_info/task_get/html/$id
"""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../../../')))
from lib.client import RestClient
from lib.config import username, password
client = RestClient(username, password)

try:
    task_id = '05211451-2692-0282-0000-f0d1d5e9012d'
    response = client.get(f'/v3/business_data/google/hotel_info/task_get/html/{task_id}')
    print(response)
    # do something with get result
except Exception as e:
    print(f'An error occurred: {e}')
