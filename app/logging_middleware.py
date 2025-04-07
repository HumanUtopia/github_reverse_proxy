import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def log_request_response(request, response):
    logging.info(f"Request: {request.method} {request.url}")
    logging.info(f"Response: {response.status_code} {response.content[:100]}")  # Log first 100 chars of response