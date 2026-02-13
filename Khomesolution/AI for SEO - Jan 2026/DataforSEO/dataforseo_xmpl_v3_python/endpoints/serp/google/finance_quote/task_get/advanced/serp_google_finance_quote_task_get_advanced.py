"""
Example: Get results for completed tasks using tasks_ready and task_get
"""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../../../')))

from lib.client import RestClient
from lib.config import username, password

client = RestClient(username, password)

try:
    result = []
    # #1 - using this method you can get a list of completed tasks
    # GET /v3/serp/google/finance_quote/tasks_ready
    # in addition to parameters in the path you can also set other search engine and type parameters
    # the full list of possible parameters is available in documentation
    tasks_ready = client.get('/v3/serp/google/finance_quote/tasks_ready')
    # you can find the full list of the response codes here https://docs.dataforseo.com/v3/appendix/errors
    if tasks_ready and tasks_ready.get('status_code') == 20000 and tasks_ready.get('tasks'):
        for task in tasks_ready['tasks']:
            if 'result' in task and task['result']:
                for task_ready in task['result']:
                    # #2 - using this method you can get results of each completed task
                    # GET /v3/serp/google/finance_quote/task_get/advanced
                    if 'endpoint_advanced' in task_ready:
                        result.append(client.get(task_ready['endpoint_advanced']))
                    
                    # #3 - another way to get the task results by id
                    # GET /v3/serp/google/finance_quote/task_get/advanced
                    """
                    if 'id' in task_ready:
                        result.append(client.get('/v3/serp/google/finance_quote/task_get/advanced/' + task_ready['id']))
                    """
    print(result)
    # do something with result
except Exception as e:
    print(f'An error occurred: {e}')
