import io
import threading
import socketserver
import logging
from http import server
from picamera2.outputs import FileOutput
from picamera2.encoders import JpegEncoder
from camera import picam2, denoise_image, encode_jpeg
from commands import handle_command
from urllib.parse import urlparse, parse_qs
from DHT22 import read_dht22

class StreamingOutput(io.BufferedIOBase):
    def __init__(self):
        self.frame = None
        self.condition = threading.Condition()

    def write(self, buf):
        with self.condition:
            self.frame = denoise_image(buf, encode_jpeg=True)
            self.condition.notify_all()


class StreamingHandler(server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(301)
            self.send_header('Location', '/index.html')
            self.end_headers()
        elif self.path == '/index.html':
            content = PAGE.encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.send_header('Content-Length', len(content))
            self.end_headers()
            self.wfile.write(content)


        elif self.path.startswith('/control'):
            try:
                # Parse query parameters
                parsed_url = urlparse(self.path)
                params = parse_qs(parsed_url.query)

                if 'cmd' in params:
                    cmd = params['cmd'][0]  # Extract the command
                    handle_command(cmd)  # Pass it to your function

                    self.send_response(200)
                    self.send_header("Content-Type", "text/plain")
                    self.end_headers()
                    self.wfile.write(f"Executed command: {cmd}".encode())  # Send response

                else:
                    self.send_error(400, "Missing 'cmd' parameter")

            except Exception as e:
                self.send_error(500, f"Error executing command: {str(e)}")

        # DHT22 DATA
        elif self.path == '/get_dht':
            try:
                temperature, humidity = read_dht22()
                if temperature is not None and humidity is not None:
                    response = f'{{"temperature": {temperature:.1f}, "humidity": {humidity:.1f}}}'
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/json')
                    self.send_header('Content-Length', len(response))
                    self.end_headers()
                    self.wfile.write(response.encode())
                else:
                    self.send_error(500, "Failed to read DHT22 sensor")
            except Exception as e:
                self.send_error(500, f"Error reading DHT22: {str(e)}")

        elif self.path == '/stream.mjpg':
            self.send_response(200)
            self.send_header('Age', 0)
            self.send_header('Cache-Control', 'no-cache, private')
            self.send_header('Pragma', 'no-cache')
            self.send_header('Content-Type', 'multipart/x-mixed-replace; boundary=FRAME')
            self.end_headers()
            try:
                while True:
                    with output.condition:
                        output.condition.wait()
                        frame = output.frame
                    self.wfile.write(b'--FRAME\r\n')
                    self.send_header('Content-Type', 'image/jpeg')
                    self.send_header('Content-Length', len(frame))
                    self.end_headers()
                    self.wfile.write(frame)
                    self.wfile.write(b'\r\n')
            except Exception as e:
                logging.warning(
                    'Removed streaming client %s: %s',
                    self.client_address, str(e))
        else:
            self.send_error(404)
            self.end_headers()


class StreamingServer(socketserver.ThreadingMixIn, server.HTTPServer):
    allow_reuse_address = True
    daemon_threads = True


def start_streaming_server(picam2):
    """Run the stream server while using the given Picamera2 instance."""
    global output
    output = StreamingOutput()  # Initialize output here
    picam2.start_recording(JpegEncoder(), FileOutput(output))
    try:
        address = ('', 8080)
        server = StreamingServer(address, StreamingHandler)
        server.serve_forever()
    finally:
        picam2.stop_recording()


def start_stream():
    global PAGE

    with open('webpage.html', 'r') as f:
        PAGE = f.read()

    threading.Thread(target=start_streaming_server, args=(picam2,), daemon=True).start()
