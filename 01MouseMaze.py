import pygame
import random
import time
from collections import deque

# --- ตั้งค่าคอนฟิกูเรชัน ---
GRID_SIZE = 30
CELL_SIZE = 24  # ขนาดช่องพิกเซล (สเกลช่อง 15cm)
WIDTH = GRID_SIZE * CELL_SIZE
HEIGHT = GRID_SIZE * CELL_SIZE + 60  # เผื่อพื้นที่ UI ด้านล่าง
GAME_DURATION = 180  # จำกัดเวลา 3 นาที (180 วินาที)

# --- สีสันสไตล์ Pixel Art ---
COLOR_BG = (26, 26, 26)         # พื้นหลังนอกแมพ
COLOR_WALL = (61, 59, 64)       # สีบล็อกกำแพงหินพิกเซล
COLOR_PATH = (143, 139, 130)    # สีพื้นทางเดินหินพิกเซล
COLOR_START = (38, 115, 77)     # จุดเริ่ม (เขียวหม่น)
COLOR_FINISH = (166, 50, 50)    # จุดจบ (แดงหม่น)
COLOR_TEXT = (235, 235, 235)    # สีตัวอักษร UI
COLOR_SCENT = (245, 215, 66)    # สีกลิ่นชีสสีเหลืองเรืองแสง
COLOR_MOUSE = (180, 180, 185)   # สีตัวหนูพิกเซล

class PixelMazeAutoGame:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Pixel Mouse Maze: 100% Auto-Pilot Scent Solver")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 28)
        self.reset_game()

    def generate_maze(self):
        """ สร้างเขาวงกตซับซ้อนขนาด 30x30 ด้วยวิธี DFS """
        self.maze = [[1] * GRID_SIZE for _ in range(GRID_SIZE)]
        stack = [(0, 0)]
        self.maze[0][0] = 0

        while stack:
            cx, cy = stack[-1]
            neighbors = []
            for dx, dy in [(-2, 0), (2, 0), (0, -2), (0, 2)]:
                nx, ny = cx + dx, cy + dy
                if 0 <= nx < GRID_SIZE and 0 <= ny < GRID_SIZE and self.maze[ny][nx] == 1:
                    neighbors.append((nx, ny))

            if neighbors:
                nx, ny = random.choice(neighbors)
                self.maze[cy + (ny - cy) // 2][cx + (nx - cx) // 2] = 0
                self.maze[ny][nx] = 0
                stack.append((nx, ny))
            else:
                stack.pop()

        self.maze[0][0] = 0

    def find_shortest_path(self, start, target):
        """ อัลกอริทึม BFS หาเส้นทางสั้นที่สุด (จำลองเวลาคำนวณและกลิ่นชีส) """
        queue = deque([[start]])
        visited = {start}

        while queue:
            path = queue.popleft()
            x, y = path[-1]

            if (x, y) == target:
                return path

            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nx, ny = x + dx, y + dy
                if 0 <= nx < GRID_SIZE and 0 <= ny < GRID_SIZE and self.maze[ny][nx] == 0:
                    if (nx, ny) not in visited:
                        visited.add((nx, ny))
                        new_path = list(path)
                        new_path.append((nx, ny))
                        queue.append(new_path)
        return []

    def setup_points(self):
        """ การันตีว่าระยะทางเดินเชื่อมหากันต้องใช้พลังการคำนวณ (ก้าวเดิน) อย่างต่ำ 5 ครั้ง """
        self.start_pos = (0, 0)
        while True:
            self.generate_maze()
            # เลือกจุดจบให้ห่างออกไปเพื่อให้เขาวงกตท้าทาย
            potential_finishes = [(GRID_SIZE-1, GRID_SIZE-1), (GRID_SIZE-1, 2), (2, GRID_SIZE-1)]
            self.finish_pos = random.choice(potential_finishes)
            self.maze[self.finish_pos[1]][self.finish_pos[0]] = 0
            
            path = self.find_shortest_path(self.start_pos, self.finish_pos)
            if len(path) >= 6:  # เกิน 5 ช่องชัวร์ๆ ตามเงื่อนไข Computation time ขั้นต่ำ
                break

    def reset_game(self):
        self.setup_points()
        self.mouse_pos = list(self.start_pos)
        self.start_time = time.time()
        self.time_left = GAME_DURATION
        self.game_over = False
        self.win = False
        
        # ตั้งค่าสำหรับการขยับอัตโนมัติ
        self.last_auto_move_time = time.time()
        self.auto_move_delay = 0.1  # หนูจะเดินเองทุกๆ 0.1 วินาที (ปรับเพิ่ม/ลดความเร็วได้ที่นี่)

    def handle_input(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            
            if event.type == pygame.KEYDOWN:
                # ลบระบบควบคุมการเดินออกทั้งหมด เหลือเพียงปุ่ม 'R' เพื่อสุ่มด่านใหม่
                if self.game_over or self.win:
                    if event.key == pygame.K_r:
                        self.reset_game()
        return True

    def update(self):
        if not self.game_over and not self.win:
            # 1. อัปเดตเวลาถอยหลัง 3 นาที
            elapsed = time.time() - self.start_time
            self.time_left = max(0, GAME_DURATION - elapsed)
            if self.time_left <= 0:
                self.game_over = True
                return

            # 2. Algorithm การเดินอัตโนมัติ (Auto-Pathfinding)
            current_time = time.time()
            if current_time - self.last_auto_move_time >= self.auto_move_delay:
                # คำนวณเส้นทางสั้นที่สุดจากตำแหน่งปัจจุบันของหนูไปยังชีส
                path = self.find_shortest_path(tuple(self.mouse_pos), self.finish_pos)
                
                if len(path) > 1:
                    # ดึงพิกัดช่องถัดไป (Index ที่ 1 เพราะ Index 0 คือจุดที่หนูยืนอยู่ปัจจุบัน)
                    next_step = path[1]
                    self.mouse_pos = list(next_step)
                    self.last_auto_move_time = current_time
                    
                    # ตรวจสอบเงื่อนไขการชนะเมื่อเดินถึงชีส
                    if tuple(self.mouse_pos) == self.finish_pos:
                        self.win = True

    def draw_pixel_sprite(self, color, x, y, size):
        """ ฟังก์ชันวาดสไปรต์สไตล์พิกเซลแบบตารางย่อย """
        surf = pygame.Surface((size, size))
        surf.fill(color)
        pygame.draw.rect(surf, (0, 0, 0), (0, 0, size, size), 1)
        self.screen.blit(surf, (x, y))

    def draw_mouse_pixel(self, cx, cy):
        """ วาดตัวหนูพิกเซลจำลองขนาด 16x16 พิกเซลให้อยู่ตรงกลางช่องพอดี """
        mx = cx * CELL_SIZE + (CELL_SIZE - 16) // 2
        my = cy * CELL_SIZE + (CELL_SIZE - 16) // 2
        
        pygame.draw.rect(self.screen, COLOR_MOUSE, (mx, my, 16, 16))
        pygame.draw.rect(self.screen, (240, 150, 150), (mx+2, my-2, 4, 4))
        pygame.draw.rect(self.screen, (240, 150, 150), (mx+10, my-2, 4, 4))
        pygame.draw.rect(self.screen, (0, 0, 0), (mx+4, my+4, 2, 2))
        pygame.draw.rect(self.screen, (0, 0, 0), (mx+10, my+4, 2, 2))

    def draw(self):
        self.screen.fill(COLOR_BG)

        # 1. วาดแผนที่เขาวงกตพิกเซล
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                px = x * CELL_SIZE
                py = y * CELL_SIZE
                if self.maze[y][x] == 1:
                    self.draw_pixel_sprite(COLOR_WALL, px, py, CELL_SIZE)
                else:
                    self.draw_pixel_sprite(COLOR_PATH, px, py, CELL_SIZE)

        # 2. วาดจุดเริ่มต้น และ จุดจบ (ชีส)
        self.draw_pixel_sprite(COLOR_START, self.start_pos[0]*CELL_SIZE, self.start_pos[1]*CELL_SIZE, CELL_SIZE)
        self.draw_pixel_sprite(COLOR_FINISH, self.finish_pos[0]*CELL_SIZE, self.finish_pos[1]*CELL_SIZE, CELL_SIZE)
        
        # วาดรูปชีสพิกเซลสีเหลืองในช่อง Finish
        fx = self.finish_pos[0]*CELL_SIZE + 4
        fy = self.finish_pos[1]*CELL_SIZE + 4
        pygame.draw.polygon(self.screen, (245, 190, 20), [(fx+8, fy), (fx, fy+14), (fx+16, fy+14)])
        pygame.draw.circle(self.screen, (200, 140, 10), (fx+5, fy+10), 2)

        # 3. ระบบ "ได้กลิ่นชีสระยะสั้นที่สุด" (Scent Hint System)
        current_path = self.find_shortest_path(tuple(self.mouse_pos), self.finish_pos)
        if len(current_path) > 1 and not self.game_over and not self.win:
            next_step = current_path[1]
            hx = next_step[0] * CELL_SIZE + CELL_SIZE // 2
            hy = next_step[1] * CELL_SIZE + CELL_SIZE // 2
            pygame.draw.rect(self.screen, COLOR_SCENT, (hx-3, hy-3, 6, 6))

        # 4. วาดหนูพิกเซลขนาด 16x16 พิกเซล
        self.draw_mouse_pixel(self.mouse_pos[0], self.mouse_pos[1])

        # 5. ส่วนแสดงผล UI ด้านล่าง (Dashboard)
        minutes = int(self.time_left) // 60
        seconds = int(self.time_left) % 60
        time_str = f"Time Left: {minutes:02d}:{seconds:02d}"

        if self.win:
            ui_text = "✨ AUTO-PILOT SUCCESS! MOUSE FOUND CHEESE! (Press 'R')"
        elif self.game_over:
            ui_text = "💀 TIME OUT! MOUSE DIED IN MAZE... (Press 'R' to Retry)"
        else:
            ui_text = f"{time_str}  |  Mode: 100% Autonomous (Scent Tracking...)"

        text_surf = self.font.render(ui_text, True, COLOR_TEXT)
        self.screen.blit(text_surf, (15, HEIGHT - 40))

        pygame.display.flip()

    def run(self):
        running = True
        while running:
            running = self.handle_input()
            self.update()
            self.draw()
            self.clock.tick(30)
        pygame.quit()

if __name__ == "__main__":
    game = PixelMazeAutoGame()
    game.run()