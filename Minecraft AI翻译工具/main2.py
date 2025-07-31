import tkinter as tk
from tkinter import scrolledtext
import os
from tkinterdnd2 import TkinterDnD, DND_FILES
import threading
from tkinter import ttk

def interlace_texts(text1, text2):
    """根据键值对规则合并两段文本"""
    # 解析第一段文本为字典 {key: value}
    dict1 = {}
    for line in text1.split('\n'):
        if '=' in line:
            key, value = line.split('=', 1)
            dict1[key.strip()] = value.strip()
    
    # 解析第二段文本为字典 {key: value}
    dict2 = {}
    for line in text2.split('\n'):
        if '=' in line:
            key, value = line.split('=', 1)
            dict2[key.strip()] = value.strip()
    
    # 合并匹配的键，过滤空值
    result = []
    for key in dict1:
        if key in dict2:
            val1 = dict1[key]
            val2 = dict2[key]
            if val1 and val2:  # 两个值都不为空才输出
                result.append(f"{val1}={val2}")
    
    return '\n'.join(result)

from difflib import SequenceMatcher

class TextProcessor:
    def __init__(self):
        self.length_threshold = 100
        self.similarity_threshold = 0.8
        self.progress = 0
        self.running = False
        self.enable_similarity_check = True

    def is_similar(self, a, b):
        """检查两行是否相似（基于字符串相似度）"""
        return SequenceMatcher(None, a, b).ratio() >= self.similarity_threshold

    def remove_similar_lines(self, text, progress_callback=None):
        """
        去除相似的和过长的行
        - 使用实例变量中的阈值参数
        - 支持进度回调
        """
        lines = text.split('\n')
        result = []
        self.running = True
        
        for i, line in enumerate(lines):
            if not self.running:
                break
                
            stripped = line.strip()
            if not stripped:  # 保留空行
                result.append(line)
                continue
                
            # 检查是否过长
            if len(stripped) > self.length_threshold:
                continue
                
            # 检查是否与已保留的行相似（如果启用相似度检查）
            keep = True
            if self.enable_similarity_check:
                for kept_line in result:
                    if self.is_similar(stripped, kept_line.strip()):
                        keep = False
                        break
                        
            if keep:
                result.append(line)
            
            # 更新进度
            self.progress = (i + 1) / len(lines) * 100
            if progress_callback:
                progress_callback(self.progress)
        
        self.running = False
        return '\n'.join(result)

def save_to_file():
    """获取输入、合并、去重并保存结果"""
    text1 = text_area1.get("1.0", tk.END).strip()
    text2 = text_area2.get("1.0", tk.END).strip()
    
    if not text1 or not text2:
        status_label.config(text="错误：两个文本框都必须输入内容")
        return
    
    # 禁用按钮避免重复点击
    process_btn.config(state=tk.DISABLED)
    status_label.config(text="处理中...")
    progress_bar['value'] = 0
    
    def process_and_save():
        try:
            # 合并文本
            interlaced = interlace_texts(text1, text2)
            original_size = len(interlaced.encode('utf-8'))
            
            # 在后台线程中处理文本
            cleaned = text_processor.remove_similar_lines(interlaced, update_progress)
            processed_size = len(cleaned.encode('utf-8'))
            
            # 计算压缩率
            compression_ratio = 1 - (processed_size / original_size)
            
            # 保存结果
            with open('system_prompt.txt', 'w', encoding='utf-8') as f:
                f.write(cleaned)
            
            # 更新状态
            root.after(0, lambda: status_label.config(
                text=f"成功：保存完成 (原始:{len(interlaced.splitlines())}行 处理后:{len(cleaned.splitlines())}行 压缩率:{compression_ratio:.2%})"
            ))
        except Exception as e:
            root.after(0, lambda: status_label.config(text=f"错误：{str(e)}"))
        finally:
            root.after(0, lambda: process_btn.config(state=tk.NORMAL))
    
    # 启动处理线程
    threading.Thread(target=process_and_save, daemon=True).start()
    

# 创建支持拖放的主窗口
root = TkinterDnD.Tk()

def handle_drop_left(event):
    """处理左边文本框的文件拖放"""
    filepath = event.data.strip('{}')
    if filepath.lower().endswith('en_us.lang'):
        with open(filepath, 'r', encoding='utf-8') as f:
            text_area1.delete('1.0', tk.END)
            text_area1.insert(tk.END, f.read())

def handle_drop_right(event):
    """处理右边文本框的文件拖放"""
    filepath = event.data.strip('{}')
    if filepath.lower().endswith('zh_cn.lang'):
        with open(filepath, 'r', encoding='utf-8') as f:
            text_area2.delete('1.0', tk.END)
            text_area2.insert(tk.END, f.read())
root.title("文本交替合并工具")
root.geometry("800x700")

# 创建处理器实例
text_processor = TextProcessor()

# 参数控制框架
param_frame = tk.Frame(root)
param_frame.pack(pady=10, fill=tk.X)

# 相似度检查开关
sim_check_var = tk.BooleanVar(value=True)
sim_check = tk.Checkbutton(
    param_frame,
    text="启用相似度检查",
    variable=sim_check_var,
    command=lambda: setattr(text_processor, 'enable_similarity_check', sim_check_var.get())
)
sim_check.pack(side=tk.LEFT, padx=5)

# 相似度阈值滑动条
sim_label = tk.Label(param_frame, text="相似度阈值:")
sim_label.pack(side=tk.LEFT, padx=5)
sim_scale = ttk.Scale(param_frame, from_=0.0, to=1.0, value=0.8)
sim_scale.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
sim_value = tk.Label(param_frame, text="0.6")
sim_value.pack(side=tk.LEFT, padx=5)

def update_sim_threshold(val):
    text_processor.similarity_threshold = float(val)
    sim_value.config(text=f"{float(val):.2f}")

sim_scale.config(command=update_sim_threshold)

# 长度阈值滑动条
len_label = tk.Label(param_frame, text="最大长度:")
len_label.pack(side=tk.LEFT, padx=5)
len_scale = ttk.Scale(param_frame, from_=100, to=1000, value=500)
len_scale.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
len_value = tk.Label(param_frame, text="160")
len_value.pack(side=tk.LEFT, padx=5)

def update_len_threshold(val):
    text_processor.length_threshold = int(float(val))
    len_value.config(text=str(int(float(val))))

len_scale.config(command=update_len_threshold)

# 进度条
progress_bar = ttk.Progressbar(root, orient="horizontal", length=300, mode="determinate")
progress_bar.pack(pady=5)

def update_progress(percent):
    progress_bar['value'] = percent

# 创建输入区域框架
input_frame = tk.Frame(root)
input_frame.pack(pady=10, fill=tk.BOTH, expand=True)

# 第一个文本输入区域
label1 = tk.Label(input_frame, text="拖入en_us.lang:")
label1.grid(row=0, column=0, sticky='w')
text_area1 = scrolledtext.ScrolledText(input_frame, wrap=tk.WORD, width=40, height=15)
text_area1.grid(row=1, column=0, padx=5, pady=5, sticky='nsew')
text_area1.drop_target_register(DND_FILES)
text_area1.dnd_bind('<<Drop>>', handle_drop_left)

# 第二个文本输入区域
label2 = tk.Label(input_frame, text="拖入zh_cn.lang:")
label2.grid(row=0, column=1, sticky='w')
text_area2 = scrolledtext.ScrolledText(input_frame, wrap=tk.WORD, width=40, height=15)
text_area2.grid(row=1, column=1, padx=5, pady=5, sticky='nsew')
text_area2.drop_target_register(DND_FILES)
text_area2.dnd_bind('<<Drop>>', handle_drop_right)

# 配置网格权重使文本框可扩展
input_frame.grid_columnconfigure(0, weight=1)
input_frame.grid_columnconfigure(1, weight=1)
input_frame.grid_rowconfigure(1, weight=1)

# 添加处理按钮
process_btn = tk.Button(root, text="合并并去重保存", command=save_to_file)
process_btn.pack(pady=10)

# 状态标签
status_label = tk.Label(root, text="", fg="blue")
status_label.pack()

# 运行主循环
root.mainloop()
