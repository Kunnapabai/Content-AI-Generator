"""
Method: GET
Endpoint: https://api.dataforseo.com/v3/keywords_data/bing/search_volume_history/task_get/$id
@see https://docs.dataforseo.com/v3/keywords_data/bing/search_volume_history/tasks_ready/?bash
"""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../../')))
from lib.client import RestClient
from lib.config import username, password
client = RestClient(username, password)

try:
    task_id = '07121547-0696-0260-0000-54d9e57ee0c3'
    response = client.get(f'/v3/keywords_data/bing/search_volume_history/task_get/{task_id}')
    print(response)
    # do something with get result
except Exception as e:
    print(f'An error occurred: {e}')
