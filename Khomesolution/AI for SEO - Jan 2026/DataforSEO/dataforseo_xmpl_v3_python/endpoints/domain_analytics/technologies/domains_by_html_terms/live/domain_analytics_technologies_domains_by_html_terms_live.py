"""
Method: POST
Endpoint: https://api.dataforseo.com/v3/domain_analytics/technologies/domains_by_html_terms/live
@see https://docs.dataforseo.com/v3/domain_analytics/technologies/domains_by_html_terms/live/
"""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../../')))
from lib.client import RestClient
from lib.config import username, password
client = RestClient(username, password)

post_data = []
post_data.append({
        'search_terms': [
            'data-attrid'
        ],
        'order_by': [
            'last_visited,desc'
        ],
        'limit': 10,
        'offset': 0
    })
try:
    response = client.post('/v3/domain_analytics/technologies/domains_by_html_terms/live', post_data)
    print(response)
    # do something with post result
except Exception as e:
    print(f'An error occurred: {e}')
