#!/bin/bash
FileName="/home/pi/Projects/HkPiCamMqtt/hello_world_file.py"

#if ping -c 1 www.google.com &> /dev/null; then
#    python3 $FileName
#else
#    python3 /home/pi/Projects/HkPiCamMqtt/hello_world_file2.py
#fi


# 'main_mqtt_motion_face' 프로세스가 동작 중인지 확인
if ! pgrep -f "main_mqtt_motion_face" > /dev/null; then
    # ping을 보내 연결을 확인
    if ping -c 1 ictrobot.hknu.ac.kr &> /dev/null; then
        python3 $FileName
    else
        python3 /home/pi/Projects/HkPiCamMqtt/hello_world_file2.py
    fi
fi

