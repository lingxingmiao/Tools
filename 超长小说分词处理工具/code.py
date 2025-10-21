import time
import usb_hid
import supervisor
import sys
from adafruit_hid.keyboard import Keyboard
from adafruit_hid.keycode import Keycode
keyboard = Keyboard(usb_hid.devices)
while True:
    if supervisor.runtime.serial_bytes_available:
        try:
            command = sys.stdin.readline().strip()
            if command == "paste":
                keyboard.press(Keycode.CONTROL, Keycode.V)
                keyboard.release_all()
                time.sleep(0.1)
        except Exception as e:
            pass
    time.sleep(0.01)