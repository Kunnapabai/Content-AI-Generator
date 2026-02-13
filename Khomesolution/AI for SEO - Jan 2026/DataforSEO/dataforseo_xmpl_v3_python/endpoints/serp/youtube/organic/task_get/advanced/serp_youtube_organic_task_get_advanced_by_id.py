"""
Method: GET
Endpoint: https://api.dataforseo.com/v3/serp/youtube/organic/task_get/advanced/$id
@see https://docs.dataforseo.com/v3/serp/youtube/organic/task_get/advanced
"""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../../../')))
from lib.client import RestClient
from lib.config import username, password
client = RestClient(username, password)

try:
    task_id = '11221957-0696-0066-0000-75be7f0cc10e'
    response = client.get(f'/v3/serp/youtube/organic/task_get/advanced/{task_id}')
    print(response)
    # do something with get result
except Exception as e:
    print(f'An error occurred: {e}')
