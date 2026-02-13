"""
Method: POST
Endpoint: https://api.dataforseo.com/v3/content_analysis/category_trends/live
@see https://docs.dataforseo.com/v3/content_analysis/category_trends/live/
"""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../')))
from lib.client import RestClient
from lib.config import username, password
client = RestClient(username, password)

post_data = []
post_data.append({
        'category_code': 10994,
        'date_from': '2022-05-10',
        'date_group': 'month',
        'search_mode': 'one_per_domain',
        'internal_list_limit': 10,
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
    response = client.post('/v3/content_analysis/category_trends/live', post_data)
    print(response)
    # do something with post result
except Exception as e:
    print(f'An error occurred: {e}')
