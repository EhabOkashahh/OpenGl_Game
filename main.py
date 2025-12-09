from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import sys
import random
import time

# Window settings
WIN_W, WIN_H = 800, 600
PLAYER_W, PLAYER_H = 100, 20
BLOCK_SIZE = 30

# Game state
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

def now():
    return time.time()

# Draw rectangle
def draw_rect(x, y, w, h):
    glBegin(GL_QUADS)
    glVertex2f(x, y)
    glVertex2f(x + w, y)
    glVertex2f(x + w, y + h)
    glVertex2f(x, y + h)
    glEnd()

# Bitmap text
def draw_text(x, y, text):
    glRasterPos2f(x, y)
    for ch in text:
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(ch))

# Block classes
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
        glColor3f(0, 1, 0)
        draw_rect(self.x, self.y, self.size, self.size)

# Reset game
def reset_game():
    global blocks, score, lives, spawn_timer, game_over, game_running, paused, on_home_page
    blocks = []
    score = 0
    lives = 5
    spawn_timer = 0.0
    game_over = False
    paused = False
    game_running = True
    on_home_page = False

# Collision check
def rects_overlap(x1, y1, w1, h1, x2, y2, w2, h2):
    return not (x1+w1 < x2 or x2+w2 < x1 or y1+h1 < y2 or y2+h2 < y1)

# Display
def display():
    global on_home_page, paused, score, lives, blocks, player_x, game_running, game_over
    glClear(GL_COLOR_BUFFER_BIT)
    glLoadIdentity()

    # Home page
    if on_home_page:
        glColor3f(1, 1, 1)
        draw_text(WIN_W/2 - 120, WIN_H/2 + 10, "WELCOME TO THE GAME")
        draw_text(WIN_W/2 - 110, WIN_H/2 - 20, "Press SPACE to Start")
        glutSwapBuffers()
        return

    # Player
    glColor3f(0.2, 0.7, 0.9)
    draw_rect(player_x - PLAYER_W/2, player_y, PLAYER_W, PLAYER_H)

    # Draw blocks
    for b in blocks:
        if isinstance(b, BombBlock):
            glColor3f(0, 1, 0)
        else:
            glColor3f(0.9, 0.3, 0.3)
        b.draw()

    # UI (fixed indentation)
    glColor3f(1, 1, 1)
    draw_text(10, WIN_H - 30, f"Score: {score}")
    draw_text(200, WIN_H - 30, f"Lives: {lives}")

    # Pause screen
    if paused:
        glColor3f(1, 1, 0)
        draw_text(WIN_W/2 - 60, WIN_H/2, "PAUSED")
        draw_text(WIN_W/2 - 120, WIN_H/2 - 30, "Press P to Resume")

    # Game over screen
    if game_over:
        glColor3f(1, 0, 0)
        draw_text(WIN_W/2 - 80, WIN_H/2 + 30, "GAME OVER")
        draw_text(WIN_W/2 - 120, WIN_H/2 + 0, f"Final Score: {score}")
        draw_text(WIN_W/2 - 160, WIN_H/2 - 30, "Press SPACE to Restart")

    glutSwapBuffers()

# Timer/update
def update(value):
    global last_time, spawn_timer, score, lives, game_over, game_running

    t = now()
    dt = t - last_time if last_time != 0 else 1/60.0
    last_time = t

    if game_running and not game_over and not paused:
        # Spawn blocks
        spawn_timer += dt
        difficulty = 1.0 + score * 0.02
        if spawn_timer >= spawn_interval / difficulty:
            spawn_timer = 0.0
            x = random.randint(0, WIN_W - BLOCK_SIZE)
            speed = random.uniform(120, 220) + score * 3

            # 15% of blocks are bombs
            if random.random() < 0.15:
                blocks.append(BombBlock(x, WIN_H, BLOCK_SIZE, speed))
            else:
                blocks.append(Block(x, WIN_H, BLOCK_SIZE, speed))

        # Update blocks
        to_remove = []
        for b in blocks:
            b.update(dt)
            px = player_x - PLAYER_W/2
            py = player_y

            if rects_overlap(px, py, PLAYER_W, PLAYER_H, b.x, b.y, b.size, b.size):
                if isinstance(b, BombBlock):
                    lives -= 1
                else:
                    score += 1
                to_remove.append(b)

            elif b.y + b.size < 0:
                to_remove.append(b)
                if not isinstance(b, BombBlock):
                    lives -= 1
                if lives <= 0:
                    game_over = True
                    game_running = False

        for r in to_remove:
            if r in blocks:
                blocks.remove(r)

    glutPostRedisplay()
    glutTimerFunc(16, update, 0)

# Keyboard
def keyboard_down(key, x, y):
    global game_running, game_over, on_home_page, paused
    if key == b'\x1b':
        sys.exit(0)

    if key == b' ':
        if on_home_page:
            reset_game()
        elif game_over:
            reset_game()

    if key == b'p':
        if game_running and not game_over:
            paused = not paused

# Movement keys
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
    if not paused and game_running:
        if keys_held['left']:
            player_x -= int(player_speed * dt)
        if keys_held['right']:
            player_x += int(player_speed * dt)

    half = PLAYER_W // 2
    if player_x - half < 0:
        player_x = half
    if player_x + half > WIN_W:
        player_x = WIN_W - half

    glutTimerFunc(16, movement_timer, 0)

# Window reshape
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
    glClearColor(0.1, 0.1, 0.1, 1.0)

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
