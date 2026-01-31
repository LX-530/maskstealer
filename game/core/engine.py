import pygame
import sys
import random
import math
from collections import deque

from game.core.map import Map, TILE_EMPTY, TILE_WALL, TILE_STAIRS, TILE_SIZE
from game.entities.player import Player
from game.entities.monster import Monster
from game.systems.sprite_loader import SpriteLoader
from game.systems.monster_loader import MonsterLoader
from game.effects.laser import LaserBeam
from game.effects.particles import ParticleSystem

# 颜色定义
GOLD = (255, 215, 0)
YELLOW = (255, 255, 0)
ORANGE = (255, 100, 0)
GREEN = (0, 255, 0)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255,0,0)

class GameEngine:
    def __init__(self, screen, font):
        self.screen = screen
        self.font = font
        self.clock = pygame.time.Clock()
        self.FPS = 60
        self.state = "game"
        self.victory = False
        self.move_speed = 5

        # 精灵加载器
        self.sprite_loader = SpriteLoader()
        print("开始加载精灵资源...")
        self.sprite_loader.load_sprites()

        # 玩家、地图初始化
        self.player = Player("勇者", self.sprite_loader)
        self.map = Map(120, 80)
        self.player.x, self.player.y = self.map.player_position

        # 让玩家能用于闪避碰撞检测
        self.player.set_map_reference(self.map)

        # 房间中心
        self.room_centers = self.map.get_room_centers()

        self.last_damage_time = 0  # 新增这一行

        self.last_attack_sound_time = 0
        self.attack_sound = None  # 接收主程序传递的攻击音效
        self.lasers = []
        self.particles = ParticleSystem()

        # 起点/终点选择逻辑（不改动）
        if len(self.room_centers) >= 2:
            self.start_room = self._find_closest_room_center(self.player.x, self.player.y)
            farthest_room, path_distance = self._find_farthest_room_by_path(
                (self.player.x, self.player.y)
            )

            if farthest_room and farthest_room != self.start_room:
                self.end_room = farthest_room
                print(f"终点设置完成 - 路径距离: {int(path_distance)}")
            else:
                max_distance = -1
                self.end_room = self.start_room
                for center in self.room_centers:
                    if center != self.start_room:
                        dist = self._manhattan_dist(self.start_room, center)
                        if dist > max_distance:
                            max_distance = dist
                            self.end_room = center
                print("使用空间距离回退方案")
        else:
            self.start_room = (self.player.x, self.player.y)
            self.end_room = (self.player.x + 300, self.player.y + 300)

        # 相机初始化
        self.camera_x = self.player.x - self.screen.get_width() // 2
        self.camera_y = self.player.y - self.screen.get_height() // 2

        print(f"起点: {self.start_room}, 终点: {self.end_room}, 房间数: {len(self.room_centers)}")

        # ---------------- 怪物系统初始化 ----------------
        print("开始加载怪物资源...")
        self.monster_loader = MonsterLoader()
        self.monster_loader.load_monster_gifs()  # 加载所有怪物GIF
        self.monsters = []  # 存储所有怪物实例

        # 修改 game_engine.py 中怪物生成部分（约第95-110行）
        # 为每个房间创建一个随机怪物（跳过起点和终点房间）
        for room in self.map.rooms:
            # 计算房间中心像素坐标
            room_center = (
                room["x"] + room["width"] // 2,
                room["y"] + room["height"] // 2
            )
            room_center_pixel = (
                room_center[0] * TILE_SIZE + TILE_SIZE // 2,
                room_center[1] * TILE_SIZE + TILE_SIZE // 2
            )

            # 跳过起点附近和终点房间的怪物生成
            is_start_room = self._manhattan_dist(room_center_pixel, self.start_room) < 100
            is_end_room = self._manhattan_dist(room_center_pixel, self.end_room) < 100

            if is_start_room or is_end_room:
                continue  # 跳过起点和终点房间

            # 随机选择怪物类型
            monster_type = self.monster_loader.get_random_monster_type()
            if monster_type:
                monster = Monster(
                    monster_type=monster_type,
                    monster_loader=self.monster_loader,
                    room=room,
                    map_instance=self.map
                )
                self.monsters.append(monster)
                print(f"生成怪物：{monster_type}（房间中心：{room_center_pixel}）")
        print(f"怪物生成完成，共 {len(self.monsters)} 个怪物")

    # ---------------- 路径计算 ----------------

    def _find_farthest_room_by_path(self, start_pos):
        if not self.room_centers or len(self.room_centers) < 2:
            return None, 0

        start_room = self._find_closest_room_center(start_pos[0], start_pos[1])

        visited = {start_room: 0}
        queue = deque([(start_room, 0)])

        max_distance = 0
        farthest_room = start_room

        while queue:
            current_room, current_dist = queue.popleft()

            for room_center in self.room_centers:
                if room_center not in visited:
                    if self._rooms_connected(current_room, room_center):
                        path_dist = current_dist + self._manhattan_dist(current_room, room_center)
                        visited[room_center] = path_dist
                        queue.append((room_center, path_dist))

                        if path_dist > max_distance:
                            max_distance = path_dist
                            farthest_room = room_center

        return farthest_room, max_distance

    def _rooms_connected(self, room1, room2):
        from game.core.map import TILE_SIZE

        x1, y1 = int(room1[0] // TILE_SIZE), int(room1[1] // TILE_SIZE)
        x2, y2 = int(room2[0] // TILE_SIZE), int(room2[1] // TILE_SIZE)

        if not (0 <= x1 < self.map.width and 0 <= y1 < self.map.height):
            return False
        if not (0 <= x2 < self.map.width and 0 <= y2 < self.map.height):
            return False

        visited = set()
        queue = deque([(x1, y1)])
        visited.add((x1, y1))

        max_steps = 1000
        steps = 0

        while queue and steps < max_steps:
            x, y = queue.popleft()
            steps += 1

            if x == x2 and y == y2:
                return True

            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nx, ny = x + dx, y + dy
                if (nx, ny) not in visited:
                    if 0 <= nx < self.map.width and 0 <= ny < self.map.height:
                        if self.map.tiles[ny][nx] == TILE_EMPTY:
                            visited.add((nx, ny))
                            queue.append((nx, ny))

        return False

    # ---------------- 内部逻辑 ----------------

    def _manhattan_dist(self, pos1, pos2):
        return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])

    def _find_closest_room_center(self, x, y):
        if not self.room_centers:
            return (x, y)
        return min(self.room_centers, key=lambda c: self._manhattan_dist((x, y), c))

    def _handle_player_movement(self):
        if self.victory:
            self.player.set_animation_state(is_moving=False)
            return
        # 记录移动前的位置（用于碰撞回弹）
        self.last_player_x = self.player.x
        self.last_player_y = self.player.y

        keys = pygame.key.get_pressed()
        dx, dy = 0, 0

        if keys[pygame.K_w]:
            dy -= self.move_speed
        if keys[pygame.K_s]:
            dy += self.move_speed
        if keys[pygame.K_a]:
            dx -= self.move_speed
        if keys[pygame.K_d]:
            dx += self.move_speed

        # 斜向速度修正
        if dx != 0 and dy != 0:
            factor = 0.7071
            dx = int(dx * factor)
            dy = int(dy * factor)

        new_x = self.player.x + dx
        new_y = self.player.y + dy
        r = self.player.radius

        if self._can_move(new_x, self.player.y, r):
            self.player.x = new_x
        if self._can_move(self.player.x, new_y, r):
            self.player.y = new_y

        is_moving = dx != 0 or dy != 0
        if is_moving:
            self.player.set_direction(dx, dy)
        self.player.set_animation_state(is_moving)

    def _can_move(self, x, y, radius):
        points = [
            (x - radius, y),
            (x + radius, y),
            (x, y - radius),
            (x, y + radius)
        ]

        for px, py in points:
            if not self.map.is_passable(px, py):
                return False
        return True

    def _check_victory(self):
        if self._manhattan_dist((self.player.x, self.player.y), self.end_room) <= 30:
            self.victory = True
            self.state = "victory"
            print("到达最远房间！游戏胜利！")

    # ---------------- 更新与绘制 ----------------

    def update(self):
        delta_time = self.clock.tick(self.FPS)

        if self.state == "game" and not self.victory:
            self._handle_player_movement()
            self._check_victory()
            self._check_monster_collision()  # 移动碰撞检测到攻击逻辑前

            # 处理玩家攻击
            self._handle_player_attack()
            # 更新怪物和他们的 projectile
            for monster in self.monsters[:]:
                monster.check_player_in_room(self.player.x, self.player.y)
                monster.update_behavior(self.player.x, self.player.y)
                monster.update_projectiles()  # 更新小点
                monster.update_animation()

                # 检测小点是否命中玩家
                if monster.is_ranged:
                    for projectile in monster.projectiles[:]:
                        if projectile.check_collision(self.player):
                            self._handle_projectile_hit()
                            monster.projectiles.remove(projectile)
                            break

                # 移除死亡怪物
                if monster.current_health <= 0:
                    self.particles.spawn_burst(
                        monster.x,
                        monster.y,
                        monster.get_death_color(),
                    )
                    self.monsters.remove(monster)

        # 让动画永远更新（防止 idle 停住）
        self.player.update_animation(delta_time)

        self.lasers = [laser for laser in self.lasers if laser.is_alive()]
        self.particles.update(delta_time)

        # 相机平滑跟随
        target_x = self.player.x - self.screen.get_width() // 2
        target_y = self.player.y - self.screen.get_height() // 2

        self.camera_x += int((target_x - self.camera_x) * 0.1)
        self.camera_y += int((target_y - self.camera_y) * 0.1)

    def draw(self):
        self.screen.fill(BLACK)
        self.map.render(self.screen, self.camera_x, self.camera_y)

        # ---------------- 新增：绘制怪物（在地图之后、玩家之前） ----------------
        for monster in self.monsters:
            monster.draw(self.screen, self.camera_x, self.camera_y)

        self.particles.draw(self.screen, self.camera_x, self.camera_y)
        for laser in self.lasers:
            laser.draw(self.screen, self.camera_x, self.camera_y)

        # 玩家绘制（永远在画面中心）
        px = self.screen.get_width() // 2
        py = self.screen.get_height() // 2
        self.player.draw(self.screen, px, py)

        # 终点标记
        end_x = self.end_room[0] - self.camera_x
        end_y = self.end_room[1] - self.camera_y

        pulse = abs(math.sin(pygame.time.get_ticks() * 0.003)) * 0.5 + 0.5
        outer_radius = int(20 + pulse * 8)

        pygame.draw.circle(self.screen, GOLD, (int(end_x), int(end_y)), outer_radius, 2)

        angle = pygame.time.get_ticks() * 0.002
        for i in range(8):
            a = angle + i * math.pi / 4
            x1 = end_x + math.cos(a) * 15
            y1 = end_y + math.sin(a) * 15
            x2 = end_x + math.cos(a) * 8
            y2 = end_y + math.sin(a) * 8
            pygame.draw.line(self.screen, YELLOW, (int(x1), int(y1)), (int(x2), int(y2)), 2)

        pygame.draw.circle(self.screen, GOLD, (int(end_x), int(end_y)), 6)
        pygame.draw.circle(self.screen, ORANGE, (int(end_x), int(end_y)), 3)

        # HUD 信息
        hint_text = (
            f"坐标: ({int(self.player.x)}, {int(self.player.y)}) | "
            f"距终点: {int(self._manhattan_dist((self.player.x, self.player.y), self.end_room))} | "
            f"按J攻击(激光)，按K闪避"
        )
        text_surface = self.font.render(hint_text, True, WHITE)
        self.screen.blit(text_surface, (10, 10))

        # 胜利界面
        if self.victory:
            victory_text = "到达最远房间！按R重新开始"
            surface = self.font.render(victory_text, True, GREEN)
            rect = surface.get_rect(center=(self.screen.get_width() // 2,
                                           self.screen.get_height() // 2))
            bg_rect = rect.inflate(20, 10)
            pygame.draw.rect(self.screen, BLACK, bg_rect)
            pygame.draw.rect(self.screen, GOLD, bg_rect, 2)
            self.screen.blit(surface, rect)

        # 新增：死亡界面
        if self.state == "gameover":
            gameover_text = "游戏结束！按R重新开始"
            surface = self.font.render(gameover_text, True, RED)
            rect = surface.get_rect(center=(self.screen.get_width() // 2,
                                            self.screen.get_height() // 2))
            bg_rect = rect.inflate(20, 10)
            pygame.draw.rect(self.screen, BLACK, bg_rect)
            pygame.draw.rect(self.screen, RED, bg_rect, 2)
            self.screen.blit(surface, rect)

        pygame.display.flip()

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:
                # J 攻击
                if event.key == pygame.K_j:
                    if not self.victory:
                        self.player.start_attack()
                    continue

                # K 闪避
                if event.key == pygame.K_k:
                    if not self.victory:
                        self.player.start_evade()
                    continue

                # 胜利界面 R 重开
                if event.key == pygame.K_r and self.victory:
                    try:
                        self.__init__(self.screen, self.font)
                        if len(self.map.get_room_centers()) < 2:
                            self.__init__(self.screen, self.font)
                    except Exception as e:
                        print(f"地图生成失败，重试: {e}")
                        self.__init__(self.screen, self.font)
                    continue
                # 死亡或胜利界面 R 重开
                if event.key == pygame.K_r and (self.victory or self.state == "gameover"):
                    try:
                        self.__init__(self.screen, self.font)
                        if len(self.map.get_room_centers()) < 2:
                            self.__init__(self.screen, self.font)
                    except Exception as e:
                        print(f"地图生成失败，重试: {e}")
                        self.__init__(self.screen, self.font)
                    continue

                # ESC 退出
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()

    # 在_handle_player_attack方法中修改，确保按J立即播放音效
    def _handle_player_attack(self):
        if not self.player.is_attacking:
            return

        # 立即播放攻击音效（无需命中检测）
        current_time = pygame.time.get_ticks()
        # 200毫秒冷却，防止快速按J重复播放
        if current_time - self.last_attack_sound_time > 200:
            if self.attack_sound:
                self.attack_sound.play()
            self.last_attack_sound_time = current_time

        if self.player.consume_attack_emit(current_time):
            laser = LaserBeam(self.player.x, self.player.y, self.player.direction)
            self.lasers.append(laser)
            if self._apply_laser_damage(laser):
                self.player.attack_hit = True

        # 攻击命中检测逻辑（仅在未命中过的情况下检测）
        if not self.player.attack_hit:
            attack_range = 30
            player_radius = self.player.radius
            for monster in self.monsters:
                if not monster.is_active:
                    continue
                dist = math.hypot(self.player.x - monster.x, self.player.y - monster.y)
                if dist < player_radius + attack_range:
                    # 攻击命中，怪物扣血
                    monster.current_health -= 1
                    self.player.attack_hit = True  # 标记为已命中
                    print(f"击中 {monster.type}! 剩余生命值: {monster.current_health}")
                    break

        # 不提前结束攻击状态，让动画完整播放

    def _apply_laser_damage(self, laser):
        x1, y1, x2, y2 = laser.get_segment()
        hit_any = False
        for monster in self.monsters:
            if not monster.is_active:
                continue
            dist = self._distance_point_to_segment(monster.x, monster.y, x1, y1, x2, y2)
            if dist <= monster.hit_radius + laser.width:
                monster.current_health -= 2
                hit_any = True
        return hit_any

    def _distance_point_to_segment(self, px, py, x1, y1, x2, y2):
        dx = x2 - x1
        dy = y2 - y1
        if dx == 0 and dy == 0:
            return math.hypot(px - x1, py - y1)
        t = ((px - x1) * dx + (py - y1) * dy) / (dx * dx + dy * dy)
        t = max(0.0, min(1.0, t))
        closest_x = x1 + t * dx
        closest_y = y1 + t * dy
        return math.hypot(px - closest_x, py - closest_y)

    # 在game_engine.py的_check_monster_collision方法中修改，约420-446行
    def _check_monster_collision(self):
        """检测玩家与怪物的碰撞并处理扣血（添加冷却机制和闪避无敌）"""
        current_time = pygame.time.get_ticks()
        # 检查是否在冷却时间内（2000毫秒 = 2秒）或玩家正在闪避
        if current_time - self.last_damage_time < 2000 or self.player.is_evading:
            return  # 闪避时直接返回，不进行扣血检测

        player_radius = self.player.radius
        for monster in self.monsters:
            if monster.is_active and monster.current_health > 0:  # 只检测激活且存活的怪物
                dist = math.hypot(self.player.x - monster.x, self.player.y - monster.y)
                if dist < player_radius + monster.hit_radius:
                    # 玩家扣血
                    if self.player.current_health > 0:
                        self.player.current_health -= 1
                        self.last_damage_time = current_time  # 更新最后扣血时间
                        print(f"玩家受伤! 剩余生命值: {self.player.current_health}")

                    # 碰撞回弹
                    self.player.x = self.last_player_x
                    self.player.y = self.last_player_y

                    # 玩家死亡处理
                    if self.player.current_health <= 0:
                        print("玩家死亡!")
                        self.state = "gameover"
                    break

    # 添加处理 projectile 命中的方法
    def _handle_projectile_hit(self):
        """处理小点命中玩家"""
        current_time = pygame.time.get_ticks()
        # 检查冷却和闪避状态
        if current_time - self.last_damage_time < 2000 or self.player.is_evading:
            return

        # 玩家扣血
        if self.player.current_health > 0:
            self.player.current_health -= 1
            self.last_damage_time = current_time
            print(f"玩家被远程攻击击中! 剩余生命值: {self.player.current_health}")

        # 玩家死亡处理
        if self.player.current_health <= 0:
            print("玩家死亡!")
            self.state = "gameover"
