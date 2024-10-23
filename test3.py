import requests
import speech_recognition as sr
from gtts import gTTS
import pygame
import os
import time
import paho.mqtt.client as mqtt

# การตั้งค่า MQTT
MQTT_BROKER = "mqtt.app-thailand.com"
MQTT_PORT = 1883
MQTT_TOPIC_REQUEST = "gtts/spin"

# Node-RED API URL
NODE_RED_API_URL = "http://127.0.0.1:1880/restData" # เปลี่ยน URL ตามการตั้งค่าของคุณ

# สร้าง Recognizer และ Microphone objects
recog = sr.Recognizer()
mic = sr.Microphone()

# เริ่มต้น pygame mixer
pygame.mixer.init()

# ตั้งค่า MQTT client
mqtt_client = mqtt.Client()

def on_connect(client, userdata, flags, rc):
    print(f"เชื่อมต่อกับ MQTT Broker สำเร็จ รหัสผลลัพธ์: {rc}")
# ฟังก์ชันสำหรับพูดข้อความ
def speak(text):
    if text:  # ตรวจสอบว่าข้อความไม่ว่าง
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

# ฟังก์ชันดึงผลลัพธ์จาก Node-RED API
def fetch_node_red_result():
    try:
        response = requests.get(NODE_RED_API_URL)
        if response.status_code == 200:
            return response.json().get("result", "")
        else:
            return "ไม่สามารถดึงข้อมูลจาก Node-RED ได้"
    except Exception as e:
        print(f"เกิดข้อผิดพลาดในการดึง API: {e}")
        return "เกิดข้อผิดพลาดในการดึงข้อมูล"

mqtt_client.on_connect = on_connect
mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
mqtt_client.loop_start()  # เริ่ม loop MQTT client ใน background

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

                # ส่งข้อความคีย์เวิร์ดที่ตรวจพบไปยัง Node-RED ผ่าน MQTT
                mqtt_client.publish(MQTT_TOPIC_REQUEST, text)
                
                # ดึงผลลัพธ์จาก Node-RED ผ่าน REST API
                result = fetch_node_red_result()
                print(f"ผลลัพธ์จาก Node-RED: {result}")
                speak(result)
                
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
