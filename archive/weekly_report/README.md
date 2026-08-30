# 文件自动归类工具 + mock 周报接口

这个文件夹混了好几个不相关的东西，都是早期练习：

- `file_organizer.py` + `file_organizer_gui.py` —— 用 stdlib `os`/`shutil` 把文件按扩展名归类，并用 `tkinter` 做了个图形界面（选文件夹 → 一点归类 → 弹窗提示）。
- `app.py` —— 一个 **mock** 的 Flask 接口 `POST /generate_report`，返回**硬编码**的"模拟周报"，没有调任何大模型。
- `llm_test.py` —— 用 OpenAI SDK 调 Kimi/Moonshot 的连通性冒烟测试。

> ⚠️ 已知问题：GUI 从 `file_organizer` 导入的是 `organize_by_extension`，但 `file_organizer.py` 里定义的其实是 `organize_files` —— **函数名对不上**，直接跑 GUI 会报错。这是练习骨架遗留的坑。

**为什么在 archive**：大多是练习骨架 + mock 接口，算不上 AI 作品；唯一像样的"文件自动归类工具"也不是 Agent 项目。原 README 是一份作品集待办清单，已用本 README 替换。

## 怎么跑（仅供参考）

- 命令行版整理器：`python file_organizer.py`
- GUI 版整理器（需先修正函数名）：`python file_organizer_gui.py`
- mock 接口：`python app.py`，然后 `POST /generate_report`
