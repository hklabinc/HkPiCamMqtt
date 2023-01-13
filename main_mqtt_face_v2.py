import time
import cv2
import base64
import datetime
import json
import sys
import paho.mqtt.client as mqtt


if len(sys.argv) != 2:
    print("Insufficient arguments! => Usage: python3 main_image_send_mqtt.py [camera_id]")
    sys.exit()

isEvent = True
if isEvent:
    face_cascade = cv2.CascadeClassifier("haarcascades/haarcascade_frontalface_default.xml")
    eye_cascade = cv2.CascadeClassifier("haarcascades/haarcascade_eye.xml")
    
    

## For MQTT #########################################################################################################
# 콜백 함수 정의하기
#  (mqttc.connect를 잘 되면) 서버 연결이 잘되면 on_connect 실행 (이벤트가 발생하면 호출)
def on_connect(client, userdata, flags, rc):
    print("rc: " + str(rc))
   
# (mqttc.subscribe가 잘 되면) 구독(subscribe)을 완료하면
# on_subscrbie가 호출됨 (이벤트가 발생하면 호출됨)
def on_subscribe(client, obj, mid, granted_qos):
    print("Subscribe complete : " + str(client)+ ", "  + str(mid) + " " + str(granted_qos))

# 브로커에게 메시지가 도착하면 on_message 실행 (이벤트가 발생하면 호출)
def on_message(client, obj, msg):
    print(msg.topic + ", " + str(client)+ ", " + str(msg.qos) + ", " + str(msg.payload))

    global isImage, isEvent          # global로 선언해야    
    global para_interval, para_scale, para_width, para_height

    command = msg.payload.decode('utf8')
    if command == "Start":        
        isImage = True
        isEvent = True
    elif command == "Stop":        
        isImage = False
        isEvent = False
    elif "interval" in command:
        para_interval = float(command.split("=")[1])
    elif "scale" in command:
        para_scale = float(command.split("=")[1])        
       
 
# (mqttc.publish가 잘 되면) 메시지를 publish하면 on_publish실행 (이벤트가 발생하면 호출)
def on_publish(client, obj, mid):
    # 용도 : publish를 보내고 난 후 처리를 하고 싶을 때
    # 사실 이 콜백함수는 잘 쓰진 않는다.
    print("mid: " + str(mid) + ", " + str(client))
 
# 클라이언트 생성
mqttc = mqtt.Client()
#mqttc = mqtt.Client("Cam_01")

# 콜백 함수 할당하기
mqttc.on_message = on_message
mqttc.on_connect = on_connect
# mqttc.on_publish = on_publish
mqttc.on_subscribe = on_subscribe

# 브로커 연결 설정
# 참고로 브로커를 Cloudmqtt 홈페이지를 사용할 경우
# 미리 username과 password, topic이 등록 되어있어야함.
url = "ictrobot.hknu.ac.kr"
port = 8085
pub_topic = "aicms/fromCam"  
sub_topic = "aicms/toCam"
#username = "HONG" # Cloud mqtt
#password = "1234"
  
# 클라이언트 설정 후 연결 시도
#mqttc.username_pw_set(username, password)
mqttc.connect(host=url, port=port)
#mqttc.connect("ictrobot.hknu.ac.kr", 8085)
 
# QoS level 0으로 구독 설정, 정상적으로 subscribe 되면 on_subscribe 호출됨
mqttc.subscribe(sub_topic, 0)
mqttc.loop_start()
#########################################################################################################


past = time.time()
past2 = time.time()
cameraId = sys.argv[1]
isImage = True
para_interval = 0.5
para_interval2 = para_interval
para_scale = 1.0
WIDTH = 320
HEIGHT = 240
print(f'cameraId: {cameraId}, isImage: {isImage}, isEvent: {isEvent}, interval: {para_interval}, scale: {para_scale}')
# url = 'rtsp://admin:init123!!@sean715.iptime.org:554/SD'
url = 0
cap = cv2.VideoCapture(url)
# cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)  # 카메라 영상 넓이
# cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480) # 카메라 영상 높이

while True :
    ret, frame = cap.read()
    # print(time.time())
    # cv2.imshow("video", frame)
    k = cv2.waitKey(30) & 0xff
    if k == 27:  # Esc 키를 누르면 종료
        break  
    
    # 주기적으로 이미지를 서버에 전송 
    now = time.time()        
    if isImage and (now-past) > para_interval:    
        frame_scaled = cv2.resize(frame, (int(para_scale*WIDTH), int(para_scale*HEIGHT)), interpolation=cv2.INTER_LINEAR)        # Image resize          
        retval, frame_jgp = cv2.imencode('.jpg', frame_scaled)                # Convert to jpg
        frame_string = base64.b64encode(frame_jgp).decode('utf8')      # Convert to base64 string   
        
        json_object = {
            "addr": cameraId,
            "time": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3],
            "type": "image",            
            "label": "none",                
            "image": frame_string
            }

        mqttc.publish(pub_topic, json.dumps(json_object))        
        print(f"[HHCHOI] Sent Image of {sys.getsizeof(json.dumps(json_object))} bytes at {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}")
        past = now

    # Face Detector: 얼굴 발생시 이벤트 전송 
    now2 = time.time() 
    if isEvent and (now2-past2) > para_interval2:       
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        faces = face_cascade.detectMultiScale(gray, 1.2, 5)
        # print("Number of faces detected: " + str(len(faces)))

        for (x, y, w, h) in faces:
            frame = cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 1)
            roi_gray = gray[y:y + h, x:x + w]
            roi_color = frame[y:y + h, x:x + w]
            eyes = eye_cascade.detectMultiScale(roi_gray)
            for (ex, ey, ew, eh) in eyes:
                cv2.rectangle(roi_color, (ex, ey), (ex + ew, ey + eh), (0, 255, 0), 1)
                
        if len(faces) > 0:  # 얼굴이 존재하면 
            frame_scaled = cv2.resize(frame, (int(para_scale*WIDTH), int(para_scale*HEIGHT)), interpolation=cv2.INTER_LINEAR)        # Image resize          
            retval, frame_jgp = cv2.imencode('.jpg', frame_scaled)                # Convert to jpg
            frame_string = base64.b64encode(frame_jgp).decode('utf8')      # Convert to base64 string   
            
            json_object = {
                "addr": cameraId,
                "time": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3],
                "type": "event",            
                "label": "face",                
                "image": frame_string
                }

            mqttc.publish(pub_topic, json.dumps(json_object))        
            print(f"[HHCHOI] Sent Event ({len(faces)} faces) of {sys.getsizeof(json.dumps(json_object))} bytes at {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}")
            past2 = now2




