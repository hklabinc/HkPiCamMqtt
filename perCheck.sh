#!/bin/bash

# 'main_mqtt_motion_face' 프로세스가 동작 중인지 확인
if ! pgrep -f "main_mqtt_motion_face" > /dev/null; then

    # ping을 보내 연결을 확인
    if ping -c 1 ictrobot.hknu.ac.kr &> /dev/null; then
	bash /home/pi/Projects/HkPiCamMqtt/start.sh 2
#        python3 /home/pi/Projects/HkPiCamMqtt/hello_world_file.py
#    else
#        python3 /home/pi/Projects/HkPiCamMqtt/hello_world_file2.py
    fi
fi

