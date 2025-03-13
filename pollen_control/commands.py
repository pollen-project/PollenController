from camera import take_picture, camera_settings
from motor import move_motor
from focus import focus


def handle_command(command):
    if command == "img":
        take_picture()

    elif command == "set c":
        camera_settings("color")

    elif command == "set g":
        camera_settings("grey")

    elif command == "denoise":
        camera_settings("denoise")

    elif command[0:1] == "a":
        steps = int(command[1:])
        move_motor("focus", steps)

    elif command[0:1] == "b":
        steps = int(command[1:])
        move_motor("tape", steps)

    elif command == "focus":
        focus()

    else:
        print("Unknown command")
