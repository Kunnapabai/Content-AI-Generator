"""
Method: POST
Endpoint: https://api.dataforseo.com/v3/serp/ai_summary
"""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))
from lib.client import RestClient
from lib.config import username, password
client = RestClient(username, password)

post_data = []
post_data.append({
        'task_id': '10181052-0696-0066-1000-c98593b145f7',
        'prompt': 'give a short description of 100 characters',
        'include_links': True,
        'fetch_content': True,
        'support_extra': True
    })
try:
    response = client.post('/v3/serp/ai_summary', post_data)
    print(response)
    # do something with post result
except Exception as e:
    print(f'An error occurred: {e}')
