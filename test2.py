import speech_recognition as sr
from gtts import gTTS
import pygame
import os
import time
import paho.mqtt.client as mqtt

# การตั้งค่า MQTT
MQTT_BROKER = "mqtt.app-thailand.com"
MQTT_PORT = 1883
MQTT_TOPIC = "gtts/spin"

# สร้าง Recognizer และ Microphone objects
recog = sr.Recognizer()
mic = sr.Microphone()

# เริ่มต้น pygame mixer
pygame.mixer.init()

# ตั้งค่า MQTT client
mqtt_client = mqtt.Client()

def on_connect(client, userdata, flags, rc):
    print(f"เชื่อมต่อกับ MQTT Broker สำเร็จ รหัสผลลัพธ์: {rc}")

mqtt_client.on_connect = on_connect
mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
mqtt_client.loop_start()  # เริ่ม loop MQTT client ใน background

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

# กำหนดข้อความที่ต้องการให้โปรแกรมตอบหรือเล่นไฟล์เสียง
responses = {
    ("ดี", "ไง",): "สวัสดีค่ะ มีอะไรให้ช่วยไหมคะ",
    ("ขอบ","คุณ"): "มีอะไรปรึกษาได้นะ ถ้าก๊ะเขาแกล้งอีก เดี๋ยวไปจัดการให้ ",
    ("รอน","ron"): "อัซรอน วันสุไลมาน",
}

# เพิ่มการตอบกลับด้วยไฟล์เสียง
sound_responses = {
    ("day", "one"): "PUN - DAY ONE.mp3",
    ("หัว", "กระ"): "กระดาษ.mp3",
    ("รวม",): "รวมเพลง 90.mp3",
    ("ปฐมนิเทศ", "วันไหน"): "patom.mp3",
    ("อนาชีด","อิสลาม"): "อัดฮัม.mp3",
    ("ถึง","เวลา"): "อาซาน.mp3",
    ("บรรยาย","ศาสนา"): "บรรยาย.mp3",
}

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
                
                # ตรวจสอบว่าคำใดใน responses ปรากฏในข้อความที่จดจำได้หรือไม่
                response_found = False
                for keys, response in responses.items():
                    if any(key in text for key in keys):
                        speak(response)  # พูดข้อความที่ตั้งไว้
                        response_found = True
                        # ส่งข้อความคีย์เวิร์ดที่ตรวจพบผ่าน MQTT
                        mqtt_client.publish(MQTT_TOPIC, f"พบคีย์เวิร์ด: {keys}")
                        break
                
                # ตรวจสอบว่าคำใดใน sound_responses ปรากฏในข้อความที่จดจำได้หรือไม่
                for keys, sound_file in sound_responses.items():
                    if any(key in text for key in keys):
                        play_sound(sound_file)  # เล่นไฟล์เสียงที่ตั้งไว้
                        response_found = True
                        # ส่งข้อความคีย์เวิร์ดที่ตรวจพบผ่าน MQTT
                        mqtt_client.publish(MQTT_TOPIC, f"พบคีย์เวิร์ดเสียง: {keys}")
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
