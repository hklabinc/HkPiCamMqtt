import imageio

# 웹캠으로부터 비디오 스트림 생성
reader = imageio.get_reader('<video0>')

# 첫 번째 이미지 캡처
image = reader.get_next_data()

# 이미지 파일로 저장
imageio.imwrite('captured_image.jpg', image)

# 리더 종료
reader.close()

print("이미지가 성공적으로 캡처되고 저장되었습니다.")
