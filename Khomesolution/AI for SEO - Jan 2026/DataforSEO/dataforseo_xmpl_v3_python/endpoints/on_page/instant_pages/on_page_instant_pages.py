"""
Method: POST
Endpoint: https://api.dataforseo.com/v3/on_page/instant_pages
"""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))
from lib.client import RestClient
from lib.config import username, password
client = RestClient(username, password)

post_data = []
post_data.append({
        'url': 'https://dataforseo.com/blog',
        'custom_js': 'meta = {}; meta.url = document.URL; meta;'
    })
try:
    response = client.post('/v3/on_page/instant_pages', post_data)
    print(response)
    # do something with post result
except Exception as e:
    print(f'An error occurred: {e}')
