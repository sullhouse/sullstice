import boto3
import os
import json

def is_development_environment():
    """Check if we're running in a development environment"""
    # This will check if we're running on a local machine
    try:
        # Could also check for other environment variables or conditions that indicate development
        return os.getenv("ENVIRONMENT") != "production"
    except:
        # Default to assuming we're in development if we can't determine
        return True

# Load AWS credentials
AWS_ACCESS_KEY = None
AWS_SECRET_KEY = None
AWS_REGION = "us-east-1"  # Change if using another region

# Try to load credentials from JSON file if in development
if is_development_environment():
    try:
        json_path = os.path.join(os.path.dirname(__file__), 'aws_ses_access_keys.json')
        with open(json_path, 'r') as f:
            credentials = json.load(f)
            AWS_ACCESS_KEY = credentials.get('aws_access_key')
            AWS_SECRET_KEY = credentials.get('aws_secret_access_key')
        print("✅ Loaded AWS credentials from local JSON file")
    except Exception as e:
        print(f"⚠️ Could not load AWS credentials from JSON: {str(e)}")

# Fall back to environment variables if not set from JSON
if not AWS_ACCESS_KEY or not AWS_SECRET_KEY:
    AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY")
    AWS_SECRET_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
    print("ℹ️ Using AWS credentials from environment variables")

# Sender email
SENDER_EMAIL = "no-reply@sullstice.com"

# Initialize AWS SES client
ses_client = boto3.client(
    "ses",
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY,
    region_name=AWS_REGION,
)

def send_email(subject, body, recipient_email, cc_email=None):
    try:
        destination = {"ToAddresses": [recipient_email]}
        if cc_email:
            destination["CcAddresses"] = [cc_email]
            
        response = ses_client.send_email(
            Source=SENDER_EMAIL,
            Destination=destination,
            Message={
                "Subject": {"Data": subject},
                "Body": {"Text": {"Data": body}},
            },
        )
        print(f"✅ Email sent! Message ID: {response['MessageId']}")
    except Exception as e:
        print(f"❌ Error sending email: {str(e)}")
