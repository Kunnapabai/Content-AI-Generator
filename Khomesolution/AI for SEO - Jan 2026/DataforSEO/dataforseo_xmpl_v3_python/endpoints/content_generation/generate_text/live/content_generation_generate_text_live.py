"""
Method: POST
Endpoint: https://api.dataforseo.com/v3/content_generation/generate_text/live
@see https://docs.dataforseo.com/v3/content_generation/generate_text/live/
"""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../')))
from lib.client import RestClient
from lib.config import username, password
client = RestClient(username, password)

post_data = []
post_data.append({
        'topic': 'Steve Jobs',
        'sub_topics': [
            'Apple',
            'Pixar',
            'Amazing Products'
        ],
        'description': 'Take a closer look at Steve Jobs\' life and his incredible impact on the tech industry, with a special focus on the development of the iPhone.',
        'meta_keywords': [
            'iPhone',
            'sell',
            'CEO'
        ],
        'creativity_index': 0.8,
        'word_count': 50,
        'include_conclusion': True
    })
try:
    response = client.post('/v3/content_generation/generate_text/live', post_data)
    print(response)
    # do something with post result
except Exception as e:
    print(f'An error occurred: {e}')
