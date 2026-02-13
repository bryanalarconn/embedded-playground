from machine import Pin, PWM
import time

trig = Pin(2, Pin.OUT)
echo = Pin(3, Pin.IN)

motor = PWM(Pin(15))
motor.freq(200)
motor.duty_u16(0)

# Kill switch button: GP14 -> GND
button = Pin(14, Pin.IN, Pin.PULL_UP)

NEAR = 10
FAR = 200

enabled = False
press_start = None
LONG_PRESS_MS = 1500
DEBOUNCE_MS = 50

def distance_cm(timeout_us=30000):
    trig.low()
    time.sleep_us(2)
    trig.high()
    time.sleep_us(10)
    trig.low()

    start = time.ticks_us()
    while echo.value() == 0:
        if time.ticks_diff(time.ticks_us(), start) > timeout_us:
            return None

    pulse_start = time.ticks_us()
    while echo.value() == 1:
        if time.ticks_diff(time.ticks_us(), pulse_start) > timeout_us:
            return None

    pulse_end = time.ticks_us()
    pulse_us = time.ticks_diff(pulse_end, pulse_start)
    return pulse_us / 58.0

print("Running. Long Press button to enable vibration.")

while True:
    btn = button.value()
    now = time.ticks_ms()

    # ---- Button pressed ----
    if btn == 0 and press_start is None:
        press_start = now

    # ---- Button released ----
    if btn == 1 and press_start is not None:
        press_time = time.ticks_diff(now, press_start)

        if press_time >= LONG_PRESS_MS and not enabled:
            enabled = True
            print("SYSTEM ON (long press)")
        elif press_time < LONG_PRESS_MS and enabled:
            enabled = False
            print("SYSTEM OFF (short press)")

        press_start = None
        time.sleep_ms(DEBOUNCE_MS)

    # ---- System OFF ----
    if not enabled:
        motor.duty_u16(0)
        time.sleep(0.05)
        continue


    d = distance_cm()
    if d is None:
        motor.duty_u16(0)
    else:
        if d <= NEAR:
            duty = 65535
        elif d >= FAR:
            duty = 0
        else:
            duty = int(65535 * (FAR - d) / (FAR - NEAR))
            

        motor.duty_u16(duty)
        print("Dist:", round(d, 1), "cm | duty:", duty)

    time.sleep(0.08)
