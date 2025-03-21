from camera import take_picture, camera_settings, take_picture_all
from motor import move_motor
from focus import focus


def handle_command(command):
    if command == "take_picture":
        take_picture_all()

    elif command == "take_picture_all":
        take_picture_all()

    elif command == "set c":
        camera_settings("color")

    elif command == "set g":
        camera_settings("grey")

    elif command == "denoise":
        camera_settings("denoise")

    elif command[0:1] == "a":
        steps = int(command[1:])
        move_motor("focus", steps)

    elif command[:11] == "calibration":
        steps = int(command[11:])
        move_motor("focus", steps)

    elif command[0:1] == "b":
        steps = int(command[1:])
        move_motor("tape", steps)

    elif command[:4] == "tape":
        steps = int(command[4:])
        move_motor("tape", steps)

    elif command == "focus":
        focus()
    
  

    else:
        print("Unknown command")
