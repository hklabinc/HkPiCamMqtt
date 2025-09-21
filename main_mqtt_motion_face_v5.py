import cv2, sys, time, base64, datetime, json, threading
import numpy as np
import paho.mqtt.client as mqtt

if len(sys.argv) != 2:
    print("Usage: python3 main_image_send_mqtt.py [camera_id]")
    sys.exit()

cameraId = sys.argv[1]

# ===== Parameters =====
isImage, isEvent, isQuery = False, False, True
para_interval = 0.5
para_interval2, para_interval3 = para_interval, para_interval
para_scale = 1.0
para_threshold = 50      # motion: pixel count threshold
WIDTH, HEIGHT = 320, 240
threshold_move = 50      # motion: per-pixel diff threshold

print(f'cameraId: {cameraId}, isImage: {isImage}, isEvent: {isEvent}, interval: {para_interval}, scale: {para_scale}')

# ===== Camera Capture Thread =====
CAMERA_SOURCE = 0
cap = cv2.VideoCapture(CAMERA_SOURCE)
latest_frame = None
stop_thread = False

def camera_reader():
    global latest_frame
    while not stop_thread:
        ret, frame = cap.read()
        if ret:
            latest_frame = frame
        time.sleep(0.01)  # small delay to avoid 100% CPU

thread_cam = threading.Thread(target=camera_reader, daemon=True)
thread_cam.start()

# ===== Cascade Classifiers =====
face_cascade = cv2.CascadeClassifier("haarcascades/haarcascade_frontalface_default.xml")
eye_cascade = cv2.CascadeClassifier("haarcascades/haarcascade_eye.xml")

# ===== MQTT Callbacks =====
def on_connect(client, userdata, flags, rc):
    print("Connected, rc:", rc)

def on_subscribe(client, obj, mid, granted_qos):
    print("Subscribed:", mid, granted_qos)

def on_message(client, obj, msg):
    global isImage, isEvent, isQuery, para_interval, para_scale, para_threshold, latest_frame

    try:
        command = msg.payload.decode('utf8').replace('True', 'true').replace('False', 'false')
        jsonRxMsg = json.loads(command)
        print("Received:", jsonRxMsg)

        if jsonRxMsg.get('isPing'):
            if latest_frame is not None:
                frame_scaled = cv2.resize(latest_frame, (int(para_scale * WIDTH), int(para_scale * HEIGHT)))
                _, frame_jpg = cv2.imencode('.jpg', frame_scaled)
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
                print(f"[{cameraId}] Sent Pong")

        if 'isImage' in jsonRxMsg: isImage = jsonRxMsg['isImage']
        if 'isEvent' in jsonRxMsg: isEvent = jsonRxMsg['isEvent']
        if 'isQuery' in jsonRxMsg: isQuery = jsonRxMsg['isQuery']
        if 'scale' in jsonRxMsg: para_scale = float(jsonRxMsg['scale'])
        if 'interval' in jsonRxMsg: para_interval = float(jsonRxMsg['interval'])
        if 'threshold' in jsonRxMsg: para_threshold = int(jsonRxMsg['threshold'])

    except Exception as e:
        print("Error in on_message:", e)

# ===== MQTT Setup =====
mqttc = mqtt.Client()
mqttc.on_message = on_message
mqttc.on_connect = on_connect
mqttc.on_subscribe = on_subscribe

MQTT_HOST = "hawkai.hknu.ac.kr"
MQTT_PORT = 8085
pub_topic = "hawkai/from/ffffffff"
sub_topic = "hawkai/to/ffffffff"

mqttc.connect(MQTT_HOST, MQTT_PORT)
mqttc.subscribe(sub_topic, 0)
mqttc.loop_start()

# ===== Main Loop =====
past1, past2, past3 = 0, 0, 0
img_first, img_second = None, None

try:
    while True:
        frame = latest_frame
        if frame is None:
            time.sleep(0.05)
            continue

        now = time.time()

        # --- Periodic Image Sender ---
        if isImage and (now - past1) > para_interval:
            frame_scaled = cv2.resize(frame, (int(para_scale*WIDTH), int(para_scale*HEIGHT)))
            _, frame_jpg = cv2.imencode('.jpg', frame_scaled)
            frame_string = base64.b64encode(frame_jpg).decode('utf8')

            json_object = {
                "addr": cameraId,
                "time": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3],
                "type": "image",
                "label": "none",
                "image": frame_string
            }
            mqttc.publish(pub_topic, json.dumps(json_object))
            print(f"[{cameraId}] Sent Image")
            past1 = now

        # --- Motion Detector ---
        if isEvent and (now - past2) > para_interval2:
            if img_first is None or img_second is None:
                img_first, img_second = frame, frame
            else:
                img_third = frame
                diff1 = cv2.absdiff(cv2.cvtColor(img_first, cv2.COLOR_BGR2GRAY),
                                    cv2.cvtColor(img_second, cv2.COLOR_BGR2GRAY))
                diff2 = cv2.absdiff(cv2.cvtColor(img_second, cv2.COLOR_BGR2GRAY),
                                    cv2.cvtColor(img_third, cv2.COLOR_BGR2GRAY))
                _, diff1_thres = cv2.threshold(diff1, threshold_move, 255, cv2.THRESH_BINARY)
                _, diff2_thres = cv2.threshold(diff2, threshold_move, 255, cv2.THRESH_BINARY)
                diff = cv2.bitwise_and(diff1_thres, diff2_thres)

                diff_cnt = cv2.countNonZero(diff)
                if diff_cnt > para_threshold:
                    scr = img_third.copy()
                    nzero = np.nonzero(diff)
                    cv2.rectangle(scr, (min(nzero[1]), min(nzero[0])),
                                       (max(nzero[1]), max(nzero[0])), (0,255,0), 1)
                    cv2.putText(scr, "Motion Detected", (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,255,0))

                    frame_scaled = cv2.resize(scr, (int(para_scale*WIDTH), int(para_scale*HEIGHT)))
                    _, frame_jpg = cv2.imencode('.jpg', frame_scaled)
                    frame_string = base64.b64encode(frame_jpg).decode('utf8')

                    json_object = {
                        "addr": cameraId,
                        "time": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3],
                        "type": "event",
                        "label": "motion",
                        "image": frame_string
                    }
                    mqttc.publish(pub_topic, json.dumps(json_object))
                    print(f"[{cameraId}] Sent Motion Event")

                img_first, img_second = img_second, img_third
            past2 = now  # 주기 강제 갱신

        # --- Face Detector ---
        if isEvent and (now - past3) > para_interval3:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, 1.2, 5)

            if len(faces) > 0:
                for (x,y,w,h) in faces:
                    cv2.rectangle(frame, (x,y), (x+w,y+h), (255,0,0), 1)
                    roi_gray = gray[y:y+h, x:x+w]
                    eyes = eye_cascade.detectMultiScale(roi_gray)
                    for (ex,ey,ew,eh) in eyes:
                        cv2.rectangle(frame[y:y+h, x:x+w], (ex,ey), (ex+ew,ey+eh), (0,255,0), 1)

                frame_scaled = cv2.resize(frame, (int(para_scale*WIDTH), int(para_scale*HEIGHT)))
                _, frame_jpg = cv2.imencode('.jpg', frame_scaled)
                frame_string = base64.b64encode(frame_jpg).decode('utf8')

                json_object = {
                    "addr": cameraId,
                    "time": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3],
                    "type": "event",
                    "label": "face",
                    "image": frame_string
                }
                mqttc.publish(pub_topic, json.dumps(json_object))
                print(f"[{cameraId}] Sent Face Event")

            past3 = now  # 주기 강제 갱신

        # ESC 종료 감지 (윈도우 없는 경우 무시됨)
        if cv2.waitKey(1) & 0xFF == 27:
            break

except KeyboardInterrupt:
    print("Interrupted by user")

finally:
    stop_thread = True
    thread_cam.join()
    cap.release()
    mqttc.loop_stop()
    cv2.destroyAllWindows()
    print("Clean exit complete")
