"""
Method: POST
Endpoint: https://api.dataforseo.com/v3/dataforseo_labs/apple/bulk_app_metrics/live
@see https://docs.dataforseo.com/v3/dataforseo_labs/apple/bulk_app_metrics/live/
"""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../../')))
from lib.client import RestClient
from lib.config import username, password
client = RestClient(username, password)

post_data = []
post_data.append({
        'app_ids': [
            '686449807',
            '835599320',
            '310633997',
            '284882215'
        ],
        'language_name': 'English',
        'location_code': 2840
    })
try:
    response = client.post('/v3/dataforseo_labs/apple/bulk_app_metrics/live', post_data)
    print(response)
    # do something with post result
except Exception as e:
    print(f'An error occurred: {e}')
