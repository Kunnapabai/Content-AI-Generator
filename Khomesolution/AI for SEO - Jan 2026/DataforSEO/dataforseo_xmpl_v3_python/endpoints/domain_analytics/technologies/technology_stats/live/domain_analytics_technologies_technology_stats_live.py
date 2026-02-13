"""
Method: POST
Endpoint: https://api.dataforseo.com/v3/domain_analytics/technologies/technology_stats/live
@see https://docs.dataforseo.com/v3/domain_analytics/technologies/technology_stats/live/
"""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../../')))
from lib.client import RestClient
from lib.config import username, password
client = RestClient(username, password)

post_data = []
post_data.append({
        'technology': 'jQuery',
        'date_from': '2022-01-01',
        'date_to': '2023-06-01'
    })
try:
    response = client.post('/v3/domain_analytics/technologies/technology_stats/live', post_data)
    print(response)
    # do something with post result
except Exception as e:
    print(f'An error occurred: {e}')
