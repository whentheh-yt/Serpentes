import tkinter as tk
import random
from collections import deque

# ----- Configuration -----
NUM_WINDOWS = 4
ROWS, COLS = 8, 8
CELL = 36
TICK_MS = 120
ANIM_MS = 60            # window animation tick
SWAP_INTERVAL_MS = 7501 # how often to consider a swap
SWAP_DURATION_MS = 7500  # duration of a swap animation
DRIFT_RADIUS = 1920       # max distance from base position

ENEMY_SPAWN_LENGTH = 10         # Player length required to spawn enemy
ENEMY_INITIAL_LENGTH = 3        # Starting length of enemy snake
ENEMY_HEAD_COLOR = "#aa0000"
ENEMY_BODY_COLOR = "#ff5555"
ENEMY_SPEED_FACTOR = 1          # Multiplier for enemy moves per tick (1 = same as player)

HEAD_COLOR = "#0b8847"
BODY_COLOR = "#3cd593"
FOOD_COLOR = "#cc2224"
BG_COLOR = "#222428"

class Serpentes:
    def __init__(self, root):
        self.root = root
        self.windows = []
        self.canvases = []
        self.base_positions = []   # [(x,y), ...] base placement
        self.current_positions = []# [(x,y), ...] live positions (floats)
        self.velocities = []       # [(dx,dy), ...] for drift
        self.window_size = (COLS*CELL, ROWS*CELL)
        self.running = True
        self.score = 0
        self.swapping = set()

        self.direction = "Right"
        self.next_direction = "Right"
        self.drift_enabled = False
        self.swap_enabled = False
        self.swap_scheduled = False

        self._anim_after_id = None
        self._swap_after_id = None

        self.enemy_snake = None
        self.enemy_dir = None

        self.init_windows()
        self.reset_game()
        self.root.after(TICK_MS, self.game_tick)
        self.root.bind_all("<Key>", self.on_key)

    def get_drift_speed(self):
        base_speed = 0.2
        growth_factor = 0.05
        return base_speed + growth_factor * len(self.snake)
    
    def init_windows(self):
        w_px, h_px = self.window_size
        offset_x = 50
        offset_y = 60
        spacing = 10
        for i in range(NUM_WINDOWS):
            if i == 0:
                win = self.root
                win.title(f"Serpentes")
                win.protocol("WM_DELETE_WINDOW", lambda: None)
            else:
                win = tk.Toplevel(self.root)
                win.title(f"Serpentes")
                win.protocol("WM_DELETE_WINDOW", lambda: None)
            x = offset_x + i * (w_px + spacing)
            y = offset_y
            win.geometry(f"{w_px}x{h_px}+{x}+{y}")
            win.resizable(False, False)
            canvas = tk.Canvas(win, bg=BG_COLOR, width=w_px, height=h_px, highlightthickness=0)
            canvas.pack()
            self.windows.append(win)
            self.canvases.append(canvas)
            self.base_positions.append((x, y))
            self.current_positions.append([float(x), float(y)])
            self.velocities.append([0.0, 0.0])

    def enable_window_behaviours_if_needed(self):
        if len(self.snake) >= 5 and not self.drift_enabled:
            self.drift_enabled = True
            self.swap_enabled = True
            for v in self.velocities:
                v[0] = random.uniform(-self.get_drift_speed(), self.get_drift_speed())
                v[1] = random.uniform(-self.get_drift_speed(), self.get_drift_speed())
            self._anim_after_id = self.root.after(ANIM_MS, self.animate_windows)
            self._swap_after_id = self.root.after(SWAP_INTERVAL_MS, self.maybe_swap_windows)

    def disable_window_behaviours(self):
        self.drift_enabled = False
        self.swap_enabled = False
        if self._anim_after_id:
            try:
                self.root.after_cancel(self._anim_after_id)
            except Exception:
                pass
            self._anim_after_id = None
        if self._swap_after_id:
            try:
                self.root.after_cancel(self._swap_after_id)
            except Exception:
                pass
            self._swap_after_id = None
        for v in self.velocities:
            v[0] = v[1] = 0.0
        for i, win in enumerate(self.windows):
            bx, by = self.base_positions[i]
            self.current_positions[i][0] = float(bx)
            self.current_positions[i][1] = float(by)
            win.geometry(f"{self.window_size[0]}x{self.window_size[1]}+{bx}+{by}")

    def animate_windows(self):
        if not self.drift_enabled or not self.running:
            self._anim_after_id = None
            return

        for i in range(NUM_WINDOWS):
            if i in self.swapping:
                continue

            bx, by = self.base_positions[i]
            cx, cy = self.current_positions[i]
            vx, vy = self.velocities[i]

            nx = cx + vx
            ny = cy + vy

            dx = nx - bx
            dy = ny - by
            if abs(dx) > DRIFT_RADIUS:
                nx = bx + max(min(dx, DRIFT_RADIUS), -DRIFT_RADIUS)
                self.velocities[i][0] = -vx * 0.9
            if abs(dy) > DRIFT_RADIUS:
                ny = by + max(min(dy, DRIFT_RADIUS), -DRIFT_RADIUS)
                self.velocities[i][1] = -vy * 0.9

            self.velocities[i][0] += random.uniform(-0.4, 0.4)
            self.velocities[i][1] += random.uniform(-0.4, 0.4)
            self.velocities[i][0] = max(min(self.velocities[i][0], self.get_drift_speed()), -self.get_drift_speed())
            self.velocities[i][1] = max(min(self.velocities[i][1], self.get_drift_speed()), -self.get_drift_speed())

            self.current_positions[i][0] = nx
            self.current_positions[i][1] = ny
            self.windows[i].geometry(f"{self.window_size[0]}x{self.window_size[1]}+{int(round(nx))}+{int(round(ny))}")

        self._anim_after_id = self.root.after(ANIM_MS, self.animate_windows)

    def maybe_swap_windows(self):
        if not self.swap_enabled or not self.running:
            self._swap_after_id = None
            return

        if random.random() < 0.55:
            a, b = random.sample(range(NUM_WINDOWS), 2)
            if a not in self.swapping and b not in self.swapping:
                self.animate_swap(a, b, SWAP_DURATION_MS)

        self._swap_after_id = self.root.after(SWAP_INTERVAL_MS, self.maybe_swap_windows)

    def animate_swap(self, a, b, duration_ms):
        if a == b or a in self.swapping or b in self.swapping:
            return

        self.swapping.add(a)
        self.swapping.add(b)

        # snapshot positions and pause velocities
        start_a_x = float(self.current_positions[a][0])
        start_a_y = float(self.current_positions[a][1])
        start_b_x = float(self.current_positions[b][0])
        start_b_y = float(self.current_positions[b][1])
        target_a_x = start_b_x
        target_a_y = start_b_y
        target_b_x = start_a_x
        target_b_y = start_a_y

        old_vel_a = self.velocities[a].copy()
        old_vel_b = self.velocities[b].copy()
        self.velocities[a][0] = self.velocities[a][1] = 0.0
        self.velocities[b][0] = self.velocities[b][1] = 0.0

        steps = max(6, duration_ms // ANIM_MS)
        dx_a = (target_a_x - start_a_x) / steps
        dy_a = (target_a_y - start_a_y) / steps
        dx_b = (target_b_x - start_b_x) / steps
        dy_b = (target_b_y - start_b_y) / steps

        def step_frame(step=0):
            if not self.running:
                # cleanup if game stopped
                self.swapping.discard(a)
                self.swapping.discard(b)
                return
            if step >= steps:
                # final snap, swap base positions so future drift makes sense
                self.current_positions[a][0], self.current_positions[a][1] = target_a_x, target_a_y
                self.current_positions[b][0], self.current_positions[b][1] = target_b_x, target_b_y
                # swap base positions so drift anchors follow
                self.base_positions[a], self.base_positions[b] = self.base_positions[b], self.base_positions[a]
                self.windows[a].geometry(f"{self.window_size[0]}x{self.window_size[1]}+{int(round(target_a_x))}+{int(round(target_a_y))}")
                self.windows[b].geometry(f"{self.window_size[0]}x{self.window_size[1]}+{int(round(target_b_x))}+{int(round(target_b_y))}")
                # restore gentle velocities; if old was zero, give a small random nudge
                def restore(old):
                    vx = old[0] if abs(old[0]) > 1e-3 else random.uniform(-0.6, 0.6)
                    vy = old[1] if abs(old[1]) > 1e-3 else random.uniform(-0.6, 0.6)
                    return [vx, vy]
                self.velocities[a] = restore(old_vel_a)
                self.velocities[b] = restore(old_vel_b)
                self.swapping.discard(a)
                self.swapping.discard(b)
                return

            xa = start_a_x + dx_a * (step + 1)
            ya = start_a_y + dy_a * (step + 1)
            xb = start_b_x + dx_b * (step + 1)
            yb = start_b_y + dy_b * (step + 1)

            self.current_positions[a][0], self.current_positions[a][1] = xa, ya
            self.current_positions[b][0], self.current_positions[b][1] = xb, yb

            self.windows[a].geometry(f"{self.window_size[0]}x{self.window_size[1]}+{int(round(xa))}+{int(round(ya))}")
            self.windows[b].geometry(f"{self.window_size[0]}x{self.window_size[1]}+{int(round(xb))}+{int(round(yb))}")

            self.root.after(ANIM_MS, lambda: step_frame(step + 1))

        step_frame(0)

    def reset_game(self):
        self.running = True
        self.score = 0
        self.direction = "Right"
        self.next_direction = "Right"
    
    # reset player snake
        mid_r = ROWS // 2
        mid_c = COLS // 2
        self.snake = deque([
            (0, mid_r, mid_c - 2),
            (0, mid_r, mid_c - 1),
            (0, mid_r, mid_c),
        ])
    
    # ----- reset enemy snake -----
        self.enemy_snake = None
        self.enemy_dir = None
    
    # reset window behaviours
        self.disable_window_behaviours()
        # reset positions to base
        for i, (bx, by) in enumerate(self.base_positions):
            self.current_positions[i][0] = float(bx)
            self.current_positions[i][1] = float(by)
            self.windows[i].geometry(f"{self.window_size[0]}x{self.window_size[1]}+{bx}+{by}")
        self.place_food()
        self.draw_all()

    def place_food(self):
        while True:
            w = random.randrange(NUM_WINDOWS)
            r = random.randrange(ROWS)
            c = random.randrange(COLS)
            if (w, r, c) not in self.snake:
                self.food = (w, r, c)
                return

    def on_key(self, event):
        key = event.keysym.lower()
        if key in ("left", "a"):
            if self.direction != "Right":
                self.next_direction = "Left"
        elif key in ("right", "d"):
            if self.direction != "Left":
                self.next_direction = "Right"
        elif key in ("up", "w"):
            if self.direction != "Down":
                self.next_direction = "Up"
        elif key in ("down", "s"):
            if self.direction != "Up":
                self.next_direction = "Down"
        elif key == "r":
            if not self.running:
                self.close_game_over()
                self.reset_game()

    def step(self):
        head_w, head_r, head_c = self.snake[-1]
        self.direction = self.next_direction
        nw, nr, nc = head_w, head_r, head_c
        if self.direction == "Left":
            nc -= 1
            if nc < 0:
                nw = (head_w - 1) % NUM_WINDOWS
                nc = COLS - 1
        elif self.direction == "Right":
            nc += 1
            if nc >= COLS:
                nw = (head_w + 1) % NUM_WINDOWS
                nc = 0
        elif self.direction == "Up":
            nr -= 1
        elif self.direction == "Down":
            nr += 1
    
        if nr < 0 or nr >= ROWS:
            self.game_over("You hit the wall.")
            return

        new_head = (nw, nr, nc)
        if new_head in self.snake or (self.enemy_snake and new_head in self.enemy_snake):
            self.game_over("You rammed into a snake.")
            return

        ate = new_head == self.food
        self.snake.append(new_head)
        if not ate:
            self.snake.popleft()
        else:
            self.score += 1
            self.place_food()

    # enable behaviours when long enough
        self.enable_window_behaviours_if_needed()

    # spawn enemy snake when length >= 10
        if len(self.snake) >= ENEMY_SPAWN_LENGTH and self.enemy_snake is None:
            while True:
                w = random.randrange(NUM_WINDOWS)
                r = random.randrange(ROWS)
                c = random.randrange(COLS)
                if (w, r, c) not in self.snake:
                    self.enemy_snake = deque([(w, r, c)])
                    self.enemy_dir = random.choice(["Left", "Right", "Up", "Down"])
                    break

    # move enemy snake
        if self.enemy_snake:
            eh_w, eh_r, eh_c = self.enemy_snake[-1]
            dir = self.enemy_dir
            enw, enr, enc = eh_w, eh_r, eh_c

    # simple movement logic
            if dir == "Left":
                enc -= 1
            elif dir == "Right":
                enc += 1
            elif dir == "Up":
                enr -= 1
            elif dir == "Down":
                enr += 1

    # handle window wrap for horizontal movement
            if enc < 0:
                enc = COLS - 1
                enw = (enw - 1) % NUM_WINDOWS
            elif enc >= COLS:
                enc = 0
                enw = (enw + 1) % NUM_WINDOWS

    # handle vertical wall bounce
            if enr < 0:
                enr = 0
                self.enemy_dir = random.choice(["Down", "Left", "Right"])
            elif enr >= ROWS:
                enr = ROWS - 1
                self.enemy_dir = random.choice(["Up", "Left", "Right"])

            new_ehead = (enw, enr, enc)
            if new_ehead in self.snake or new_ehead in self.enemy_snake:
            # change direction if blocked
                self.enemy_dir = random.choice(["Left", "Right", "Up", "Down"])
            else:
                self.enemy_snake.append(new_ehead)
                if len(self.enemy_snake) > ENEMY_INITIAL_LENGTH:
                    self.enemy_snake.popleft()

    def draw_all(self):
        for idx, canvas in enumerate(self.canvases):
            canvas.delete("all")
            if self.food[0] == idx:
                _, fr, fc = self.food
                self.draw_cell(canvas, fr, fc, FOOD_COLOR)
            for i, (w, r, c) in enumerate(self.snake):
                if w != idx:
                    continue
                color = HEAD_COLOR if i == len(self.snake) - 1 else BODY_COLOR
                self.draw_cell(canvas, r, c, color)
        # draw enemy snake
            if self.enemy_snake:
                for i, (w, r, c) in enumerate(self.enemy_snake):
                    if w != idx:
                        continue
                    color = "#aa0000" if i == len(self.enemy_snake) - 1 else "#ff5555"
                    self.draw_cell(canvas, r, c, color)

    def draw_cell(self, canvas, row, col, color):
        x1 = col * CELL
        y1 = row * CELL
        x2 = x1 + CELL
        y2 = y1 + CELL
        pad = 2
        canvas.create_rectangle(x1 + pad, y1 + pad, x2 - pad, y2 - pad, fill=color, outline="")

    def game_tick(self):
        if self.running:
            self.step()
            if self.running:
                self.draw_all()
        self.root.after(TICK_MS, self.game_tick)

    def game_over(self, reason):
        self.running = False
        # stop animations
        self.disable_window_behaviours()
        self.show_game_over(reason)

    def show_game_over(self, reason):
        go = tk.Toplevel(self.root)
        go.title("R.I.P Serpentes ⚀⚀")
        go.geometry("520x220")
        go.resizable(False, False)

        title = tk.Label(go, text="⚀⚀ SNAKE EYES ⚀⚀", font=("Segoe UI", 28, "bold"))
        title.pack(pady=(12, 6))

        death_label = tk.Label(go, text=reason, wraplength=480, justify="left", fg="red", font=("Segoe UI", 11))
        death_label.pack(padx=12)

        note = tk.Label(go, text=f"Score: {self.score} — Watch your snake near the end!", wraplength=480, justify="left", font=("Segoe UI", 10))
        note.pack(pady=(8, 0), padx=12)

        btn_frame = tk.Frame(go)
        btn_frame.pack(pady=10)

        def restart():
            go.destroy()
            self.reset_game()

        def close_all():
            self.root.quit()
            self.root.destroy()

        btn_ok = tk.Button(btn_frame, text="Restart", command=restart)
        btn_ok.pack(side="left", padx=6)
        btn_close = tk.Button(btn_frame, text="Close", command=close_all)
        btn_close.pack(side="left", padx=6)

        self._game_over_window = go

    def close_game_over(self):
        if hasattr(self, "_game_over_window") and self._game_over_window.winfo_exists():
            self._game_over_window.destroy()
            del self._game_over_window

if __name__ == "__main__":
    root = tk.Tk()
    root.title("Serpentes — world 0")
    app = Serpentes(root)
    root.mainloop()
