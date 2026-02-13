"""
Method: GET
Endpoint: https://api.dataforseo.com/v3/serp/google/organic/task_get/html/$id
@see https://docs.dataforseo.com/v3/serp/google/organic/task_get/html
"""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../../../')))
from lib.client import RestClient
from lib.config import username, password
client = RestClient(username, password)

try:
    task_id = '12091537-1535-0066-0000-29589faecd6d'
    response = client.get(f'/v3/serp/google/organic/task_get/html/{task_id}')
    print(response)
    # do something with get result
except Exception as e:
    print(f'An error occurred: {e}')
