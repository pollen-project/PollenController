from math import floor

from camera import calculate_sharpness
from motor import motors


def focus():
    step_size = 10
    direction = 1  # 1 for forward, -1 for backwars
    motor = motors["focus"]
    previous_sharpness = 0
    best_sharpness = 0
    increase_counter = 0
    decrease_counter = 0
    peak_found = False
    time_running = 0

    try:
        while time_running < 200:
            result = motor.move(step_size * direction)

            if not result:
                direction *= -1

            sharpness = floor(calculate_sharpness())

            if peak_found:
                if sharpness + 1 >= best_sharpness:
                    break
            else:
                if sharpness > previous_sharpness:
                    increase_counter += 1

                    # if increase_counter == 3:
                    #     step_size = 5

                elif sharpness < previous_sharpness:
                    if increase_counter > 0:
                        decrease_counter += 1

                        if decrease_counter >= 3:
                            direction *= -1
                            step_size = 5
                            increase_counter = 0
                            decrease_counter = 0
                            peak_found = True

                else:
                    increase_counter = 0
                    decrease_counter = 0

                if sharpness > best_sharpness:
                    best_sharpness = sharpness

            previous_sharpness = sharpness
            print(f"[focus] sharpness={sharpness} best_sharpness={best_sharpness} increase_counter={increase_counter} decrease_counter={decrease_counter} peak_found={str(peak_found)} position={motor.position}")

            time_running += 1


        # sharpness = calculate_sharpness()
        # while sharpness < 15:
        #     motors["focus"].move(10)
        #     sharpness = calculate_sharpness()

        print('Focus done')
    except KeyboardInterrupt:
        print('Focus cancelled')
