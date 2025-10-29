import pygame, math, sys, random

# --- Game Settings ---
# All tweakable parameters are defined here for easy adjustment
GAME_SETTINGS = {
    # Damage System
    "DAMAGE_ENABLED": False,              # Set to False to disable all damage
    "WALL_DAMAGE_PER_FRAME": 0.2,       # Damage per frame when off-track/hitting walls (e.g., 0.2 = 12/sec at 60 FPS)
    "CAR_COLLISION_DAMAGE": 2.0,        # Damage per car-to-car collision
    "DAMAGE_DEBUFF_THRESHOLDS": [30, 60, 90],  # Damage levels for debuffs (5%, 15%, 30% performance reduction)
    
    # Healing System
    "HEALING_ENABLED": False,             # Set to False to disable all healing
    "DAMAGE_RECOVERY_PER_FRAME": 0.1,   # Passive damage recovery per frame (e.g., 0.1 = 6/sec at 60 FPS)
    "CLEAN_LAP_BONUS_RECOVERY": 10.0,   # Damage recovered for completing a lap without collisions
    
    # Player Car Settings
    "PLAYER_THRUST": 0.12,              # Acceleration rate (higher = faster acceleration)
    "PLAYER_DRAG": 0.988,                # Velocity retention (higher = less slowdown, 0.97–0.995)
    "PLAYER_MAX_SPEED": 21.0,           # Top speed cap
    "PLAYER_BASE_TURN_RATE": 5.0,       # Turning sharpness (higher = sharper turns)
    "PLAYER_TURN_SPEED_FACTOR": 0.08,   # How speed reduces turning (lower = better high-speed turns)
    "PLAYER_STEER_RESPONSE": 0.4,       # Steering responsiveness (higher = snappier, 0.2–0.6)
    "PLAYER_GRIP_FACTOR": 1.5,          # Road traction multiplier (lower = less grip, e.g., 0.5 for slippery)
    "PLAYER_RANDOMNESS": 0.01,          # ±% randomness for player car (e.g., 0.02 = ±2%, 0.0 = no randomness)
    
    # AI Car Settings (lists for AI1, AI2, AI3)
    "AI_THRUSTS": [0.12, 0.12, 0.12],       # Acceleration rates
    "AI_DRAGS": [0.988, 0.988, 0.988],         # Velocity retention
    "AI_MAX_SPEEDS": [22.0, 22.0, 22.0],       # Top speed caps
    "AI_BASE_TURN_RATES": [4.0, 4.0, 4.0],     # Turning sharpness
    "AI_TURN_SPEED_FACTORS": [0.1, 0.1, 0.1],  # Speed's effect on turning
    "AI_STEER_RESPONSES": [0.4, 0.4, 0.4],     # Steering responsiveness
    "AI_GRIP_FACTORS": [1.5, 1.5, 1.5],        # Road traction
    "AI_RANDOMNESS": [0.02, 0.02, 0.02]        # ±% randomness per AI (e.g., 0.05 = ±5%)
}

pygame.init()

# --- setup ---
screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
W, H = screen.get_size()
pygame.display.set_caption("F1 Car with Collision + AI Opponents")
clock = pygame.time.Clock()

# Assume original track dimensions
ORIG_W, ORIG_H = 1920, 1080

# --- Image Loading & Setup ---
try:
    player_ship_img = pygame.image.load("car.png").convert_alpha()
    track_img_original = pygame.image.load("track.png").convert_alpha()
    track_img = pygame.transform.smoothscale(track_img_original, (W, H))
except pygame.error as e:
    print(f"Error loading images: {e}. Using simple placeholder.")
    player_ship_img = pygame.Surface((50, 30), pygame.SRCALPHA)
    pygame.draw.rect(player_ship_img, (220, 0, 0), (0, 0, 50, 30), 0, 5)
    track_img = pygame.Surface((W, H), pygame.SRCALPHA)
    pygame.draw.rect(track_img, (0, 0, 0), (0, 0, W, H), 50)

# --- Static Collision Mask Setup ---
collision_mask = pygame.mask.from_surface(track_img)

# --- AI Waypoints (scaled to screen size) ---
WAYPOINTS_ORIG = [
    (540, 260, 18.0), (440, 270, 16.0), (355, 280, 12.0), (275, 310, 10.0), (235, 365, 10.0), (180, 425, 10.0),
    (155, 525, 14.0), (150, 640, 18.0), (200, 750, 22.0), (280, 830, 22.0), (380, 890, 22.0), (500, 920, 22.0),
    (630, 930, 22.0), (760, 930, 22.0), (880, 930, 22.0), (990, 930, 22.0), (1120, 930, 22.0), (1230, 925, 22.0),
    (1350, 920, 22.0), (1460, 910, 18.0), (1580, 870, 14.0), (1660, 780, 12.0), (1725, 670, 10.0),
    (1775, 565, 10.0), (1810, 460, 6.0), (1805, 350, 6.0), (1750, 270, 6.0), (1660, 230, 6.0),
    (1560, 245, 6.0), (1515, 300, 6.0), (1480, 365, 6.0), (1405, 445, 6.0), (1300, 500, 6.0),
    (1215, 500, 6.0), (1160, 480, 6.0), (1115, 440, 6.0), (1060, 370, 6.0), (950, 310, 7.0),
    (840, 270, 10.0), (740, 260, 18.0), (650, 255, 18.0), (540, 260, 18.0)
]
WAYPOINTS = [(int(x * W / ORIG_W), int(y * H / ORIG_H), speed) for x, y, speed in WAYPOINTS_ORIG]

# --- Start/Finish Line (scaled) ---
START_LINE_X1, START_LINE_X2 = int(550 * W / ORIG_W), int(580 * W / ORIG_W)
START_LINE_Y1, START_LINE_Y2 = int(163 * H / ORIG_H), int(415 * H / ORIG_H)
START_LINE_RECT = pygame.Rect(
    START_LINE_X1, START_LINE_Y1,
    START_LINE_X2 - START_LINE_X1, START_LINE_Y2 - START_LINE_Y1
)

# --- Raycast Function for AI Vision ---
def raycast(start_x, start_y, angle, collision_mask, W, H, max_dist=100, step=2):
    dir_x = math.cos(math.radians(angle))
    dir_y = -math.sin(math.radians(angle))
    for d in range(0, max_dist, step):
        px = start_x + dir_x * d
        py = start_y + dir_y * d
        if px < 0 or px >= W or py < 0 or py >= H:
            return max_dist
        if collision_mask.get_at((int(px), int(py))):
            return d
    return max_dist

# --- Format Time Function ---
def format_time(ms):
    seconds = ms // 1000
    minutes = seconds // 60
    seconds = seconds % 60
    milliseconds = ms % 1000
    return f"{minutes:02d}:{seconds:02d}.{milliseconds:03d}"

# --- Car Class Definition ---
class Car(pygame.sprite.Sprite):
    def __init__(self, x, y, angle, image, is_ai=False, name="Player", color=(255, 255, 255)):
        super().__init__()
        self.original_image = image
        self.image = image
        self.rect = self.image.get_rect(center=(x, y))
        self.x, self.y = float(x), float(y)
        self.angle = float(angle)
        self.vx, self.vy = 0.0, 0.0
        
        # Physics parameters (set via GAME_SETTINGS in reset_game or initialization)
        self.thrust = 0.1
        self.drag = 0.985
        self.MAX_SPEED = 15.0
        self.base_turn_rate = 3.5
        self.turn_speed_factor = 0.2
        self.steer_response = 0.4
        self.grip_factor = 1.0
        
        # Initialize effective parameters
        self.effective_thrust = self.thrust
        self.effective_max_speed = self.MAX_SPEED
        self.effective_base_turn_rate = self.base_turn_rate
        
        self.speed_limit = 1.0
        self.is_ai = is_ai
        self.name = name
        self.color = color
        self.waypoint_index = 0
        
        # Steering parameters
        self.current_steer = 0.0
        self.max_steer = 1.0
        
        # Lap tracking
        self.lap = 0
        self.crossed_line = False
        self.current_lap_start = pygame.time.get_ticks()
        self.current_lap_time = 0
        self.best_lap_time = float('inf')
        self.last_lap_time = 0
        self.mask = None
        self.rotate_and_update_rect()
        self.offset = random.uniform(-20, 20) if is_ai else 0
        
        # Randomness and damage
        self.variance_factor = 0.0  # Set via GAME_SETTINGS
        self.damage = 0.0
        self.damage_recovery_rate = GAME_SETTINGS["DAMAGE_RECOVERY_PER_FRAME"]
        self.clean_lap_bonus_recovery = GAME_SETTINGS["CLEAN_LAP_BONUS_RECOVERY"]
        self.lap_damage_increase = 0.0

    def apply_random_variations(self):
        if self.variance_factor == 0:
            return
        def vary(value):
            return value * random.uniform(1 - self.variance_factor, 1 + self.variance_factor)
        self.thrust = vary(self.thrust)
        self.drag = vary(self.drag)
        self.MAX_SPEED = vary(self.MAX_SPEED)
        self.base_turn_rate = vary(self.base_turn_rate)
        self.turn_speed_factor = vary(self.turn_speed_factor)
        self.steer_response = vary(self.steer_response)
        self.grip_factor = vary(self.grip_factor)
        self.effective_thrust = self.thrust
        self.effective_max_speed = self.MAX_SPEED
        self.effective_base_turn_rate = self.base_turn_rate

    def apply_damage_debuffs(self):
        if not GAME_SETTINGS["DAMAGE_ENABLED"]:
            self.effective_thrust = self.thrust
            self.effective_max_speed = self.MAX_SPEED
            self.effective_base_turn_rate = self.base_turn_rate
            return
        thresholds = GAME_SETTINGS["DAMAGE_DEBUFF_THRESHOLDS"]
        if self.damage < thresholds[0]:
            debuff_factor = 1.0
        elif self.damage < thresholds[1]:
            debuff_factor = 0.95
        elif self.damage < thresholds[2]:
            debuff_factor = 0.85
        else:
            debuff_factor = 0.70
        self.effective_thrust = self.thrust * debuff_factor
        self.effective_max_speed = self.MAX_SPEED * debuff_factor
        self.effective_base_turn_rate = self.base_turn_rate * debuff_factor

    def rotate_and_update_rect(self):
        self.image = pygame.transform.rotate(self.original_image, self.angle)
        self.rect = self.image.get_rect(center=(self.x, self.y))
        self.mask = pygame.mask.from_surface(self.image)

    def update_waypoint(self):
        target_waypoint = WAYPOINTS[self.waypoint_index]
        dx = target_waypoint[0] - self.x
        dy = target_waypoint[1] - self.y
        if math.hypot(dx, dy) < 150:
            self.waypoint_index = (self.waypoint_index + 1) % len(WAYPOINTS)

    def apply_collision(self, collision_mask):
        offset = (int(self.rect.left), int(self.rect.top))
        overlap = collision_mask.overlap(self.mask, offset)
        if overlap:
            self.speed_limit = 0.1
            self.grip_factor = max(0.3, self.grip_factor - 0.05)
            if GAME_SETTINGS["DAMAGE_ENABLED"]:
                self.damage += GAME_SETTINGS["WALL_DAMAGE_PER_FRAME"]
                self.lap_damage_increase += GAME_SETTINGS["WALL_DAMAGE_PER_FRAME"]
                self.damage = min(100, self.damage)
        else:
            self.speed_limit = min(1.0, self.speed_limit + 0.02)
            self.grip_factor = min(1.0, self.grip_factor + 0.03)
        current_speed = math.hypot(self.vx, self.vy)
        self.apply_damage_debuffs()
        max_allowed = self.effective_max_speed * self.speed_limit
        if current_speed > max_allowed:
            scale = max_allowed / current_speed
            self.vx *= scale
            self.vy *= scale

    def update_physics(self, keys=None):
        self.apply_damage_debuffs()
        if not self.is_ai and keys:
            target_steer = 0.0
            if keys[pygame.K_LEFT]:
                target_steer += self.max_steer
            if keys[pygame.K_RIGHT]:
                target_steer -= self.max_steer
            self.current_steer += (target_steer - self.current_steer) * self.steer_response
            speed = math.hypot(self.vx, self.vy)
            effective_turn_rate = (self.effective_base_turn_rate * self.grip_factor) / (1 + speed * self.turn_speed_factor)
            self.angle += self.current_steer * effective_turn_rate
            if keys[pygame.K_LCTRL]:
                self.vx += math.cos(math.radians(self.angle)) * self.effective_thrust
                self.vy -= math.sin(math.radians(self.angle)) * self.effective_thrust
            if keys[pygame.K_SPACE]:
                self.vx -= math.cos(math.radians(self.angle)) * self.effective_thrust
                self.vy += math.sin(math.radians(self.angle)) * self.effective_thrust

        speed = math.hypot(self.vx, self.vy)
        heading_x = math.cos(math.radians(self.angle))
        heading_y = -math.sin(math.radians(self.angle))
        if speed < 2.0:
            self.vx = heading_x * speed
            self.vy = heading_y * speed
        else:
            align_strength = 0.05
            self.vx += (heading_x * speed - self.vx) * align_strength
            self.vy += (heading_y * speed - self.vy) * align_strength

        self.x += self.vx
        self.y += self.vy
        self.vx *= self.drag
        self.vy *= self.drag
        self.rotate_and_update_rect()
        
        if GAME_SETTINGS["HEALING_ENABLED"]:
            self.damage = max(0, self.damage - self.damage_recovery_rate)

    def steer_ai(self, other_cars):
        self.apply_damage_debuffs()
        target_waypoint = WAYPOINTS[self.waypoint_index]
        target_x = target_waypoint[0] + self.offset
        target_y = target_waypoint[1]
        dx = target_x - self.x
        dy = target_y - self.y
        target_angle = math.degrees(math.atan2(-dy, dx))
        angle_diff = (target_angle - self.angle + 180) % 360 - 180
        steering_rate = 2.5
        if angle_diff > steering_rate:
            self.angle += steering_rate
        elif angle_diff < -steering_rate:
            self.angle -= steering_rate
        else:
            self.angle = target_angle

        avoidance_steer = 0
        for other_car in other_cars:
            if other_car == self:
                continue
            odx = other_car.x - self.x
            ody = other_car.y - self.y
            dist = math.hypot(odx, ody)
            if dist < 80 and dist > 0:
                rel_angle = math.degrees(math.atan2(-ody, odx)) - self.angle
                rel_angle = (rel_angle + 180) % 360 - 180
                closeness = (80 - dist) / 80
                steer_away = -math.copysign(1, rel_angle) * closeness * 4.0
                avoidance_steer += steer_away

        self.angle += avoidance_steer

        thresh = 60
        max_d = thresh
        step = 1
        left_dist = raycast(self.x, self.y, self.angle + 30, collision_mask, W, H, max_dist=max_d, step=step)
        right_dist = raycast(self.x, self.y, self.angle - 30, collision_mask, W, H, max_dist=max_d, step=step)
        front_dist = raycast(self.x, self.y, self.angle, collision_mask, W, H, max_dist=max_d, step=step)

        wall_avoidance_steer = 0
        steer_strength = 3.0
        if left_dist < thresh:
            closeness = (thresh - left_dist) / thresh
            wall_avoidance_steer -= closeness * steer_strength
        if right_dist < thresh:
            closeness = (thresh - right_dist) / thresh
            wall_avoidance_steer += closeness * steer_strength
        self.angle += wall_avoidance_steer

        accel_factor = 1.0
        if front_dist < thresh:
            accel_factor = 0.5 + 0.5 * (front_dist / thresh)

        current_speed = math.hypot(self.vx, self.vy)
        target_speed = WAYPOINTS[self.waypoint_index][2]
        next_index = (self.waypoint_index + 1) % len(WAYPOINTS)
        next_speed = WAYPOINTS[next_index][2]
        dist_to_waypoint = math.hypot(dx, dy)
        blend_factor = max(0, min(1, dist_to_waypoint / 150))
        target_speed = target_speed * blend_factor + next_speed * (1 - blend_factor)

        speed_accel_factor = 1.0
        if current_speed > target_speed:
            speed_accel_factor = 0.0
            if current_speed > target_speed * 1.1:
                brake_strength = 0.3
                self.vx -= math.cos(math.radians(self.angle)) * brake_strength
                self.vy += math.sin(math.radians(self.angle)) * brake_strength
        elif current_speed < target_speed * 0.9:
            speed_accel_factor = 1.0
        else:
            speed_accel_factor = 0.5

        effective_accel = min(accel_factor, speed_accel_factor)
        self.vx += math.cos(math.radians(self.angle)) * self.effective_thrust * effective_accel
        self.vy -= math.sin(math.radians(self.angle)) * self.effective_thrust * effective_accel

# --- Car-to-Car Collision Handling ---
def apply_car_collisions(cars):
    for i, car1 in enumerate(cars):
        for car2 in cars[i+1:]:
            offset = (int(car2.rect.left - car1.rect.left), int(car2.rect.top - car1.rect.top))
            if car1.mask.overlap(car2.mask, offset):
                if GAME_SETTINGS["DAMAGE_ENABLED"]:
                    car1.damage += GAME_SETTINGS["CAR_COLLISION_DAMAGE"]
                    car2.damage += GAME_SETTINGS["CAR_COLLISION_DAMAGE"]
                    car1.lap_damage_increase += GAME_SETTINGS["CAR_COLLISION_DAMAGE"]
                    car2.lap_damage_increase += GAME_SETTINGS["CAR_COLLISION_DAMAGE"]
                    car1.damage = min(100, car1.damage)
                    car2.damage = min(100, car2.damage)
                
                dx = car2.x - car1.x
                dy = car2.y - car1.y
                dist = math.hypot(dx, dy)
                if dist == 0:
                    dist = 1
                    dx = random.uniform(-1, 1)
                    dy = random.uniform(-1, 1)
                overlap = 40 - dist
                if overlap > 0:
                    push_x = (dx / dist) * (overlap / 2)
                    push_y = (dy / dist) * (overlap / 2)
                    car1.x -= push_x
                    car1.y -= push_y
                    car2.x += push_x
                    car2.y += push_y
                    car1.rotate_and_update_rect()
                    car2.rotate_and_update_rect()

                rel_vx = car1.vx - car2.vx
                rel_vy = car1.vy - car2.vy
                proj = (rel_vx * dx + rel_vy * dy) / (dist ** 2)
                impulse_x = proj * dx
                impulse_y = proj * dy
                bounciness = 0.8
                car1.vx -= bounciness * impulse_x
                car1.vy -= bounciness * impulse_y
                car2.vx += bounciness * impulse_x
                car2.vy += bounciness * impulse_y

                car1.speed_limit = max(0.4, car1.speed_limit - 0.15)
                car2.speed_limit = max(0.4, car2.speed_limit - 0.15)

# --- Create Checkered Line Surface ---
def create_finish_line_surface(rect):
    surface = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
    checker_size = 10
    for x in range(0, rect.width, checker_size):
        for y in range(0, rect.height, checker_size):
            color = (255, 255, 255) if ((x // checker_size) + (y // checker_size)) % 2 == 0 else (0, 0, 0)
            pygame.draw.rect(surface, color, (x, y, checker_size, checker_size))
    return surface

# --- Lap Check ---
def check_lap_crossing(car, num_laps, game_mode):
    in_zone = START_LINE_RECT.collidepoint(car.x, car.y)
    if in_zone and not car.crossed_line:
        current_time = pygame.time.get_ticks()
        car.current_lap_time = current_time - car.current_lap_start
        if car.lap > 0:
            car.last_lap_time = car.current_lap_time
            if car.current_lap_time < car.best_lap_time:
                car.best_lap_time = car.current_lap_time
        car.lap += 1
        car.current_lap_start = current_time
        car.crossed_line = True
        
        if GAME_SETTINGS["HEALING_ENABLED"] and car.lap > 0 and car.lap_damage_increase == 0:
            car.damage = max(0, car.damage - car.clean_lap_bonus_recovery)
        car.lap_damage_increase = 0.0
        
        if game_mode == "race" and car.lap > num_laps:
            return car.name
    elif not in_zone:
        car.crossed_line = False
    return None

# --- Reset Game Function ---
def reset_game(game_mode):
    base_x, base_y = 700 * W / ORIG_W, 300 * H / ORIG_H
    grid_offsets = [
        (-40 * W / ORIG_W, 40 * H / ORIG_H),
        (40 * W / ORIG_W, 20 * H / ORIG_H),
        (-40 * W / ORIG_W, -20 * H / ORIG_H),
        (40 * W / ORIG_W, -40 * H / ORIG_H),
    ]
    if game_mode == "practice":
        grid_offsets = [
            (0, 0),
            (0, -50 * H / ORIG_H),
            (0, -100 * H / ORIG_H),
            (0, -150 * H / ORIG_H),
        ]

    player_car.x, player_car.y = base_x + grid_offsets[0][0], base_y + grid_offsets[0][1]
    player_car.angle = 180.0
    player_car.vx, player_car.vy = 0.0, 0.0
    player_car.speed_limit = 1.0
    player_car.thrust = GAME_SETTINGS["PLAYER_THRUST"]
    player_car.drag = GAME_SETTINGS["PLAYER_DRAG"]
    player_car.MAX_SPEED = GAME_SETTINGS["PLAYER_MAX_SPEED"]
    player_car.base_turn_rate = GAME_SETTINGS["PLAYER_BASE_TURN_RATE"]
    player_car.turn_speed_factor = GAME_SETTINGS["PLAYER_TURN_SPEED_FACTOR"]
    player_car.steer_response = GAME_SETTINGS["PLAYER_STEER_RESPONSE"]
    player_car.grip_factor = GAME_SETTINGS["PLAYER_GRIP_FACTOR"]
    player_car.variance_factor = GAME_SETTINGS["PLAYER_RANDOMNESS"]
    player_car.apply_random_variations()
    player_car.lap = 0
    player_car.crossed_line = False
    player_car.current_lap_start = pygame.time.get_ticks()
    player_car.current_lap_time = 0
    player_car.best_lap_time = float('inf')
    player_car.last_lap_time = 0
    player_car.waypoint_index = 0
    player_car.damage = 0.0
    player_car.lap_damage_increase = 0.0
    player_car.rotate_and_update_rect()

    for i, ai_car in enumerate(ai_cars):
        ai_car.x, ai_car.y = base_x + grid_offsets[i+1][0], base_y + grid_offsets[i+1][1]
        ai_car.angle = 180.0
        ai_car.vx, ai_car.vy = 0.0, 0.0
        ai_car.speed_limit = 1.0
        ai_car.thrust = GAME_SETTINGS["AI_THRUSTS"][i]
        ai_car.drag = GAME_SETTINGS["AI_DRAGS"][i]
        ai_car.MAX_SPEED = GAME_SETTINGS["AI_MAX_SPEEDS"][i]
        ai_car.base_turn_rate = GAME_SETTINGS["AI_BASE_TURN_RATES"][i]
        ai_car.turn_speed_factor = GAME_SETTINGS["AI_TURN_SPEED_FACTORS"][i]
        ai_car.steer_response = GAME_SETTINGS["AI_STEER_RESPONSES"][i]
        ai_car.grip_factor = GAME_SETTINGS["AI_GRIP_FACTORS"][i]
        ai_car.variance_factor = GAME_SETTINGS["AI_RANDOMNESS"][i]
        ai_car.apply_random_variations()
        ai_car.lap = 0
        ai_car.crossed_line = False
        ai_car.current_lap_start = pygame.time.get_ticks()
        ai_car.current_lap_time = 0
        ai_car.best_lap_time = float('inf')
        ai_car.last_lap_time = 0
        ai_car.waypoint_index = 0
        ai_car.offset = random.uniform(-20, 20)
        ai_car.damage = 0.0
        ai_car.lap_damage_increase = 0.0
        ai_car.rotate_and_update_rect()

# --- Game Initialization ---
player_car = Car(
    700 * W / ORIG_W, 300 * H / ORIG_H, 180.0, player_ship_img,
    is_ai=False, name="Marlowe", color=(255, 255, 255)
)
player_car.thrust = GAME_SETTINGS["PLAYER_THRUST"]
player_car.drag = GAME_SETTINGS["PLAYER_DRAG"]
player_car.MAX_SPEED = GAME_SETTINGS["PLAYER_MAX_SPEED"]
player_car.base_turn_rate = GAME_SETTINGS["PLAYER_BASE_TURN_RATE"]
player_car.turn_speed_factor = GAME_SETTINGS["PLAYER_TURN_SPEED_FACTOR"]
player_car.steer_response = GAME_SETTINGS["PLAYER_STEER_RESPONSE"]
player_car.grip_factor = GAME_SETTINGS["PLAYER_GRIP_FACTOR"]
player_car.variance_factor = GAME_SETTINGS["PLAYER_RANDOMNESS"]
player_car.apply_random_variations()

ai_colors = [(50, 50, 255), (50, 255, 50), (255, 50, 50)]
ai_cars = []
for i, color in enumerate(ai_colors):
    ai_img = player_ship_img.copy()
    ai_img.fill((*color, 255), special_flags=pygame.BLEND_RGBA_MULT)
    ai_car = Car(
        700 * W / ORIG_W, 250 * H / ORIG_H - i*50, 180.0, ai_img,
        is_ai=True, name=f"AI{i+1}", color=color
    )
    ai_car.thrust = GAME_SETTINGS["AI_THRUSTS"][i]
    ai_car.drag = GAME_SETTINGS["AI_DRAGS"][i]
    ai_car.MAX_SPEED = GAME_SETTINGS["AI_MAX_SPEEDS"][i]
    ai_car.base_turn_rate = GAME_SETTINGS["AI_BASE_TURN_RATES"][i]
    ai_car.turn_speed_factor = GAME_SETTINGS["AI_TURN_SPEED_FACTORS"][i]
    ai_car.steer_response = GAME_SETTINGS["AI_STEER_RESPONSES"][i]
    ai_car.grip_factor = GAME_SETTINGS["AI_GRIP_FACTORS"][i]
    ai_car.variance_factor = GAME_SETTINGS["AI_RANDOMNESS"][i]
    ai_car.apply_random_variations()
    ai_cars.append(ai_car)

all_sprites = pygame.sprite.Group(player_car, *ai_cars)
font = pygame.font.SysFont(None, 24)
big_font = pygame.font.SysFont(None, 100)
medium_font = pygame.font.SysFont(None, 36)
finish_line_surface = create_finish_line_surface(START_LINE_RECT)

# Game states and variables
state = "menu"
game_mode = "practice"
num_laps = 0
menu_options = ["Practice", "Race", "Quit"]
lap_options = [3, 5, 10, 20]
selected_option = 0
selected_lap = 1
countdown_start = 0
winner = None

# --- Main Loop ---
running = True
while running:
    keys = pygame.key.get_pressed()

    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            running = False
        if e.type == pygame.KEYDOWN:
            if e.key == pygame.K_ESCAPE:
                state = "menu"
                winner = None
            if state == "menu":
                if e.key == pygame.K_UP:
                    selected_option = (selected_option - 1) % len(menu_options)
                if e.key == pygame.K_DOWN:
                    selected_option = (selected_option + 1) % len(menu_options)
                if e.key in (pygame.K_RETURN, pygame.K_SPACE):
                    if selected_option == 0:
                        game_mode = "practice"
                        num_laps = 0
                        reset_game(game_mode)
                        state = "racing"
                    elif selected_option == 1:
                        state = "lap_select"
                    elif selected_option == 2:
                        running = False
            elif state == "lap_select":
                if e.key == pygame.K_UP:
                    selected_lap = (selected_lap - 1) % len(lap_options)
                if e.key == pygame.K_DOWN:
                    selected_lap = (selected_lap + 1) % len(lap_options)
                if e.key in (pygame.K_RETURN, pygame.K_SPACE):
                    game_mode = "race"
                    num_laps = lap_options[selected_lap]
                    reset_game(game_mode)
                    state = "countdown"
                    countdown_start = pygame.time.get_ticks()
            elif state == "race_end":
                if e.key in (pygame.K_RETURN, pygame.K_SPACE):
                    state = "menu"
                    winner = None

    if state == "countdown":
        elapsed = pygame.time.get_ticks() - countdown_start
        if elapsed >= 3000:
            state = "racing"

    if state == "racing":
        all_cars = [player_car] + ai_cars
        for ai_car in ai_cars:
            ai_car.steer_ai(all_cars)

        for car in all_sprites:
            if car.is_ai:
                car.update_physics()
            else:
                car.update_physics(keys)
            car.apply_collision(collision_mask)

        apply_car_collisions(all_cars)

        for car in all_cars:
            car.update_waypoint()

        if game_mode == "race":
            for car in all_cars:
                win = check_lap_crossing(car, num_laps, game_mode)
                if win:
                    winner = win
                    state = "race_end"
                    break
        else:
            for car in all_cars:
                check_lap_crossing(car, num_laps, game_mode)

    # --- Drawing ---
    screen.fill((80, 80, 80))

    if state == "menu":
        welcome_text = big_font.render("Welcome to Max Racing!", True, (255, 255, 255))
        screen.blit(welcome_text, (W // 2 - welcome_text.get_width() // 2, H // 4))
        for i, option in enumerate(menu_options):
            text = option if i != 1 else f"Race ({lap_options[selected_lap]} Laps)"
            color = (0, 255, 0) if i == selected_option else (255, 255, 255)
            option_text = font.render(text, True, color)
            screen.blit(option_text, (W // 2 - option_text.get_width() // 2, H // 2 + i * 40))

    elif state == "lap_select":
        title_text = big_font.render("Select Number of Laps", True, (255, 255, 255))
        screen.blit(title_text, (W // 2 - title_text.get_width() // 2, H // 4))
        for i, lap in enumerate(lap_options):
            color = (0, 255, 0) if i == selected_lap else (255, 255, 255)
            lap_text = font.render(f"{lap} Lap{'s' if lap > 1 else ''}", True, color)
            screen.blit(lap_text, (W // 2 - lap_text.get_width() // 2, H // 2 + i * 40))

    elif state == "countdown":
        elapsed = pygame.time.get_ticks() - countdown_start
        if elapsed < 1000:
            text = "Ready"
        elif elapsed < 2000:
            text = "Set"
        else:
            text = "Go"
        countdown_text = big_font.render(text, True, (255, 255, 0))
        screen.blit(track_img, (0, 0))
        screen.blit(finish_line_surface, (START_LINE_X1, START_LINE_Y1))
        all_sprites.draw(screen)
        screen.blit(countdown_text, (W // 2 - countdown_text.get_width() // 2, H // 2))

    elif state == "racing":
        screen.blit(track_img, (0, 0))
        screen.blit(finish_line_surface, (START_LINE_X1, START_LINE_Y1))
        all_sprites.draw(screen)

        player_speed = math.hypot(player_car.vx, player_car.vy)
        cube_color = (255, 0, 0) if player_car.speed_limit < 1.0 else (0, 255, 0)
        pygame.draw.rect(screen, cube_color, (10, 10, 20, 20))
        speed_pct = (player_speed / player_car.MAX_SPEED) * 100
        text = font.render(f"P1 Speed: {speed_pct:5.1f}% ({player_speed:4.1f})", True, (255, 255, 255))
        screen.blit(text, (40, 10))
        player_current = pygame.time.get_ticks() - player_car.current_lap_start
        screen.blit(font.render(f"Player Lap: {player_car.lap}{'/' + str(num_laps) if game_mode == 'race' else ''}", True, (255, 255, 255)), (40, 40))
        screen.blit(font.render(f"Current Lap: {format_time(player_current)}", True, (255, 255, 255)), (40, 70))
        screen.blit(font.render(
            f"Last Lap: {format_time(player_car.last_lap_time) if player_car.last_lap_time > 0 else '--:--.---'}",
            True, (255, 255, 255)), (40, 100))
        screen.blit(font.render(
            f"Best Lap: {format_time(player_car.best_lap_time) if player_car.best_lap_time != float('inf') else '--:--.---'}",
            True, (255, 255, 255)), (40, 130))
        screen.blit(font.render(f"Damage: {int(player_car.damage)}%", True, (255, 0, 0)), (40, 160))

        leaderboard_y = 10
        screen.blit(font.render("Leaderboard:", True, (255, 255, 255)), (W - 200, leaderboard_y))
        leaderboard_y += 30
        all_cars = sorted(
            [player_car] + ai_cars,
            key=lambda c: (
                -c.lap,
                -c.waypoint_index,
                math.hypot(c.x - WAYPOINTS[c.waypoint_index][0], c.y - WAYPOINTS[c.waypoint_index][1])
            )
        )
        for i, car in enumerate(all_cars):
            lap_str = f"{i+1}. {car.name}: {car.lap}{'/' + str(num_laps) if game_mode == 'race' else ''}"
            screen.blit(font.render(lap_str, True, car.color), (W - 200, leaderboard_y + i * 20))
        
    elif state == "race_end":
        screen.blit(track_img, (0, 0))
        screen.blit(finish_line_surface, (START_LINE_X1, START_LINE_Y1))
        all_sprites.draw(screen)

        overlay = pygame.Surface((W, H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 128))
        screen.blit(overlay, (0, 0))

        winner_text = big_font.render(f"{winner} Wins!", True, (255, 255, 0))
        screen.blit(winner_text, (W // 2 - winner_text.get_width() // 2, H // 3 - 50))

        standings_text = medium_font.render("Race Standings", True, (255, 255, 255))
        screen.blit(standings_text, (W // 2 - standings_text.get_width() // 2, H // 3 + 50))

        screen.blit(font.render("Pos  Driver    Best Lap    Last Lap", True, (255, 255, 255)),
                    (W // 2 - 200, H // 3 + 100))
        screen.blit(font.render("-" * 40, True, (255, 255, 255)),
                    (W // 2 - 200, H // 3 + 120))

        cars = sorted(
            [player_car] + ai_cars,
            key=lambda c: (
                -c.lap,
                -c.waypoint_index,
                math.hypot(c.x - WAYPOINTS[c.waypoint_index][0], c.y - WAYPOINTS[c.waypoint_index][1])
            )
        )

        y_offset = 140
        for i, car in enumerate(cars, start=1):
            best = format_time(car.best_lap_time) if car.best_lap_time != float('inf') else '--:--.---'
            last = format_time(car.last_lap_time) if car.last_lap_time > 0 else '--:--.---'
            line = f"{i:>2}. {car.name:<8}  {best}    {last}"
            screen.blit(font.render(line, True, car.color),
                        (W // 2 - 200, H // 3 + y_offset))
            y_offset += 20

        prompt_text = font.render("Press ENTER to return to menu", True, (255, 255, 255))
        screen.blit(prompt_text, (W // 2 - prompt_text.get_width() // 2, H // 3 + y_offset + 20))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()

