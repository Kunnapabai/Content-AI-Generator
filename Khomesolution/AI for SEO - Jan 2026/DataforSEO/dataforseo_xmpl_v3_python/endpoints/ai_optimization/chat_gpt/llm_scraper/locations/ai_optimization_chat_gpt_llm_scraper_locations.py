"""
Method: GET
Endpoint: https://api.dataforseo.com/v3/ai_optimization/chat_gpt/llm_scraper/locations
@see https://docs.dataforseo.com/v3/ai_optimization/chat_gpt/llm_scraper/locations
"""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../../')))
from lib.client import RestClient
from lib.config import username, password
client = RestClient(username, password)

try:
    response = client.get('/v3/ai_optimization/chat_gpt/llm_scraper/locations')
    print(response)
    # do something with get result
except Exception as e:
    print(f'An error occurred: {e}')
