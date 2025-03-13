import io
import threading
import socketserver
import logging
from http import server
from picamera2.outputs import FileOutput
from picamera2.encoders import JpegEncoder
from camera import picam2, denoise_image
from commands import handle_command

class StreamingOutput(io.BufferedIOBase):
    def __init__(self):
        self.frame = None
        self.condition = threading.Condition()

    def write(self, buf):
        with self.condition:
            self.frame = denoise_image(buf)
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
        elif self.path == '/control?cmd=take_picture':
            try:
                handle_command("img")  # Runs the function
                
                self.send_response(200)
                self.send_header("Content-Type", "text/plain")
                self.end_headers()
                
                self.wfile.write(b"Picture function executed successfully")  # Send a simple response
            
            except Exception as e:
                self.send_error(500, f"Error executing picture function: {str(e)}")

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
