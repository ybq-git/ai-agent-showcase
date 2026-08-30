#把一个列表的所有字符串都反转，并返回新列表
def reverse_strings_in_list(string_list):
    # 列表推导：遍历 string_list 中的每个字符串 s，使用切片 s[::-1] 将字符串反转，
    # 并把所有反转后的字符串组成一个新的列表返回
    return [s[::-1] for s in string_list]

#测试
test_list = ["hello", "world", "python"]
print(reverse_strings_in_list(test_list))  # 输出: ['olleh', 'dlrow', 'nohtyp'] 

def batch_rename_files(folder_path, old_str, new_str):
    """将文件夹内所有包含old_str的文件名替换为new_str"""
    import os
    for filename in os.listdir(folder_path):
        if old_str in filename:
            old_file = os.path.join(folder_path, filename)
            new_file = os.path.join(folder_path, filename.replace(old_str, new_str))
            os.rename(old_file, new_file)