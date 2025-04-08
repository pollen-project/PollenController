from camera import calculate_sharpness
from motor import motors
from time import sleep

def focus():
    motor = motors["focus"]
    step_size = 2
    max_steps = 60

    print("[focus] Starting coarse scan to find best focus...")

    best_sharpness = 0
    best_step_index = 0
    sharpness_log = []

    # --------- PHASE 1: Scan forward and find peak ----------
    for i in range(max_steps):
        sharpness = calculate_sharpness()
        sharpness_log.append(sharpness)
        print(f"[focus] Step {i}, Sharpness: {sharpness:.2f}")

        if sharpness > best_sharpness:
            best_sharpness = sharpness
            best_step_index = i

        if i > best_step_index + 2 and sharpness < best_sharpness * 0.97:
            print("[focus] Sharpness dropped after peak — stopping scan.")
            break

        motor.move(step_size)
        #sleep(2)

    print(f"[focus] Coarse scan complete. Best sharpness: {best_sharpness:.2f} at step {best_step_index}")

    # --------- PHASE 2: Backtrack live by sharpness ----------
    print("[focus] Re-approaching best focus with live sharpness check...")

    current_sharpness = calculate_sharpness()
    last_sharpness = current_sharpness
    reverse_attempts = 0
    max_reverse_attempts = 20
    found_peak = False

    for i in range(max_reverse_attempts):
        motor.move(-1)  # small backstep

        sharpness = calculate_sharpness()
        print(f"[focus] Backtrack step {i}, Sharpness: {sharpness:.2f}")

        if sharpness >= best_sharpness * 0.995:
            found_peak = True
            print("[focus] Reached best sharpness region again.")
            break

        if sharpness < last_sharpness * 0.98:
            print("[focus] Sharpness dropped further — maybe overshot.")
            break

        last_sharpness = sharpness

    if not found_peak:
        print("[focus] WARNING: Failed to return to sharpest point.")

    print(f"[focus] Final focus: Sharpness ≈ {calculate_sharpness():.2f} — autofocus complete.")
