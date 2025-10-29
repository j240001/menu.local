import pygame, math, sys

pygame.init()

# --- setup ---
screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
W, H = screen.get_size()
pygame.display.set_caption("F1 Car with Collision + AI Opponent")
clock = pygame.time.Clock()

# --- Image Loading & Setup ---
try:
    player_ship_img = pygame.image.load("car.png").convert_alpha()
    # Load and scale the track image. It is crucial it is converted with alpha.
    track_img_original = pygame.image.load("track.png").convert_alpha()
    track_img = pygame.transform.smoothscale(track_img_original, (W, H))
except pygame.error as e:
    print(f"Error loading images: {e}. Using simple placeholder.")
    # Fallback Car
    player_ship_img = pygame.Surface((50, 30), pygame.SRCALPHA)
    pygame.draw.rect(player_ship_img, (220, 0, 0), (0, 0, 50, 30), 0, 5)
    # Placeholder Track: Gray road with Black borders (for collision testing)
    track_img = pygame.Surface((W, H), pygame.SRCALPHA)
    pygame.draw.rect(track_img, (0, 0, 0), (0, 0, W, H), 50) # Black borders (Collision color)


# --- Static Collision Mask Setup (The Fix!) ---
# Since the track image is transparent where the road is, 
# pygame.mask.from_surface will ONLY include the opaque (black) collision areas.
collision_mask = pygame.mask.from_surface(track_img)


# --- AI Waypoints ---
# IMPORTANT: Adjusted to run COUNTER-CLOCKWISE (CCW).
# Waypoints are now defined in CCW order starting from the right side.
WAYPOINTS = [
    (560, 250),         # Start/Finish
    (440, 270), 
    (355, 280),
    (275, 310),
    (235, 365),
    (180, 425),
    (155, 525),
    (150, 640),
    (200, 750),
    (280, 830),
    (380, 890),
    (500, 920),
    (630, 930),
    (760, 930),
    (880, 930),
    (990, 930),
    (1120, 930),
    (1230, 925),
    (1350, 920),
    (1460, 910),
    (1580, 870),
    (1660, 780),
    (1725, 670),
    (1775, 565),
    (1810, 460),
    (1805, 350),
    (1750, 270),
    (1660, 230),
    (1560, 245),
    (1515, 300),
    (1480, 365),
    (1405, 445),
    (1300, 500),
    (1215, 500),
    (1160, 480),
    (1115, 440),
    (1060, 370),
    (950, 310),
    (840, 270),
    (740, 260),
    (650, 255),
    (560, 250),      # Back to start
]

# --- Raycast Function for AI Vision ---
def raycast(start_x, start_y, angle, collision_mask, W, H, max_dist=100, step=2):
    dir_x = math.cos(math.radians(angle))
    dir_y = -math.sin(math.radians(angle))
    for d in range(0, max_dist, step):
        px = start_x + dir_x * d
        py = start_y + dir_y * d
        if px < 0 or px >= W or py < 0 or py >= H:
            return max_dist  # Out of bounds, treat as no wall
        if collision_mask.get_at((int(px), int(py))):
            return d  # Hit wall
    return max_dist  # No hit

# --- Car Class Definition ---
class Car(pygame.sprite.Sprite):
    def __init__(self, x, y, angle, image, is_ai=False):
        super().__init__()
        self.original_image = image
        self.image = image
        self.rect = self.image.get_rect(center=(x, y))
        self.x, self.y = float(x), float(y)
        self.angle = float(angle)
        self.vx, self.vy = 0.0, 0.0
        self.thrust = 0.45
        self.drag = 0.980
        self.MAX_SPEED = 8.5
        self.speed_limit = 1.0
        self.is_ai = is_ai
        self.waypoint_index = 0
        
        # FIX 1: Ensure mask is created immediately upon initialization
        self.mask = None 
        self.rotate_and_update_rect() 


    def rotate_and_update_rect(self):
        # Rotate image and update rect/mask for collision check
        self.image = pygame.transform.rotate(self.original_image, self.angle)
        self.rect = self.image.get_rect(center=(self.x, self.y))
        # Recalculate mask for the rotated image (MUST happen here)
        self.mask = pygame.mask.from_surface(self.image) 

    def apply_collision(self, collision_mask):
        # 1. Check Collision
        offset = (int(self.rect.left), int(self.rect.top))
        
        # The fix relies on self.mask being properly calculated in rotate_and_update_rect
        if collision_mask.overlap(self.mask, offset):
            self.speed_limit = 0.1 # Slow down severely on impact
        else:
            self.speed_limit = min(1.0, self.speed_limit + 0.02) # Recover speed gradually
        
        # 2. Apply Speed Limit
        current_speed = math.hypot(self.vx, self.vy)
        max_allowed = self.MAX_SPEED * self.speed_limit
        if current_speed > max_allowed:
            scale = max_allowed / current_speed
            self.vx *= scale
            self.vy *= scale

    def update_physics(self, keys=None):
        
        # --- Apply Player Input (if not AI) ---
        if not self.is_ai and keys:
            # Steering 
            if keys[pygame.K_LEFT]:
                self.angle += 4
            if keys[pygame.K_RIGHT]:
                self.angle -= 4
            
            # Acceleration
            if keys[pygame.K_LCTRL]:
                self.vx += math.cos(math.radians(self.angle)) * self.thrust
                self.vy -= math.sin(math.radians(self.angle)) * self.thrust
            
            # Braking/Reverse
            if keys[pygame.K_SPACE]:
                self.vx -= math.cos(math.radians(self.angle)) * self.thrust
                self.vy += math.sin(math.radians(self.angle)) * self.thrust


        # --- Car Handling Logic ---
        speed = math.hypot(self.vx, self.vy)
        heading_x = math.cos(math.radians(self.angle))
        heading_y = -math.sin(math.radians(self.angle))

        # if moving slow, align velocity to facing direction
        if speed < 2.0:
            self.vx = heading_x * speed
            self.vy = heading_y * speed
        else:
            # blend a little toward facing direction for smoother control
            align_strength = 0.05
            self.vx += (heading_x * speed - self.vx) * align_strength
            self.vy += (heading_y * speed - self.vy) * align_strength

        # Motion and Drag
        self.x += self.vx
        self.y += self.vy
        self.vx *= self.drag
        self.vy *= self.drag

        # Update sprite properties (includes updating self.mask)
        self.rotate_and_update_rect()

    def steer_ai(self):
        target_waypoint = WAYPOINTS[self.waypoint_index]
        
        # 1. Calculate desired angle to the target
        dx = target_waypoint[0] - self.x
        dy = target_waypoint[1] - self.y
        target_angle = math.degrees(math.atan2(-dy, dx))
        
        # 2. Find the shortest turn direction (angle difference)
        angle_diff = (target_angle - self.angle + 180) % 360 - 180

        # 3. Steer toward waypoint
        steering_rate = 2.5 
        if angle_diff > steering_rate:
            self.angle += steering_rate
        elif angle_diff < -steering_rate:
            self.angle -= steering_rate
        else:
            self.angle = target_angle 

        # 4. Raycast for wall avoidance (vision)
        thresh = 60  # Avoidance threshold distance (tune this)
        max_d = thresh
        step = 1  # Smaller step for accuracy (but more CPU; 2-5 is faster)
        left_dist = raycast(self.x, self.y, self.angle + 30, collision_mask, W, H, max_dist=max_d, step=step)
        right_dist = raycast(self.x, self.y, self.angle - 30, collision_mask, W, H, max_dist=max_d, step=step)
        front_dist = raycast(self.x, self.y, self.angle, collision_mask, W, H, max_dist=max_d, step=step)

        # Calculate avoidance steering (steer away from close walls)
        avoidance_steer = 0
        steer_strength = 3.0  # How aggressively to steer away (tune this)
        if left_dist < thresh:
            closeness = (thresh - left_dist) / thresh
            avoidance_steer -= closeness * steer_strength  # Steer right (away from left wall)
        if right_dist < thresh:
            closeness = (thresh - right_dist) / thresh
            avoidance_steer += closeness * steer_strength  # Steer left (away from right wall)

        # Apply avoidance after waypoint steering
        self.angle += avoidance_steer

        # 5. Accelerate with slowdown if front wall is close
        accel_factor = 1.0
        if front_dist < thresh:
            accel_factor = 0.5 + 0.5 * (front_dist / thresh)  # Slow down (min 50% thrust)
        self.vx += math.cos(math.radians(self.angle)) * self.thrust * accel_factor
        self.vy -= math.sin(math.radians(self.angle)) * self.thrust * accel_factor

        # 6. Check if waypoint reached
        if math.hypot(dx, dy) < 150: # Tolerance radius
            self.waypoint_index = (self.waypoint_index + 1) % len(WAYPOINTS)


# --- Game Initialization ---
# Player car (CW direction)
player_car = Car(700, 300, 180.0, player_ship_img, is_ai=False)

# AI car (CCW direction)
ai_img = player_ship_img.copy()
ai_img.fill((50, 50, 255, 255), special_flags=pygame.BLEND_RGBA_MULT)
# Start the AI car slightly offset and pointing to the left (90 degrees)
ai_car = Car(700, 250, 180.0, ai_img, is_ai=True)
ai_car.drag = 0.990
ai_car.MAX_SPEED = 8.6 

all_sprites = pygame.sprite.Group(player_car, ai_car)
font = pygame.font.SysFont(None, 24)

# --- Main Game Loop ---
running = True
while running:
    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            running = False
        if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
            running = False

    # --- Input ---
    keys = pygame.key.get_pressed()
    
    # --- AI Control ---
    ai_car.steer_ai()
    
    # --- Update All Cars ---
    for car in all_sprites:
        # 1. Physics Update (moves car, applies drag, updates rotation/rect/mask)
        if car.is_ai:
            car.update_physics()
        else:
            car.update_physics(keys)
            
        # 2. Collision Check (using the static mask derived from the track's black areas)
        car.apply_collision(collision_mask)


    # --- Drawing ---
    screen.fill((80, 80, 80)) # Draw the road color (where the track is transparent)
    screen.blit(track_img, (0, 0)) # Overlay the track image (black walls)

    # Draw all cars
    all_sprites.draw(screen)

    # --- Debug UI (Player) ---
    player_speed = math.hypot(player_car.vx, player_car.vy)
    
    # Collision Indicator (based on player car's speed limit)
    player_collision_active = player_car.speed_limit < 1.0
    cube_color = (255, 0, 0) if player_collision_active else (0, 255, 0)
    pygame.draw.rect(screen, cube_color, (10, 10, 20, 20))

    # Speedometer
    speed_pct = (player_speed / player_car.MAX_SPEED) * 100
    text = font.render(f"P1 Speed: {speed_pct:5.1f}% ({player_speed:4.1f})", True, (255, 255, 255))
    screen.blit(text, (40, 10))
    
    # --- Debug UI (AI) ---
    ai_speed = math.hypot(ai_car.vx, ai_car.vy)
    ai_text = font.render(f"AI Speed: {ai_speed:4.1f} | Target WP: {ai_car.waypoint_index}", True, (0, 0, 255))
    screen.blit(ai_text, (W - 300, 10))


    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()
