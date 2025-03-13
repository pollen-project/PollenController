from camera import calculate_sharpness
from motor import move_motor


def focus():
    global focus_motor_pos

    try:
        sharpness = calculate_sharpness()
        while sharpness < 20:
            move_motor("focus",10)
            sharpness = calculate_sharpness()

        print('Focus done')
    except KeyboardInterrupt:
        print('Focus cancelled')
