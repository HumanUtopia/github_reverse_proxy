def handle_exceptions(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logging.error(f"Error occurred: {str(e)}")
            return Response("An error occurred", status=500)
    return wrapper