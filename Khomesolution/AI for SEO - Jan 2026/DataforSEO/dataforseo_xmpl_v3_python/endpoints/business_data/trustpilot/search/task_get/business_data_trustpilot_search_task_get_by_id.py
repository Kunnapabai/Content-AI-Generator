"""
Method: GET
Endpoint: https://api.dataforseo.com/v3/business_data/trustpilot/search/task_get/$id
@see https://docs.dataforseo.com/v3/business_data/trustpilot/search/task_get
"""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../../')))
from lib.client import RestClient
from lib.config import username, password
client = RestClient(username, password)

try:
    task_id = '11072149-2692-0374-0000-34e3f9f81c8d'
    response = client.get(f'/v3/business_data/trustpilot/search/task_get/{task_id}')
    print(response)
    # do something with get result
except Exception as e:
    print(f'An error occurred: {e}')
