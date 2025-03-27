from camera import take_picture, camera_settings, take_picture_all
from motor import motors
from focus import focus
from automation import auto_take_pictures, auto_stop


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

    elif command[:11] == "calibration":
        steps = int(command[11:])
        motors["focus"].move(steps)

    elif command == "focus home":
        motors["focus"].home()

    elif command[:4] == "tape":
        steps = int(command[4:])
        motors["tape"].move(steps)

    elif command == "focus":
        focus()

    elif command == "auto":
        auto_take_pictures()

    elif command == "auto test":
        auto_take_pictures(testing=True)

    elif command == "auto stop":
        auto_stop()

    elif command[0:1] == "a":
        steps = int(command[1:])
        motors["focus"].move(steps)

    elif command[0:1] == "b":
        steps = int(command[1:])
        motors["tape"].move(steps)

    else:
        print("Unknown command")
