"""
Method: GET
Endpoint: https://api.dataforseo.com/v3/on_page/summary/$id
"""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))
from lib.client import RestClient
from lib.config import username, password
client = RestClient(username, password)

try:
    task_id = '08101056-0696-0216-0000-721423f84e3d'
    response = client.get(f'/v3/on_page/summary/{task_id}')
    print(response)
    # do something with get result
except Exception as e:
    print(f'An error occurred: {e}')
