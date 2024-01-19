# 에러 발생!! - Python 2.x 환경에서 SimpleCV를 사용해야 함!!!!

from SimpleCV import Camera, Display
import time

# 카메라 초기화
cam = Camera()

# 디스플레이 윈도우 생성 (선택 사항)
display = Display()

# 카메라로부터 이미지 캡처
img = cam.getImage()

# 이미지 저장
img.save("captured_image.jpg")

# 이미지 표시 (선택 사항)
img.show()

# 디스플레이 윈도우가 닫힐 때까지 기다림 (선택 사항)
while not display.isDone():
    time.sleep(0.1)

print("이미지가 성공적으로 캡처되고 저장되었습니다.")
