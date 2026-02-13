"""
Method: POST
Endpoint: https://api.dataforseo.com/v3/content_generation/generate_meta_tags/live
@see https://docs.dataforseo.com/v3/content_generation/generate_meta_tags/live/
"""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../')))
from lib.client import RestClient
from lib.config import username, password
client = RestClient(username, password)

post_data = []
post_data.append({
        'text': 'The idea to develop an instrument for local SEO didn’t come to the GMB Crush CEO, Matteo Barletta, out of the blue. Having a huge interest in search engine optimization, Matteo has come a long way from being an SEO freelancer to launching his own agency, SEO Heroes. At some point, he and his team noticed that it was quite challenging to work with local SEO projects, especially those related to Google My Business listings. There were simply no tools that could streamline their work and provide the functionality the agency needed.

“We started to develop the idea of ​​our tool capable of doing Google Business SEO audits, tracking stats, and generating business proposals at the same time.',
        'creativity': 0.9
    })
try:
    response = client.post('/v3/content_generation/generate_meta_tags/live', post_data)
    print(response)
    # do something with post result
except Exception as e:
    print(f'An error occurred: {e}')
