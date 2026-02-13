"""
Method: POST
Endpoint: https://api.dataforseo.com/v3/appendix/webhook_resend
"""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))
from lib.client import RestClient
from lib.config import username, password
client = RestClient(username, password)

post_data = []
post_data.append({
        'id': '08241357-0696-0066-0000-d1211922951d'
    })
try:
    response = client.post('/v3/appendix/webhook_resend', post_data)
    print(response)
    # do something with post result
except Exception as e:
    print(f'An error occurred: {e}')
