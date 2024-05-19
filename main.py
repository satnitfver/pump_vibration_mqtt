import math
import time
from machine import Pin, I2C, reset, Timer
from mpu6050 import MPU6050
import network
from umqtt.simple import MQTTClient
import secrets

# Wi-Fi credentials
SSID = secrets.ssid
PASSWORD = secrets.ssidpassword

# MQTT broker details
MQTT_BROKER = "192.x.x.x"
MQTT_PORT = 1883
MQTT_TOPIC = "pump/vibration"

# Connect to Wi-Fi
def connect_to_wifi(ssid, password):
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(ssid, password)
    
    while not wlan.isconnected():
        print('Connecting to Wi-Fi...')
        time.sleep(1)
    
    print('Connected to Wi-Fi:', wlan.ifconfig())

# Initialize I2C and MPU6050
i2c = I2C(0, scl=Pin(2), sda=Pin(1), freq=400000)
mpu = MPU6050(i2c, addr=0x68)

# Parameters for vibration detection
threshold = 0.5  # Adjust based on your sensitivity needs
previous_magnitude = 0

# Function to reset on watchdog timeout
def reset_on_watchdog(t):
    print('Watchdog triggered! Resetting...')
    reset()

# Setup watchdog timer (10 seconds for example)
watchdog_timer = Timer(-1)
watchdog_timer.init(period=10000, mode=Timer.ONE_SHOT, callback=reset_on_watchdog)

# Function to refresh watchdog timer
def refresh_watchdog():
    watchdog_timer.deinit()
    watchdog_timer.init(period=10000, mode=Timer.ONE_SHOT, callback=reset_on_watchdog)

# Connect to Wi-Fi
connect_to_wifi(SSID, PASSWORD)

# Initialize MQTT client
client = MQTTClient("pico_client", MQTT_BROKER, port=MQTT_PORT, keepalive=3600)

# Function to connect to MQTT broker with retry
def connect_to_mqtt():
    while True:
        try:
            client.connect()
            print('Connected to MQTT Broker')
            break
        except Exception as e:
            print('Failed to connect to MQTT Broker:', e)
            time.sleep(5)

# Connect to the MQTT broker
connect_to_mqtt()

def get_magnitude(accel):
    return math.sqrt(accel['x']**2 + accel['y']**2 + accel['z']**2)

while True:
    try:
        # Refresh the watchdog timer
        refresh_watchdog()
        
        # Get accelerometer data
        accel = mpu.get_accel_data()
        
        # Calculate magnitude of acceleration
        current_magnitude = get_magnitude(accel)
        
        # Detect significant change
        if abs(current_magnitude - previous_magnitude) > threshold:
            print("Vibration detected!")
            print("Magnitude: {:.2f}".format(current_magnitude))
            
            # Send MQTT message
            message = "{:.2f}".format(current_magnitude)
            client.publish(MQTT_TOPIC, message)
            print("MQTT message sent")

        # Update previous magnitude
        previous_magnitude = current_magnitude
        
        # Delay for next sample
        time.sleep(0.01)  # Sampling rate of 100 Hz

    except OSError as e:
        print('Error:', e)
        # Attempt to reconnect to MQTT broker on error
        connect_to_mqtt()
    except Exception as e:
        print('Unexpected error:', e)
        reset()  # Reset on unexpected errors

