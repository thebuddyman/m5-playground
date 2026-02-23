import os, sys, io
import M5
from M5 import *
import time
import random

try:
    import fonts 
except ImportError:
    pass

# --- GLOBAL VARIABLES & SETTINGS ---
COLORS_SAND = [0xFFFFAA, 0xFFFFD2, 0xFDF69B] 
COLOR_BG = 0x000000    

W = 33
H = 60
MAX_SAND = 1980 
OFFSET_X = 16
OFFSET_Y = 0

# 0 = Empty, 10-12 = Real Sand, 20-22 = Ghost Sand
grid = bytearray([0] * (W * H))
old_grid = bytearray([255] * (W * H))

current_state = "MENU"   
menu_selection = 25      
TOTAL_SECONDS = 1500     

remaining_ms = 0
last_tick_time = 0
spawned_sand = 0
is_upside_down = False
has_beeped = False
last_time_str = ""

# --- HELPER FUNCTIONS ---
def update_physics():
    for y in range(H - 2, -1, -1):
        left_to_right = random.getrandbits(1)
        x_range = range(W) if left_to_right else range(W - 1, -1, -1)
        
        for x in x_range:
            i = y * W + x
            grain_type = grid[i]
            
            # If the pixel is sand (Real or Ghost)
            if grain_type >= 10:
                below = i + W
                if grid[below] == 0:
                    grid[below] = grain_type
                    grid[i] = 0
                else:
                    below_left = below - 1
                    below_right = below + 1
                    can_left = (x > 0) and (grid[below_left] == 0)
                    can_right = (x < W - 1) and (grid[below_right] == 0)
                    
                    if can_left and can_right:
                        if random.getrandbits(1):
                            grid[below_left] = grain_type; grid[i] = 0
                        else:
                            grid[below_right] = grain_type; grid[i] = 0
                    elif can_left:
                        grid[below_left] = grain_type; grid[i] = 0
                    elif can_right:
                        grid[below_right] = grain_type; grid[i] = 0
                    else:
                        slide_left = (x > 0) and (grid[i - 1] == 0)
                        slide_right = (x < W - 1) and (grid[i + 1] == 0)
                        
                        if slide_left and slide_right:
                            if random.getrandbits(1):
                                grid[i - 1] = grain_type; grid[i] = 0
                            else:
                                grid[i + 1] = grain_type; grid[i] = 0
                        elif slide_left:
                            grid[i - 1] = grain_type; grid[i] = 0
                        elif slide_right:
                            grid[i + 1] = grain_type; grid[i] = 0
                        else:
                            # Evaporate Ghost Sand (20, 21, 22) when it gets stuck
                            if grain_type >= 20:
                                grid[i] = 0 

def draw_grid():
    for i in range(W * H):
        if grid[i] != old_grid[i]:
            old_grid[i] = grid[i]
            
            val = grid[i]
            if val >= 10:
                # Modulo 10 turns 10/20 into 0, 11/21 into 1, 12/22 into 2
                color_index = val % 10 
                color = COLORS_SAND[color_index]
            else:
                color = COLOR_BG
            
            x = i % W
            y = i // W
            Display.fillRect(1 + x * 4, y * 4, 4, 4, color)

def draw_menu():
    Widgets.setRotation(0) 
    Widgets.fillScreen(0x000000)
    
    try:
        Display.setFont(fonts.DejaVu9) 
    except:
        Display.setTextSize(1)

    Display.setTextColor(0xFFFFFF)
    Display.drawString("Select Duration:", 10, 20)
    
    if menu_selection == 25:
        Display.setTextColor(COLORS_SAND[0])
        Display.drawString("25 Mins <", 10, 50)
        Display.setTextColor(0x888888)
        Display.drawString("50 Mins", 10, 70)
    else:
        Display.setTextColor(0x888888)
        Display.drawString("25 Mins", 10, 50)
        Display.setTextColor(COLORS_SAND[0])
        Display.drawString("50 Mins <", 10, 70)
        
    #Display.setTextColor(0xFFFFFF)
    #Display.drawString("BtnB (Side): Select", 5, 180)
    #Display.drawString("BtnA (Front): Start", 5, 210)

def start_timer():
    global TOTAL_SECONDS, remaining_ms, last_tick_time
    global spawned_sand, has_beeped, is_upside_down
    
    TOTAL_SECONDS = menu_selection * 60
    remaining_ms = TOTAL_SECONDS * 1000 
    
    for i in range(W * H): 
        grid[i] = 0
        old_grid[i] = 255
        
    Widgets.fillScreen(0x000000)
    spawned_sand = 0
    has_beeped = False
    
    accel = Imu.getAccel()
    is_upside_down = accel[1] < -0.5
    if is_upside_down:
        Widgets.setRotation(2)
    else:
        Widgets.setRotation(0)
        
    last_tick_time = time.ticks_ms()


# --- MAIN UIFLOW STRUCTURE ---
def setup():
    M5.begin()
    Speaker.setVolume(128)
    draw_menu() 

def loop():
    global current_state, menu_selection, is_upside_down, has_beeped
    global remaining_ms, last_tick_time, spawned_sand, last_time_str
    
    M5.update() 
    
    # ==========================================
    # MENU STATE
    # ==========================================
    if current_state == "MENU":
        if M5.BtnB.wasPressed():
            if menu_selection == 25:
                menu_selection = 50
            else:
                menu_selection = 25
            draw_menu() 
            
        if M5.BtnA.wasPressed():
            start_timer()
            current_state = "TIMER" 
            
    # ==========================================
    # TIMER STATE
    # ==========================================
    elif current_state == "TIMER":
        
        # Press B to cancel
        if M5.BtnB.wasPressed():
            current_state = "MENU"
            draw_menu()
            return 
            
        accel = Imu.getAccel()
        acc_y = accel[1]
        
        is_vertical = abs(acc_y) > 0.6
        currently_upside_down = acc_y < -0.5
        
        # DEVICE FLIPPING
        if currently_upside_down != is_upside_down and is_vertical:
            is_upside_down = currently_upside_down
            
            for i in range(W * H): 
                grid[i] = 0
                old_grid[i] = 255
                
            Widgets.fillScreen(0x000000)
            spawned_sand = 0
            has_beeped = False
            last_time_str = ""
            last_tick_time = time.ticks_ms()

            remaining_ms = TOTAL_SECONDS * 1000
            
            if is_upside_down:
                Widgets.setRotation(2)
            else:
                Widgets.setRotation(0)
                
        # HARDWARE CLOCK MATH
        current_time = time.ticks_ms()
        
        if is_vertical:
            delta = time.ticks_diff(current_time, last_tick_time)
            last_tick_time = current_time
            remaining_ms -= delta
            if remaining_ms < 0:
                remaining_ms = 0
                
            progress_ratio = 1.0 - (remaining_ms / (TOTAL_SECONDS * 1000.0))
            target_sand = int(progress_ratio * MAX_SAND)
            
            spawned_this_frame = False
            
            # Spawn Real Sand (IDs 10, 11, or 12)
            if spawned_sand < target_sand and grid[OFFSET_Y * W + OFFSET_X] == 0:
                grid[OFFSET_Y * W + OFFSET_X] = 10 + random.randint(0, 2)
                spawned_sand += 1
                spawned_this_frame = True
                
            # Spawn Ghost Sand (IDs 20, 21, or 22)
            if not spawned_this_frame and remaining_ms > 0:
                if grid[OFFSET_Y * W + OFFSET_X] == 0:
                    grid[OFFSET_Y * W + OFFSET_X] = 20 + random.randint(0, 2)
                    
            update_physics()
        else:
            # Paused! 
            last_tick_time = current_time
            
            
        # CHAMELEON TEXT TIMER
        seconds_left = (remaining_ms + 999) // 1000
        mins = seconds_left // 60
        secs = seconds_left % 60
        time_str = "{:02d}:{:02d}".format(mins, secs)
        
        if time_str != last_time_str:
            last_time_str = time_str
            # Clear middle rows so large text doesn't overlap
            for i in range(25 * W, 35 * W):
                old_grid[i] = 255 
                
        draw_grid()
        
        if seconds_left <= 180:
            # If any sand (ID 10 or higher) is behind the text, turn text Black
            if grid[30 * W + 16] >= 10:
                Display.setTextColor(COLOR_BG)
            else:
                # Otherwise, text is Gold
                Display.setTextColor(COLORS_SAND[0])
            
            try:
                Display.setFont(fonts.DejaVu18)
            except:
                Display.setTextSize(2)
                
            Display.drawString(time_str, 35, 110)
            Display.setTextSize(1) # Reset for menu!
        
        # END ALARM
        if remaining_ms <= 0:
            if not has_beeped:
                Speaker.tone(4000, 500)
                has_beeped = True
        else:
            has_beeped = False
            
    time.sleep_ms(10)

if __name__ == '__main__':
    try:
        setup()
        while True:
            loop()
    except (Exception, KeyboardInterrupt) as e:
        try:
            from utility import print_error_msg
            print_error_msg(e)
        except ImportError:
            pass