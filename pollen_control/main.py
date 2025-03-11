import automation as automation
from camera import picam2, picture, camera_settings 
from stream_server import start_stream
from motor import setup_motor, move_motor
from focus import focus

def main():
    start_stream()
    setup_motor()
    
    while True:
        command = input("Enter command: ").strip().lower()
        
        if command == "img":
            picture()

        elif command =="set c":
            camera_settings("color")

        elif command =="set g":
            camera_settings("grey")
            
        elif command =="denoise":
            camera_settings("denoise")
       
        elif command[0:1] == "a":
            steps = int(command[1:])
            move_motor("focus", steps)
            
        elif command[0:1] == "b":
            steps = int(command[1:])
            move_motor("tape", steps)
         
        elif command == "focus":
            print("focusing...")
            focus()
        
        elif command == "exit":
            print("Exiting...")
            break
        else:
            print("Unknown command. Try 'run focus' or 'exit'.")

if __name__ == "__main__":
    main()