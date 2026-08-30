# 贪吃蛇（Pygame）

用 Pygame 写的经典贪吃蛇小游戏：方向键 / WASD 控制，ESC 退出，死后按 R 重开。

- 自带一个 **headless 冒烟测试** `test_snake.py`：用 dummy 视频/音频驱动在后台运行，不弹窗口也能验证逻辑。

**为什么在 archive**：这是个**用 Python 写的、和 AI Agent 无关的小游戏**。放 AI 作品集主页会显得"跑题"，所以归档。但它本身能跑、能展示通用编程能力——哪天想展示 Python 基本功可以单独拎出来。

## 怎么跑

1. `pip install pygame`
2. `python snake_game.py`（游戏）；`python test_snake.py`（无头测试）

## 文件

- `snake_game.py` —— 主游戏
- `test_snake.py` —— 无头冒烟测试
