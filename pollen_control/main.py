from stream_server import start_stream
from commands import handle_command


def main():
    start_stream()
    
    while True:
        command = input("Enter command: ").strip().lower()

        if command == "exit":
            print("Exiting...")
            break
        else:
            handle_command(command)


if __name__ == "__main__":
    main()
