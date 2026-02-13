"""
Method: GET
Endpoint: https://api.dataforseo.com/v3/app_data/google/app_reviews/task_get/advanced/$id
@see https://docs.dataforseo.com/v3/app_data/google/app_reviews/task_get/advanced/
"""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../../../')))
from lib.client import RestClient
from lib.config import username, password
client = RestClient(username, password)

try:
    task_id = '04201911-2692-0425-0000-bf9ec715f6d6'
    response = client.get(f'/v3/app_data/google/app_reviews/task_get/advanced/{task_id}')
    print(response)
    # do something with get result
except Exception as e:
    print(f'An error occurred: {e}')
