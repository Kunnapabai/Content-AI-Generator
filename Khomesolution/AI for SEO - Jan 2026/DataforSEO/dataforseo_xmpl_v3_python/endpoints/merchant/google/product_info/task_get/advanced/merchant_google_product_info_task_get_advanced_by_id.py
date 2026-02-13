"""
Method: GET
Endpoint: https://api.dataforseo.com/v3/merchant/google/product_info/task_get/advanced/$id
@see https://docs.dataforseo.com/v3/merchant/google/product_info/task_get/advanced
"""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../../../')))
from lib.client import RestClient
from lib.config import username, password
client = RestClient(username, password)

try:
    task_id = '07192047-0696-0455-0000-f0df9c2bb0f6'
    response = client.get(f'/v3/merchant/google/product_info/task_get/advanced/{task_id}')
    print(response)
    # do something with get result
except Exception as e:
    print(f'An error occurred: {e}')
