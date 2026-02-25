import os, sys, io
import M5
from M5 import *
from hardware import *
import time
import random

BLOCK_SIZE = 10
GRID_W = 24
GRID_H = 13

COLOR_SNAKE = 0x000000
COLOR_BG = 0xC5E713
COLOR_APPLE = 0xFF0000
COLOR_TEXT = 0x000000

snake = []
dx = 1
dy = 0
apple = (0,0)
score = 0
game_over = False
game_started = False
can_turn = True

def spawn_apple():
  global apple
  while True:
    fx = random.randint(0, GRID_W -1)
    fy = random.randint(0, GRID_H-1)
    if (fx,fy) not in snake:
        apple = (fx,fy)
        break

def reset_game():
  global snake, dx, dy, score, game_over
  snake = [(5, 5), (4, 5), (3, 5)]
  dx = 1
  dy = 0
  score = 0
  game_over = False
    
  M5.Lcd.fillScreen(COLOR_BG)
  M5.Lcd.setTextColor(COLOR_TEXT, COLOR_BG)
  
  spawn_apple()
    
  # Draw the starting snake
  for segment in snake:
    seg_x = segment[0] * BLOCK_SIZE
    seg_y = segment[1] * BLOCK_SIZE
    M5.Lcd.fillRect(seg_x, seg_y, BLOCK_SIZE, BLOCK_SIZE, COLOR_SNAKE)

  # Draw the starting apple
  x_pixel = apple[0] * BLOCK_SIZE
  y_pixel = apple[1] * BLOCK_SIZE
  M5.Lcd.fillRect(x_pixel, y_pixel, BLOCK_SIZE, BLOCK_SIZE, COLOR_APPLE)

# FIX 1: Cleaned up setup!
def setup():
  M5.begin()
  M5.Lcd.setRotation(3)
  reset_game()
  M5.Lcd.setTextSize(1)
  M5.Lcd.setTextColor(COLOR_TEXT, COLOR_BG)
  M5.Lcd.drawString("Press A to start", 70, 110)

def loop():
  global dx, dy, score, game_over, game_started, can_turn

  M5.update()

  if not game_started:
    if BtnA.wasPressed():
      M5.Lcd.fillRect(0, 105, 240, 30, COLOR_BG)
      game_started = True
    else:
      return

  if game_over:
    if BtnA.wasPressed():
      reset_game()
    return

  accel = M5.Imu.getAccel()
  ay = accel[1] # This is the Y-axis

  # CONTROLS
  if can_turn:
    # SNAP RIGHT: Right hand down (Positive ay)
    if BtnB.wasPressed() or ay > 0.8: 
      dx, dy = -dy, dx   # Turn Left math
      can_turn = False
      
    # SNAP LEFT: Left hand down (Negative ay)
    elif BtnA.wasPressed() or ay < -0.8:
      dx, dy = dy, -dx   # Turn Right math
      can_turn = False

  head_x, head_y = snake[0]
  new_head = (head_x + dx, head_y + dy)

  # COLLISION
  if (new_head[0] < 0 or new_head[0] >= GRID_W or
    new_head[1] < 0 or new_head[1] >= GRID_H or
    new_head in snake):

    for _ in range(3):
      for segment in snake:
        M5.Lcd.fillRect(segment[0] * BLOCK_SIZE, segment[1] * BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE, COLOR_BG)
      time.sleep(0.15)

      for segment in snake:
        M5.Lcd.fillRect(segment[0] * BLOCK_SIZE, segment[1] * BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE, COLOR_SNAKE)
      time.sleep(0.15)
    
    # FIX 2: Better Text Layout!
    M5.Lcd.fillScreen(COLOR_BG)
    M5.Lcd.setTextColor(COLOR_TEXT, COLOR_BG)

    M5.Lcd.setTextSize(2)
    M5.Lcd.drawString("GAME OVER", 60, 15)

    M5.Lcd.setTextSize(6)
    score_str = str(score)
    text_width = M5.Lcd.textWidth(score_str)
    center_x = 130 - (text_width // 2)
    M5.Lcd.drawString(score_str, center_x, 43)

    M5.Lcd.setTextSize(1)
    M5.Lcd.drawString("Press A to play again", 64, 110)

    game_over = True
    return

  snake.insert(0, new_head)
  can_turn = True

  if new_head == apple:
    score += 1
    spawn_apple()
  else:
    old_tail_x = snake[-1][0] * BLOCK_SIZE
    old_tail_y = snake[-1][1] * BLOCK_SIZE
    M5.Lcd.fillRect(old_tail_x, old_tail_y, BLOCK_SIZE, BLOCK_SIZE, COLOR_BG)  
    snake.pop()

  new_hx = new_head[0] * BLOCK_SIZE
  new_hy = new_head[1] * BLOCK_SIZE
  M5.Lcd.fillRect(new_hx, new_hy, BLOCK_SIZE, BLOCK_SIZE, COLOR_SNAKE)

  # Draw the apple
  x_pixel = apple[0] * BLOCK_SIZE
  y_pixel = apple[1] * BLOCK_SIZE
  M5.Lcd.fillRect(x_pixel, y_pixel, BLOCK_SIZE, BLOCK_SIZE, COLOR_APPLE)

  # NEW: Draw the score on the top left
  M5.Lcd.setTextSize(1)
  M5.Lcd.setTextColor(COLOR_TEXT, COLOR_BG)
  M5.Lcd.drawString(f"{score}", 2, 2)

if __name__ == '__main__':
  try:
    setup()
    while True:
      loop()
      time.sleep(0.1)
  except (Exception, KeyboardInterrupt) as e:
    try:
      from utility import print_error_msg
      print_error_msg(e)
    except ImportError:
      print("please update to latest firmware")