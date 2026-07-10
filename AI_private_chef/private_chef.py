# -*- coding: utf-8 -*-
"""
私人厨师智能食谱推荐系统 —— 命令行 Demo
用法：python private_chef.py
"""

from agent import chat

IMAGE_URL = "https://img95.699pic.com/photo/50586/2246.jpg_wh860.jpg"

if __name__ == "__main__":
    print("=" * 60)
    print("    Private Chef - CLI Demo")
    print("=" * 60)
    print(f"\nImage: {IMAGE_URL}")
    print("Question: help me see what I can cook\n")
    print("Thinking...\n")

    messages = chat(
        text="帮我看看能做什么",
        image_source=IMAGE_URL,
        thread_id="cli_demo",
    )

    for m in messages:
        m.pretty_print()

    print("\nDone. For web UI run: streamlit run app.py")
