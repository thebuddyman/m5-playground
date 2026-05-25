import os, sys, io
import M5
from M5 import *
from hardware import *
import time
import random

# Screen (portrait, rotation 0): 135 W x 240 H
SCREEN_W = 135
SCREEN_H = 240

# Road
ROAD_LEFT = 15
ROAD_RIGHT = SCREEN_W - 15   # 120
ROAD_W = ROAD_RIGHT - ROAD_LEFT

# Car
CAR_W = 25
CAR_H = 30
CAR_Y = SCREEN_H - 40        # 200

# Obstacles
OBS_W = 25
OBS_H = 20

# Physics
SPEED_GAIN = 18.0            # car drift per g of tilt
MAX_VX = 7
DEADZONE = 0.08

# Difficulty levels: advance with score.
#   speed       - obstacle scroll speed (px/frame)
#   spawn       - frames between spawn events
#   double_p    - probability a spawn event drops 2 obstacles (across distinct
#                 lanes out of 3, so a lane is always free)
#   until_score - top score for this level; you graduate to the next at +1
LEVELS = [
  {"name": "EASY",   "speed": 2, "spawn": 28, "double_p": 0.0,  "until_score": 8},
  {"name": "NORMAL", "speed": 3, "spawn": 22, "double_p": 0.20, "until_score": 20},
  {"name": "HARD",   "speed": 5, "spawn": 14, "double_p": 0.55, "until_score": 36},
  {"name": "EXPERT", "speed": 7, "spawn": 10, "double_p": 0.80, "until_score": 10**9},
]

# Colors
COLOR_BG       = 0x202020    # off-road
COLOR_ROAD     = 0x404040    # asphalt
COLOR_LINE     = 0xF0E040    # dashed centerline
COLOR_CAR      = 0xE53935
COLOR_CAR_DARK = 0x6A1B1B
COLOR_OBS      = 0x29B6F6
COLOR_OBS2     = 0xFFB300
COLOR_OBS3     = 0x66BB6A
COLOR_TEXT     = 0xFFFFFF

OBS_COLORS = [COLOR_OBS, COLOR_OBS2, COLOR_OBS3]

# Game state
car_x = 0.0
obstacles = []               # list of [x, y, color]
frame = 0
next_spawn = 0
dash_offset = 0
score = 0
game_started = False
game_over = False


def reset_game():
  global car_x, obstacles, frame, next_spawn, dash_offset, score, game_over
  car_x = ROAD_LEFT + (ROAD_W - CAR_W) / 2.0
  obstacles = []
  frame = 0
  next_spawn = 30
  dash_offset = 0
  score = 0
  game_over = False
  M5.Lcd.fillScreen(COLOR_BG)


def current_level():
  for lvl in LEVELS:
    if score <= lvl["until_score"]:
      return lvl
  return LEVELS[-1]


def draw_road():
  # Off-road sides
  M5.Lcd.fillRect(0, 0, ROAD_LEFT, SCREEN_H, COLOR_BG)
  M5.Lcd.fillRect(ROAD_RIGHT, 0, SCREEN_W - ROAD_RIGHT, SCREEN_H, COLOR_BG)
  # Asphalt
  M5.Lcd.fillRect(ROAD_LEFT, 0, ROAD_W, SCREEN_H, COLOR_ROAD)
  # Dashed centerline (scrolls with dash_offset)
  cx = SCREEN_W // 2 - 2
  dash_h = 14
  gap = 12
  step = dash_h + gap
  y = (dash_offset % step) - step
  while y < SCREEN_H:
    if y + dash_h > 0:
      y0 = max(y, 0)
      y1 = min(y + dash_h, SCREEN_H)
      M5.Lcd.fillRect(cx, y0, 4, y1 - y0, COLOR_LINE)
    y += step


def draw_car():
  x = int(car_x)
  y = CAR_Y
  M5.Lcd.fillRect(x, y, CAR_W, CAR_H, COLOR_CAR)
  # Wheels
  M5.Lcd.fillRect(x - 2, y + 4, 4, 6, COLOR_CAR_DARK)
  M5.Lcd.fillRect(x + CAR_W - 2, y + 4, 4, 6, COLOR_CAR_DARK)
  M5.Lcd.fillRect(x - 2, y + CAR_H - 10, 4, 6, COLOR_CAR_DARK)
  M5.Lcd.fillRect(x + CAR_W - 2, y + CAR_H - 10, 4, 6, COLOR_CAR_DARK)
  # Windshield
  M5.Lcd.fillRect(x + 4, y + 6, CAR_W - 8, 8, COLOR_CAR_DARK)


def draw_obstacles():
  for ob in obstacles:
    M5.Lcd.fillRect(int(ob[0]), int(ob[1]), OBS_W, OBS_H, ob[2])


def draw_score():
  M5.Lcd.setTextSize(1)
  M5.Lcd.setTextColor(COLOR_TEXT, COLOR_ROAD)
  M5.Lcd.drawString(str(score), ROAD_LEFT + 3, 3)
  name = current_level()["name"]
  M5.Lcd.drawString(name, ROAD_RIGHT - M5.Lcd.textWidth(name) - 3, 3)


def spawn_obstacles(count):
  # 3 lane slots inside the road. Pick `count` distinct lanes so there's
  # always at least one free lane (count is capped at 2).
  lanes_n = 3
  lane_w = ROAD_W // lanes_n
  count = max(1, min(count, lanes_n - 1))
  pool = [0, 1, 2]
  picks = []
  for _ in range(count):
    i = random.randint(0, len(pool) - 1)
    picks.append(pool.pop(i))
  for lane in picks:
    x = ROAD_LEFT + lane * lane_w + (lane_w - OBS_W) // 2
    color = OBS_COLORS[random.randint(0, len(OBS_COLORS) - 1)]
    obstacles.append([x, -OBS_H, color])


def collides(ax, ay, aw, ah, bx, by, bw, bh):
  return (ax < bx + bw and ax + aw > bx and
          ay < by + bh and ay + ah > by)


def show_title():
  M5.Lcd.fillScreen(COLOR_BG)
  M5.Lcd.setTextColor(COLOR_TEXT, COLOR_BG)
  M5.Lcd.setTextSize(2)
  M5.Lcd.drawString("TILT", 45, 40)
  M5.Lcd.drawString("DODGE", 35, 65)
  M5.Lcd.setTextSize(1)
  M5.Lcd.drawString("Tilt to steer", 25, 110)
  M5.Lcd.drawString("Avoid traffic", 25, 125)
  M5.Lcd.drawString("Press A to start", 12, 170)


def show_game_over():
  # Brief flash of the car.
  for _ in range(3):
    M5.Lcd.fillRect(int(car_x), CAR_Y, CAR_W, CAR_H, COLOR_ROAD)
    time.sleep(0.12)
    M5.Lcd.fillRect(int(car_x), CAR_Y, CAR_W, CAR_H, COLOR_CAR)
    time.sleep(0.12)

  M5.Lcd.fillScreen(COLOR_BG)
  M5.Lcd.setTextColor(COLOR_TEXT, COLOR_BG)

  M5.Lcd.setTextSize(2)
  go = "GAME OVER"
  M5.Lcd.drawString(go, (SCREEN_W - M5.Lcd.textWidth(go)) // 2, 30)

  M5.Lcd.setTextSize(5)
  s = str(score)
  M5.Lcd.drawString(s, (SCREEN_W - M5.Lcd.textWidth(s)) // 2, 75)

  M5.Lcd.setTextSize(1)
  lvl_str = "Level: " + current_level()["name"]
  M5.Lcd.drawString(lvl_str, (SCREEN_W - M5.Lcd.textWidth(lvl_str)) // 2, 140)

  prompt = "Press A to play again"
  M5.Lcd.drawString(prompt, (SCREEN_W - M5.Lcd.textWidth(prompt)) // 2, 170)


def setup():
  M5.begin()
  M5.Lcd.setRotation(0)
  reset_game()
  show_title()


def loop():
  global car_x, frame, next_spawn, dash_offset, score, game_started, game_over

  M5.update()

  if not game_started:
    if BtnA.wasPressed():
      game_started = True
      reset_game()
    return

  if game_over:
    if BtnA.wasPressed():
      reset_game()
      show_title()
      game_started = False
    return

  # --- Read tilt --- (negate so tilt-left moves car left)
  accel = M5.Imu.getAccel()
  ax = -accel[0]
  if abs(ax) < DEADZONE:
    ax = 0.0

  vx = ax * SPEED_GAIN
  if vx > MAX_VX:
    vx = MAX_VX
  elif vx < -MAX_VX:
    vx = -MAX_VX

  car_x += vx
  if car_x < ROAD_LEFT:
    car_x = ROAD_LEFT
  elif car_x > ROAD_RIGHT - CAR_W:
    car_x = ROAD_RIGHT - CAR_W

  lvl = current_level()

  # --- Spawn ---
  if frame >= next_spawn:
    count = 2 if random.randint(0, 99) < int(lvl["double_p"] * 100) else 1
    spawn_obstacles(count)
    next_spawn = frame + lvl["spawn"]

  # --- Move obstacles ---
  speed = lvl["speed"]
  alive = []
  for ob in obstacles:
    ob[1] += speed
    if ob[1] >= SCREEN_H:
      score += 1
    else:
      alive.append(ob)
  obstacles[:] = alive

  # --- Collision ---
  cx = int(car_x)
  for ob in obstacles:
    if collides(cx, CAR_Y, CAR_W, CAR_H, int(ob[0]), int(ob[1]), OBS_W, OBS_H):
      game_over = True
      show_game_over()
      return

  # --- Render ---
  dash_offset += speed
  draw_road()
  draw_obstacles()
  draw_car()
  draw_score()

  frame += 1


if __name__ == '__main__':
  try:
    setup()
    while True:
      loop()
      time.sleep(0.05)
  except (Exception, KeyboardInterrupt) as e:
    try:
      from utility import print_error_msg
      print_error_msg(e)
    except ImportError:
      print("please update to latest firmware")
