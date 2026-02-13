"""
Method: POST
Endpoint: https://api.dataforseo.com/v3/on_page/redirect_chains
"""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))
from lib.client import RestClient
from lib.config import username, password
client = RestClient(username, password)

post_data = []
post_data.append({
        'id': '06081310-0696-0216-0000-7edde8059143'
    })
try:
    response = client.post('/v3/on_page/redirect_chains', post_data)
    print(response)
    # do something with post result
except Exception as e:
    print(f'An error occurred: {e}')
