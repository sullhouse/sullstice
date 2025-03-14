from google.cloud import bigquery
import datetime
import random

def main(request):

    if request.is_json:
        # Get the JSON data
        request_json = request.get_json()

        # Generate a timestamp for the filename
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

        # Create a filename with the timestamp
        filename = f"request_{timestamp}.json"

        response_json = {
            "name": "NAME",
            "email": "EMAIL",
            "days": [
                {
                    "thursday": True,
                    "friday": True,
                    "saturday": True,
                    "sunday": True,
                }
            ]
        }

        return response_json
    else:
        # Handle non-JSON requests (optional)
        return "Request is not a JSON object"