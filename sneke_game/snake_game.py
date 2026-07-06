"""
贪吃蛇游戏 (Snake Game)
使用 Pygame 编写的经典贪吃蛇小游戏

运行方式:
    python snake_game.py

控制:
    ↑ ↓ ← →  或  W S A D  控制方向
    ESC      退出游戏
    游戏结束后按 R 重新开始
"""

import random
import sys
from typing import List, Tuple

import pygame

# --- 游戏配置 ---
WINDOW_WIDTH = 640
WINDOW_HEIGHT = 480
GRID_SIZE = 20
GRID_WIDTH = WINDOW_WIDTH // GRID_SIZE
GRID_HEIGHT = WINDOW_HEIGHT // GRID_SIZE

# 颜色定义 (R, G, B)
COLOR_BACKGROUND = (20, 20, 20)
COLOR_GRID_LINE = (40, 40, 40)
COLOR_SNAKE_HEAD = (0, 200, 0)
COLOR_SNAKE_BODY = (0, 255, 0)
COLOR_SNAKE_OUTLINE = (0, 150, 0)
COLOR_FOOD = (255, 50, 50)
COLOR_FOOD_GLOW = (180, 30, 30)
COLOR_TEXT = (255, 255, 255)
COLOR_GAME_OVER = (255, 80, 80)

# 帧率（蛇移动速度）
FPS = 10

# 方向常量
UP = (0, -1)
DOWN = (0, 1)
LEFT = (-1, 0)
RIGHT = (1, 0)

Point = Tuple[int, int]


class SnakeGame:
    def __init__(self) -> None:
        pygame.init()
        pygame.display.set_caption("贪吃蛇 Snake Game")
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("simhei", 28)
        self.big_font = pygame.font.SysFont("simhei", 48)
        self.reset_game()

    def reset_game(self) -> None:
        """重置游戏状态"""
        start_x = GRID_WIDTH // 2
        start_y = GRID_HEIGHT // 2
        self.snake: List[Point] = [
            (start_x, start_y),
            (start_x - 1, start_y),
            (start_x - 2, start_y),
        ]
        self.direction = RIGHT
        self.next_direction = RIGHT
        self.score = 0
        self.game_over = False
        self.food = self.spawn_food()

    def spawn_food(self) -> Point:
        """在空白位置生成食物"""
        while True:
            food = (
                random.randint(0, GRID_WIDTH - 1),
                random.randint(0, GRID_HEIGHT - 1),
            )
            if food not in self.snake:
                return food

    def handle_events(self) -> bool:
        """处理输入事件，返回 False 表示需要退出游戏"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return False

                if self.game_over:
                    if event.key == pygame.K_r:
                        self.reset_game()
                    continue

                # 防止直接反向移动
                if event.key in (pygame.K_UP, pygame.K_w):
                    if self.direction != DOWN:
                        self.next_direction = UP
                elif event.key in (pygame.K_DOWN, pygame.K_s):
                    if self.direction != UP:
                        self.next_direction = DOWN
                elif event.key in (pygame.K_LEFT, pygame.K_a):
                    if self.direction != RIGHT:
                        self.next_direction = LEFT
                elif event.key in (pygame.K_RIGHT, pygame.K_d):
                    if self.direction != LEFT:
                        self.next_direction = RIGHT

        return True

    def update(self) -> None:
        """更新游戏逻辑"""
        if self.game_over:
            return

        self.direction = self.next_direction

        head_x, head_y = self.snake[0]
        new_head = (
            head_x + self.direction[0],
            head_y + self.direction[1],
        )

        # 撞墙检测
        if (
            new_head[0] < 0
            or new_head[0] >= GRID_WIDTH
            or new_head[1] < 0
            or new_head[1] >= GRID_HEIGHT
        ):
            self.game_over = True
            return

        # 撞自己检测
        if new_head in self.snake:
            self.game_over = True
            return

        self.snake.insert(0, new_head)

        # 吃食物检测
        if new_head == self.food:
            self.score += 10
            self.food = self.spawn_food()
        else:
            self.snake.pop()

    def draw_grid(self) -> None:
        """绘制背景网格"""
        for x in range(0, WINDOW_WIDTH, GRID_SIZE):
            pygame.draw.line(self.screen, COLOR_GRID_LINE, (x, 0), (x, WINDOW_HEIGHT))
        for y in range(0, WINDOW_HEIGHT, GRID_SIZE):
            pygame.draw.line(self.screen, COLOR_GRID_LINE, (0, y), (WINDOW_WIDTH, y))

    def draw_snake(self) -> None:
        """绘制蛇"""
        for index, segment in enumerate(self.snake):
            rect = pygame.Rect(
                segment[0] * GRID_SIZE,
                segment[1] * GRID_SIZE,
                GRID_SIZE,
                GRID_SIZE,
            )
            color = COLOR_SNAKE_HEAD if index == 0 else COLOR_SNAKE_BODY
            pygame.draw.rect(self.screen, color, rect, border_radius=4)
            pygame.draw.rect(self.screen, COLOR_SNAKE_OUTLINE, rect, width=1, border_radius=4)

            # 画眼睛（只在头部）
            if index == 0:
                self.draw_eyes(segment, rect)

    def draw_eyes(self, segment: Point, rect: pygame.Rect) -> None:
        """绘制蛇的眼睛"""
        eye_size = 4
        offset = 5

        if self.direction == RIGHT:
            eye1 = (rect.right - offset, rect.top + offset)
            eye2 = (rect.right - offset, rect.bottom - offset)
        elif self.direction == LEFT:
            eye1 = (rect.left + offset, rect.top + offset)
            eye2 = (rect.left + offset, rect.bottom - offset)
        elif self.direction == UP:
            eye1 = (rect.left + offset, rect.top + offset)
            eye2 = (rect.right - offset, rect.top + offset)
        else:  # DOWN
            eye1 = (rect.left + offset, rect.bottom - offset)
            eye2 = (rect.right - offset, rect.bottom - offset)

        for eye in (eye1, eye2):
            pygame.draw.circle(self.screen, COLOR_TEXT, eye, eye_size)

    def draw_food(self) -> None:
        """绘制食物"""
        center = (
            self.food[0] * GRID_SIZE + GRID_SIZE // 2,
            self.food[1] * GRID_SIZE + GRID_SIZE // 2,
        )
        pygame.draw.circle(self.screen, COLOR_FOOD_GLOW, center, GRID_SIZE // 2 - 1)
        pygame.draw.circle(self.screen, COLOR_FOOD, center, GRID_SIZE // 2 - 4)

    def draw_score(self) -> None:
        """绘制分数"""
        score_text = self.font.render(f"得分: {self.score}", True, COLOR_TEXT)
        self.screen.blit(score_text, (10, 10))

    def draw_game_over(self) -> None:
        """绘制游戏结束界面"""
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
        overlay.set_alpha(180)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))

        game_over_text = self.big_font.render("游戏结束", True, COLOR_GAME_OVER)
        score_text = self.font.render(f"最终得分: {self.score}", True, COLOR_TEXT)
        restart_text = self.font.render("按 R 重新开始", True, COLOR_TEXT)

        self.screen.blit(
            game_over_text,
            (
                WINDOW_WIDTH // 2 - game_over_text.get_width() // 2,
                WINDOW_HEIGHT // 2 - 60,
            ),
        )
        self.screen.blit(
            score_text,
            (
                WINDOW_WIDTH // 2 - score_text.get_width() // 2,
                WINDOW_HEIGHT // 2 + 10,
            ),
        )
        self.screen.blit(
            restart_text,
            (
                WINDOW_WIDTH // 2 - restart_text.get_width() // 2,
                WINDOW_HEIGHT // 2 + 55,
            ),
        )

    def draw(self) -> None:
        """渲染整个画面"""
        self.screen.fill(COLOR_BACKGROUND)
        self.draw_grid()
        self.draw_food()
        self.draw_snake()
        self.draw_score()

        if self.game_over:
            self.draw_game_over()

        pygame.display.flip()

    def run(self) -> None:
        """主循环"""
        running = True
        while running:
            running = self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(FPS)

        pygame.quit()
        sys.exit()


def main() -> None:
    game = SnakeGame()
    game.run()


if __name__ == "__main__":
    main()
