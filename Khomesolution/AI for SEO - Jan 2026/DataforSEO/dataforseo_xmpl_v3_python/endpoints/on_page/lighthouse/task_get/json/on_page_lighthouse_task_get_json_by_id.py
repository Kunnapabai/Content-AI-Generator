"""
Method: GET
Endpoint: https://api.dataforseo.com/v3/on_page/lighthouse/task_get/json/$id
"""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../../')))
from lib.client import RestClient
from lib.config import username, password
client = RestClient(username, password)

try:
    task_id = '07201659-2692-0317-0000-e6ef306f636f'
    response = client.get(f'/v3/on_page/lighthouse/task_get/json/{task_id}')
    print(response)
    # do something with get result
except Exception as e:
    print(f'An error occurred: {e}')
