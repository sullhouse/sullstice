import logging
import os
import json
import boto3
from data_loader import load_updated_event_details
from html_generator import generate_details_html
from flask import Response

def is_development_environment():
    """Check if we're running in a development environment"""
    try:
        return os.getenv("ENVIRONMENT") != "production"
    except:
        return True

def get_aws_credentials():
    """Load AWS credentials from file or environment variables"""
    AWS_ACCESS_KEY = None
    AWS_SECRET_KEY = None
    CLOUDFRONT_DISTRIBUTION_ID = None
    AWS_REGION = "us-east-1"  # Change if using another region

    if is_development_environment():
        try:
            json_path = os.path.join(os.path.dirname(__file__), 'aws_access_keys.json')
            with open(json_path, 'r') as f:
                credentials = json.load(f)
                AWS_ACCESS_KEY = credentials.get('aws_access_key')
                AWS_SECRET_KEY = credentials.get('aws_secret_access_key')
                CLOUDFRONT_DISTRIBUTION_ID = credentials.get('cloudfront_distribution_id')
            logging.info("Loaded AWS credentials from local JSON file")
        except Exception as e:
            logging.warning(f"Could not load AWS credentials from JSON: {str(e)}")

    # Fall back to environment variables if not set from JSON
    if not AWS_ACCESS_KEY or not AWS_SECRET_KEY:
        AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY")
        AWS_SECRET_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
        CLOUDFRONT_DISTRIBUTION_ID = os.getenv("CLOUDFRONT_DISTRIBUTION_ID")
        logging.info("Using AWS credentials from environment variables")
    
    return AWS_ACCESS_KEY, AWS_SECRET_KEY, AWS_REGION, CLOUDFRONT_DISTRIBUTION_ID

def upload_to_s3(html_content, file_path='details.html'):
    """
    Upload HTML content to S3 bucket
    
    Args:
        html_content: HTML content to upload
        file_path: Path where to store the file in the bucket
    
    Returns:
        Boolean indicating success or failure
    """
    try:
        aws_access_key, aws_secret_key, aws_region, cloudfront_distribution_id = get_aws_credentials()
        bucket_name = 'sullstice.com'  # Replace with your actual bucket name
        
        # Initialize S3 client
        s3_client = boto3.client(
            's3',
            aws_access_key_id=aws_access_key,
            aws_secret_access_key=aws_secret_key,
            region_name=aws_region
        )
        
        # Upload content to S3
        s3_client.put_object(
            Bucket=bucket_name,
            Key=file_path,
            Body=html_content,
            ContentType='text/html',
            #ACL='public-read'  # Make it publicly readable
        )
        
        logging.info(f"Successfully uploaded {file_path} to {bucket_name}")
        return True
    except Exception as e:
        logging.error(f"Error uploading to S3: {str(e)}")
        return False

import datetime

def create_cloudfront_invalidation(paths=['/details.html']):
    """
    Create CloudFront invalidation for specified paths
    
    Args:
        paths: List of paths to invalidate
    
    Returns:
        Boolean indicating success or failure
    """
    try:
        aws_access_key, aws_secret_key, aws_region, cloudfront_distrubution_id = get_aws_credentials()
        
        # Initialize CloudFront client
        cloudfront_client = boto3.client(
            'cloudfront',
            aws_access_key_id=aws_access_key,
            aws_secret_access_key=aws_secret_key,
            region_name=aws_region
        )
        
        # Create invalidation
        response = cloudfront_client.create_invalidation(
            DistributionId=cloudfront_distrubution_id,
            InvalidationBatch={
                'Paths': {
                    'Quantity': len(paths),
                    'Items': paths
                },
                'CallerReference': str(int(datetime.datetime.now().timestamp()))
            }
        )
        
        invalidation_id = response['Invalidation']['Id']
        logging.info(f"Created CloudFront invalidation {invalidation_id} for {paths}")
        return True
    except Exception as e:
        logging.error(f"Error creating CloudFront invalidation: {str(e)}")
        return False

def main(request):
    """
    Handle requests for updated event details HTML
    
    Args:
        request: Flask request object
        
    Returns:
        HTML content as a response
    """
    try:
        # Get the updated content from Google Docs
        doc_content = load_updated_event_details()
        
        if not doc_content:
            return {"error": "Could not load document content"}, 500
        
        # Generate the HTML content using the new generator function
        html_content = generate_details_html(doc_content)
        
        # Check for deploy parameter in multiple possible locations
        deploy_to_s3 = False
        
        # Method 1: Try regular Flask request.args
        if hasattr(request, 'args') and hasattr(request.args, 'get'):
            deploy_param = request.args.get('deploy')
            if deploy_param is not None:
                deploy_to_s3 = deploy_param.lower() == 'true'
                logging.info(f"Found deploy parameter in request.args: {deploy_param}")
        
        # Method 2: Check request URL path directly
        if not deploy_to_s3 and hasattr(request, 'path'):
            path = request.path
            if '?' in path and 'deploy=true' in path.lower():
                deploy_to_s3 = True
                logging.info("Found deploy=true in URL path")
        
        # Method 3: Check URL query string
        if not deploy_to_s3 and hasattr(request, 'query_string'):
            query_str = request.query_string.decode('utf-8')
            if 'deploy=true' in query_str.lower():
                deploy_to_s3 = True
                logging.info("Found deploy=true in query_string")
                
        # Method 4: Parse request.url if available
        if not deploy_to_s3 and hasattr(request, 'url'):
            if 'deploy=true' in request.url.lower():
                deploy_to_s3 = True
                logging.info("Found deploy=true in request.url")
        
        # Log whether we're going to deploy or not for debugging
        logging.info(f"Deploy to S3: {deploy_to_s3}")
        
        if deploy_to_s3:
            # Upload to S3
            upload_success = upload_to_s3(html_content, 'details.html')
            
            if upload_success:
                # Create CloudFront invalidation
                invalidation_success = create_cloudfront_invalidation(['/details.html'])
                
                if invalidation_success:
                    return Response(
                        f"HTML content updated successfully and deployed to S3. CloudFront invalidation created.", 
                        mimetype='text/plain'
                    )
                else:
                    return Response(
                        f"HTML content uploaded to S3, but CloudFront invalidation failed.", 
                        mimetype='text/plain'
                    )
            else:
                return Response(f"Generated HTML but failed to upload to S3.", mimetype='text/plain')
        
        # Return HTML response
        return Response(html_content, mimetype='text/html')
    
    except Exception as e:
        logging.error(f"Error handling updated details request: {e}")
        return {"error": str(e)}, 500
