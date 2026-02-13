"""
Method: POST
Endpoint: https://api.dataforseo.com/v3/business_data/google/questions_and_answers/live
@see https://docs.dataforseo.com/v3/business_data/google/questions_and_answers/live/
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
        'keyword': 'The Last Bookstore'
    })
try:
    response = client.post('/v3/business_data/google/questions_and_answers/live', post_data)
    print(response)
    # do something with post result
except Exception as e:
    print(f'An error occurred: {e}')
