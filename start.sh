CamName="HK_PiCam04"
FileName="/home/pi/Projects/HkPiCamMqtt/main_mqtt_motion_face_v5.py"

if [ $# == 0 ]; then
        python3 $FileName $CamName
elif [ $1 == 1 ]; then
        nohup python3 $FileName $CamName &
elif [ $1 == 2 ]; then
        nohup python3 $FileName $CamName 1>/dev/null 2>&1 &
else
        python3 $FileName $CamName
fi

