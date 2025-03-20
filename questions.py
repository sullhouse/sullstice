import uuid
from datetime import datetime
from flask import Response
from sullstice_ai import answer_question
from google.cloud import bigquery
import aws_email  # Import AWS email module

# Initialize BigQuery client
bigquery_client = bigquery.Client()

def store_question_in_bigquery(question, answer):
    """
    Store question and answer in BigQuery
    
    Args:
        question: String containing the question
        answer: String containing the answer
    """
    try:
        # Prepare data for insertion
        row_data = {
            "id": str(uuid.uuid4()),
            "timestamp": datetime.now().isoformat(),
            "question": question,
            "answer": answer
        }
        
        # Define the table reference
        table_ref = bigquery_client.dataset("guests").table("questions")
        
        # Insert the row
        errors = bigquery_client.insert_rows_json(table_ref, [row_data])
        
        if errors:
            print(f"Encountered errors while inserting row: {errors}")
        else:
            print("Question data inserted into BigQuery")
    except Exception as e:
        print(f"Error storing question in BigQuery: {str(e)}")

def main(request):
    """
    Handle questions API requests
    
    Args:
        request: Flask request object
        
    Returns:
        Dictionary with question and answer
    """
    
    try:
        # Get the question from the request JSON
        request_json = request.get_json()
        question = request_json.get('question', '')
        
        if not question:
            return {"error": "No question provided", "status": "error"}
        
        # Get the answer using the answer_question function from sullstice_ai
        answer = answer_question(question)
        
        # Store the question and answer in BigQuery
        store_question_in_bigquery(question, answer)
        
        # Send email notification
        email_subject = "Sullstice Question"
        email_body = f"Question: {question}\n\nAnswer: {answer}"
        
        # Send email notification to administrator
        aws_email.send_email(
            subject=email_subject,
            body=email_body,
            recipient_email="sullhouse@gmail.com",
            sender_email="sullstice-ai-assistant@sullstice.com",
            reply_to_email="sullhouse@gmail.com"
        )
        
        # Prepare response data
        response_data = {
            "question": question,
            "answer": answer,
            "status": "success"
        }
        
        return response_data
        
    except Exception as e:
        return {"error": str(e), "status": "error"}