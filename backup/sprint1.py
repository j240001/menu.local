import pygame, math, sys

pygame.init()

# --- setup ---
screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
W, H = screen.get_size()
pygame.display.set_caption("F1 Car with Collision + Speedometer")
clock = pygame.time.Clock()

# --- make an F1-style car sprite (pointing right = 0°) ---
# Use SRCALPHA so the mask is correctly generated from the shape, not the bounding box
ship_img = pygame.image.load("car.png").convert_alpha()


# --- Load your custom track image ---
track_img = pygame.image.load("track.png").convert_alpha()
track_img = pygame.transform.smoothscale(track_img, (W, H))  # resize if needed

collision_surface = track_img.copy()
collision_mask = pygame.mask.from_surface(collision_surface)


# --- initial state ---
x, y = W / 2, H / 2 - 250
angle = 180.
vx, vy = 0.0, 0.0
thrust = 0.45
drag = 0.980
MAX_SPEED = 19.0

font = pygame.font.SysFont(None, 24)
running = True
collision_active = False
speed_limit = 1.0

while running:
    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            running = False
        if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
            running = False

    # --- input ---
    keys = pygame.key.get_pressed()
    if keys[pygame.K_LEFT]:
        angle += 4
    if keys[pygame.K_RIGHT]:
        angle -= 4
    if keys[pygame.K_LCTRL]:
        vx += math.cos(math.radians(angle)) * thrust
        vy -= math.sin(math.radians(angle)) * thrust
    if keys[pygame.K_SPACE]:
        vx -= math.cos(math.radians(angle)) * thrust
        vy += math.sin(math.radians(angle)) * thrust

    # --- motion / car handling ---
    speed = math.hypot(vx, vy)
    heading_x = math.cos(math.radians(angle))
    heading_y = -math.sin(math.radians(angle))

    # if moving slow, align velocity to facing direction
    if speed < 2.0:  # tweak this threshold to taste
        vx = heading_x * speed
        vy = heading_y * speed
    else:
        # blend a little toward facing direction for smoother control
        align_strength = 0.04  # higher = snappier steering at speed
        vx += (heading_x * speed - vx) * align_strength
        vy += (heading_y * speed - vy) * align_strength

    # update position
    x += vx
    y += vy

    # natural drag / friction
    vx *= drag
    vy *= drag


    # wrap around edges (this bypasses collision, but is kept for the original logic)
    if x < -30: x = W + 30
    if x > W + 30: x = -30
    if y < -30: y = H + 30
    if y > H + 30: y = -30

    # draw background first
    screen.fill((80, 80, 80))  # light gray asphalt
    # then overlay your track sprite
    screen.blit(track_img, (0, 0))




    # --- mask-based collision check ---
    rotated = pygame.transform.rotate(ship_img, angle)
    ship_mask_rotated = pygame.mask.from_surface(rotated)
    rect = rotated.get_rect(center=(x, y))
    
    # FIX 2: The offset must be the positive top-left screen position of the rotated sprite.
    # It was incorrectly set to negative values before.
    offset = (int(rect.left), int(rect.top))

    collision_active = False
    # Check if the car's mask overlaps with the static wall mask
    if collision_mask.overlap(ship_mask_rotated, offset):
        collision_active = True
        speed_limit = 0.1 # Slow down severely
    else:
        # Gradually return to max speed limit
        speed_limit = min(1.0, speed_limit + 0.02)

    current_speed = math.hypot(vx, vy)
    max_allowed = MAX_SPEED * speed_limit
    
    # Apply speed limit
    if current_speed > max_allowed:
        scale = max_allowed / current_speed
        vx *= scale
        vy *= scale

    # --- draw car ---
    screen.blit(rotated, rect)

    # --- debug UI ---
    cube_color = (255, 0, 0) if collision_active else (0, 255, 0)
    pygame.draw.rect(screen, cube_color, (10, 10, 20, 20))

    speed = math.hypot(vx, vy)
    speed_pct = (speed / MAX_SPEED) * 100
    text = font.render(f"Speed: {speed_pct:5.1f}% ({speed:4.1f})", True, (255, 255, 255))
    screen.blit(text, (40, 10))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()
