import mysql.connector
import speech_recognition as sr
from gtts import gTTS
import pygame
import os
import time

# เชื่อมต่อกับฐานข้อมูล MySQL
db = mysql.connector.connect(
    host="mqtt.app-thailand.com",
    user="coe",  # เปลี่ยนเป็น username ของคุณ
    password="coe",  # เปลี่ยนเป็น password ของคุณ
    database="gtts"
)

cursor = db.cursor()
 
# สร้าง Recognizer และ Microphone objects
recog = sr.Recognizer()
mic = sr.Microphone()

# เริ่มต้น pygame mixer
pygame.mixer.init()

# ฟังก์ชันสำหรับพูดข้อความ
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

# ฟังก์ชันสำหรับเล่นไฟล์เสียงที่กำหนด
def play_sound(filename):
    try:
        pygame.mixer.music.load(filename)
        pygame.mixer.music.play()
        
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)
        
        pygame.mixer.music.stop()
    except Exception as e:
        print(f"เกิดข้อผิดพลาดในการเล่นไฟล์เสียง: {e}")

# ฟังก์ชันดึงข้อมูลจากฐานข้อมูล
def fetch_responses(text):
    # ดึงข้อความตอบกลับ
    cursor.execute("SELECT response_text FROM text_responses WHERE keywords LIKE %s", (f"%{text}%",))
    response = cursor.fetchone()
    if response:
        return response[0]
    
    # ดึงไฟล์เสียง
    cursor.execute("SELECT sound_file FROM sound_responses WHERE keywords LIKE %s", (f"%{text}%",))
    sound_file = cursor.fetchone()
    if sound_file:
        return sound_file[0]
    
    return None

# คำสั่งเสียงสำหรับหยุดโปรแกรม
stop_commands = ("หยุด", "จบ", "เลิก", "พอ", "ออกจากโปรแกรม")

try:
    with mic as source:
        print("กำลังฟัง...")
        while True:
            audio = recog.listen(source)
            try:
                text = recog.recognize_google(audio, language='th')
                print(text)
                
                # ตรวจสอบว่ามีคำสั่งหยุดโปรแกรมหรือไม่
                if any(command in text for command in stop_commands):
                    msg = "โปรแกรมกำลังจะหยุดทำงาน"
                    print(msg)
                    speak(msg)
                    break  # ใช้ break เพื่อออกจาก loop และหยุดโปรแกรม
                
                # ดึงข้อมูลจากฐานข้อมูล
                result = fetch_responses(text)
                
                if result:
                    # ถ้าเป็นข้อความให้พูด
                    if result.endswith(".mp3"):
                        play_sound(result)  # เล่นไฟล์เสียง
                    else:
                        speak(result)  # พูดข้อความ
                else:
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
