import pygame, sys, math
pygame.init()

# --- Window setup ---
W, H = 800, 600
screen = pygame.display.set_mode((W, H))
pygame.display.set_caption("Pole Position Road")
clock = pygame.time.Clock()

# --- Road parameters ---
road_width = 2000
seg_height = 10
camera_depth = 0.84
position = 0
speed = 200
horizon = int(H * 0.55)

def project(y, camera_height=1500):
    """Simple perspective projection from pseudo-3D to screen Y"""
    return horizon + int(camera_height / (y + 1))

def draw_segment(i, color_left, color_right, color_road, curve):
    # simulate distance into the screen
    z1 = i * seg_height + position
    z2 = (i + 1) * seg_height + position
    if z2 == 0: z2 = 1

    x1 = math.sin(curve + z1 * 0.0015) * 1200
    x2 = math.sin(curve + z2 * 0.0015) * 1200

    y1 = project(z1)
    y2 = project(z2)

    scale1 = camera_depth / (z1 if z1 else 1)
    scale2 = camera_depth / (z2 if z2 else 1)

    road_w1 = road_width * scale1
    road_w2 = road_width * scale2

    # road
    pygame.draw.polygon(screen, color_road, [
        (W/2 - road_w1 + x1, y1),
        (W/2 + road_w1 + x1, y1),
        (W/2 + road_w2 + x2, y2),
        (W/2 - road_w2 + x2, y2)
    ])

    # curbs
    curb_w1 = road_w1 * 0.03
    curb_w2 = road_w2 * 0.03
    pygame.draw.polygon(screen, color_left, [
        (W/2 - road_w1 - curb_w1 + x1, y1),
        (W/2 - road_w1 + x1, y1),
        (W/2 - road_w2 + x2, y2),
        (W/2 - road_w2 - curb_w2 + x2, y2)
    ])
    pygame.draw.polygon(screen, color_right, [
        (W/2 + road_w1 + x1, y1),
        (W/2 + road_w1 + curb_w1 + x1, y1),
        (W/2 + road_w2 + curb_w2 + x2, y2),
        (W/2 + road_w2 + x2, y2)
    ])

def draw_road():
    global position
    position += speed * 0.016
    if position >= seg_height:
        position -= seg_height

    # background
    screen.fill((90, 200, 255))  # sky
    pygame.draw.rect(screen, (0, 180, 0), (0, horizon, W, H - horizon))  # grass

    # draw from farthest to nearest
    for i in range(60, 0, -1):
        color_road = (50, 50, 50)
        if (i // 3) % 2 == 0:
            color_left, color_right = (255, 0, 0), (255, 255, 255)
        else:
            color_left, color_right = (255, 255, 255), (255, 0, 0)

        curve = math.sin(position * 0.001) * 2.0  # gentle sway
        draw_segment(i, color_left, color_right, color_road, curve)

# --- Main loop ---
running = True
while running:
    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            running = False

    draw_road()
    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()
