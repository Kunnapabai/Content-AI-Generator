"""
Method: GET
Endpoint: https://api.dataforseo.com/v3/keywords_data/google_ads/search_volume/task_get/$id
@see https://docs.dataforseo.com/v3/keywords\_data/google_ads/search\_volume/task\_get
"""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../../')))
from lib.client import RestClient
from lib.config import username, password
client = RestClient(username, password)

try:
    task_id = '11241817-0696-0110-0000-a86a0d4efd9a'
    response = client.get(f'/v3/keywords_data/google_ads/search_volume/task_get/{task_id}')
    print(response)
    # do something with get result
except Exception as e:
    print(f'An error occurred: {e}')
