import imageio
import matplotlib.pyplot as plt
from IPython import display

# 웹캠으로부터 비디오 스트림 생성
reader = imageio.get_reader('<video0>')

plt.ion()  # 대화형 모드 활성화

try:
    while True:
        image = reader.get_next_data()  # 다음 이미지 캡처
        plt.imshow(image)  # 이미지 표시
        display.clear_output(wait=True)  # 출력 지우기
        display.display(plt.gcf())  # 현재 figure 표시
        plt.pause(0.1)  # 잠시 대기
except KeyboardInterrupt:
    # 사용자가 중단하면 루프 종료
    print("스트리밍 중단됨")

reader.close()  # 리더 종료
