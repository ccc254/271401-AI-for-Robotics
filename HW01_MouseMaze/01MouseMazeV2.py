import pygame
import random
import time
import json
import os
from collections import deque

# --- ตั้งค่าคอนฟิกูเรชัน ---
GRID_SIZE = 30
CELL_SIZE = 24  # ขนาดช่องพิกเซล
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
        self.screen_caption = "Pixel Mouse Maze: JSON Map & Decision Logger"
        pygame.display.set_caption(self.screen_caption)
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 28)
        self.load_map_from_json()
        self.reset_game()

    def load_map_from_json(self):
        """ โหลดแผนที่จากไฟล์ map.json """
        json_file = "map01.json"
        if not os.path.exists(json_file):
            raise FileNotFoundError(f"ไม่พบไฟล์ '{json_file}' กรุณาสร้างไฟล์ไว้ในโฟลเดอร์เดียวกันกับโค้ด Python")
        
        with open(json_file, 'r') as f:
            data = json.load(f)
            
        global GRID_SIZE, WIDTH, HEIGHT
        GRID_SIZE = data.get("grid_size", 30)
        WIDTH = GRID_SIZE * CELL_SIZE
        HEIGHT = GRID_SIZE * CELL_SIZE + 60
        
        self.maze = data["maze"]
        self.start_pos = tuple(data["start_pos"])
        self.finish_pos = tuple(data["finish_pos"])
        print(f"📂 โหลดแผนที่สำเร็จ! ขนาดเขาวงกต: {GRID_SIZE}x{GRID_SIZE}")

    def find_shortest_path(self, start, target):
        """ อัลกอริทึม BFS หาเส้นทางสั้นที่สุด """
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

    def check_surroundings(self, pos):
        """ ตรวจสอบทิศทางรอบตัวหนูว่ามีอะไรติดกำแพง (ชน) บ้าง """
        x, y = pos
        directions = {
            "บน": (0, -1),
            "ล่าง": (0, 1),
            "ซ้าย": (-1, 0),
            "ขวา": (1, 0)
        }
        
        collision_states = []
        for name, (dx, dy) in directions.items():
            nx, ny = x + dx, y + dy
            # ถ้าออกนอกแมพ หรือ เจอเลข 1 แปลว่าชนกำแพง
            if not (0 <= nx < GRID_SIZE and 0 <= ny < GRID_SIZE) or self.maze[ny][nx] == 1:
                collision_states.append(name)
                
        return collision_states

    def get_move_direction(self, current, next_step):
        """ คำนวณหาทิศทางที่จะเดินจากจุดปัจจุบันไปยังจุดถัดไป """
        dx = next_step[0] - current[0]
        dy = next_step[1] - current[1]
        if dx == 1: return "ขวา"
        if dx == -1: return "ซ้าย"
        if dy == 1: return "ล่าง"
        if dy == -1: return "บน"
        return "หยุดอยู่กับที่"

    def reset_game(self):
        self.mouse_pos = list(self.start_pos)
        self.start_time = time.time()
        self.time_left = GAME_DURATION
        self.game_over = False
        self.win = False
        
        # --- เพิ่มตัวแปรสำหรับเก็บจำนวนก้าวและเวลาที่จบ ---
        self.step_count = 0
        self.final_time = 0.0
        
        # ตั้งค่าสำหรับการขยับอัตโนมัติ
        self.last_auto_move_time = time.time()
        self.auto_move_delay = 0.1 # ความเร็วในการก้าวเดิน (วินาทีต่อช่อง)
        
        print("\n🚀 เริ่มเกมใหม่! กำลังเดินทางไปหาเป้าหมาย...")

    def handle_input(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            
            if event.type == pygame.KEYDOWN:
                if self.game_over or self.win:
                    if event.key == pygame.K_r:
                        self.reset_game()
        return True

    def update(self):
        if not self.game_over and not self.win:
            # 1. อัปเดตเวลาถอยหลัง
            elapsed = time.time() - self.start_time
            self.time_left = max(0, GAME_DURATION - elapsed)
            if self.time_left <= 0:
                self.game_over = True
                print("💀 TIME OUT! หนูหมดเวลาตัดสินใจตัวตายในเขาวงกต")
                return

            # 2. การตัดสินใจเดินอัตโนมัติ และจับเวลาการคำนวณ Pathfinding
            current_time = time.time()
            if current_time - self.last_auto_move_time >= self.auto_move_delay:
                
                # จับเวลาการทำงานของ BFS Algorithm
                calc_start = time.perf_counter()
                path = self.find_shortest_path(tuple(self.mouse_pos), self.finish_pos)
                calc_time = time.perf_counter() - calc_start
                
                # ตรวจสอบสถานะกำแพงรอบข้าง (ชนทิศไหนบ้าง)
                collisions = self.check_surroundings(self.mouse_pos)
                collision_str = ", ".join(collisions) if collisions else "ไม่มี"
                
                if len(path) > 1:
                    next_step = path[1]
                    # คำนวณทิศที่จะเดิน
                    move_dir = self.get_move_direction(self.mouse_pos, next_step)
                    
                    # ปริ้นสถานะการตัดสินใจ (Decision State) ลง Terminal
                    print(f"🤖 [Decision State] พิกัดปัจจุบัน: {self.mouse_pos} | ชนกำแพงทิศ: [{collision_str}] -> ตัดสินใจเดิน: [{move_dir}] | ระยะเหลือ: {len(path)-1} ช่อง | ใช้เวลาคำนวณ: {calc_time*1000:.4f} ms")
                    
                    # บันทึกการเดิน
                    self.mouse_pos = list(next_step)
                    self.last_auto_move_time = current_time
                    self.step_count += 1  # เพิ่มจำนวนก้าวทุกครั้งที่ขยับ
                    
                    # ตรวจสอบเงื่อนไขการชนะ
                    if tuple(self.mouse_pos) == self.finish_pos:
                        self.win = True
                        self.final_time = time.time() - self.start_time
                        print(f"\n✨ [🏆 SUCCESS] หนูหาชีสเจอแล้ว!")
                        print(f"📍 จำนวนก้าวที่ใช้ทั้งหมด: {self.step_count} ก้าว")
                        print(f"⏱️ ใช้เวลาเดินทางทั้งหมด: {self.final_time:.2f} วินาที\n")
                else:
                    print(f"⚠️ [Error] ไม่พบเส้นทางไปยังเป้าหมาย! พิกัดปัจจุบัน: {self.mouse_pos} | ชนกำแพงทิศ: [{collision_str}]")
                    self.game_over = True

    def draw_pixel_sprite(self, color, x, y, size):
        surf = pygame.Surface((size, size))
        surf.fill(color)
        pygame.draw.rect(surf, (0, 0, 0), (0, 0, size, size), 1)
        self.screen.blit(surf, (x, y))

    def draw_mouse_pixel(self, cx, cy):
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

        # 2. วาดจุดเริ่มต้น และ จุดจบ
        self.draw_pixel_sprite(COLOR_START, self.start_pos[0]*CELL_SIZE, self.start_pos[1]*CELL_SIZE, CELL_SIZE)
        self.draw_pixel_sprite(COLOR_FINISH, self.finish_pos[0]*CELL_SIZE, self.finish_pos[1]*CELL_SIZE, CELL_SIZE)
        
        # วาดรูปชีสพิกเซลในช่อง Finish
        fx = self.finish_pos[0]*CELL_SIZE + 4
        fy = self.finish_pos[1]*CELL_SIZE + 4
        pygame.draw.polygon(self.screen, (245, 190, 20), [(fx+8, fy), (fx, fy+14), (fx+16, fy+14)])
        pygame.draw.circle(self.screen, (200, 140, 10), (fx+5, fy+10), 2)

        # 3. ระบบกลิ่นชีส (Scent Hint)
        current_path = self.find_shortest_path(tuple(self.mouse_pos), self.finish_pos)
        if len(current_path) > 1 and not self.game_over and not self.win:
            next_step = current_path[1]
            hx = next_step[0] * CELL_SIZE + CELL_SIZE // 2
            hy = next_step[1] * CELL_SIZE + CELL_SIZE // 2
            pygame.draw.rect(self.screen, COLOR_SCENT, (hx-3, hy-3, 6, 6))

        # 4. วาดหนู
        self.draw_mouse_pixel(self.mouse_pos[0], self.mouse_pos[1])

        # 5. UI Dashboard ด้านล่าง
        minutes = int(self.time_left) // 60
        seconds = int(self.time_left) % 60
        time_str = f"Time Left: {minutes:02d}:{seconds:02d}"

        if self.win:
            # ปรับให้แสดงจำนวนก้าวในหน้าจอเกมตอนชนะด้วย
            ui_text = f"✨ SUCCESS! {self.step_count} Steps in {self.final_time:.1f}s (Press 'R' to Retry)"
        elif self.game_over:
            ui_text = "💀 GAME OVER... (Press 'R' to Retry)"
        else:
            ui_text = f"{time_str}  |  Steps: {self.step_count}  |  Mode: JSON Auto-Solver"

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