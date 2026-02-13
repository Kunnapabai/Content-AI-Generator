"""
Method: GET
Endpoint: https://api.dataforseo.com/v3/serp/naver/organic/task_get/regular/$id
@see https://docs.dataforseo.com/v3/serp/naver/organic/task_get/regular
"""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../../../')))
from lib.client import RestClient
from lib.config import username, password
client = RestClient(username, password)

try:
    task_id = '12091722-1535-0066-0000-1803f27dfe73'
    response = client.get(f'/v3/serp/naver/organic/task_get/regular/{task_id}')
    print(response)
    # do something with get result
except Exception as e:
    print(f'An error occurred: {e}')
