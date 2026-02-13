"""
Method: GET
Endpoint: https://api.dataforseo.com/v3/serp/google/finance_markets/task_get/advanced/$id
@see https://docs.dataforseo.com/v3/serp/google/finance_markets/task_get/advanced/
"""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../../../')))
from lib.client import RestClient
from lib.config import username, password
client = RestClient(username, password)

try:
    task_id = '03051738-0696-0066-0000-e59299b01755'
    response = client.get(f'/v3/serp/google/finance_markets/task_get/advanced/{task_id}')
    print(response)
    # do something with get result
except Exception as e:
    print(f'An error occurred: {e}')
