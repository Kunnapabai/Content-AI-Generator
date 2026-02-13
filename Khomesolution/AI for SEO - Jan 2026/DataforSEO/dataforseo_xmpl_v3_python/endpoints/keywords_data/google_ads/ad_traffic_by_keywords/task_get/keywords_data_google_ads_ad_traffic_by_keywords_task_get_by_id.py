"""
Method: GET
Endpoint: https://api.dataforseo.com/v3/keywords_data/google_ads/ad_traffic_by_keywords/task_get/$id
@see https://docs.dataforseo.com/v3/keywords\_data/google_ads/ad\_traffic\_by\_keywords/task\_get
"""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../../')))
from lib.client import RestClient
from lib.config import username, password
client = RestClient(username, password)

try:
    task_id = '11251534-0696-0111-0000-f87c5621ae38'
    response = client.get(f'/v3/keywords_data/google_ads/ad_traffic_by_keywords/task_get/{task_id}')
    print(response)
    # do something with get result
except Exception as e:
    print(f'An error occurred: {e}')
