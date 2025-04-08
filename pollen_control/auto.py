from time import sleep
from stream_server import start_stream
from automation import start_auto_picture_loop
from uploading import start_upload_queue
import threading

if __name__ == "__main__":
    # Start stream in a separate thread
    threading.Thread(target=start_stream, daemon=True).start()
    
    # Start upload queue in a separate thread
    threading.Thread(target=start_upload_queue, daemon=True).start()
    
    # Start auto picture loop in a separate thread
    threading.Thread(target=start_auto_picture_loop, daemon=True).start()
    
    # Keep main thread alive
    while True:
        sleep(1)