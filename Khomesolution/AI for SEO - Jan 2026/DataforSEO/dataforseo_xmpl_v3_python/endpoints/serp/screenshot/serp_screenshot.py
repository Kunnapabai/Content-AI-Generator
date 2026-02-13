"""
Method: POST
Endpoint: https://api.dataforseo.com/v3/serp/screenshot
@see https://api.dataforseo.com/v3/serp/screenshot
"""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))
from lib.client import RestClient
from lib.config import username, password
client = RestClient(username, password)

post_data = []
post_data.append({
        'task_id': '07131637-0696-0066-0000-5934d7e3dcbd',
        'browser_screen_scale_factor': 0.5
    })
try:
    response = client.post('/v3/serp/screenshot', post_data)
    print(response)
    # do something with post result
except Exception as e:
    print(f'An error occurred: {e}')
