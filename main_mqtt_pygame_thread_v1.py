import sys, time, base64, datetime, json
import pygame
import pygame.camera
import paho.mqtt.client as mqtt
import threading, queue
from PIL import Image
from io import BytesIO

# 필요한 상수와 변수 설정
WIDTH, HEIGHT = 320, 240
MAX_QUEUE_SIZE = 10             # If queue size is greater than MAX_QUEUE_SIZE, queue becomes clear
DETECT_PERIOD = 0.5             # Captured image is put into the queue every DETECT_PERIOD

if len(sys.argv) != 2:
    print("Insufficient arguments! => Usage: python3 main_image_send_mqtt.py [camera_id]")
    sys.exit()
   
past1, past2, past3 = time.time(), time.time(), time.time()
cameraId = sys.argv[1]
isImage = False
isEvent = False
isQuery = True
para_interval = 0.5
para_interval2, para_interval3 = para_interval, para_interval
para_scale = 1.0
para_threshold = 50     # 달라진 픽셀 갯수 기준치 설정 (defalut=10 or 20)
print(f'cameraId: {cameraId}, isImage: {isImage}, isEvent: {isEvent}, interval: {para_interval}, scale: {para_scale}')

# for Motion Detection
threshold_move = 50     # 달라진 픽셀 값 기준치 설정 (defalut=50)



## For MQTT #########################################################################################################
# 콜백 함수 정의하기
#  (mqttc.connect를 잘 되면) 서버 연결이 잘되면 on_connect 실행 (이벤트가 발생하면 호출)
def on_connect(client, userdata, flags, rc):
    print("rc: " + str(rc))
   
# (mqttc.subscribe가 잘 되면) 구독(subscribe)을 완료하면 on_subscrbie가 호출됨 (이벤트가 발생하면 호출됨)
def on_subscribe(client, obj, mid, granted_qos):
    print("Subscribe complete : " + str(client)+ ", "  + str(mid) + " " + str(granted_qos))

# (mqttc.publish가 잘 되면) 메시지를 publish하면 on_publish실행 (용도: publish를 보내고 난 후 처리를 하고 싶을 때 (사실 이 콜백함수는 잘 쓰진 않는다.))
def on_publish(client, obj, mid):    
    print("mid: " + str(mid) + ", " + str(client))

# 브로커에게 메시지가 도착하면 on_message 실행 (이벤트가 발생하면 호출)
def on_message(client, obj, msg):
    print(msg.topic + ", " + str(client)+ ", " + str(msg.qos) + ", " + str(msg.payload))

    global isImage, isEvent, isQuery          # global로 선언해야    
    global para_interval, para_scale, para_threshold    
    
    command = msg.payload.decode('utf8').replace('True', 'true').replace('False', 'false')    # True, False를 true, false로 변경해야        
    jsonRxMsg = json.loads(command)                     # JSON string to dict string
    print(jsonRxMsg)
        
    if jsonRxMsg.get('isPing') is not None:
        print(jsonRxMsg['isPing'])       

        # Pygame 이미지를 PIL 이미지 객체로 변환
        frame = camera.get_image()
        pil_string_image = pygame.image.tostring(frame, "RGB", False)
        pil_image = Image.frombytes("RGB", frame.get_size(), pil_string_image)

        # PIL 이미지를 JPEG로 변환하고 Base64 인코딩
        buffer = BytesIO()
        pil_image.save(buffer, format="JPEG")
        frame_jpg = buffer.getvalue()
        frame_string = base64.b64encode(frame_jpg).decode('utf8')
        
        objPong = {
                "isImage": isImage,
                "isEvent": isEvent,
                "isQuery": isQuery,
                "scale": para_scale,
                "interval": para_interval,
                "threshold": para_threshold
            }

        json_object = {
            "addr": cameraId,
            "time": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3],
            "type": "pong",            
            "label": json.dumps(objPong),                
            "image": frame_string
            }

        mqttc.publish(pub_topic, json.dumps(json_object))        
        print(f"[{cameraId}] Sent Pong of {sys.getsizeof(json.dumps(json_object))} bytes at {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}")

    if jsonRxMsg.get('isImage') is not None:        
        isImage = jsonRxMsg['isImage']
    if jsonRxMsg.get('isEvent') is not None:        
        isEvent = jsonRxMsg['isEvent']
    if jsonRxMsg.get('isQuery') is not None:        
        isQuery = jsonRxMsg['isQuery']
    if jsonRxMsg.get('scale') is not None:        
        para_scale = float(jsonRxMsg['scale'])
    if jsonRxMsg.get('interval') is not None:        
        para_interval = float(jsonRxMsg['interval'])
    if jsonRxMsg.get('threshold') is not None:        
        para_threshold = int(jsonRxMsg['threshold'])
      
 
# 클라이언트 생성
mqttc = mqtt.Client()
#mqttc = mqtt.Client("Cam_01")

# 콜백 함수 할당하기
mqttc.on_message = on_message
mqttc.on_connect = on_connect
mqttc.on_subscribe = on_subscribe
# mqttc.on_publish = on_publish

# 브로커 연결 설정
server = "hawkai.hknu.ac.kr"
port = 8085
pub_topic = "hawkai/from/ffffffff"  
sub_topic = "hawkai/to/ffffffff"
#username = "HONG" 
#password = "1234"
  
# 클라이언트 설정 후 연결 시도
#mqttc.username_pw_set(username, password)      # username과 password 설정되어 있으면
mqttc.connect(host=server, port=port)
mqttc.subscribe(sub_topic, 0)       # QoS level 0으로 구독 설정, 정상적으로 subscribe 되면 on_subscribe 호출됨
mqttc.loop_start()
#########################################################################################################



# Pygame 카메라 초기화
pygame.init()
pygame.camera.init()

# 카메라 리스트 받기
camlist = pygame.camera.list_cameras()
if not camlist:
    raise ValueError("No camera found!")

# 카메라 설정
camera = pygame.camera.Camera(camlist[0], (WIDTH, HEIGHT))
camera.start()


def process_image(frame):    
    
    # 주기적으로 이미지를 서버에 전송 
    now1 = time.time()   
    if isImage:    
        # Pygame 이미지를 PIL 이미지 객체로 변환
        pil_string_image = pygame.image.tostring(frame, "RGB", False)
        pil_image = Image.frombytes("RGB", frame.get_size(), pil_string_image)

        # PIL 이미지를 JPEG로 변환하고 Base64 인코딩
        buffer = BytesIO()
        pil_image.save(buffer, format="JPEG")
        frame_jpg = buffer.getvalue()
        frame_string = base64.b64encode(frame_jpg).decode('utf8')        
        
        json_object = {
            "addr": cameraId,
            "time": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3],
            "type": "image",            
            "label": "none",                
            "image": frame_string
            }

        mqttc.publish(pub_topic, json.dumps(json_object))        
        print(f"[{cameraId}] Sent Image of {sys.getsizeof(json.dumps(json_object))} bytes at {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}")
        past1 = now1




#########################################################################################################
## Added for Threading                                                                                  #
#########################################################################################################

q = queue.Queue()

### Receiving Thread ###
def receive():
    print("Start Receive thread...")    
    while True:
        image = camera.get_image()
        if q.qsize() > MAX_QUEUE_SIZE:
            q.queue.clear()
        
        q.put(image)
        time.sleep(DETECT_PERIOD)

### Processing Thread ### 
def process():
    print("Start Process thread...")    
    while True:        
        if not q.empty():
            frame = q.get()
            process_image(frame)
        
            

### Main Thread ###
if __name__ == '__main__':
    try:
        recv_thread = threading.Thread(target=receive, daemon=True)
        proc_thread = threading.Thread(target=process, daemon=True)
        recv_thread.start()
        proc_thread.start()

        while True:
            time.sleep(100)
    except (KeyboardInterrupt, SystemExit):
        print('Exiting program.')
        camera.stop()
        pygame.quit()
        sys.exit()