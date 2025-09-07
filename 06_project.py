from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
import time, random, math

# Window
WIN_W, WIN_H = 1000, 800
ASPECT = WIN_W / float(WIN_H)
FOV_Y = 70.0
FPS = 60
FRAME_MS = int(1000 / FPS)

# Camera
first_person = False
cam_height_third = 140.0
cam_back_third   = 260.0
cam_yaw = 0.0
cam_pitch = 0.0

# Pause
paused = False

# Lanes
LANE_W = 120.0
LANE_X = (-LANE_W, 0.0, LANE_W)
PLAYER_LANE = 1
PLAYER_Y = 0.0
PLAYER_BASE_Z = 26.0
JUMP_DUR = 0.60
JUMP_H   = 70.0

# State
jumping = False
jump_t  = 0.0
ask_restart = False
game_over = False
t_last = 0.0  

# Forward base speed 
PLAYER_SPEED_BASE = 200.0

# Slow Boost modifiers
SLOW_MULT   = 0.55
SLOW_TIME   = 2.0
slow_left   = 0.0

BOOST_TIME  = 3.0
BOOST_MULT  = 1.5
boost_left  = 0.0

# Bullets
bullets = []
BULLET_SPEED = 500.0
BULLET_COOLDOWN = 0.25
shoot_cooldown = 0.0
BULLET_SPAWN_AHEAD = 40.0

# Enemies
enemies = []
ENEMY_SPEED      = 100.0
ENEMY_SPEED_MULT = 1.0
ENEMY_BODY_R = 20.0
ENEMY_HEAD_R = 10.0
PULSE_SPEED = 2.2
PULSE_AMP   = 0.28
SPAWN_INTERVAL_BASE = 3.0
SPAWN_INTERVAL_MULT = 1.0
spawn_timer = 0.0
MAX_ENEMIES = 4
# Items & obstacles
items = []
ROW_INTERVAL_BASE = 1.0
ROW_INTERVAL_MULT = 1.0
row_timer = 0.0
ITEM_SPEED      = 100.0
ITEM_SPEED_MULT = 1.0
COIN_SCORE = 10
ITEM_COIN_Z  = 6.0
ITEM_BOOST_Z = 6.0

score = 0
lives = 5
MAX_LIVES = 5
streak = 0
cheat_mode = False

# Multiplier
multiplier = 1
multiplier_time = 0.0
MULTIPLIER_DURATION = 10.0

# Moving Block
MOVING_BLOCKER_SPEED = 90.0
MOVING_BLOCKER_WIDTH = 28.0
MOVING_BLOCKER_HEIGHT = 30.0

# Snow 
SNOW_ENABLED = True
SNOW_COUNT = 240
SNOW_TOP_Z = 380.0
SNOW_BOTTOM_Z = 0.0
snow = []

def _spawn_one_snow(y_base):
    return {
        'x': random.uniform(-LANE_W*2.0, LANE_W*2.0),
        'y': y_base + random.uniform(300.0, 1600.0),
        'z': random.uniform(SNOW_TOP_Z*0.6, SNOW_TOP_Z),
        'vz': random.uniform(70.0, 120.0),
        'vx': random.uniform(-18.0, 18.0),
        'size': random.uniform(1.2, 3.0),
        'phase': random.uniform(0, math.pi*2)
    }

def init_snow():
    snow.clear()
    if not SNOW_ENABLED: return
    for _ in range(SNOW_COUNT):
        snow.append(_spawn_one_snow(PLAYER_Y))

def update_snow(dt):
    if not SNOW_ENABLED: return
    t = time.perf_counter()
    wind = 10.0*math.sin(t*0.35) + 6.0*math.sin(t*0.97 + 1.7)
    for f in snow:
        sway = 0.6*math.sin(t*1.2 + f['phase'])
        f['x'] += (f['vx'] + wind + sway) * dt * 0.15
        f['z'] -= f['vz'] * dt
        if f['z'] <= SNOW_BOTTOM_Z or f['y'] < PLAYER_Y - 200.0:
            f.update(_spawn_one_snow(PLAYER_Y))

def draw_snow():
    if not SNOW_ENABLED: return
    glPointSize(2.5)
    glBegin(GL_POINTS)
    glColor3f(1,1,1)
    for f in snow:
        glVertex3f(f['x'], f['y'], f['z'])
    glEnd()

def clamp_lane(i): return max(0, min(2, i))
def lane_x(i): return LANE_X[clamp_lane(i)]

# Player 
def draw_cube(sz):
    s = sz * 0.5
    glBegin(GL_QUADS)
    glVertex3f(-s,-s, s); glVertex3f( s,-s, s); glVertex3f( s, s, s); glVertex3f(-s, s, s)
    glVertex3f(-s,-s,-s); glVertex3f(-s, s,-s); glVertex3f( s, s,-s); glVertex3f( s,-s,-s)
    glVertex3f( s,-s,-s); glVertex3f( s, s,-s); glVertex3f( s, s, s); glVertex3f( s,-s, s)
    glVertex3f(-s,-s,-s); glVertex3f(-s,-s, s); glVertex3f(-s, s, s); glVertex3f(-s, s,-s)
    glVertex3f(-s, s,-s); glVertex3f(-s, s, s); glVertex3f( s, s, s); glVertex3f( s, s,-s)
    glVertex3f(-s,-s,-s); glVertex3f( s,-s,-s); glVertex3f( s,-s, s); glVertex3f(-s,-s, s)
    glEnd()

def player_z():
    if not jumping: return PLAYER_BASE_Z
    t = max(0.0, min(JUMP_DUR, jump_t))
    u = t / JUMP_DUR
    return PLAYER_BASE_Z + (4.0 * JUMP_H * u * (1.0 - u))

def draw_player():
    base_x = lane_x(PLAYER_LANE)
    base_y = PLAYER_Y
    base_z = player_z()
    glPushMatrix()
    glTranslatef(base_x, base_y, base_z)
    glColor3f(0.2,0.7,0.3)
    glScalef(1.4,2,0.7)
    draw_cube(28)
    glPopMatrix()
    wheel_z = base_z - 14.0
    glPushMatrix()
    glTranslatef(base_x, base_y, wheel_z)
    glColor3f(0.15,0.15,0.15)
    for dx,dy in [(-14,-8),(14,-8),(14,8),(-14,8)]:
        glPushMatrix(); glTranslatef(dx,dy,0)
        quad = gluNewQuadric()
        gluSphere(quad,6,8,8); glPopMatrix()
    glPopMatrix()
    cart_top = base_z + 14.0
    glPushMatrix()
    glTranslatef(base_x, base_y, cart_top + 12)
    glColor3f(0.2,0.6,0.9)
    glScalef(0.6,0.4,1.0)
    draw_cube(24)
    glPopMatrix()
    glPushMatrix()
    glTranslatef(base_x, base_y, cart_top + 24 + 8)
    glColor3f(0.9,0.8,0.6)
    quad = gluNewQuadric()
    gluSphere(quad, 8, 12, 12)
    glPopMatrix()

# Bullets
def draw_bullets():
    glColor3f(1,1,0)
    for b in bullets:
        glPushMatrix()
        glTranslatef(lane_x(b['lane']), b['y'], PLAYER_BASE_Z+10)
        draw_cube(8)
        glPopMatrix()

def update_bullets(dt):
    rem = []
    for b in bullets:
        b['y'] += BULLET_SPEED * dt
        if b['y'] > PLAYER_Y + 2000:
            rem.append(b)
    for b in rem:
        if b in bullets: bullets.remove(b)

# Enemies
def draw_enemies():
    t = time.perf_counter()
    for e in enemies:
        x = lane_x(e['lane']); y = e['y']
        wiggle = math.sin(t*PULSE_SPEED + e['phase'])
        scale = 1.0 + PULSE_AMP * wiggle
        body_r = ENEMY_BODY_R * scale
        head_r = ENEMY_HEAD_R * scale
        head_z = 20 + body_r + head_r
        glPushMatrix()
        glTranslatef(x, y, 20)
        glColor3f(1,0,0)
        quad = gluNewQuadric()
        gluSphere(quad, body_r, 16,16)
        glPopMatrix()
        glPushMatrix()
        glTranslatef(x, y, head_z)
        glColor3f(0,0,0)
        quad2 = gluNewQuadric()
        gluSphere(quad2, head_r, 12,12)
        glPopMatrix()

def spawn_enemy():
    if len(enemies) >= MAX_ENEMIES: return
    lane = random.choice([0,1,2])
    y = PLAYER_Y + 1200
    enemies.append({'lane':lane,'y':y,'phase':random.uniform(0,math.pi*2)})

def update_enemies(dt):
    global lives, game_over, streak, score
    speed = ENEMY_SPEED * ENEMY_SPEED_MULT
    rem = []
    for e in list(enemies):
        e['y'] -= speed * dt
        if e['y'] < PLAYER_Y - 200:
            rem.append(e)
            streak = 0
        if abs(e['y']-PLAYER_Y) < 30 and e['lane']==PLAYER_LANE:
            if player_z() - PLAYER_BASE_Z > 18.0:
                rem.append(e)
            else:
                lives -= 1
                streak = 0
                rem.append(e)
                if lives <= 0:
                    lives = 0
                    set_game_over()
    for e in rem:
        if e in enemies: enemies.remove(e)

# Items and obstacles
def spawn_row(y_at):
    for ln in (0,1,2):
        r = random.random()
        if r < 0.60:
            continue
        elif r < 0.72:
            items.append({'kind':'coin','lane':ln,'y':y_at,'data':{}})
        elif r < 0.735:  # rarer life packs
            items.append({'kind':'life','lane':ln,'y':y_at,'data':{}})
        elif r < 0.82:
            items.append({'kind':'hurdle','lane':ln,'y':y_at,'data':{'w':LANE_W*0.9,'t':10.0,'h':44.0}})
        elif r < 0.88:
            items.append({'kind':'boost','lane':ln,'y':y_at,'data':{}})
        elif r < 0.92:
            items.append({'kind':'slow','lane':ln,'y':y_at,'data':{'len':90.0}})
        elif r < 0.95:
            items.append({'kind':'star','lane':ln,'y':y_at,'data':{}})
        elif r < 0.97:
            items.append({'kind':'boost_pad','lane':ln,'y':y_at,'data':{}})
        elif r < 0.985:
            items.append({'kind':'pillar','lane':ln,'y':y_at,'data':{'h':80.0}})
        else:
            start_x = lane_x(ln)
            items.append({'kind':'moving_blocker','lane':ln,'y':y_at,'data':{'xpos':start_x,'dir':random.choice([-1,1]), 'target_lane':ln}})

def update_items(dt):
    global items, boost_left, lives, score, slow_left, multiplier, multiplier_time, streak
    speed = ITEM_SPEED * ITEM_SPEED_MULT
    rem = []
    for it in list(items):
        kind = it['kind']
        if kind == 'moving_blocker':
            dd = it['data']
            dd['xpos'] += MOVING_BLOCKER_SPEED * dd['dir'] * dt
            if dd['xpos'] < LANE_X[0] - 20: dd['dir'] = 1
            if dd['xpos'] > LANE_X[2] + 20: dd['dir'] = -1
            it['y'] -= speed * dt
            if abs(it['y'] - PLAYER_Y) < 30 and abs(dd['xpos'] - lane_x(PLAYER_LANE)) < 40:
                lives -= 1
                streak = 0
                rem.append(it)
                if lives <= 0: set_game_over()
            if it['y'] < PLAYER_Y - 200:
                rem.append(it)
            continue
        it['y'] -= speed * dt
        if it['y'] < PLAYER_Y - 200:
            rem.append(it)
            continue
        if it['lane'] == PLAYER_LANE and abs(it['y'] - PLAYER_Y) < 30:
            if kind == 'coin':
                score += COIN_SCORE * multiplier
                streak += 1
                rem.append(it)
            elif kind == 'boost':
                boost_left = BOOST_TIME
                rem.append(it)
            elif kind == 'hurdle':
                bar_h = it['data'].get('h', 44.0)
                cart_top = player_z() + 14.0
                if cart_top < bar_h - 2.0:
                    lives -= 1
                    streak = 0
                    rem.append(it)
                    if lives <= 0:
                        set_game_over()
            elif kind == 'slow':
                slow_left = SLOW_TIME
                rem.append(it)
            elif kind == 'life':
                if lives < MAX_LIVES:
                    lives += 1
                rem.append(it)
            elif kind == 'star':
                if not cheat_mode:
                    multiplier = 2
                    multiplier_time = MULTIPLIER_DURATION
                rem.append(it)
            elif kind == 'boost_pad':
                boost_left = BOOST_TIME
                rem.append(it)
            elif kind == 'pillar':
                cart_top = player_z() + 14.0
                if cart_top < it['data'].get('h',80.0):
                    lives -= 1
                    streak = 0
                    rem.append(it)
                    if lives <= 0: set_game_over()
                else:
                    rem.append(it)
    for it in rem:
        if it in items: items.remove(it)

def draw_items():
    t = time.perf_counter()
    for it in items:
        x = lane_x(it['lane']); y = it['y']
        kind = it['kind']
        if kind == 'coin':
            glPushMatrix()
            glTranslatef(x, y, ITEM_COIN_Z)
            glRotatef((t * 220.0) % 360.0, 0, 1, 0)
            quad = gluNewQuadric()
            glColor3f(1.0, 0.6, 0.1)
            gluCylinder(quad, 8.0, 8.0, 4.0, 20, 1)
            glPopMatrix()
        elif kind == 'boost':
            glPushMatrix()
            glTranslatef(x, y, ITEM_BOOST_Z)
            glColor3f(0.2, 1.0, 0.2)
            glScalef(20,4,2); draw_cube(2.0)
            glPopMatrix()
        elif kind == 'hurdle':
            w = it['data'].get('w', LANE_W*0.9)
            tH = it['data'].get('t', 10.0)
            h = it['data'].get('h', 44.0)
            glColor3f(0.85, 0.2, 0.2)
            glPushMatrix()
            glTranslatef(x, y, h*0.5)
            glScalef(w/28.0, tH/28.0, h/28.0)
            draw_cube(28.0)
            glPopMatrix()
        elif kind == 'slow':
            length = it['data'].get('len', 90.0)
            halfL = length * 0.5
            x0 = x - LANE_W*0.45; x1 = x + LANE_W*0.45
            y0 = y - halfL; y1 = y + halfL
            glColor3f(0.85, 0.90, 1.0)
            glBegin(GL_QUADS)
            glVertex3f(x0, y0, 0.0); glVertex3f(x1, y0, 0.0); glVertex3f(x1, y1, 0.0); glVertex3f(x0, y1, 0.0)
            glEnd()
        elif kind == 'life':
            glPushMatrix()
            glTranslatef(x, y, ITEM_COIN_Z)
            glColor3f(0.8, 0.1, 0.9)
            quad = gluNewQuadric()
            gluSphere(quad, 8.0, 12, 12)
            glPopMatrix()
        elif kind == 'star':
            glPushMatrix()
            glTranslatef(x, y, ITEM_COIN_Z)
            glRotatef((t * 90.0) % 360.0, 0,1,0)
            glColor3f(1.0, 0.9, 0.2)
            glScalef(1.2,1.2,1.2)
            draw_cube(12.0)
            glPopMatrix()
        elif kind == 'boost_pad':
            glColor3f(0.2, 0.4, 1.0)
            halfW = LANE_W*0.45
            glBegin(GL_QUADS)
            glVertex3f(x-halfW, y-20, 0.1); glVertex3f(x+halfW, y-20, 0.1)
            glVertex3f(x+halfW, y+20, 0.1); glVertex3f(x-halfW, y+20, 0.1)
            glEnd()
        elif kind == 'pillar':
            h = it['data'].get('h',80.0)
            glColor3f(0.6,0.4,0.3)
            glPushMatrix()
            glTranslatef(x, y, h*0.5)
            quad = gluNewQuadric()
            gluCylinder(quad, 14.0, 14.0, h, 16,1)
            glPopMatrix()
        elif kind == 'moving_blocker':
            dd = it['data']
            xpos = dd['xpos']
            glColor3f(0.9, 0.2, 0.2)
            glPushMatrix()
            glTranslatef(xpos, y, MOVING_BLOCKER_HEIGHT*0.5)
            glScalef(MOVING_BLOCKER_WIDTH/28.0, 18.0/28.0, MOVING_BLOCKER_HEIGHT/28.0)
            draw_cube(28.0)
            glPopMatrix()

# Collisions bullets enemies
def check_bullet_hits():
    global score, streak, lives
    rem_b, rem_e = [], []
    for b in list(bullets):
        for e in list(enemies):
            if b['lane'] == e['lane'] and abs(b['y'] - e['y']) < 30:
                rem_b.append(b); rem_e.append(e)
                score += 5 * multiplier
                streak += 1
                if (streak % 3 == 0) and (not cheat_mode):
                    if lives < MAX_LIVES: lives += 1
    for b in rem_b:
        if b in bullets: bullets.remove(b)
    for e in rem_e:
        if e in enemies: enemies.remove(e)

#bullets vs solid obstacles
def _bullet_hits_obstacle(b, it):
    kind = it['kind']
    by = b['y']
    if kind == 'hurdle':
        if it['lane'] == b['lane'] and abs(it['y'] - by) < 30:
            h = it['data'].get('h', 44.0)
            bullet_z = PLAYER_BASE_Z + 10.0
            return bullet_z <= (h + 2.0)
    elif kind == 'pillar':
        if it['lane'] == b['lane'] and abs(it['y'] - by) < 30:
            return True
    elif kind == 'moving_blocker':
        if abs(it['y'] - by) < 30:
            xpos = it['data'].get('xpos', lane_x(it['lane']))
            if abs(xpos - lane_x(b['lane'])) < 40:
                return True
    return False

def check_bullet_vs_obstacles():
    rem_b = []
    for b in list(bullets):
        for it in items:
            if it['kind'] not in ('hurdle', 'pillar', 'moving_blocker'):
                continue
            if _bullet_hits_obstacle(b, it):
                rem_b.append(b)
                break
    for b in rem_b:
        if b in bullets:
            bullets.remove(b)

# Difficulty Ramp (every 30s)
difficulty_level = 1
time_since_ramp = 0.0

def apply_ramp():
    global difficulty_level, PLAYER_SPEED_BASE, ENEMY_SPEED_MULT, ITEM_SPEED_MULT, SPAWN_INTERVAL_MULT, ROW_INTERVAL_MULT, MAX_ENEMIES
    difficulty_level += 1
    PLAYER_SPEED_BASE += 14.0
    ENEMY_SPEED_MULT *= 1.05
    ITEM_SPEED_MULT  *= 1.04
    SPAWN_INTERVAL_MULT = max(0.55, SPAWN_INTERVAL_MULT * 0.92)
    ROW_INTERVAL_MULT   = max(0.60, ROW_INTERVAL_MULT   * 0.94)
    MAX_ENEMIES = min(10, MAX_ENEMIES + 1)

# HUD & messages
hud_messages = []

def push_message(txt, duration=2.0):
    hud_messages.append({'text':txt, 'time':duration})

# Custom vector font 
FONT_5X7 = {
    'A': ["01110","10001","10001","11111","10001","10001","10001"],
    'B': ["11110","10001","11110","10001","10001","10001","11110"],
    'C': ["01110","10001","10000","10000","10000","10001","01110"],
    'D': ["11100","10010","10001","10001","10001","10010","11100"],
    'E': ["11111","10000","11110","10000","10000","10000","11111"],
    'F': ["11111","10000","11110","10000","10000","10000","10000"],
    'G': ["01110","10001","10000","10011","10001","10001","01110"],
    'H': ["10001","10001","11111","10001","10001","10001","10001"],
    'I': ["11111","00100","00100","00100","00100","00100","11111"],
    'J': ["00111","00010","00010","00010","10010","10010","01100"],
    'K': ["10001","10010","10100","11000","10100","10010","10001"],
    'L': ["10000","10000","10000","10000","10000","10000","11111"],
    'M': ["10001","11011","10101","10101","10001","10001","10001"],
    'N': ["10001","11001","10101","10011","10001","10001","10001"],
    'O': ["01110","10001","10001","10001","10001","10001","01110"],
    'P': ["11110","10001","10001","11110","10000","10000","10000"],
    'Q': ["01110","10001","10001","10001","10101","10010","01101"],
    'R': ["11110","10001","10001","11110","10100","10010","10001"],
    'S': ["01110","10001","10000","01110","00001","10001","01110"],
    'T': ["11111","00100","00100","00100","00100","00100","00100"],
    'U': ["10001","10001","10001","10001","10001","10001","01110"],
    'V': ["10001","10001","10001","10001","01010","01010","00100"],
    'W': ["10001","10001","10001","10101","10101","11011","10001"],
    'X': ["10001","01010","00100","00100","00100","01010","10001"],
    'Y': ["10001","01010","00100","00100","00100","00100","00100"],
    'Z': ["11111","00001","00010","00100","01000","10000","11111"],
    '0': ["01110","10001","10011","10101","11001","10001","01110"],
    '1': ["00100","01100","00100","00100","00100","00100","01110"],
    '2': ["01110","10001","00001","00010","00100","01000","11111"],
    '3': ["11110","00001","00001","01110","00001","00001","11110"],
    '4': ["00010","00110","01010","10010","11111","00010","00010"],
    '5': ["11111","10000","11110","00001","00001","10001","01110"],
    '6': ["01110","10000","11110","10001","10001","10001","01110"],
    '7': ["11111","00001","00010","00100","01000","01000","01000"],
    '8': ["01110","10001","10001","01110","10001","10001","01110"],
    '9': ["01110","10001","10001","01111","00001","00001","01110"],
    ' ': ["00000","00000","00000","00000","00000","00000","00000"],
    ':': ["00000","00100","00000","00000","00100","00000","00000"],
    '(': ["00010","00100","01000","01000","01000","00100","00010"],
    ')': ["01000","00100","00010","00010","00010","00100","01000"],
    '-': ["00000","00000","00000","11111","00000","00000","00000"],
    '?': ["01110","10001","00001","00010","00100","00000","00100"],
    'x': ["00000","00000","10001","01010","00100","01010","10001"],
}

# lower uppercase map
for ch in "abcdefghijklmnopqrstuvwxyz":
    if ch not in FONT_5X7:
        FONT_5X7 = FONT_5X7 if 'FONT_5X7' in globals() else {}
    if ch.upper() in FONT_5X7:
        FONT_5X7[ch] = FONT_5X7[ch.upper()]

def _draw_char_5x7(x, y, ch, scale=2.0):
    pat = FONT_5X7.get(ch, FONT_5X7.get(ch.lower(), FONT_5X7['?']))
    s = scale
    glBegin(GL_QUADS)
    for row in range(7):
        bits = pat[6 - row]
        for col in range(5):
            if bits[col] == '1':
                x0 = x + col * s
                y0 = y + row * s
                x1 = x0 + s
                y1 = y0 + s
                glVertex2f(x0, y0); glVertex2f(x1, y0); glVertex2f(x1, y1); glVertex2f(x0, y1)
    glEnd()

def draw_text(x, y, text, font=None):
    depth_was_enabled = glIsEnabled(GL_DEPTH_TEST)
    if depth_was_enabled: glDisable(GL_DEPTH_TEST)
    glMatrixMode(GL_PROJECTION); glPushMatrix(); glLoadIdentity()
    gluOrtho2D(0, WIN_W, 0, WIN_H)
    glMatrixMode(GL_MODELVIEW); glPushMatrix(); glLoadIdentity()
    glColor3f(1, 1, 1)
    cursor_x = x
    for ch in text:
        _draw_char_5x7(cursor_x, y, ch, scale=2.0)
        cursor_x += 12
    glPopMatrix()
    glMatrixMode(GL_PROJECTION); glPopMatrix()
    glMatrixMode(GL_MODELVIEW)
    if depth_was_enabled: glEnable(GL_DEPTH_TEST)

def draw_hud():
    depth_was_enabled = glIsEnabled(GL_DEPTH_TEST)
    if depth_was_enabled:
        glDisable(GL_DEPTH_TEST)
    pad_x = 16; pad_top = 50
    panel_w, panel_h = 720, 96
    x0 = pad_x; y0 = WIN_H - pad_top - panel_h; x1 = x0 + panel_w; y1 = y0 + panel_h
    glMatrixMode(GL_PROJECTION); glPushMatrix(); glLoadIdentity()
    gluOrtho2D(0, WIN_W, 0, WIN_H)
    glMatrixMode(GL_MODELVIEW); glPushMatrix(); glLoadIdentity()
    glColor3f(0.12, 0.12, 0.15)
    glBegin(GL_QUADS)
    glVertex2f(x0, y0); glVertex2f(x1, y0); glVertex2f(x1, y1); glVertex2f(x0, y1)
    glEnd()
    glColor3f(1,1,1)
    glBegin(GL_LINE_LOOP)
    glVertex2f(x0, y0); glVertex2f(x1, y0); glVertex2f(x1, y1); glVertex2f(x0, y1)
    glEnd()
    draw_text(x0+12, y1-28, f"Score: {int(score)}")
    draw_text(x0+12, y1-52, f"Lives: {lives}")
    draw_text(x0+170, y1-52, f"Streak: {streak}")
    draw_text(x0+300, y1-28, f"Lv: {difficulty_level}")
    if boost_left > 0.0:
        draw_text(x0+360, y1-52, "BOOST")
    if slow_left > 0.0:
        draw_text(x0+420, y1-52, "SLOW")
    if multiplier > 1:
        draw_text(x0+360, y1-28, f"Multiplier: x{multiplier} ({int(multiplier_time)}s)")
    msg_y = WIN_H - 120
    for m in list(hud_messages):
        draw_text(WIN_W//2 - len(m['text'])*4, msg_y, m['text'])
        msg_y -= 20
    if game_over:
        draw_text(WIN_W//2-220, WIN_H//2+10, "GAME OVER - Press R to Restart")
    if ask_restart and not game_over:
        draw_text(WIN_W//2-140, WIN_H//2+100, "Restart now? (Y/N)")
    glPopMatrix()
    glMatrixMode(GL_PROJECTION); glPopMatrix()
    glMatrixMode(GL_MODELVIEW)
    if depth_was_enabled:
        glEnable(GL_DEPTH_TEST)

# Camera setup
def setupCamera():
    global ASPECT, cam_yaw, cam_pitch
    glMatrixMode(GL_PROJECTION); glLoadIdentity()
    gluPerspective(FOV_Y, ASPECT, 0.1, 5000.0)
    glMatrixMode(GL_MODELVIEW); glLoadIdentity()
    if first_person:
        cx, cy, cz = 0.0, PLAYER_Y - 40, 60
        gluLookAt(cx, cy, cz, 0.0, cy + 160, cz, 0, 0, 1)
    else:
        cx, cy, cz = 0.0, PLAYER_Y - cam_back_third, cam_height_third
        gluLookAt(cx, cy, cz, 0.0, PLAYER_Y + 300, 40, 0, 0, 1)

# Floor
def draw_floor():
    seg_len = 800.0
    z = 0.0
    start = int(PLAYER_Y // seg_len - 1) * seg_len
    for k in range(8):
        y0 = start + k*seg_len
        y1 = y0 + seg_len
        glBegin(GL_QUADS)
        glColor3f(0.75,0.60,0.95)
        glVertex3f(-LANE_W*1.5, y0, z); glVertex3f(-LANE_W*0.5, y0, z)
        glVertex3f(-LANE_W*0.5, y1, z); glVertex3f(-LANE_W*1.5, y1, z)
        glEnd()
        glBegin(GL_QUADS)
        glColor3f(0.92,0.92,0.95)
        glVertex3f(-LANE_W*0.5, y0, z); glVertex3f( LANE_W*0.5, y0, z)
        glVertex3f( LANE_W*0.5, y1, z); glVertex3f(-LANE_W*0.5, y1, z)
        glEnd()
        glColor3f(0.8, 0.8, 0.8)
        glBegin(GL_LINES)
        glVertex3f(-LANE_W*0.5, y0, z+1.0); glVertex3f(-LANE_W*0.5, y1, z+1.0)
        glVertex3f( LANE_W*0.5, y0, z+1.0); glVertex3f( LANE_W*0.5, y1, z+1.0)
        glEnd()
        glBegin(GL_QUADS)
        glColor3f(0.75,0.60,0.95)
        glVertex3f( LANE_W*0.5, y0, z); glVertex3f( LANE_W*1.5, y0, z)
        glVertex3f( LANE_W*1.5, y1, z); glVertex3f( LANE_W*0.5, y1, z)
        glEnd()

def draw_tunnel():
    seg_len = 800.0
    z_floor = 0.0
    wall_h = 220.0
    ceil_z = wall_h
    start = int(PLAYER_Y // seg_len - 1) * seg_len
    for k in range(8):
        y0 = start + k*seg_len
        y1 = y0 + seg_len
        glBegin(GL_QUADS)
        glColor3f(0.68, 0.82, 1.0)
        glVertex3f(-LANE_W*1.8, y0, z_floor); glVertex3f(-LANE_W*1.5, y0, z_floor)
        glVertex3f(-LANE_W*1.5, y0, ceil_z); glVertex3f(-LANE_W*1.8, y0, ceil_z)
        glVertex3f(-LANE_W*1.8, y1, z_floor); glVertex3f(-LANE_W*1.5, y1, z_floor)
        glVertex3f(-LANE_W*1.5, y1, ceil_z); glVertex3f(-LANE_W*1.8, y1, ceil_z)
        glEnd()
        glBegin(GL_QUADS)
        glColor3f(0.7, 0.8, 1.0)
        glVertex3f(LANE_W*1.5, y0, z_floor); glVertex3f(LANE_W*1.8, y0, z_floor)
        glVertex3f(LANE_W*1.8, y0, ceil_z); glVertex3f(LANE_W*1.5, y0, ceil_z)
        glVertex3f(LANE_W*1.5, y1, z_floor); glVertex3f(LANE_W*1.8, y1, z_floor)
        glVertex3f(LANE_W*1.8, y1, ceil_z); glVertex3f(LANE_W*1.5, y1, ceil_z)
        glEnd()
        glBegin(GL_QUADS)
        glColor3f(0.65, 0.75, 0.95)
        glVertex3f(-LANE_W*1.5, y0, ceil_z); glVertex3f( LANE_W*1.5, y0, ceil_z)
        glVertex3f( LANE_W*1.5, y1, ceil_z); glVertex3f(-LANE_W*1.5, y1, ceil_z)
        glEnd()

def update_messages(dt):
    for m in list(hud_messages):
        m['time'] -= dt
        if m['time'] <= 0: hud_messages.remove(m)
#Game state
def set_game_over():
    global game_over
    game_over = True
    push_message("You died", 3.0)

def reset_all():
    global PLAYER_LANE, jumping, jump_t, game_over, t_last, first_person, ask_restart, PLAYER_Y
    global bullets, enemies, items, score, lives, streak, spawn_timer, row_timer, cheat_mode, boost_left, slow_left
    global PLAYER_SPEED_BASE, ENEMY_SPEED_MULT, ITEM_SPEED_MULT, SPAWN_INTERVAL_MULT, ROW_INTERVAL_MULT, difficulty_level, time_since_ramp
    global multiplier, multiplier_time
    PLAYER_LANE = 1
    jumping = False
    jump_t = 0.0
    game_over = False
    first_person = False
    ask_restart = False
    PLAYER_Y = 0.0
    bullets.clear()
    enemies.clear()
    items.clear()
    score = 0
    lives = 5
    streak = 0
    cheat_mode = False
    spawn_timer = 1.0
    row_timer = 0.5
    boost_left = 0.0
    slow_left = 0.0
    PLAYER_SPEED_BASE = 200.0
    ENEMY_SPEED_MULT  = 1.0
    ITEM_SPEED_MULT   = 1.0
    SPAWN_INTERVAL_MULT = 1.0
    ROW_INTERVAL_MULT   = 1.0
    difficulty_level = 1
    time_since_ramp = 0.0
    multiplier = 1
    multiplier_time = 0.0
    init_snow()
    t_last = time.perf_counter()


def game_update(dt):
    global t_last, jump_t, jumping, PLAYER_Y, shoot_cooldown
    global spawn_timer, row_timer, boost_left, slow_left, time_since_ramp, score
    global multiplier, multiplier_time
    if paused:
        return
    if game_over:
        return
    if boost_left > 0.0:
        score += int(2 * dt * (1 if multiplier == 1 else multiplier))
    if boost_left > 0.0: boost_left = max(0.0, boost_left - dt)
    if slow_left  > 0.0: slow_left  = max(0.0, slow_left  - dt)
    forward_mult = 1.0
    if boost_left > 0.0: forward_mult *= BOOST_MULT
    if slow_left  > 0.0: forward_mult *= SLOW_MULT
    PLAYER_Y += PLAYER_SPEED_BASE * forward_mult * dt
    score += 1 * dt * multiplier
    if jumping:
        jump_t += dt
        if jump_t >= JUMP_DUR:
            jumping = False
            jump_t = 0.0
    global shoot_cooldown
    shoot_cooldown = max(0.0, shoot_cooldown - dt)
    update_bullets(dt)
    update_enemies(dt)
    update_items(dt)
    check_bullet_hits()
    check_bullet_vs_obstacles()  # <-- remove bullets when they hit hurdles/pillars/moving cubes
    update_snow(dt)
    update_messages(dt)
    _cheat_autopilot_if_ready()
    spawn_timer -= dt
    spawn_ivl = SPAWN_INTERVAL_BASE * SPAWN_INTERVAL_MULT
    if spawn_timer <= 0.0:
        spawn_enemy()
        spawn_timer = spawn_ivl
    row_timer -= dt
    row_ivl = ROW_INTERVAL_BASE * ROW_INTERVAL_MULT
    if row_timer <= 0.0:
        spawn_row(PLAYER_Y + 1200.0)
        row_timer = row_ivl
    time_since_ramp += dt
    if time_since_ramp >= 30.0:
        time_since_ramp = 0.0
        apply_ramp()
        push_message(f"Difficulty increased: Lv {difficulty_level}", 2.5)
    if multiplier_time > 0.0:
        multiplier_time -= dt
        if multiplier_time <= 0.0:
            multiplier_time = 0.0
            multiplier = 1

# Cheat 
def _nearest_enemy_ahead():
    best = None
    best_score = None
    for e in enemies:
        dy = e['y'] - PLAYER_Y
        if dy < -50: continue
        lane_dist = abs(e['lane'] - PLAYER_LANE)
        score_val = (dy if dy >= 0 else 9_999_999) + lane_dist * 10.0
        if best is None or score_val < best_score:
            best = e; best_score = score_val
    return best

def _hurdle_ahead_in_lane():
    for it in items:
        if it['kind'] != 'hurdle': continue
        if it['lane'] != PLAYER_LANE: continue
        dy = it['y'] - PLAYER_Y
        if 0 <= dy <= 80:
            return True
    return False

def _pillar_ahead_in_lane(max_ahead=140.0, lane=None):
    ln = PLAYER_LANE if lane is None else lane
    for it in items:
        if it['kind'] != 'pillar':
            continue
        if it['lane'] != ln:
            continue
        dy = it['y'] - PLAYER_Y
        if 0.0 <= dy <= max_ahead:
            return True
    return False

# Moving cube threat check
def _moving_blocker_threat_in_lane(max_ahead=140.0, lane=None):
    ln = PLAYER_LANE if lane is None else lane
    lx = lane_x(ln)
    for it in items:
        if it['kind'] != 'moving_blocker':
            continue
        dy = it['y'] - PLAYER_Y
        if 0.0 <= dy <= max_ahead:
            xpos = it['data'].get('xpos', lane_x(it['lane']))
            if abs(xpos - lx) < 40:
                return True
    return False

def _cheat_autopilot_if_ready():
    global shoot_cooldown, PLAYER_LANE, jumping, jump_t
    if not cheat_mode or game_over:
        return
    if _pillar_ahead_in_lane(max_ahead=140.0) or _moving_blocker_threat_in_lane(max_ahead=140.0):
        candidates = [ln for ln in (PLAYER_LANE-1, PLAYER_LANE+1, 0, 1, 2) if 0 <= ln <= 2]
        for ln in candidates:
            if ln == PLAYER_LANE:
                continue
            if (not _pillar_ahead_in_lane(max_ahead=140.0, lane=ln)) and (not _moving_blocker_threat_in_lane(max_ahead=140.0, lane=ln)):
                PLAYER_LANE = ln
                break
    if (not jumping) and _hurdle_ahead_in_lane():
        jumping = True
        jump_t = 0.0
    if shoot_cooldown > 0.0:
        return
    tgt = _nearest_enemy_ahead()
    if tgt is None: return
    PLAYER_LANE = tgt['lane']
    bullets.append({'lane': PLAYER_LANE, 'y': PLAYER_Y + BULLET_SPAWN_AHEAD})
    shoot_cooldown = BULLET_COOLDOWN

# Render
def showScreen():
    global ASPECT, t_last
    now = time.perf_counter()
    if t_last == 0.0:
        t_last = now
    dt = now - t_last
    t_last = now
    game_update(dt)
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()
    glViewport(0, 0, WIN_W, WIN_H)
    ASPECT = WIN_W / float(WIN_H)
    setupCamera()
    draw_floor()
    draw_tunnel()
    draw_snow()
    draw_player()
    draw_bullets()
    draw_enemies()
    draw_items()
    draw_hud()
    glutSwapBuffers()

# Input
def keyboardListener(key, x, y):
    global PLAYER_LANE, jumping, jump_t, ask_restart, first_person, game_over, cheat_mode, paused
    k = key
    if ask_restart:
        if k in (b'y', b'Y'): reset_all(); ask_restart=False
        elif k in (b'n', b'N', b'\x1b'): ask_restart=False
        return
    if k == b'a': PLAYER_LANE = clamp_lane(PLAYER_LANE - 1)
    elif k == b'd': PLAYER_LANE = clamp_lane(PLAYER_LANE + 1)
    elif k == b' ' and not jumping:
        jumping = True; jump_t = 0.0
    elif k == b'f':
        first_person = not first_person
    elif k == b'c':
        cheat_mode = not cheat_mode
        if cheat_mode:
            push_message("Cheat ON: auto-aim/autofire", 2.0)
        else:
            push_message("Cheat OFF", 1.2)
    elif k == b'r':
        if game_over: reset_all()
        else: ask_restart = True
    elif k == b'p':
        paused = not paused
        push_message("Paused" if paused else "Resumed", 1.0)

def specialListener(key, x, y):
    global FOV_Y, cam_back_third, cam_height_third
    if key == GLUT_KEY_UP:
        FOV_Y = max(35.0, FOV_Y - 2.0)
    elif key == GLUT_KEY_DOWN:
        FOV_Y = min(110.0, FOV_Y + 2.0)
    elif key == GLUT_KEY_LEFT:
        cam_back_third = max(100.0, cam_back_third - 10.0)
    elif key == GLUT_KEY_RIGHT:
        cam_back_third = min(500.0, cam_back_third + 10.0)

def mouseListener(button, state, x, y):
    global shoot_cooldown, PLAYER_LANE, first_person
    if button == GLUT_LEFT_BUTTON and state == GLUT_DOWN and shoot_cooldown <= 0.0 and not game_over:
        if cheat_mode:
            tgt = _nearest_enemy_ahead()
            lane_for_shot = tgt['lane'] if tgt is not None else PLAYER_LANE
            PLAYER_LANE = lane_for_shot
        else:
            lane_for_shot = PLAYER_LANE
        bullets.append({'lane': lane_for_shot, 'y': PLAYER_Y + BULLET_SPAWN_AHEAD})
        shoot_cooldown = BULLET_COOLDOWN
    elif button == GLUT_RIGHT_BUTTON and state == GLUT_DOWN:
        first_person = not first_person

def init_gl():
    glClearColor(0.05, 0.06, 0.12, 1.0)
    glEnable(GL_DEPTH_TEST)
    glEnable(GL_POINT_SMOOTH)

def main():
    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(WIN_W, WIN_H)
    glutCreateWindow(b"Subway Shot 3D")
    init_gl()
    reset_all()
    glutDisplayFunc(showScreen)
    glutKeyboardFunc(keyboardListener)
    glutSpecialFunc(specialListener)
    glutMouseFunc(mouseListener)
    glutIdleFunc(showScreen)
    glutMainLoop()

if __name__ == "__main__":
    main()
