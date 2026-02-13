"""
Method: GET
Endpoint: https://api.dataforseo.com/v3/serp/google/search_by_image/task_get/html/$id
@see https://docs.dataforseo.com/v3/serp/google/search_by_image/task_get/html
"""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../../../')))
from lib.client import RestClient
from lib.config import username, password
client = RestClient(username, password)

try:
    task_id = '03051341-0696-0066-0000-88c181a4d623'
    response = client.get(f'/v3/serp/google/search_by_image/task_get/html/{task_id}')
    print(response)
    # do something with get result
except Exception as e:
    print(f'An error occurred: {e}')
