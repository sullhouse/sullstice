import functions_framework
from flask import Response
from google.cloud import storage
from flask import Response, Flask, request
from flask_cors import CORS
import json
import datetime
import uuid
import os

app = Flask(__name__)

# Define allowed origins
ALLOWED_ORIGINS = os.environ.get('ALLOWED_ORIGINS', 
    'http://sullstice.com,http://localhost:8000,http://127.0.0.1:8000'
).split(',')

# Configure CORS
CORS(app, resources={
    r"/*": {
        "origins": ALLOWED_ORIGINS,
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type", "x-access-token"],
        "supports_credentials": True
    }
})

def handle_request(request):
    """Main handler function that can be called either by Flask route or Cloud Function"""
    # Handle preflight OPTIONS requests
    if request.method == 'OPTIONS':
        response = Response()
        response.headers.add('Access-Control-Allow-Origin', request.headers.get('Origin', '*'))
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,x-access-token')
        response.headers.add('Access-Control-Allow-Methods', 'GET,POST,OPTIONS')
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        return response
    """Main Cloud Function that saves the request to a file and dispatches requests based on the URL path.

    Args:
        request (flask.Request): The request object.

    Returns:
        str: The response from the called function.
    """

    # Get a reference to the GCS bucket and folder
    bucket_name = "sullstice"  # Replace with your bucket name
    folder_name = "requests"
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)

    # Extract data from the request and save in readable format
    try:
        # Get the JSON data
        request_json = request.get_json()

        # Generate a timestamp for the filename
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        short_uuid = str(uuid.uuid4())[:8]

        # Create a filename with the timestamp
        filename = f"request_{timestamp}_{short_uuid}.json"

        # Construct the full path within the bucket
        blob = bucket.blob(f"{folder_name}/{filename}")

        # Create a dictionary to hold the entire request data
        request_data = {
            "path": request.path,
            "headers": dict(request.headers),
            "json": request_json
        }

        # Save the request data to the GCS bucket
        blob.upload_from_string(
            data=json.dumps(request_data),
            content_type='application/json'
        )

        # Get the function name from the request URL
        function_name = request.path.split("/")[-1]

        # Define a dictionary mapping function names to modules
        functions = {
            "rsvp": "rsvp.main",  # Module name and function name
        }

        # Import the corresponding module dynamically
        if function_name in functions:
            module_name, function_name = functions[function_name].rsplit(".", 1)
            imported_module = __import__(module_name)
            function = getattr(imported_module, function_name)
            # Call the function with the request
            response = function(request)

            folder_name = "responses"

            # Store the response in a file
            try:
                # Create a filename with the timestamp
                filename = f"response_{timestamp}_{short_uuid}.json"

                # Construct the full path within the bucket
                blob = bucket.blob(f"{folder_name}/{filename}")

                # Upload the entire request data in a readable format
                blob.upload_from_string(json.dumps(response, indent=2))
            except Exception as e:
                error_response = Response(json.dumps({"error": str(e)}), status=500, mimetype='application/json')
                return error_response

            # Return the response as JSON
            json_response = Response(json.dumps(response), status=200, mimetype='application/json')
            return json_response
        else:
            error_response = Response(json.dumps({"error": "Function not found"}), status=404, mimetype='application/json')
            return error_response

    except Exception as e:
        error_response = Response(json.dumps({"error": str(e)}), status=500, mimetype='application/json')
        return error_response
    
# Cloud Function entry point
@functions_framework.http
def hello_http(request):
    """Cloud Function entry point"""
    return handle_request(request)

# Flask route for local development
@app.route('/<path:path>', methods=['GET', 'POST', 'OPTIONS'])
def flask_handler(path):
    """Flask route handler for local development"""
    return handle_request(request)

if __name__ == '__main__':
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'operative-connect-lite-41ee5442dc06.json'
    app.run(host='127.0.0.1', port=5000, debug=True)
