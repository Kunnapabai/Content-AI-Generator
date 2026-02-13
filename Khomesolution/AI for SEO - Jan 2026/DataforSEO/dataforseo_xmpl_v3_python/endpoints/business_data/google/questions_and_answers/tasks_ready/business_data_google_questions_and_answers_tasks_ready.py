"""
Method: GET
Endpoint: https://api.dataforseo.com/v3/business_data/google/questions_and_answers/tasks_ready
@see https://docs.dataforseo.com/v3/business_data/google/questions_and_answers/tasks_ready/
"""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../../')))
from lib.client import RestClient
from lib.config import username, password
client = RestClient(username, password)

try:
    response = client.get('/v3/business_data/google/questions_and_answers/tasks_ready')
    print(response)
    # do something with get result
except Exception as e:
    print(f'An error occurred: {e}')
