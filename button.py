#!/usr/bin/python

import RPi.GPIO as GPIO
from subprocess import call
import time

btnPin = 5

GPIO.setmode(GPIO.BOARD)
GPIO.setup(btnPin, GPIO.IN, GPIO.PUD_UP)

while True:
    GPIO.wait_for_edge(btnPin,GPIO.RISING,bouncetime=100)
    time.sleep(0.1)
    print(GPIO.input(btnPin))
    if GPIO.input(btnPin)==1:
        call(["bash", '/home/pi/Projects/HkPiCamMqtt/restart.sh', '2'])
