import lgpio
import time

# Set up
LED_PIN = 21
h = lgpio.gpiochip_open(0)  # Open GPIO chip
lgpio.gpio_claim_output(h, LED_PIN)  # Set pin as output

print("Starting LED blink test...")

try:
    for i in range(10):  # Blink 10 times
        lgpio.gpio_write(h, LED_PIN, 1)  # Turn ON
        print(f"LED ON - blink {i+1}")
        time.sleep(0.1)
        
        lgpio.gpio_write(h, LED_PIN, 0)  # Turn OFF
        print(f"LED OFF - blink {i+1}")
        time.sleep(0.1)
        
except KeyboardInterrupt:
    print("\nStopped by user")
    
finally:
    lgpio.gpiochip_close(h)  # Clean up
    print("GPIO cleaned up")