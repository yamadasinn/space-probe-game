import pygame
import math
import sys
import os

# === 初期化 ===
pygame.init()
screen = pygame.display.set_mode((1000, 800))
pygame.display.set_caption("宇宙探査機ゲーム")
font = pygame.font.SysFont(None, 24)

# === 探査機の質量 ===
probe_mass = 600  # kg

# === 公転する惑星データ ===
planet_data = [
    ("S", 160, 0.03, 3000, (180, 180, 180), 0),
    ("K", 280, 0.025, 3500, (255, 160, 100), 0),
    ("T", 400, 0.02, 4000, (100, 200, 255), 0),
    ("A", 600, 0.017, 3800, (255, 100, 100), 0),
    ("M", 1000, 0.01, 9000, (200, 180, 140), 0),
    ("D", 1400, 0.008, 8000, (210, 180, 120), 0),
    ("O", 1800, 0.006, 7000, (150, 220, 220), 0),
    ("I", 2200, 0.005, 6800, (100, 150, 255), 0),
    ("U", 2600, 0.004, 2000, (200, 200, 255), 0)
]

# === 惑星の現在位置リスト ===
planets = []
for name, radius, speed, mass, color, angle_p in planet_data:
    angle_rad = angle_p
    x = radius * math.cos(angle_rad)
    y = radius * math.sin(angle_rad)
    planets.append({"name": name, "radius": radius, "speed": speed, "mass": mass, "color": color, "angle": angle_rad, "vx": 0, "vy": 0, "x": x, "y": y})

# === 地球の位置から探査機スタート ===
earth = next(p for p in planets if p["name"] == "T")
x, y = earth["x"], earth["y"]
vx = -8 * math.sin(earth["angle"])
vy = 8 * math.cos(earth["angle"])
angle = 0
zoom = 0.5

G = 0.1  # 重力定数
trajectory = []
clock = pygame.time.Clock()
running = True

# === 軌道円描画関数 ===
def draw_orbit_circle(screen, cam_x, cam_y, zoom, radius, color):
    points = []
    for deg in range(0, 360, 4):
        rad = math.radians(deg)
        x = radius * math.cos(rad)
        y = radius * math.sin(rad)
        sx = 500 + (x - cam_x) * zoom
        sy = 400 + (y - cam_y) * zoom
        if math.isfinite(sx) and math.isfinite(sy):
            points.append((int(sx), int(sy)))
    if len(points) > 1:
        pygame.draw.lines(screen, color, True, points, 1)

# === 軌道予測線と軌道要素描画 ===
def draw_predicted_trajectory():
    temp_x, temp_y = x, y
    temp_vx, temp_vy = vx, vy
    temp_traj = []

    future_planets = []
    for p in planets:
        future_planets.append({"radius": p["radius"], "angle": p["angle"], "speed": p["speed"], "mass": p["mass"]})

    min_r = float('inf')
    max_r = 0

    for _ in range(600):
        future_positions = []
        for fp in future_planets:
            fp["angle"] += fp["speed"]
            px = fp["radius"] * math.cos(fp["angle"])
            py = fp["radius"] * math.sin(fp["angle"])
            future_positions.append((px, py, fp["mass"]))

        ax = ay = 0
        for fx, fy, mass in future_positions:
            dx = fx - temp_x
            dy = fy - temp_y
            r = math.hypot(dx, dy)
            min_r = min(min_r, r)
            max_r = max(max_r, r)
            if r != 0:
                f = G * mass / r**2
                ax += f * dx / r
                ay += f * dy / r

        temp_vx += ax
        temp_vy += ay
        temp_x += temp_vx
        temp_y += temp_vy
        temp_traj.append((temp_x, temp_y))

    for tx, ty in temp_traj:
        sx, sy = world_to_screen(tx, ty)
        pygame.draw.circle(screen, (255, 255, 0), (sx, sy), 1)

    if min_r != float('inf') and max_r != 0:
        peri_img = font.render(f"近日点: {min_r:.0f}", True, (255, 180, 180))
        apo_img = font.render(f"遠日点: {max_r:.0f}", True, (180, 180, 255))
        screen.blit(peri_img, (10, 750))
        screen.blit(apo_img, (10, 770))

# === メインループ ===
while running:
    screen.fill((0, 0, 20))
    keys = pygame.key.get_pressed()
    shift = keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]

    # 操作
    thrust_force = 100
    acceleration = thrust_force / probe_mass

    if keys[pygame.K_z]:
        rad = math.radians(angle)
        vx += acceleration * math.cos(rad)
        vy += acceleration * math.sin(rad)
    if keys[pygame.K_c]:
        rad = math.radians(angle)
        vx -= acceleration * math.cos(rad)
        vy -= acceleration * math.sin(rad)
    if keys[pygame.K_x]:
        vx *= 0.98
        vy *= 0.98
    if keys[pygame.K_a]:
        angle -= 3
    if keys[pygame.K_d]:
        angle += 3
    if shift and keys[pygame.K_1]:
        zoom *= 1.05
    if shift and keys[pygame.K_2]:
        zoom /= 1.05

    # 惑星運動
    for p in planets:
        fx = fy = 0
        for other in planets:
            if p == other: continue
            dx = other["x"] - p["x"]
            dy = other["y"] - p["y"]
            r = math.hypot(dx, dy)
            if r != 0:
                f = G * other["mass"] / r**2
                fx += f * dx / r
                fy += f * dy / r
        p["vx"] += fx
        p["vy"] += fy
        p["angle"] += p["speed"]
        p["x"] = p["radius"] * math.cos(p["angle"])
        p["y"] = p["radius"] * math.sin(p["angle"])

    # 探査機運動
    ax = ay = 0
    for p in planets:
        dx = p["x"] - x
        dy = p["y"] - y
        r = math.hypot(dx, dy)
        if r != 0:
            f = G * p["mass"] / r**2
            ax += f * dx / r
            ay += f * dy / r

    vx += ax
    vy += ay
    x += vx
    y += vy
    trajectory.append((x, y))

    # 座標変換
    cam_x, cam_y = x, y
    def world_to_screen(wx, wy):
        sx = 500 + (wx - cam_x) * zoom
        sy = 400 + (wy - cam_y) * zoom
        return int(sx), int(sy)

    # 軌道円
    for p in planets:
        draw_orbit_circle(screen, cam_x, cam_y, zoom, p["radius"], (100, 100, 100))

    # 軌道履歴
    for tx, ty in trajectory[-1000:]:
        sx, sy = world_to_screen(tx, ty)
        pygame.draw.circle(screen, (80, 160, 255), (sx, sy), 1)

    # 予測軌道
    draw_predicted_trajectory()

    # 惑星描画
    for p in planets:
        sx, sy = world_to_screen(p["x"], p["y"])
        pygame.draw.circle(screen, p["color"], (sx, sy), max(3, int(8 * zoom)))
        name_img = font.render(p["name"], True, (255, 255, 255))
        screen.blit(name_img, (sx + 6, sy - 6))

    # 探査機描画
    sx, sy = world_to_screen(x, y)
    pygame.draw.circle(screen, (255, 255, 255), (sx, sy), 5)
    fx = sx + 10 * math.cos(math.radians(angle))
    fy = sy + 10 * math.sin(math.radians(angle))
    pygame.draw.line(screen, (255, 0, 0), (sx, sy), (fx, fy), 2)

    # 速度表示
    speed = math.hypot(vx, vy)
    speed_img = font.render(f"速度: {speed:.2f} km/s", True, (255, 255, 255))
    screen.blit(speed_img, (800, 770))

    # イベント処理
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
