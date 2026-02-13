"""
Method: POST
Endpoint: https://api.dataforseo.com/v3/keywords_data/google_ads/ad_traffic_by_keywords/task_post
@see https://docs.dataforseo.com/v3/keywords\_data/google_ads/ad\_traffic\_by\_keywords/task\_post
"""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../../')))
from lib.client import RestClient
from lib.config import username, password
client = RestClient(username, password)

post_data = []
post_data.append({
        'language_code': 'en',
        'location_code': 2840,
        'bid': 999,
        'match': 'exact',
        'keywords': [
            'buy laptop',
            'cheap laptops for sale',
            'purchase laptop'
        ]
    })
try:
    response = client.post('/v3/keywords_data/google_ads/ad_traffic_by_keywords/task_post', post_data)
    print(response)
    # do something with post result
except Exception as e:
    print(f'An error occurred: {e}')
