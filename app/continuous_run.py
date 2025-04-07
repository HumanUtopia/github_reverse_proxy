import os
import time

def run_server():
    while True:
        try:
            os.system('python app/reverse_proxy.py')
        except Exception as e:
            logging.error(f"Server crashed: {str(e)}")
            time.sleep(5)  # Wait for 5 seconds before restarting

if __name__ == '__main__':
    run_server()