"""
Method: POST
Endpoint: https://api.dataforseo.com/v3/on_page/page_screenshot
@see https://docs.dataforseo.com/v3/on_page/page_screenshot
"""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))
from lib.client import RestClient
from lib.config import username, password
client = RestClient(username, password)

post_data = []
post_data.append({
        'url': 'https://dataforseo.com/faq'
    })
try:
    response = client.post('/v3/on_page/page_screenshot', post_data)
    print(response)
    # do something with post result
except Exception as e:
    print(f'An error occurred: {e}')
