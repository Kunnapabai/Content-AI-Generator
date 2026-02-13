"""
Method: POST
Endpoint: https://api.dataforseo.com/v3/keywords_data/bing/audience_estimation/live
@see https://docs.dataforseo.com/v3/keywords_data/bing/audience_estimation/live
"""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../../')))
from lib.client import RestClient
from lib.config import username, password
client = RestClient(username, password)

post_data = []
post_data.append({
        'location_coordinate': '29.6821525,-82.4098881,100',
        'age': [
            'twenty_five_to_thirty_four',
            'eighteen_to_twenty_four',
            'unknown'
        ],
        'bid': 1,
        'daily_budget': 24,
        'gender': [
            'male'
        ],
        'industry': [
            806303407,
            806301758
        ],
        'job_function': [
            806298607
        ]
    })
try:
    response = client.post('/v3/keywords_data/bing/audience_estimation/live', post_data)
    print(response)
    # do something with post result
except Exception as e:
    print(f'An error occurred: {e}')
