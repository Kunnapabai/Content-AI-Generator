"""
Method: GET
Endpoint: https://api.dataforseo.com/v3/merchant/amazon/products/task_get/html/$id
"""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../../../')))
from lib.client import RestClient
from lib.config import username, password
client = RestClient(username, password)

try:
    task_id = '04170913-0696-0179-0000-707d6a06f64b'
    response = client.get(f'/v3/merchant/amazon/products/task_get/html/{task_id}')
    print(response)
    # do something with get result
except Exception as e:
    print(f'An error occurred: {e}')
