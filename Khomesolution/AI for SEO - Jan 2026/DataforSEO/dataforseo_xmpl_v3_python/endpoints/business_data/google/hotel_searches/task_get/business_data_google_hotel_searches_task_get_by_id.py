"""
Method: GET
Endpoint: https://api.dataforseo.com/v3/business_data/google/hotel_searches/task_get/$id
"""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../../')))
from lib.client import RestClient
from lib.config import username, password
client = RestClient(username, password)

try:
    task_id = '05211407-2692-0290-0000-1af3f4fc3453'
    response = client.get(f'/v3/business_data/google/hotel_searches/task_get/{task_id}')
    print(response)
    # do something with get result
except Exception as e:
    print(f'An error occurred: {e}')
