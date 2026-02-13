"""
Method: GET
Endpoint: https://api.dataforseo.com/v3/keywords_data/bing/search_volume/task_get/$id
"""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../../')))
from lib.client import RestClient
from lib.config import username, password
client = RestClient(username, password)

try:
    task_id = '10081455-0001-0110-0000-c75b21dcca1c'
    response = client.get(f'/v3/keywords_data/bing/search_volume/task_get/{task_id}')
    print(response)
    # do something with get result
except Exception as e:
    print(f'An error occurred: {e}')
