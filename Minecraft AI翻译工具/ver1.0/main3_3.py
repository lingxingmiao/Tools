import tkinter as tk
from tkinter import filedialog
from pathlib import Path

def compare_lang_files():
    # 获取文件路径
    file1 = filedialog.askopenfilename(title="选择第一个.lang文件", filetypes=[("Lang files", "*.lang")])
    file2 = filedialog.askopenfilename(title="选择第二个.lang文件", filetypes=[("Lang files", "*.lang")])
    
    if not file1 or not file2:
        return
    
    # 读取文件内容
    def read_lang_file(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            return {line.split('=')[0].strip(): line.strip() for line in f if '=' in line}
    
    dict1 = read_lang_file(file1)
    dict2 = read_lang_file(file2)
    
    # 找出差异
    missing_in_1 = [dict2[key] for key in dict2 if key not in dict1]
    missing_in_2 = [dict1[key] for key in dict1 if key not in dict2]
    
    # 输出到nolang.lang
    with open('nolang.lang', 'w', encoding='utf-8') as f:
        if missing_in_1:
            f.write(f"# Missing in {Path(file1).name}\n")
            f.write('\n'.join(missing_in_1) + '\n\n')
        if missing_in_2:
            f.write(f"# Missing in {Path(file2).name}\n")
            f.write('\n'.join(missing_in_2) + '\n')
    
    result_text = f"比较完成！结果已保存到nolang.lang\n"
    result_text += f"{Path(file1).name}中缺少的键: {len(missing_in_1)}\n"
    result_text += f"{Path(file2).name}中缺少的键: {len(missing_in_2)}"
    result_label.config(text=result_text)

# 创建GUI
root = tk.Tk()
root.title("语言文件比较工具")
root.geometry("500x300")

tk.Label(root, text="语言文件比较工具", font=('Arial', 14)).pack(pady=10)
tk.Button(root, text="选择并比较.lang文件", command=compare_lang_files).pack(pady=20)
result_label = tk.Label(root, text="", wraplength=400)
result_label.pack()

root.mainloop()
