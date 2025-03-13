from stream_server import start_stream
from motor import setup_motor
from commands import handle_command


def main():
    start_stream()
    setup_motor()
    
    while True:
        command = input("Enter command: ").strip().lower()

        if command == "exit":
            print("Exiting...")
            break
        else:
            handle_command(command)


if __name__ == "__main__":
    main()
