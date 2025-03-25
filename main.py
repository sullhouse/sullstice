import functions_framework
from flask import Response
from google.cloud import storage
from flask import Response, Flask, request
from flask_cors import CORS
import json
import datetime
import uuid
from sullstice_ai import answer_question  # Import the answer_question function

app = Flask(__name__)
CORS(app)

def add_cors_headers(response, origin='*'):
    """
    Add CORS headers to a Flask response object
    
    Args:
        response: Flask Response object
        origin: Origin to allow, defaults to '*'
        
    Returns:
        Flask Response object with CORS headers added
    """
    response.headers.add('Access-Control-Allow-Origin', origin)
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,x-access-token')
    response.headers.add('Access-Control-Allow-Methods', 'GET,POST,OPTIONS')
    response.headers.add('Access-Control-Allow-Credentials', 'true')
    return response

@functions_framework.http
def hello_http(request):
    # Get the origin from request headers
    origin = request.headers.get('Origin', '*')

    if request.method == 'OPTIONS':
        response = Response()
        return add_cors_headers(response, origin)
    
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

    # Generate a timestamp for the filename
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    short_uuid = str(uuid.uuid4())[:8]

    # Create a filename with the timestamp
    filename = f"request_{timestamp}_{short_uuid}.json"

    # Construct the full path within the bucket
    blob = bucket.blob(f"{folder_name}/{filename}")

    # Extract the function name from the request URL, ignoring query parameters
    # This splits the path and takes the last part before any query parameters
    path_without_params = request.path.split('?')[0]
    function_name = path_without_params.strip('/').split('/')[-1]

    # Define a dictionary mapping function names to modules
    functions = {
        "rsvp": "rsvp.main",  # Module name and function name
        "questions": "questions.main",  # Updated to use questions.py main function
        "updated_event_details_html": "updated_details.main"  # New endpoint for updated event details HTML
    }

    try:
        # Different handling for GET and POST requests
        if request.method == 'GET':
            # For GET requests (like updated_event_details_html)
            # Create a dictionary with only path and headers (no JSON)
            # Ensure all data is JSON serializable by converting headers to dict
            headers_dict = {}
            for key, value in request.headers.items():
                headers_dict[key] = str(value)
                
            request_data = {
                "method": "GET",
                "path": request.path,
                "headers": headers_dict,  # Use the serializable headers dict
                "timestamp": timestamp,
                "query_parameters": dict(request.args.to_dict())  # Ensure query params are also serializable
            }
            
            # Save the request data to the GCS bucket
            blob.upload_from_string(
                data=json.dumps(request_data),
                content_type='application/json'
            )
            
            # Check if the function exists
            if function_name in functions:
                module_name = functions[function_name]
                module_name, function_name = module_name.rsplit(".", 1)
                imported_module = __import__(module_name)
                function = getattr(imported_module, function_name)
                
                # Call the function with the request
                response = function(request)
                
                # If the function returns a Response object already, just add CORS headers
                if isinstance(response, Response):
                    return add_cors_headers(response, origin)
                
                # If it returns HTML content or other string
                if isinstance(response, str):
                    html_response = Response(response, status=200, mimetype='text/html')
                    return add_cors_headers(html_response, origin)
                
                # If it returns a dictionary, convert to JSON
                json_response = Response(json.dumps(response), status=200, mimetype='application/json')
                return add_cors_headers(json_response, origin)
            else:
                error_response = Response(json.dumps({"error": "Function not found"}), status=404, mimetype='application/json')
                return add_cors_headers(error_response, origin)
                
        else:
            # For POST requests (like RSVP and questions)
            # Extract JSON data from the request
            request_json = request.get_json()
            
            # Create a dictionary to hold the entire request data
            request_data = {
                "method": request.method,
                "path": request.path,
                "headers": dict(request.headers),
                "json": request_json
            }

            # Save the request data to the GCS bucket
            blob.upload_from_string(
                data=json.dumps(request_data),
                content_type='application/json'
            )

            # Import the corresponding module dynamically
            if function_name in functions:
                module_name = functions[function_name]
                
                # Regular module import for all endpoints
                module_name, function_name = module_name.rsplit(".", 1)
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
                    return add_cors_headers(error_response, origin)

                # Return the response as JSON
                json_response = Response(json.dumps(response), status=200, mimetype='application/json')
                return add_cors_headers(json_response, origin)
            else:
                error_response = Response(json.dumps({"error": "Function not found"}), status=404, mimetype='application/json')
                return add_cors_headers(error_response, origin)

    except Exception as e:
        error_response = Response(json.dumps({"error": str(e)}), status=500, mimetype='application/json')
        return add_cors_headers(error_response, origin)