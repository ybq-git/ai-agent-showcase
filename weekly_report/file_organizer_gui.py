# 使用 python 标准库 tkinter 为文件整理器提供图形界面
# 窗口大小 400x200，标题“文件自动归类工具”。
# 界面包含：一个标签“选择要整理的文件夹：”，一个输入框（只读），一个“浏览”按钮
# （点击后弹出文件夹选择对话框），一个“开始整理”按钮（点击后调用 organize_by_extension
# 函数并弹出“整理完成！”消息框）。
# 请生成完整的 GUI 代码。

import tkinter as tk
from tkinter import filedialog, messagebox
from file_organizer import organize_by_extension


def browse_folder():
    folder_selected = filedialog.askdirectory()
    if folder_selected:
        folder_path_var.set(folder_selected)


def start_organize():
    path = folder_path_var.get()
    if not path:
        messagebox.showwarning("提示", "请先选择一个文件夹")
        return
    result = organize_by_extension(path)
    messagebox.showinfo("完成", result)


# 创建主窗口
root = tk.Tk()
root.title("文件自动归类工具")
root.geometry("400x200")

# 变量
folder_path_var = tk.StringVar()

# 标签
label = tk.Label(root, text="选择要整理的文件夹：")
label.pack(pady=10)

# 输入框
entry = tk.Entry(root, textvariable=folder_path_var, state="readonly", width=50)
entry.pack()

# 浏览按钮
browse_btn = tk.Button(root, text="浏览", command=browse_folder)
browse_btn.pack(pady=5)

# 开始整理按钮
organize_btn = tk.Button(root, text="开始整理", command=start_organize, bg="lightblue")
organize_btn.pack(pady=10)

root.mainloop()
