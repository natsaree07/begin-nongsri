import speech_recognition as sr
from gtts import gTTS
import pygame
import os
import time

# สร้าง Recognizer และ Microphone objects
recog = sr.Recognizer()
mic = sr.Microphone()

# เริ่มต้น pygame mixer
pygame.mixer.init()

def speak(text):
    try:
        filename = f"speech_{int(time.time())}.mp3"
        tts = gTTS(text=text, lang='th')
        tts.save(filename)
        pygame.mixer.music.load(filename)
        pygame.mixer.music.play()
        
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)
        
        pygame.mixer.music.stop()
        time.sleep(1)
        os.remove(filename)
    except Exception as e:
        print(f"เกิดข้อผิดพลาดในการพูด: {e}")

# กำหนดข้อความที่ต้องการให้โปรแกรมตอบ
responses = {
    ("ดี", "ไง","ช่วย"): "สวัสดีจ้า มีอะไรให้ช่วยไหม",
    ("ง่วง",):"ง่วงสุดๆ เพราะยังไม่ได้นอนที ทำงานหนักเกิน",
    ("พัก",):"ขอบคุณนะ คุณก็เช่นกัน ",
    ("ชื่อ", "ใคร"): "ฉันชื่อน้องศรี พูดไทยไม่ค่อยชัด",
    ("ข้าว", "เมนู"): "ฉันกินแล้ว อิ่มอย่างแรงนิ เมนูวันนี้คือแกงส้มปลาหมอคังดำ",
    # เพิ่มข้อความอื่นๆ ที่คุณต้องการให้ตอบกลับที่นี่
}

try:
    with mic as source:
        print("กำลังฟัง...")
        while True:
            audio = recog.listen(source)
            try:
                text = recog.recognize_google(audio, language='th')
                print(text)
                
                # ตรวจสอบว่าคำใดใน responses ปรากฏในข้อความที่จดจำได้หรือไม่
                response_found = False
                for keys, response in responses.items():
                    if any(key in text for key in keys):
                        speak(response)  # พูดข้อความที่ตั้งไว้
                        response_found = True
                        break
                
                if not response_found:
                    msg = "ไม่พบข้อความที่ต้องการสอบถาม โปรดแจ้งท่านเปา"
                    print(msg)
                    speak(msg)
                    
            except sr.UnknownValueError:
                msg = "กรุณาพูดอีกครั้ง"
                print(msg)
                speak(msg)
            except sr.RequestError:
                msg = "ไม่สามารถเชื่อมต่อกับบริการ Google Speech Recognition"
                print(msg)
                speak(msg)
except KeyboardInterrupt:
    msg = "โปรแกรมหยุดทำงาน"
    print(msg)
    speak(msg)