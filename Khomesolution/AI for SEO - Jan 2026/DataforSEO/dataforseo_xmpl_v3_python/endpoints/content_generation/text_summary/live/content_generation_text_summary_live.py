"""
Method: POST
Endpoint: https://api.dataforseo.com/v3/content_generation/text_summary/live
@see https://docs.dataforseo.com/v3/content_generation/text_summary/live/
"""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../')))
from lib.client import RestClient
from lib.config import username, password
client = RestClient(username, password)

post_data = []
post_data.append({
        'text': 'Removing [RequireHttps] does nothing but break the https redirection, and doesn\'t enforce an https url on my route. I\'ve got one method which i want to expose over http and a different one over https. If i accidentally enter http in my url for the https-only method, it should redirect. It currently works as is, the problem is that there is an undocument (seemingly unrelated) setting I have to add to get it all working. And that is the SslPort thing',
        'language_name': 'English (United States)'
    })
try:
    response = client.post('/v3/content_generation/text_summary/live', post_data)
    print(response)
    # do something with post result
except Exception as e:
    print(f'An error occurred: {e}')
