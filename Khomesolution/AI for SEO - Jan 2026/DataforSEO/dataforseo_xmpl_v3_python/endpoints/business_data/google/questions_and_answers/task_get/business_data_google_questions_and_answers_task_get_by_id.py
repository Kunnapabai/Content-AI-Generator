"""
Method: GET
Endpoint: https://api.dataforseo.com/v3/business_data/google/questions_and_answers/task_get/$id
@see https://docs.dataforseo.com/v3/business_data/google/questions_and_answers/task_get/<br><br>
"""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../../')))
from lib.client import RestClient
from lib.config import username, password
client = RestClient(username, password)

try:
    task_id = '04231153-0696-0577-0000-14a834c0e681'
    response = client.get(f'/v3/business_data/google/questions_and_answers/task_get/{task_id}')
    print(response)
    # do something with get result
except Exception as e:
    print(f'An error occurred: {e}')
