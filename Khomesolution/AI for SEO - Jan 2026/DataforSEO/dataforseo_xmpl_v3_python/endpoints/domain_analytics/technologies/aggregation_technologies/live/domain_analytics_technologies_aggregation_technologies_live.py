"""
Method: POST
Endpoint: https://api.dataforseo.com/v3/domain_analytics/technologies/aggregation_technologies/live
@see https://docs.dataforseo.com/v3/domain_analytics/technologies/aggregation_technologies/live/
"""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../../')))
from lib.client import RestClient
from lib.config import username, password
client = RestClient(username, password)

post_data = []
post_data.append({
        'keyword': 'WordPress',
        'filters': [
            [
                'country_iso_code',
                '=',
                'US'
            ],
            'and',
            [
                'domain_rank',
                '>',
                800
            ]
        ],
        'order_by': [
            'groups_count,desc'
        ],
        'limit': 10
    })
try:
    response = client.post('/v3/domain_analytics/technologies/aggregation_technologies/live', post_data)
    print(response)
    # do something with post result
except Exception as e:
    print(f'An error occurred: {e}')
