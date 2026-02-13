"""
Method: POST
Endpoint: https://api.dataforseo.com/v3/dataforseo_labs/google/domain_metrics_by_categories/live
@see https://docs.dataforseo.com/v3/dataforseo_labs/google/domain_metrics_by_categories/live/
"""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../../')))
from lib.client import RestClient
from lib.config import username, password
client = RestClient(username, password)

post_data = []
post_data.append({
        'location_code': 2840,
        'language_code': 'en',
        'category_codes': [
            13418,
            11494
        ],
        'first_date': '2021-07-01',
        'second_date': '2021-10-01',
        'limit': 3
    })
try:
    response = client.post('/v3/dataforseo_labs/google/domain_metrics_by_categories/live', post_data)
    print(response)
    # do something with post result
except Exception as e:
    print(f'An error occurred: {e}')
