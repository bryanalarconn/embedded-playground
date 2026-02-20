from machine import Pin, PWM
from micropython import const
import time

# pins
BTN_PIN   = const(10)
TRIG_PIN  = const(17)
ECHO_PIN  = const(16)
MOTOR_PIN = const(15)

# const
NEAR            = const(10)
FAR             = const(75)
LONG_PRESS_MS   = const(3000)
DEBOUNCE_MS     = const(50)
DOUBLE_CLICK_MS = const(400)
LOOP_SLEEP_MS   = const(5)    # fast loop for button responsiveness
DIST_INTERVAL_MS = const(100) # how often to fire the sensor

# hardware connections
trig  = Pin(TRIG_PIN, Pin.OUT)
echo  = Pin(ECHO_PIN, Pin.IN)
motor = PWM(Pin(MOTOR_PIN))
motor.freq(200)
motor.duty_u16(0)
btn   = Pin(BTN_PIN, Pin.IN, Pin.PULL_UP)

# helper functions
def duty_from_distance(d):
    if d <= NEAR: return 65535
    if d >= FAR:  return 0
    return int(65535 * (FAR - d) / (FAR - NEAR))

def distance_cm(timeout_us=30000):
    """Blocking ultrasonic read. ~0.6–30ms depending on distance/timeout."""
    trig.low()
    time.sleep_us(2)
    trig.high()
    time.sleep_us(10)
    trig.low()

    start = time.ticks_us()
    while echo.value() == 0:
        if time.ticks_diff(time.ticks_us(), start) > timeout_us:
            return None

    t0 = time.ticks_us()
    while echo.value() == 1:
        if time.ticks_diff(time.ticks_us(), t0) > timeout_us:
            return None

    return time.ticks_diff(time.ticks_us(), t0) / 58.0

# button handling
class Button:
    def __init__(self, pin):
        self._pin         = pin
        self._last_val    = pin.value()
        self._last_change = time.ticks_ms()
        self._press_start = None
        self._long_done   = False
        self._pending     = False
        self._pend_time   = 0

    def tick(self):
        """Returns one of: None, 'single', 'double', 'long'"""
        now = time.ticks_ms()
        val = self._pin.value()
        event = None

        # debounce edge detection
        edge = False
        if val != self._last_val and time.ticks_diff(now, self._last_change) > DEBOUNCE_MS:
            self._last_change = now
            self._last_val = val
            edge = (val == 0)

        if edge:
            if self._press_start is None:
                self._press_start = now
                self._long_done = False
            if self._pending and time.ticks_diff(now, self._pend_time) <= DOUBLE_CLICK_MS:
                self._pending = False
                event = 'double'
            else:
                self._pending   = True
                self._pend_time = now

        # long-press while held
        if not event and val == 0 and self._press_start is not None and not self._long_done:
            if time.ticks_diff(now, self._press_start) >= LONG_PRESS_MS:
                self._long_done = True
                self._pending   = False
                event = 'long'

        # release
        if val == 1 and self._press_start is not None:
            self._press_start = None
            self._long_done   = False

        # pending single-click timeout
        if not event and self._pending and time.ticks_diff(now, self._pend_time) > DOUBLE_CLICK_MS:
            self._pending = False
            event = 'single'

        return event


powered = False
mode    = 0     # 0=standby, 1=vibrate, 2=signal-only
confirm = False

button = Button(btn)
last_dist_ms = 0

def set_mode(new_mode):
    global mode, confirm
    mode    = new_mode
    confirm = False
    motor.duty_u16(0)
    label = ('STANDBY', 'VIBRATE', 'SIGNAL ONLY')[new_mode]
    print("\n*** MODE:", label, "***\n")

def power_on():
    global powered
    powered = True
    set_mode(0)
    print("\n*** POWER ON: STANDBY ***\n")

def power_off():
    global powered
    powered = False
    set_mode(0)
    print("\n*** POWER OFF ***\n")


# debugging print outs
print("Ready.")
while True:
    ev = button.tick()

    if ev == 'long':
        power_off() if powered else power_on()
    elif ev == 'double':
        if powered:
            set_mode(0)
            print("\n*** DOUBLE CLICK: STANDBY ***\n")
    elif ev == 'single':
        if powered:
            if mode == 0:
                set_mode(1)
                print("\n*** MODE 1: VIBRATE ***\n")
            elif mode == 1:
                set_mode(2)
                print("\n*** MODE 2: SIGNAL ONLY ***\n")
            else:
                set_mode(1)
                print("\n*** MODE 1: VIBRATE ***\n")

    # motor / sensor logic
    if not powered or mode == 0:
        motor.duty_u16(0)
        time.sleep_ms(LOOP_SLEEP_MS)
        continue

    now = time.ticks_ms()
    if time.ticks_diff(now, last_dist_ms) >= DIST_INTERVAL_MS:
        last_dist_ms = now
        d = distance_cm()   # blocking ~0.6–30ms; fine at 100ms intervals

        if mode == 1:
            if d is None:
                motor.duty_u16(0)
                print("Mode 1 | dist: None | duty: 0")
            else:
                duty = duty_from_distance(d)
                motor.duty_u16(duty)
                print("Mode 1 | dist:", round(d, 1), "cm | duty:", duty)

        elif mode == 2:
            motor.duty_u16(0)
            if d is None:
                confirm = False
            else:
                confirm = (d <= FAR)
            print("Mode 2 | dist:", (round(d, 1) if d is not None else None),
                  "cm | confirm_signal:", confirm)

    time.sleep_ms(LOOP_SLEEP_MS)