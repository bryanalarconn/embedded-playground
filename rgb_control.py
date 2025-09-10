import lgpio
import time

# GPIO pins for Common Anode RGB LED
RED_PIN = 16
GREEN_PIN = 20
BLUE_PIN = 21

# Set up GPIO
h = lgpio.gpiochip_open(0)
lgpio.gpio_claim_output(h, RED_PIN)
lgpio.gpio_claim_output(h, GREEN_PIN)
lgpio.gpio_claim_output(h, BLUE_PIN)

def set_color(red, green, blue):
    """Set RGB LED color for COMMON ANODE (inverted logic: 0=ON, 1=OFF)"""
    lgpio.gpio_write(h, RED_PIN, 1-red)
    lgpio.gpio_write(h, GREEN_PIN, 1-green)
    lgpio.gpio_write(h, BLUE_PIN, 1-blue)

def all_off():
    """Turn off all colors"""
    set_color(0, 0, 0)

try:
    print("RGB LED color cycling - Press Ctrl+C to stop")
    
    # Turn everything off first
    all_off()
    time.sleep(0.5)
    
    # Infinite loop cycling through colors
    while True:
        print("Red")
        set_color(1, 0, 0)
        time.sleep(1)
        
        print("Green")
        set_color(0, 1, 0)
        time.sleep(1)
        
        print("Blue")
        set_color(0, 0, 1)
        time.sleep(1)
        
except KeyboardInterrupt:
    print("\nStopping color cycle...")
    
finally:
    all_off()
    lgpio.gpiochip_close(h)
    print("RGB cycle stopped")