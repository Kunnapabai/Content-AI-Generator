"""
Method: POST
Endpoint: https://api.dataforseo.com/v3/ai_optimization/claude/llm_responses/live
@see https://docs.dataforseo.com/v3/ai_optimization/claude/llm_responses/live
"""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../../')))
from lib.client import RestClient
from lib.config import username, password
client = RestClient(username, password)

post_data = []
post_data.append({
        'system_message': 'communicate as if we are in a business meeting',
        'message_chain': [
            {
                'role': 'user',
                'message': 'Hello, what\'s up?'
            },
            {
                'role': 'ai',
                'message': 'Hello! I’m doing well, thank you. How can I assist you today? Are there any specific topics or projects you’d like to discuss in our meeting?'
            }
        ],
        'max_output_tokens': 1024,
        'temperature': 0.3,
        'top_p': 0.5,
        'web_search_country_iso_code': 'FR',
        'model_name': 'claude-opus-4-0',
        'web_search': True,
        'user_prompt': 'provide information on how relevant the amusement park business is in France now'
    })
try:
    response = client.post('/v3/ai_optimization/claude/llm_responses/live', post_data)
    print(response)
    # do something with post result
except Exception as e:
    print(f'An error occurred: {e}')
