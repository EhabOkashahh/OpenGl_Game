from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import sys
import random
import time
import pygame

SOUND_ENABLED = False

HIT_SOUND_FILE = "hit.wav"
GAMEOVER_SOUND_FILE = "game_overr.wav"
EXTRALIFE_SOUND_FILE = "extra_life.wav"

try:
    pygame.mixer.init()
    HIT_SOUND = pygame.mixer.Sound(HIT_SOUND_FILE)
    GAMEOVER_SOUND = pygame.mixer.Sound(GAMEOVER_SOUND_FILE)
    EXTRALIFE_SOUND = pygame.mixer.Sound(EXTRALIFE_SOUND_FILE)
    SOUND_ENABLED = True
except pygame.error:
    pass

WIN_W, WIN_H = 800, 600
PLAYER_W, PLAYER_H = 100, 20
BLOCK_SIZE = 30

player_x = WIN_W // 2
player_y = 40
player_speed = 800.0

on_home_page = True
paused = False
blocks = []
score = 0
lives = 5
spawn_timer = 0.0
spawn_interval = 1.0
game_running = False
game_over = False
last_time = 0.0
high_score = 0
green_catch_count = 0

STAR_COUNT = 150
stars = []

def now():
    return time.time()

def draw_rect(x, y, w, h):
    glBegin(GL_QUADS)
    glVertex2f(x, y)
    glVertex2f(x + w, y)
    glVertex2f(x + w, y + h)
    glVertex2f(x, y + h)
    glEnd()

def draw_text(x, y, text):
    glRasterPos2f(x, y)
    for ch in text:
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(ch))

class Block:
    def __init__(self, x, y, size, speed):
        self.x = x
        self.y = y
        self.size = size
        self.speed = speed

    def update(self, dt):
        self.y -= self.speed * dt

    def draw(self):
        draw_rect(self.x, self.y, self.size, self.size)

class BombBlock(Block):
    def draw(self):
        glColor3f(1, 0, 0)
        draw_rect(self.x, self.y, self.size, self.size)

def reset_game():
    global blocks, score, lives, spawn_timer, game_over, game_running
    global paused, on_home_page, stars, player_x, green_catch_count

    player_x = WIN_W // 2
    blocks = []
    score = 0
    lives = 5
    spawn_timer = 0.0
    game_over = False
    paused = False
    game_running = True
    on_home_page = False
    green_catch_count = 0

    stars.clear()
    for _ in range(STAR_COUNT):
        stars.append({
            'x': random.randint(0, WIN_W),
            'y': random.randint(0, WIN_H),
            'speed': random.uniform(5, 50),
            'size': random.uniform(1, 2)
        })

def rects_overlap(x1, y1, w1, h1, x2, y2, w2, h2):
    return not (x1 + w1 < x2 or x2 + w2 < x1 or y1 + h1 < y2 or y2 + h2 < y1)

def display():
    global high_score
    glClear(GL_COLOR_BUFFER_BIT)
    glLoadIdentity()

    glColor3f(1, 1, 1)
    glBegin(GL_POINTS)
    for s in stars:
        glVertex2f(s['x'], s['y'])
    glEnd()

    if on_home_page:
        glColor3f(1, 1, 1)
        draw_text(WIN_W/2 - 120, WIN_H/2 + 10, "WELCOME TO THE GAME")
        draw_text(WIN_W/2 - 110, WIN_H/2 - 20, "Press SPACE to Start")
        draw_text(WIN_W/2 - 120, WIN_H/2 - 70, f"HIGH SCORE: {high_score}")
        glutSwapBuffers()
        return

    glColor3f(0.2, 0.7, 0.9)
    draw_rect(player_x - PLAYER_W/2, player_y, PLAYER_W, PLAYER_H)

    for b in blocks:
        if isinstance(b, BombBlock):
            glColor3f(1, 0, 0)
        else:
            glColor3f(0, 1, 0)
        b.draw()

    glColor3f(1, 1, 1)
    draw_text(10, WIN_H - 30, f"Score: {score}")
    draw_text(200, WIN_H - 30, f"Lives: {lives}")
    draw_text(WIN_W - 200, WIN_H - 30, f"High Score: {high_score}")

    glColor3f(0, 1, 0)
    draw_text(400, WIN_H - 30, f"Catch for +1 Life: {green_catch_count}/10")

    if paused:
        glColor3f(1, 1, 0)
        draw_text(WIN_W/2 - 60, WIN_H/2, "PAUSED")
        glutSwapBuffers()
        return

    if game_over:
        is_new_high = (score == high_score and score > 0)
        glColor3f(1, 0, 0)
        draw_text(WIN_W/2 - 80, WIN_H/2 + 30, "GAME OVER")
        draw_text(WIN_W/2 - 120, WIN_H/2, f"Final Score: {score}")
        if is_new_high:
            glColor3f(1, 1, 0)
            draw_text(WIN_W/2 - 160, WIN_H/2 - 30, f"NEW SESSION HIGH: {high_score}!")
        else:
            glColor3f(1, 1, 1)
            draw_text(WIN_W/2 - 160, WIN_H/2 - 30, f"Session High: {high_score}")
        draw_text(WIN_W/2 - 160, WIN_H/2 - 60, "Press SPACE to Restart")

    glutSwapBuffers()

def update(value):
    global last_time, spawn_timer, score, lives, game_over, game_running
    global high_score, green_catch_count

    t = now()
    dt = t - last_time if last_time else 1/60
    last_time = t
    old_lives = lives

    for s in stars:
        s['y'] -= s['speed'] * dt
        if s['y'] < 0:
            s['y'] = WIN_H
            s['x'] = random.randint(0, WIN_W)

    if game_running and not paused and not game_over:
        spawn_timer += dt
        difficulty = 1 + score * 0.02

        if spawn_timer >= spawn_interval / difficulty:
            spawn_timer = 0
            x = random.randint(0, WIN_W - BLOCK_SIZE)
            speed = random.uniform(120, 220) + score * 3
            if random.random() < 0.15:
                blocks.append(BombBlock(x, WIN_H, BLOCK_SIZE, speed))
            else:
                blocks.append(Block(x, WIN_H, BLOCK_SIZE, speed))

        to_remove = []
        for b in blocks:
            b.update(dt)
            px = player_x - PLAYER_W/2

            if rects_overlap(px, player_y, PLAYER_W, PLAYER_H, b.x, b.y, b.size, b.size):
                if isinstance(b, BombBlock):
                    lives -= 1
                    if SOUND_ENABLED:
                        HIT_SOUND.play()
                else:
                    score += 1
                    green_catch_count += 1
                    if green_catch_count >= 10:
                        lives += 1
                        green_catch_count = 0
                        if lives > old_lives and SOUND_ENABLED:
                            EXTRALIFE_SOUND.play()
                to_remove.append(b)
            elif b.y + b.size < 0:
                to_remove.append(b)
                if not isinstance(b, BombBlock):
                    lives -= 1
                    if SOUND_ENABLED:
                        HIT_SOUND.play()

            if lives <= 0:
                game_over = True
                game_running = False
                if score > high_score:
                    high_score = score

        for r in to_remove:
            if r in blocks:
                blocks.remove(r)

    if game_over and SOUND_ENABLED and not pygame.mixer.get_busy():
        GAMEOVER_SOUND.play()

    glutPostRedisplay()
    glutTimerFunc(16, update, 0)

def keyboard_down(key, x, y):
    global game_running, game_over, on_home_page, paused
    if key == b'\x1b':
        sys.exit()
    if key == b' ':
        if on_home_page or game_over:
            reset_game()
    if key == b'p' and game_running and not game_over:
        paused = not paused

keys_held = {'left': False, 'right': False}

def special_down(key, x, y):
    if key == GLUT_KEY_LEFT:
        keys_held['left'] = True
    elif key == GLUT_KEY_RIGHT:
        keys_held['right'] = True

def special_up(key, x, y):
    if key == GLUT_KEY_LEFT:
        keys_held['left'] = False
    elif key == GLUT_KEY_RIGHT:
        keys_held['right'] = False

def movement_timer(value):
    global player_x
    dt = 0.016
    if game_running and not paused:
        if keys_held['left']:
            player_x -= int(player_speed * dt)
        if keys_held['right']:
            player_x += int(player_speed * dt)
    half = PLAYER_W // 2
    player_x = max(half, min(WIN_W - half, player_x))
    glutTimerFunc(16, movement_timer, 0)

def reshape(w, h):
    global WIN_W, WIN_H
    WIN_W, WIN_H = w, h
    glViewport(0, 0, w, h)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    glOrtho(0, w, 0, h, -1, 1)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()

def main():
    global last_time
    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB)
    glutInitWindowSize(WIN_W, WIN_H)
    glutCreateWindow(b"Catch the Falling Blocks")
    glClearColor(0.05, 0.05, 0.2, 1)
    glutDisplayFunc(display)
    glutReshapeFunc(reshape)
    glutKeyboardFunc(keyboard_down)
    glutSpecialFunc(special_down)
    glutSpecialUpFunc(special_up)
    glutTimerFunc(16, update, 0)
    glutTimerFunc(16, movement_timer, 0)
    last_time = now()
    glutMainLoop()

if __name__ == "__main__":
    main()
