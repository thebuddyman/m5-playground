import os, sys, io
import M5
from M5 import *
import requests 
import network

label_status = None

def autowrap_pixels(text, max_width=120):
    words = text.split()
    lines = []
    current_line = ""
    
    for word in words:
        test_line = word if not current_line else current_line + " " + word
        if M5.Lcd.textWidth(test_line) <= max_width:
            current_line = test_line
        else:
            if current_line:
                lines.append(current_line)
            current_line = word
            
    if current_line:
        lines.append(current_line)
    return lines

def btnA_wasClicked_event(state):
    global label_status
    M5.Lcd.fillRect(0, 0, 135, 200, 0x000000) 
    label_status.setText("Fetching...")
    M5.Lcd.setFont(Widgets.FONTS.DejaVu9)
    
    try:
        response = requests.get('https://official-joke-api.appspot.com/random_joke', timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            line_height = 14  
            margin_left = 8   
            current_y = 30    
            
            M5.Lcd.setTextColor(0x00d814)
            setup_text = data.get('setup', '')
            setup_lines = autowrap_pixels(setup_text, 120) 
            
            for line in setup_lines:
                M5.Lcd.setCursor(margin_left, current_y)
                M5.Lcd.print(line)
                current_y += line_height
            
            current_y += 15
            M5.Lcd.setTextColor(0xebff00)
            punch_text = data.get('punchline', '')
            punch_lines = autowrap_pixels(punch_text, 120)
            
            for line in punch_lines:
                M5.Lcd.setCursor(margin_left, current_y)
                M5.Lcd.print(line)
                current_y += line_height
            
            label_status.setText("Gimme more")
        else:
            label_status.setText("API Error")
            
    except Exception as e:
        label_status.setText("Conn Error")

def setup():
    global label_status

    M5.begin()
    Widgets.setRotation(0)
    Widgets.fillScreen(0x000000)
    
    label_status = Widgets.Label("Gimme a pun", 10, 210, 1.0, 0xffffff, 0x000000, Widgets.FONTS.DejaVu9)

    BtnA.setCallback(type=BtnA.CB_TYPE.WAS_CLICKED, cb=btnA_wasClicked_event)

def loop():
    M5.update()

if __name__ == '__main__':
    try:
        setup()
        while True:
            loop()
    except (Exception, KeyboardInterrupt) as e:
        pass