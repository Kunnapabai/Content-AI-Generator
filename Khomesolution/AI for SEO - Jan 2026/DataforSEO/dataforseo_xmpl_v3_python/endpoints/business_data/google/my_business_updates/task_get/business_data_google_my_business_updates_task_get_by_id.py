"""
Method: GET
Endpoint: https://api.dataforseo.com/v3/business_data/google/my_business_updates/task_get/$id
"""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../../')))
from lib.client import RestClient
from lib.config import username, password
client = RestClient(username, password)

try:
    task_id = '09091111-0696-0243-0000-1e835179296a'
    response = client.get(f'/v3/business_data/google/my_business_updates/task_get/{task_id}')
    print(response)
    # do something with get result
except Exception as e:
    print(f'An error occurred: {e}')
