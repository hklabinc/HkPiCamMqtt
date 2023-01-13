import time
import cv2
import base64
import datetime
import json
import sys
import numpy as np
import paho.mqtt.client as mqtt


if len(sys.argv) != 2:
    print("Insufficient arguments! => Usage: python3 main_image_send_mqtt.py [camera_id]")
    sys.exit()
   
def to_bool(value):    
    if str(value).lower() in ("yes", "y", "true",  "t", "1"): return True
    if str(value).lower() in ("no",  "n", "false", "f", "0", "0.0", "", "none", "[]", "{}"): return False
    raise Exception('Invalid value for boolean conversion: ' + str(value))

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
    if "isImage" in command:       
        isImage = to_bool(command.split("=")[1])
    elif "isEvent" in command:  
        isEvent = to_bool(command.split("=")[1])
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
url = "hawkai.hknu.ac.kr"
port = 8085
pub_topic = "hawkai/from"  
sub_topic = "hawkai/to"
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


past1, past2, past3 = time.time(), time.time(), time.time()
cameraId = sys.argv[1]
isImage = False
isEvent = False
para_interval = 0.5
para_interval2, para_interval3 = para_interval, para_interval
para_scale = 1.0
WIDTH = 320
HEIGHT = 240
print(f'cameraId: {cameraId}, isImage: {isImage}, isEvent: {isEvent}, interval: {para_interval}, scale: {para_scale}')
# url = 'rtsp://admin:init123!!@sean715.iptime.org:554/SD'
url = 0
cap = cv2.VideoCapture(url)
# cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)  # 카메라 영상 넓이
# cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480) # 카메라 영상 높이

# for Face Detection
face_cascade = cv2.CascadeClassifier("haarcascades/haarcascade_frontalface_default.xml")
eye_cascade = cv2.CascadeClassifier("haarcascades/haarcascade_eye.xml")

# for Motion Detection
threshold_move = 50     # 달라진 픽셀 값 기준치 설정 (defalut=50)
diff_compare = 20       # 달라진 픽셀 갯수 기준치 설정 (defalut=10)
ret, img_first = cap.read()  # 1번째 프레임 읽기
ret, img_second = cap.read()  # 2번째 프레임 읽기


while True :
    ret, frame = cap.read()
    # print(time.time())
    # cv2.imshow("video", frame)
    if cv2.waitKey(30) & 0xff == 27:  # Esc 키를 누르면 종료
        break  
    
    # 주기적으로 이미지를 서버에 전송 
    now1 = time.time()        
    if isImage and (now1-past1) > para_interval:    
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
        past1 = now1


    # Motion Detector: 움직임 발생시 이벤트 전송 
    now2 = time.time() 
    if isEvent and (now2-past2) > para_interval2:       
        scr = frame.copy()  # 화면에 다른점 표시할 이미지 백업 (frame이 3번째 프레임)

        # 그레이 스케일로 변경
        img_first_gray = cv2.cvtColor(img_first, cv2.COLOR_BGR2GRAY)
        img_second_gray = cv2.cvtColor(img_second, cv2.COLOR_BGR2GRAY)
        img_third_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # 이미지간의 차이점 계산
        diff_1 = cv2.absdiff(img_first_gray, img_second_gray)
        diff_2 = cv2.absdiff(img_second_gray, img_third_gray)

        # Threshold 적용
        ret, diff_1_thres = cv2.threshold(diff_1, threshold_move, 255, cv2.THRESH_BINARY)
        ret, diff_2_thres = cv2.threshold(diff_2, threshold_move, 255, cv2.THRESH_BINARY)

        # 1번째영상-2번째영상, 2번째영상-3번째영상 차이점
        diff = cv2.bitwise_and(diff_1_thres, diff_2_thres)

        # 열림 연산으로 노이즈 제거 ---①
        # k = cv2.getStructuringElement(cv2.MORPH_CROSS, (3, 3))
        # diff = cv2.morphologyEx(diff, cv2.MORPH_OPEN, k)

        # 차이가 발생한 픽셀이 갯수 판단 후 사각형 그리기
        diff_cnt = cv2.countNonZero(diff)
        if diff_cnt > diff_compare:
            nzero = np.nonzero(diff)  # 0이 아닌 픽셀의 좌표 얻기
            cv2.rectangle(scr, (min(nzero[1]), min(nzero[0])), \
                        (max(nzero[1]), max(nzero[0])), (0, 255, 0), 1)
            cv2.putText(scr, "Motion Detected", (10, 10), \
                        cv2.FONT_HERSHEY_DUPLEX, 0.3, (0, 255, 0))

        # 컬러 스케일 영상과 스레시홀드 영상을 통합해서 출력
        # stacked = np.hstack((scr, cv2.cvtColor(diff, cv2.COLOR_GRAY2BGR)))
        # cv2.imshow('motion sensor', stacked)
        # cv2.imshow('scr', scr)

        # 다음 비교를 위해 영상 저장
        img_first = img_second
        img_second = frame

        if diff_cnt > diff_compare:  # 움직임이 존재하면 MQTT로 전송 
            frame_scaled = cv2.resize(scr, (int(para_scale*WIDTH), int(para_scale*HEIGHT)), interpolation=cv2.INTER_LINEAR)        # Image resize          
            retval, frame_jgp = cv2.imencode('.jpg', frame_scaled)                # Convert to jpg
            frame_string = base64.b64encode(frame_jgp).decode('utf8')      # Convert to base64 string   
            
            json_object = {
                "addr": cameraId,
                "time": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3],
                "type": "event",            
                "label": "motion",                
                "image": frame_string
                }

            mqttc.publish(pub_topic, json.dumps(json_object))        
            print(f"[HHCHOI] Sent Event (motion) of {sys.getsizeof(json.dumps(json_object))} bytes at {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}")
            past2 = now2


    # Face Detector: 얼굴 발생시 이벤트 전송 
    now3 = time.time() 
    if isEvent and (now3-past3) > para_interval3:       
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
                
        if len(faces) > 0:  # 얼굴이 존재하면 MQTT로 전송 
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
            past3 = now3




