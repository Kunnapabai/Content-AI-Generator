"""
Method: GET
Endpoint: https://api.dataforseo.com/v3/merchant/amazon/sellers/task_get/advanced/$id
"""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../../../')))
from lib.client import RestClient
from lib.config import username, password
client = RestClient(username, password)

try:
    task_id = '07091025-2692-0309-0000-58957fc60132'
    response = client.get(f'/v3/merchant/amazon/sellers/task_get/advanced/{task_id}')
    print(response)
    # do something with get result
except Exception as e:
    print(f'An error occurred: {e}')
