"""
Method: GET
Endpoint: https://api.dataforseo.com/v3/keywords_data/bing/keywords_for_keywords/task_get/$id
"""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../../')))
from lib.client import RestClient
from lib.config import username, password
client = RestClient(username, password)

try:
    task_id = '10251444-0001-0107-0000-7fc657a2f62c'
    response = client.get(f'/v3/keywords_data/bing/keywords_for_keywords/task_get/{task_id}')
    print(response)
    # do something with get result
except Exception as e:
    print(f'An error occurred: {e}')
