import requests
from travel_planner_backend.api_config import GOOGLE_PLACES_API_KEY, GOOGLE_PLACES_BASE_URL

def test_places_api():
    """Test Google Places API with a simple query"""
    url = f"{GOOGLE_PLACES_BASE_URL}/textsearch/json"
    params = {
        'query': 'restaurants in New York',
        'key': GOOGLE_PLACES_API_KEY
    }
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()  # Raises an HTTPError if the status is 4XX, 5XX
        data = response.json()
        
        if 'error_message' in data:
            return {
                'status': 'error',
                'message': data['error_message'],
                'details': data
            }
        
        return {
            'status': 'success',
            'results_count': len(data.get('results', [])),
            'first_result': data.get('results', [])[0] if data.get('results') else None
        }
        
    except requests.exceptions.RequestException as e:
        return {
            'status': 'error',
            'message': str(e)
        }
