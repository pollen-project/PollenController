import os
import json
from pathlib import Path
import requests
from datetime import datetime
import time
from concurrent.futures import ThreadPoolExecutor
import requests
import time


upload_queue = []
queue_status = False

def start_upload_queue():
    global upload_queue
    global queue_status
    
    with ThreadPoolExecutor(max_workers=1) as executor:
        print("E: Upload thread opened")
        
        while True:
            if upload_queue:
                # Pop the first image and filename from the queue
                data = upload_queue.pop(0)
                upload_image(data)


def add_to_upload_queue(data):
    global queue_status
    queue_status = True
    upload_queue.append(data)
    print(f"Image added to queue.")

    
def upload_image(data, retries: int = 3, backoff: int = 2) -> None:
    """Uploads an image in bytes to the server."""

    url = 'https://pollen.botondhorvath.com/api/upload'
    form_data = {
        "timestamp": data["timestamp"],
        "temperature": data["temperature"],
        "humidity": data["humidity"],
        "gps": json.dumps(data["gps"]),
    }

    for attempt in range(1, retries + 1):
        try:
            # Create a file-like object from the bytes
            files = {'image': ("pollen3", data["image"], 'image/jpeg')}
            response = requests.post(url, files=files, data=form_data, timeout=10)
            print(response)
            if response.status_code == 200:
                print(f"✅ Upload successful on attempt {attempt}")
                #print("Response:", response.json())
                break
            else:
                print(f"⚠️ Attempt {attempt} failed with status code {response.status_code}")
        
        except requests.RequestException as e:
            print(f"❌ Attempt {attempt} failed with error: {e}")

        if attempt < retries:
            # Exponential backoff
            sleep_time = backoff ** attempt
            print(f"⏳ Retrying in {sleep_time} seconds...")
            time.sleep(sleep_time)
        else:
            print("🚫 All retry attempts failed.")


def get_latest_image() -> Path | None:
    photos_dir = Path("photos")
    image_extension = ".jpg"
    image_files = [f for f in photos_dir.iterdir() if f.suffix.lower() == image_extension and f.is_file()]

    if image_files:
        latest_image = max(image_files, key=lambda f: f.stat().st_mtime)
        #print("Latest image:", latest_image)
        return latest_image
    else:
        #print("No images found in", photos_dir)
        return None