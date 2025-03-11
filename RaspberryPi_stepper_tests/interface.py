from stream_server_current import setup_server, focus_home as _focus_home, focus as _focus, picture

def setup():
    setup_server()

def focus_home():
    _focus_home() 

def focus():
    _focus()  

def take_img():
    picture()
