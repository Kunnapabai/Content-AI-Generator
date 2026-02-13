"""
Method: POST
Endpoint: https://api.dataforseo.com/v3/content_analysis/sentiment_analysis/live
@see https://docs.dataforseo.com/v3/content_analysis/sentiment_analysis/live/
"""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../')))
from lib.client import RestClient
from lib.config import username, password
client = RestClient(username, password)

post_data = []
post_data.append({
        'keyword': 'logitech',
        'search_mode': 'as_is',
        'internal_list_limit': 8,
        'positive_connotation_threshold': 0.5,
        'sentiments_connotation_threshold': 1,
        'initial_dataset_filters': [
            [
                'content_info.rating.rating_value',
                '>',
                0
            ]
        ]
    })
try:
    response = client.post('/v3/content_analysis/sentiment_analysis/live', post_data)
    print(response)
    # do something with post result
except Exception as e:
    print(f'An error occurred: {e}')
