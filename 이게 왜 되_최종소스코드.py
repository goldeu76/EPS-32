from neopixel import NeoPixel
from machine import Pin, I2C
from pyhuskylens import HuskyLens, ALGORITHM_FACE_RECOGNITION
import ssd1306  # 생성형 AI 활용: OLED 디스플레이 모듈
import dht
import time

# 1. 하드웨어 I2C 초기화
i2c = I2C(0, scl=Pin(22), sda=Pin(21), freq=100000)

# 2. 허스키렌즈 초기화 및 연결 확인
huskylens = HuskyLens(i2c)

if not huskylens.knock():
    print("❌ 허스키렌즈 연결 실패!")
    print("팁: 허스키렌즈 메뉴 -> General Settings -> Protocol Type이 'I2C'인지 확인하세요.")
else:
    print("✅ 허스키렌즈 연결 성공!")
    huskylens.set_alg(ALGORITHM_FACE_RECOGNITION)

# 3. OLED 초기화
oled_width = 128
oled_height = 64
oled = ssd1306.SSD1306_I2C(oled_width, oled_height, i2c)

# 4. 네오픽셀 초기화 (14번 핀, 12개)
pin = Pin(14, Pin.OUT)
np = NeoPixel(pin, 12)

# 5. 온습도 센서 초기화 (27번 핀)
d = dht.DHT11(Pin(27))

# 6. 터치 센서 핀 초기화
touch1 = Pin(33, Pin.IN)
touch2 = Pin(32, Pin.IN)  # 예제 코드 유지 (동작X)
touch3 = Pin(35, Pin.IN)  # 예제 코드 유지 (동작X)
touch4 = Pin(34, Pin.IN)  # 예제 코드 유지 (동작X)

# 인식할 ID 설정
TARGET_IDS = [1, 2]

print("시스템을 시작합니다...")

while True:
    # --- [1] 온도 측정 ---
    try:
        d.measure()
        temp = d.temperature()
    except Exception:
        print("온습도 센서 읽기 재시도 중...")
        time.sleep(0.5)
        continue

    # --- [2] 허스키렌즈 얼굴 인식 확인 ---
    blocks = huskylens.get_blocks()
    
    face_detected = False
    detected_id = None

    for block in blocks:
        if block.ID in TARGET_IDS:
            face_detected = True
            detected_id = block.ID
            break

    # OLED 화면 청소
    oled.fill(0)

    # --- [3] 조건별 동작 제어 ---
    
    # [최우선 순위] 1번 터치 센서가 눌린 경우 (온도 상관없이 즉시 해제 동작)
    if touch1.value():
        oled.text("Status: CLEARED!", 0, 0)
        oled.text(f"Temp: {temp} C", 0, 16)
        print("clear")
        
        # 네오픽셀 초록색 (해제 완료 표시)
        for i in range(12):
            np[i] = (0, 30, 0)
        np.write()

    # [조건 1] 10도 초과 & 28도 미만 : 정상 동작
    elif 10 < temp < 28:
        oled.text("Status: Normal", 0, 0)
        oled.text(f"Temp: {temp} C", 0, 16)
        
        # 네오픽셀 은은한 흰색 (30,30,30)
        for i in range(12):
            np[i] = (30, 30, 30)
        np.write()

    # [조건 2] 10도 이하 + 얼굴 감지 필수 -> 저온 경고
    elif temp <= 10 and face_detected:
        oled.text("Status: COLD DANGER!", 0, 0)
        oled.text(f"Temp: {temp} C", 0, 16)
        
        # 네오픽셀 적당한 붉은색 (50,0,0)
        for i in range(12):
            np[i] = (50, 0, 0)
        np.write()

    # [조건 3] 28도 이상 & 33도 미만 + 얼굴 감지 필수 -> 주의
    elif 28 <= temp < 33 and face_detected:
        oled.text("Status: HEAT WARING!", 0, 0)
        oled.text(f"Temp: {temp} C", 0, 16)
        
        # 네오픽셀 주황/노란색 (50,20,0)
        for i in range(12):
            np[i] = (50, 20, 0)
        np.write()

    # [조건 4] 33도 이상 + 얼굴 감지 필수 -> 위험
    elif temp >= 33 and face_detected:
        oled.text("Status: HEAT DANGER!", 0, 0)
        oled.text(f"Temp: {temp} C", 0, 16)
        
        # 네오픽셀 붉은색 (60,0,0)
        for i in range(12):
            np[i] = (60, 0, 0)
        np.write()
        
    # [그 외 조건] 범위 밖 온도 + 얼굴 미인식 시 대기 표시
    else:
        oled.text("Status: Standby", 0, 0)
        oled.text(f"Temp: {temp} C", 0, 16)
        for i in range(12):
            np[i] = (10, 10, 10)
        np.write()

    # 허스키렌즈 인식 상태 표시
    if face_detected:
        oled.text(f"Face: ID {detected_id}", 0, 32)
    else:
        oled.text("Face: None", 0, 32)

    # OLED 화면 갱신
    oled.show()
    
    # 반복 주기 (터치를 톡 누르면 놓칠 수 있으므로 1초 동안 꾹 눌러주세요)
    time.sleep(1)