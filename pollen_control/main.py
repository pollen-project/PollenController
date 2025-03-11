import automation as automation
from camera import picam2 
from stream_server import start_stream
from motor import setup_motor, move_motor

def main():
    start_stream()
    setup_motor()
    
    while True:
        command = input("Enter command: ").strip().lower()
        
        if command == "home":
            print("Exiting...")
       
        elif command[0:1] == "a":
            steps = int(command[1:])
            move_motor("focus", steps)
            
        elif command[0:1] == "b":
            steps = int(command[1:])
            move_motor("tape", steps)
        
        elif command == "focus":
            print("Exiting...")
        elif command == "exit":
            print("Exiting...")
            break
        else:
            print("Unknown command. Try 'run focus' or 'exit'.")

if __name__ == "__main__":
    main()