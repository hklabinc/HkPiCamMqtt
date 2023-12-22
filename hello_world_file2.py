#!/usr/bin/python

from datetime import datetime

current_time = datetime.now()
current_time_string = current_time.strftime("%Y-%m-%d %H:%M:%S")
print("현재 시간:", current_time_string)

# 파일에 메시지 쓰기
with open("/home/pi/Projects/HkPiCamMqtt/hello.txt", "a") as file:
    file.write(current_time_string + " - Internet is not working!!!" + '\n')

