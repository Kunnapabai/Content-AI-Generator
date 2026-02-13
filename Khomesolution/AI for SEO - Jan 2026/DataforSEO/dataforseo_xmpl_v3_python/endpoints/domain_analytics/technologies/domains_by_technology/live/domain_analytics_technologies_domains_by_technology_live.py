"""
Method: POST
Endpoint: https://api.dataforseo.com/v3/domain_analytics/technologies/domains_by_technology/live
@see https://docs.dataforseo.com/v3/domain_analytics/technologies/domains_by_technology/live/
"""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../../')))
from lib.client import RestClient
from lib.config import username, password
client = RestClient(username, password)

post_data = []
post_data.append({
        'technology_paths': [
            {
                'path': 'content.cms',
                'name': 'Nginx'
            }
        ],
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
            'last_visited,desc'
        ],
        'limit': 10000
    })
try:
    response = client.post('/v3/domain_analytics/technologies/domains_by_technology/live', post_data)
    print(response)
    # do something with post result
except Exception as e:
    print(f'An error occurred: {e}')
