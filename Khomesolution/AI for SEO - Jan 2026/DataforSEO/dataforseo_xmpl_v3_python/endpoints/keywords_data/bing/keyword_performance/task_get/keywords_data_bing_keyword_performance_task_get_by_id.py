"""
Method: GET
Endpoint: https://api.dataforseo.com/v3/keywords_data/bing/keyword_performance/task_get/$id
"""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../../')))
from lib.client import RestClient
from lib.config import username, password
client = RestClient(username, password)

try:
    task_id = '10261501-0696-0254-0000-6f03c275b8de'
    response = client.get(f'/v3/keywords_data/bing/keyword_performance/task_get/{task_id}')
    print(response)
    # do something with get result
except Exception as e:
    print(f'An error occurred: {e}')
