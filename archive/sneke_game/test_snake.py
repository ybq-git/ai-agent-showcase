"""
贪吃蛇游戏的 headless 冒烟测试
在 Windows 上可以用 dummy 视频驱动在后台运行，无需真实显示器窗口
"""

import os
import sys

# 设置无头渲染驱动，避免弹出窗口
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

# 把项目目录加入模块搜索路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from snake_game import SnakeGame, GRID_WIDTH, GRID_HEIGHT, RIGHT, UP


def test_initialization():
    """测试游戏能正常初始化"""
    game = SnakeGame()
    assert len(game.snake) == 3, f"初始蛇长度应为 3，实际是 {len(game.snake)}"
    assert game.direction == RIGHT
    assert game.score == 0
    assert not game.game_over
    assert game.food not in game.snake
    print("[OK] 初始化测试通过")
    game.run = lambda: None  # 阻止真正进入主循环
    pygame = __import__("pygame")
    pygame.quit()


def test_movement_and_growth():
    """测试蛇移动和吃食物增长"""
    game = SnakeGame()
    game.run = lambda: None

    # 强制把食物放到蛇头前方，模拟吃到食物
    head_x, head_y = game.snake[0]
    game.food = (head_x + 1, head_y)

    initial_length = len(game.snake)
    initial_score = game.score

    game.update()  # 向前移动一格，吃到食物

    assert len(game.snake) == initial_length + 1, "吃到食物后蛇身应增长"
    assert game.score == initial_score + 10, "吃到食物后分数应增加 10"
    print("[OK] 移动与增长测试通过")
    pygame = __import__("pygame")
    pygame.quit()


def test_wall_collision():
    """测试撞墙游戏结束"""
    game = SnakeGame()
    game.run = lambda: None

    # 把蛇头放到最右边，方向朝右，下一帧会撞墙
    game.snake[0] = (GRID_WIDTH - 1, game.snake[0][1])
    game.direction = RIGHT
    game.next_direction = RIGHT

    game.update()

    assert game.game_over, "撞墙后游戏应结束"
    print("[OK]撞墙检测测试通过")
    pygame = __import__("pygame")
    pygame.quit()


def test_self_collision():
    """测试撞到自己游戏结束"""
    game = SnakeGame()
    game.run = lambda: None

    # 构造一个 U 形，让蛇头下一步会撞到自己的身体
    # 原蛇: [(10, 10), (9, 10), (8, 10)]
    game.snake = [
        (10, 10),
        (9, 10),
        (9, 11),
        (10, 11),
    ]
    game.direction = UP
    game.next_direction = UP

    # 蛇头 (10, 10) 向上到 (10, 9) 不会撞，这里改成让它撞到自己的身体
    game.snake = [
        (10, 10),
        (10, 11),
        (9, 11),
        (9, 10),
    ]
    game.direction = RIGHT
    game.next_direction = RIGHT
    # 头 (10,10) 向右到 (11,10) 不会撞，重新构造：
    # 让头旁边就是自己的身体
    game.snake = [
        (10, 10),
        (11, 10),
        (11, 9),
        (10, 9),
        (9, 9),
        (9, 10),
    ]
    game.direction = RIGHT
    game.next_direction = RIGHT
    # 头 (10,10) 向右到 (11,10)，(11,10) 是身体，会撞到自己

    game.update()
    assert game.game_over, "撞到自己后游戏应结束"
    print("[OK]撞自己检测测试通过")
    pygame = __import__("pygame")
    pygame.quit()


def test_direction_reverse_prevention():
    """测试不能直接反向移动"""
    game = SnakeGame()
    game.run = lambda: None

    # 模拟按下与当前方向相反的按键
    pygame = __import__("pygame")
    event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_LEFT)
    pygame.event.post(event)

    game.handle_events()

    # 当前方向是 RIGHT，按 LEFT 应被忽略
    assert game.next_direction == RIGHT, "不能直接反向移动"
    print("[OK]反向移动屏蔽测试通过")
    pygame.quit()


if __name__ == "__main__":
    print("开始 headless 测试...\n")
    test_initialization()
    test_movement_and_growth()
    test_wall_collision()
    test_self_collision()
    test_direction_reverse_prevention()
    print("\n[ALL TESTS PASSED] 所有测试全部通过！")
