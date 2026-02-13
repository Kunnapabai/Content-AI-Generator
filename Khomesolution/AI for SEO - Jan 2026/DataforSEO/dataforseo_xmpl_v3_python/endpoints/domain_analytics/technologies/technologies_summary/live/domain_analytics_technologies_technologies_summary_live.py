"""
Method: POST
Endpoint: https://api.dataforseo.com/v3/domain_analytics/technologies/technologies_summary/live
@see https://docs.dataforseo.com/v3/domain_analytics/technologies/technologies_summary/live/
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
        'mode': 'entry',
        'technologies': [
            'Ngi'
        ],
        'keywords': [
            'WordPress'
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
        ]
    })
try:
    response = client.post('/v3/domain_analytics/technologies/technologies_summary/live', post_data)
    print(response)
    # do something with post result
except Exception as e:
    print(f'An error occurred: {e}')
