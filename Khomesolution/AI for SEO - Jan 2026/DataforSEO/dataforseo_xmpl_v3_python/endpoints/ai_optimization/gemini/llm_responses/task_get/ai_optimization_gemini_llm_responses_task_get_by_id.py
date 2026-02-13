"""
Method: GET
Endpoint: https://api.dataforseo.com/v3/ai_optimization/gemini/llm_responses/task_get/$id
@see https://docs.dataforseo.com/v3/ai_optimization/gemini/llm_responses/task_get
"""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../../')))
from lib.client import RestClient
from lib.config import username, password
client = RestClient(username, password)

try:
    task_id = '01211202-0696-0613-0000-bbf2c3dadd0b'
    response = client.get(f'/v3/ai_optimization/gemini/llm_responses/task_get/{task_id}')
    print(response)
    # do something with get result
except Exception as e:
    print(f'An error occurred: {e}')
