"""
Method: GET
Endpoint: https://api.dataforseo.com/v3/business_data/google/reviews/task_get/$id
@see https://docs.dataforseo.com/v3/business_data/google/reviews/task_get
"""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../../')))
from lib.client import RestClient
from lib.config import username, password
client = RestClient(username, password)

try:
    task_id = '05211333-2692-0298-0000-047fc45592ce'
    response = client.get(f'/v3/business_data/google/reviews/task_get/{task_id}')
    print(response)
    # do something with get result
except Exception as e:
    print(f'An error occurred: {e}')
