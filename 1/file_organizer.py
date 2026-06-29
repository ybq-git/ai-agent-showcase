3.	# 函数功能：遍历指定文件夹，按文件扩展名自动归类并移动到对应子文件夹。
4.	# 例如 .txt 移动到 txt/ 下，.jpg 移动到 jpg/ 下。
# 请使用 os 和 shutil 标准库实现，包含完整的函数定义与注释。
import os
import shutil

def organize_files(folder_path):
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        if os.path.isfile(file_path):
            # 获取文件扩展名
            _, ext = os.path.splitext(filename)
            # 去掉扩展名前面的点
            ext = ext[1:]
            # 创建子文件夹
            subfolder_path = os.path.join(folder_path, ext)
            if not os.path.exists(subfolder_path):
                os.makedirs(subfolder_path)
            # 移动文件
            shutil.move(file_path, os.path.join(subfolder_path, filename))      
            # 测试代码，让用户输入文件夹路径并显示结果
if __name__ == "__main__":
    folder_path = input("请输入要整理的文件夹路径: ")
    if os.path.exists(folder_path) and os.path.isdir(folder_path):
        organize_files(folder_path)
        print("文件整理完成！")
    else:
        print("输入的路径无效，请确保是一个存在的文件夹。")

