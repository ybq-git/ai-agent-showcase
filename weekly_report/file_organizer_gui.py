# 使用 python 标准库 tkinter 为文件整理器提供图形界面
# 窗口大小 400x200，标题“文件自动归类工具”。
# 界面包含：一个标签“选择要整理的文件夹：”，一个输入框（只读），一个“浏览”按钮
# （点击后弹出文件夹选择对话框），一个“开始整理”按钮（点击后调用 organize_by_extension
# 函数并弹出“整理完成！”消息框）。
# 请生成完整的 GUI 代码。

import tkinter as tk                      # 导入 tkinter 模块，并简写为 tk，用于创建 GUI 界面
from tkinter import filedialog, messagebox # 从 tkinter 中导入文件对话框和消息提示框组件
from file_organizer import organize_by_extension  # 从 file_organizer 模块导入按扩展名整理文件的函数


def browse_folder():                      # 定义“浏览文件夹”按钮的回调函数
    folder_selected = filedialog.askdirectory()  # 弹出文件夹选择对话框，返回用户选择的文件夹路径
    if folder_selected:                   # 判断是否确实选择了文件夹（未点取消）
        folder_path_var.set(folder_selected)  # 将选择的路径设置到界面输入框关联的变量中


def start_organize():                     # 定义“开始整理”按钮的回调函数
    path = folder_path_var.get()          # 从输入框关联的变量中获取当前文件夹路径
    if not path:                          # 判断路径是否为空，即用户是否还没选择文件夹
        messagebox.showwarning("提示", "请先选择一个文件夹")  # 弹出警告框提示用户先选择文件夹
        return                            # 结束函数，不再继续执行后面的整理逻辑
    result = organize_by_extension(path)  # 调用整理函数，对所选文件夹按扩展名分类整理
    messagebox.showinfo("完成", result)   # 弹出信息框，显示整理完成的结果提示


# 创建主窗口
root = tk.Tk()                            # 创建 tkinter 主窗口对象，作为整个 GUI 的容器
root.title("文件自动归类工具")            # 设置窗口标题栏显示的标题
root.geometry("400x200")                  # 设置窗口的初始大小为宽 400 像素、高 200 像素

# 变量
folder_path_var = tk.StringVar()          # 创建一个字符串类型的 tkinter 变量，用于和输入框双向绑定

# 标签
label = tk.Label(root, text="选择要整理的文件夹：")  # 创建一个标签控件，显示提示文字
label.pack(pady=10)                       # 将标签添加到窗口中，上下留出 10 像素的内边距

# 输入框
entry = tk.Entry(root, textvariable=folder_path_var, state="readonly", width=50)  # 创建只读输入框，绑定变量，宽度 50 字符
entry.pack()                              # 将输入框添加到窗口中

# 浏览按钮
browse_btn = tk.Button(root, text="浏览", command=browse_folder)  # 创建“浏览”按钮，点击时调用 browse_folder 函数
browse_btn.pack(pady=5)                   # 将浏览按钮添加到窗口中，上下留出 5 像素的内边距

# 开始整理按钮
organize_btn = tk.Button(root, text="开始整理", command=start_organize, bg="lightblue")  # 创建“开始整理”按钮，设置背景色为浅蓝色
organize_btn.pack(pady=10)                # 将开始整理按钮添加到窗口中，上下留出 10 像素的内边距

root.mainloop()                           # 进入 tkinter 主事件循环，等待用户交互，保持窗口显示
