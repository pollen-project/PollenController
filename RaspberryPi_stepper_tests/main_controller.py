# controller.py
import interface

def setup():
    return interface.setup()

def focus_home():
    interface.focus_home()

def focus():
    interface.focus()

def main():
    camera = setup()

    while True:
        command = input("Enter command: ").strip().lower()

        if command == "home":
            focus_home()
        elif command == "focus":
            focus()
        elif command == "exit":
            print("Exiting...")
            break
        else:
            print("Unknown command. Try 'run focus' or 'exit'.")

if __name__ == "__main__":
    main()