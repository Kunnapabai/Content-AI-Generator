"""
Method: GET
Endpoint: https://api.dataforseo.com/v3/serp/google/ai_mode/task_get/html/$id
@see https://docs.dataforseo.com/v3/serp/google/ai_mode/task_get/html
"""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../../../')))
from lib.client import RestClient
from lib.config import username, password
client = RestClient(username, password)

try:
    task_id = '07011003-0696-0066-0000-c8fde60a6c6a'
    response = client.get(f'/v3/serp/google/ai_mode/task_get/html/{task_id}')
    print(response)
    # do something with get result
except Exception as e:
    print(f'An error occurred: {e}')
