import tkinter as tk
from tkinter import ttk, filedialog
import json
import os
import threading
import queue
import sys
import re  # 新增正则表达式模块

import TranslatorLib

class ThreadSafeLogCapture:
    """线程安全的日志捕获类"""
    def __init__(self, log_queue, task_name):
        self.log_queue = log_queue
        self.task_name = task_name
        self.buffer = ""
        self.lock = threading.Lock()
    
    def write(self, text):
        with self.lock:
            self.buffer += text
            # 处理完整的行
            lines = self.buffer.split('\n')
            # 保留最后一行（可能不完整）
            self.buffer = lines[-1]
            # 处理完整的行
            for line in lines[:-1]:
                if line.strip():  # 忽略空行
                    clean_line = line.rstrip('\r')
                    if clean_line:
                        # 使用正则表达式移除 |...| 模式（包括竖线及其之间的所有字符）
                        clean_line = re.sub(r'\|.*?\|', '', clean_line)
                        # 移除多余的空格
                        clean_line = re.sub(r'\s+', ' ', clean_line).strip()
                        if clean_line:
                            self.log_queue.put((self.task_name, clean_line))
    
    def flush(self):
        # 强制处理剩余内容
        with self.lock:
            if self.buffer.strip():
                clean_line = self.buffer.rstrip('\r')
                if clean_line:
                    # 使用正则表达式移除 |...| 模式
                    clean_line = re.sub(r'\|.*?\|', '', clean_line)
                    # 移除多余的空格
                    clean_line = re.sub(r'\s+', ' ', clean_line).strip()
                    if clean_line:
                        self.log_queue.put((self.task_name, clean_line))
                self.buffer = ""

class TranslatorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Translator Minecraft")
        self.root.geometry("1280x720")
        
        # 创建 Notebook（标签页控件）
        self.标签页控件 = ttk.Notebook(self.root)
        
        # 创建第一个标签页 - 任务列表
        self.任务列表框架 = ttk.Frame(self.标签页控件)
        self.标签页控件.add(self.任务列表框架, text="任务列表")
        
        # 创建第二个标签页 - 新建任务
        self.新建任务框架 = ttk.Frame(self.标签页控件)
        self.标签页控件.add(self.新建任务框架, text="新建任务")
        
        # 将 Notebook 添加到主窗口
        self.标签页控件.pack(expand=True, fill='both')

        # --- 新增：任务列表页面布局 ---
        # 配置 任务列表框架 的 grid 列权重，左侧20%，右侧80%
        self.任务列表框架.columnconfigure(0, weight=1)
        self.任务列表框架.columnconfigure(1, weight=4)  # 1:4 比例 ≈ 20% : 80%

        # 左侧：任务名称列表
        self.任务列表框框架 = ttk.Frame(self.任务列表框架)
        self.任务列表框框架.grid(row=0, column=0, sticky='nsew', padx=(10, 5), pady=10)

        self.任务列表框 = tk.Listbox(self.任务列表框框架)
        self.任务列表框.pack(side='left', fill='both', expand=True)

        # 左侧滚动条
        self.任务列表框滚动条 = ttk.Scrollbar(self.任务列表框框架, orient='vertical', command=self.任务列表框.yview)
        self.任务列表框滚动条.pack(side='right', fill='y')
        self.任务列表框.config(yscrollcommand=self.任务列表框滚动条.set)

        # 右侧：任务日志显示
        self.日志文本框架 = ttk.Frame(self.任务列表框架)
        self.日志文本框架.grid(row=0, column=1, sticky='nsew', padx=(5, 10), pady=10)

        self.日志文本 = tk.Text(self.日志文本框架, wrap='word', state='disabled')
        self.日志文本.pack(side='left', fill='both', expand=True)

        # 右侧滚动条
        self.日志滚动条 = ttk.Scrollbar(self.日志文本框架, orient='vertical', command=self.日志文本.yview)
        self.日志滚动条.pack(side='right', fill='y')
        self.日志文本.config(yscrollcommand=self.日志滚动条.set)

        # 配置行权重以支持垂直填充
        self.任务列表框架.rowconfigure(0, weight=1)
        
        # --- 新增：任务管理核心数据结构 ---
        self.tasks = {}  # 存储任务日志: {task_name: log_content}
        self.current_task = None  # 当前选中的任务
        self.log_queue = queue.Queue()  # 线程安全日志队列
        self.任务列表框.bind('<<ListboxSelect>>', self._on_task_select)
        self.root.after(100, self._process_log_queue)  # 启动日志处理循环
        
        # --- 新增：新建任务页面布局 ---
        # 在新建任务框架内创建一个新的Notebook
        self.新建任务子标签页 = ttk.Notebook(self.新建任务框架)
        self.新建任务子标签页.pack(expand=True, fill='both', padx=0, pady=0)
        
        # 添加子标签页
        子标签页名称 = [
            "开始",
            "设置",  # 修改此处：将"API 设置"改为"设置"
        ]
        
        # 用于保存API设置标签页的框架
        self.api设置框架 = None
        # 用于保存开始标签页的框架
        self.开始框架 = None
        
        for 名称 in 子标签页名称:
            框架 = ttk.Frame(self.新建任务子标签页)
            self.新建任务子标签页.add(框架, text=名称)
            # 保存API设置框架的引用
            if 名称 == "设置":  # 修改此处：匹配新的标签名
                self.api设置框架 = 框架
            elif 名称 == "开始":
                self.开始框架 = 框架
        
        # 在API设置标签页中添加两个容器
        if self.api设置框架 is not None:
            # 配置左右布局：左侧20%，右侧80%
            self.api设置框架.columnconfigure(0, weight=1)
            self.api设置框架.columnconfigure(1, weight=4)
            
            # 左侧容器框架
            左侧框架 = ttk.Frame(self.api设置框架)
            左侧框架.grid(row=0, column=0, sticky='nsew', padx=(10, 5), pady=10)
            
            # 右侧容器框架（预留）
            右侧框架 = ttk.Frame(self.api设置框架)
            右侧框架.grid(row=0, column=1, sticky='nsew', padx=(5, 10), pady=10)
            
            # 配置行权重
            self.api设置框架.rowconfigure(0, weight=1)
            
            # Large Language Model API 容器
            self.llm_api容器 = ttk.LabelFrame(左侧框架, text="Natural Language Processing")
            self.llm_api容器.pack(fill='both', expand=True, padx=0, pady=(0, 5))
            
            # 添加LLM API的输入字段
            self._创建api输入字段(self.llm_api容器, ["URL", "KEY", "Model"])
            
            # 新增：将k、p、温度放在一行
            self._创建k_p_温度行(self.llm_api容器)
            # 新增：将上下文开关和上下文长度放在一行
            self._创建上下文行(self.llm_api容器)
            # 新增：并发数、单次处理数、提示词位置放在一行
            self._创建并发批处理提示词行(self.llm_api容器)
            
            # Embedding API 容器
            self.embedding_api容器 = ttk.LabelFrame(左侧框架, text="Embedding")
            self.embedding_api容器.pack(fill='both', expand=True, padx=0, pady=(5, 0))
            
            # 添加Embedding API的输入字段
            self._创建api输入字段(self.embedding_api容器, ["URL", "KEY", "Model"])
            
            # 新增：Embedding参数行（Tokens长度、并发数、并行数）
            self._创建嵌入参数行(self.embedding_api容器)
            
            # 新增：Index容器（现在放在左侧框架底部）
            self.index容器 = ttk.LabelFrame(左侧框架, text="Index")
            self.index容器.pack(fill='both', expand=True, padx=0, pady=(5, 0))
            
            # 添加向量路径输入框和浏览按钮
            self._创建向量路径行(self.index容器)
            
            # 添加向量名称输入框
            self._创建向量名称行(self.index容器)
            
            # 添加向量保存量化下拉框和Q量化块大小
            self._创建量化与块大小行(self.index容器)
            
            # 新增：添加索引数量输入框
            self._创建索引数量行(self.index容器)
            
            # 新增：Other容器（现在放在右侧框架）
            self.other容器 = ttk.LabelFrame(右侧框架, text="Other")
            self.other容器.pack(fill='both', expand=True, padx=0, pady=(0, 5))
            
            # 添加缓存路径输入框和浏览按钮
            self._创建缓存路径行(self.other容器)
            
            # 新增：控制面板（保存/加载/删除功能）
            控制面板 = ttk.Frame(右侧框架)
            控制面板.pack(fill='x', padx=0, pady=(5, 0))
            
            # 配置下拉框
            config_label = ttk.Label(控制面板, text="配置:")
            config_label.pack(side='left', padx=(0, 5))
            
            self.config_var = tk.StringVar()
            self.config_combobox = ttk.Combobox(控制面板, textvariable=self.config_var, state="normal", width=15)
            self.config_combobox.pack(side='left', padx=(0, 10))
            
            # 加载已有的配置文件
            self._加载配置列表()
            
            # 保存按钮
            save_btn = ttk.Button(控制面板, text="保存", command=self._保存配置)
            save_btn.pack(side='left', padx=(0, 5))
            
            # 加载按钮
            load_btn = ttk.Button(控制面板, text="加载", command=self._加载选中配置)
            load_btn.pack(side='left', padx=(0, 5))
            
            # 删除按钮
            delete_btn = ttk.Button(控制面板, text="删除", command=self._删除选中配置)
            delete_btn.pack(side='left')
        
        # 在开始标签页中添加内容
        if self.开始框架 is not None:
            
            # 配置上下布局
            self.开始框架.rowconfigure(0, weight=0)
            self.开始框架.rowconfigure(1, weight=0)
            self.开始框架.rowconfigure(2, weight=1)
            self.开始框架.columnconfigure(0, weight=1)
            
            # 上半部分：路径配置容器
            路径配置容器 = ttk.LabelFrame(self.开始框架, text="路径配置")
            路径配置容器.grid(row=0, column=0, sticky='nsew', padx=10, pady=(10, 5))
            

            路径配置容器.columnconfigure(0, weight=1)
            路径配置容器.columnconfigure(1, weight=1)
            
            # 按 2x2 网格放置（2 行 × 2 列）
            self.输入文件0变量 = tk.StringVar()
            self.输入文件1变量 = tk.StringVar()
            self.输入路径0变量 = tk.StringVar()
            self.输出路径0变量 = tk.StringVar()
            self._创建路径输入行(路径配置容器, "输入文件0:", self.输入文件0变量, 0, 0, True)  # 第1行第1列
            self._创建路径输入行(路径配置容器, "输入文件1:", self.输入文件1变量, 0, 1, True)  # 第1行第2列
            self._创建路径输入行(路径配置容器, "输入路径0:", self.输入路径0变量, 1, 0, False) # 第2行第1列
            self._创建路径输入行(路径配置容器, "输出路径0:", self.输出路径0变量, 1, 1, False) # 第2行第2列
            
            语言设置容器 = ttk.LabelFrame(self.开始框架, text="语言设置")
            语言设置容器.grid(row=1, column=0, sticky='ew', padx=10, pady=(5, 10))
            语言设置容器.rowconfigure(0, weight=0)
            # 修改：将原始语言代码和目标语言代码输入框放在同一行
            语言输入框架 = ttk.Frame(语言设置容器)
            语言输入框架.pack(fill='x', padx=10, pady=5)
            
            self.原始语言代码变量 = tk.StringVar(value="en_us")
            self._创建语言输入行(语言输入框架, "原始语言代码:", self.原始语言代码变量, 0, 0)
            
            self.目标语言代码变量 = tk.StringVar(value="zh_cn")
            self._创建语言输入行(语言输入框架, "目标语言代码:", self.目标语言代码变量, 0, 1)
            
            # 下半部分：功能按钮容器
            功能按钮容器 = ttk.LabelFrame(self.开始框架, text="开始菜单")
            功能按钮容器.grid(row=2, column=0, sticky='nsew', padx=10, pady=(5, 10))
            # 创建按钮
            按钮列表 = [
                ("翻译语言文件", self._翻译语言文件),
                ("翻译资源包文件", self._翻译资源包文件),
                ("翻译FTBQ任务文件夹", self._翻译FTBQ任务文件夹),
                ("翻译BQ任务文件夹", self._翻译BQ任务文件夹),
                ("导出ChatML数据集文件", self._导出ChatML数据集文件),
                ("导出Alpaca数据集文件", self._导出Alpaca数据集文件),
                ("导入参考词", self._导入参考词),
                ("导入Dict_Mini参考词", self._导入Dict_Mini参考词)
            ]
            
            # 计算每行按钮数量（这里每行3个，最后一行可能少于3个）
            每行按钮数 = 3
            for i, (文本, 命令) in enumerate(按钮列表):
                行 = i // 每行按钮数
                列 = i % 每行按钮数
                btn = ttk.Button(功能按钮容器, text=文本, command=命令)
                btn.grid(row=行, column=列, padx=5, pady=5, sticky='ew')
            
            # 配置列权重使按钮均匀分布
            for i in range(每行按钮数):
                功能按钮容器.columnconfigure(i, weight=1)
    
    def _创建api输入字段(self, parent, fields):
        """在指定容器中创建API输入字段"""
        for field in fields:
            frame = ttk.Frame(parent)
            frame.pack(fill='x', padx=10, pady=5)
            
            label = ttk.Label(frame, text=f"{field}:")
            label.pack(side='left')
            
            entry = ttk.Entry(frame)
            entry.pack(side='right', fill='x', expand=True, padx=(10, 0))
            
            # 保存引用以便后续访问（可选）
            setattr(self, f"{parent.cget('text').replace(' ', '_').lower()}_{field.lower()}_entry", entry)

    def _创建上下文开关(self, parent):
        """创建上下文开关复选框"""
        frame = ttk.Frame(parent)
        frame.pack(fill='x', padx=10, pady=5)
        
        # 创建布尔变量
        var = tk.BooleanVar(value=True)
        
        # 创建复选框
        checkbox = ttk.Checkbutton(frame, text="启用上下文", variable=var)
        checkbox.pack(side='left')
        
        # 保存变量引用
        setattr(self, "llm_context_switch_var", var)

    # 删除原 _create_slider_input 方法
    # def _create_slider_input(self, parent, label_text, from_, to, initial, resolution=1):
    #     ...

    def _创建数值输入框(self, parent, label_text, from_, to, initial, increment):
        """创建带上下按键的数值输入框（Spinbox）"""
        frame = ttk.Frame(parent)
        frame.pack(fill='x', padx=10, pady=5)
        
        label = ttk.Label(frame, text=f"{label_text}:")
        label.pack(side='left')
        
        # 根据 increment 判断是否为整数
        if increment == 1:
            format_str = "%.0f"
            var = tk.IntVar(value=int(initial))
        else:
            format_str = f"%.{len(str(increment).split('.')[-1])}f"
            var = tk.DoubleVar(value=initial)
        
        # 创建 Spinbox
        spinbox = ttk.Spinbox(
            frame,
            from_=from_,
            to=to,
            increment=increment,
            textvariable=var,
            format=format_str
        )
        spinbox.pack(side='left', fill='x', expand=True, padx=(10, 0))
        
        # 保存变量引用
        setattr(self, f"llm_{label_text.replace(' ', '_')}_var", var)
    
    def _创建k_p_温度行(self, parent):
        """创建k、p、温度在同一行的输入控件"""
        frame = ttk.Frame(parent)
        frame.pack(fill='x', padx=10, pady=5)
        
        # top_k
        k_label = ttk.Label(frame, text="top_k:")
        k_label.pack(side='left')
        k_var = tk.IntVar(value=50)
        k_spinbox = ttk.Spinbox(frame, from_=1, to=100, increment=1, textvariable=k_var, format="%.0f", width=8)
        k_spinbox.pack(side='left', padx=(5, 10))
        setattr(self, "llm_top_k_var", k_var)
        
        # top_p
        p_label = ttk.Label(frame, text="top_p:")
        p_label.pack(side='left')
        p_var = tk.DoubleVar(value=0.7)
        p_spinbox = ttk.Spinbox(frame, from_=0.0, to=1.0, increment=0.01, textvariable=p_var, format="%.2f", width=8)
        p_spinbox.pack(side='left', padx=(5, 10))
        setattr(self, "llm_top_p_var", p_var)
        
        # 温度
        temp_label = ttk.Label(frame, text="温度:")
        temp_label.pack(side='left')
        temp_var = tk.DoubleVar(value=0.65)
        temp_spinbox = ttk.Spinbox(frame, from_=0.0, to=2.0, increment=0.01, textvariable=temp_var, format="%.2f", width=8)
        temp_spinbox.pack(side='left', padx=(5, 0))
        setattr(self, "llm_温度_var", temp_var)
    
    def _创建上下文行(self, parent):
        """创建上下文开关和上下文长度在同一行的输入控件"""
        frame = ttk.Frame(parent)
        frame.pack(fill='x', padx=10, pady=5)
        
        # 上下文开关
        context_var = tk.BooleanVar(value=True)
        context_checkbox = ttk.Checkbutton(frame, text="启用上下文", variable=context_var)
        context_checkbox.pack(side='left')
        setattr(self, "llm_context_switch_var", context_var)
        
        # 上下文长度
        length_label = ttk.Label(frame, text="上下文长度:")
        length_label.pack(side='left', padx=(20, 0))
        length_var = tk.IntVar(value=16384)
        length_spinbox = ttk.Spinbox(frame, from_=4, to=32768, increment=1, textvariable=length_var, format="%.0f", width=10)
        length_spinbox.pack(side='left', padx=(5, 0))
        setattr(self, "llm_上下文长度_var", length_var)
    
    def _创建并发批处理提示词行(self, parent):
        """创建并发数、单次处理数、提示词位置在同一行的输入控件"""
        frame = ttk.Frame(parent)
        frame.pack(fill='x', padx=10, pady=5)
        
        # 并发数
        concurrency_label = ttk.Label(frame, text="最大并发数:")
        concurrency_label.pack(side='left')
        concurrency_var = tk.IntVar(value=24)
        concurrency_spinbox = ttk.Spinbox(frame, from_=1, to=2147483647, increment=1, textvariable=concurrency_var, format="%.0f", width=8)
        concurrency_spinbox.pack(side='left', padx=(5, 10))
        setattr(self, "llm_并发数_var", concurrency_var)
        
        # 单次处理数
        batch_label = ttk.Label(frame, text="最大并行数:")
        batch_label.pack(side='left')
        batch_var = tk.IntVar(value=3)
        batch_spinbox = ttk.Spinbox(frame, from_=1, to=16, increment=1, textvariable=batch_var, format="%.0f", width=8)
        batch_spinbox.pack(side='left', padx=(5, 10))
        setattr(self, "llm_单次处理数_var", batch_var)
        
        # 提示词位置
        prompt_label = ttk.Label(frame, text="提示词位置:")
        prompt_label.pack(side='left')
        prompt_var = tk.StringVar(value="system")
        prompt_combobox = ttk.Combobox(frame, textvariable=prompt_var, values=["system", "user"], state="readonly", width=10)
        prompt_combobox.pack(side='left', padx=(5, 0))
        setattr(self, "llm_提示词位置_var", prompt_var)
    
    def _创建向量路径行(self, parent):
        """创建向量路径输入框和浏览按钮"""
        frame = ttk.Frame(parent)
        frame.pack(fill='x', padx=10, pady=5)
        
        label = ttk.Label(frame, text="向量路径:")
        label.pack(side='left')
        
        self.向量路径变量 = tk.StringVar(value="./Vectors")  # 设置默认值
        path_entry = ttk.Entry(frame, textvariable=self.向量路径变量)
        path_entry.pack(side='left', fill='x', expand=True, padx=(10, 5))
        
        browse_btn = ttk.Button(frame, text="浏览", command=self._浏览向量路径)
        browse_btn.pack(side='right')
    
    def _创建向量名称行(self, parent):
        """创建向量名称输入框"""
        frame = ttk.Frame(parent)
        frame.pack(fill='x', padx=10, pady=5)
        
        label = ttk.Label(frame, text="向量名称:")
        label.pack(side='left')
        
        self.向量名称变量 = tk.StringVar(value="Vectors")  # 设置默认值
        name_entry = ttk.Entry(frame, textvariable=self.向量名称变量)
        name_entry.pack(side='left', fill='x', expand=True, padx=(10, 0))
    
    def _浏览向量路径(self):
        """打开文件夹选择对话框"""
        
        folder_path = filedialog.askdirectory()
        if folder_path:
            self.向量路径变量.set(folder_path)
    
    def _创建嵌入参数行(self, parent):
        """创建Embedding的Tokens长度、并发数、并行数在同一行的输入控件"""
        frame = ttk.Frame(parent)
        frame.pack(fill='x', padx=10, pady=5)
        
        # Tokens长度
        tokens_label = ttk.Label(frame, text="最大Tokens:")
        tokens_label.pack(side='left')
        tokens_var = tk.IntVar(value=512)
        tokens_spinbox = ttk.Spinbox(frame, from_=64, to=131072, increment=64, textvariable=tokens_var, format="%.0f", width=8)
        tokens_spinbox.pack(side='left', padx=(5, 10))
        setattr(self, "embedding_tokens_var", tokens_var)
        
        # 并发数（复用相同逻辑但不同变量）
        concurrency_label = ttk.Label(frame, text="最大并发数:")
        concurrency_label.pack(side='left')
        concurrency_var = tk.IntVar(value=8)
        concurrency_spinbox = ttk.Spinbox(frame, from_=1, to=2147483647, increment=1, textvariable=concurrency_var, format="%.0f", width=8)
        concurrency_spinbox.pack(side='left', padx=(5, 10))
        setattr(self, "embedding_并发数_var", concurrency_var)
        
        # 并行数（复用相同逻辑但不同变量）
        batch_label = ttk.Label(frame, text="最大并行数:")
        batch_label.pack(side='left')
        batch_var = tk.IntVar(value=24)
        batch_spinbox = ttk.Spinbox(frame, from_=1, to=2147483647, increment=1, textvariable=batch_var, format="%.0f", width=8)
        batch_spinbox.pack(side='left', padx=(5, 0))
        setattr(self, "embedding_单次处理数_var", batch_var)
    
    def _创建量化与块大小行(self, parent):
        """创建向量保存量化和Q量化块大小在同一行的输入控件"""
        frame = ttk.Frame(parent)
        frame.pack(fill='x', padx=10, pady=5)
        
        # 量化格式
        quant_label = ttk.Label(frame, text="向量量化格式:")
        quant_label.pack(side='left')
        quant_var = tk.StringVar(value="Q4_K_X")
        quant_combobox = ttk.Combobox(
            frame,
            textvariable=quant_var,
            values=["Float32", "Float16_S1M15", "Q8_K_X", "Q4_K_X"],
            state="readonly",
            width=15
        )
        quant_combobox.pack(side='left', padx=(5, 10))
        setattr(self, "vector_quantization_var", quant_var)
        
        # Q量化块大小
        block_label = ttk.Label(frame, text="Q块大小:")
        block_label.pack(side='left')
        block_var = tk.IntVar(value=64)  # 默认值设为32（常见值）
        block_spinbox = ttk.Spinbox(
            frame,
            from_=1,
            to=256,
            increment=16,
            textvariable=block_var,
            format="%.0f",
            width=8
        )
        block_spinbox.pack(side='left', padx=(5, 0))
        setattr(self, "vector_block_size_var", block_var)

    def _创建索引数量行(self, parent):
        """创建索引数量输入框"""
        frame = ttk.Frame(parent)
        frame.pack(fill='x', padx=10, pady=5)
        
        label = ttk.Label(frame, text="索引数量:")
        label.pack(side='left')
        
        index_count_var = tk.IntVar(value=3)  # 默认值设为1000
        index_count_spinbox = ttk.Spinbox(
            frame,
            from_=1,
            to=256,
            increment=1,
            textvariable=index_count_var,
            format="%.0f",
            width=10
        )
        index_count_spinbox.pack(side='left', padx=(10, 0))
        
        setattr(self, "index_count_var", index_count_var)
    
    def _创建缓存路径行(self, parent):
        """创建缓存路径输入框和浏览按钮"""
        frame = ttk.Frame(parent)
        frame.pack(fill='x', padx=10, pady=5)
        
        label = ttk.Label(frame, text="缓存路径:")
        label.pack(side='left')
        
        default_cache_path = os.path.expanduser("~/AppData/Local/Temp")
        self.缓存路径变量 = tk.StringVar(value=default_cache_path)  # 设置默认值为系统用户缓存文件夹
        path_entry = ttk.Entry(frame, textvariable=self.缓存路径变量)
        path_entry.pack(side='left', fill='x', expand=True, padx=(10, 5))
        
        browse_btn = ttk.Button(frame, text="浏览", command=self._浏览缓存路径)
        browse_btn.pack(side='right')
    
    def _浏览缓存路径(self):
        """打开文件夹选择对话框"""
        
        folder_path = filedialog.askdirectory()
        if folder_path:
            self.缓存路径变量.set(folder_path)
    
    def _加载配置列表(self):
        """加载配置文件列表到下拉框"""
        config_file = "config.json"
        config_names = []
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    all_configs = json.load(f)
                config_names = list(all_configs.keys())
            except Exception:
                pass
        
        self.config_combobox['values'] = config_names
        if config_names:
            self.config_combobox.set(config_names[0])
    
    def _获取当前配置(self):
        """获取当前所有设置的值"""
        config = {
            # LLM API 设置
            "llm_url": getattr(self, "natural_language_processing_url_entry", ttk.Entry()).get(),
            "llm_key": getattr(self, "natural_language_processing_key_entry", ttk.Entry()).get(),
            "llm_model": getattr(self, "natural_language_processing_model_entry", ttk.Entry()).get(),
            "llm_top_k": self.llm_top_k_var.get(),
            "llm_top_p": self.llm_top_p_var.get(),
            "llm_temperature": self.llm_温度_var.get(),
            "llm_context_enabled": self.llm_context_switch_var.get(),
            "llm_context_length": self.llm_上下文长度_var.get(),
            "llm_concurrency": self.llm_并发数_var.get(),
            "llm_batch_size": self.llm_单次处理数_var.get(),
            "llm_prompt_position": self.llm_提示词位置_var.get(),
            
            # Embedding API 设置
            "embedding_url": getattr(self, "embedding_url_entry", ttk.Entry()).get(),
            "embedding_key": getattr(self, "embedding_key_entry", ttk.Entry()).get(),
            "embedding_model": getattr(self, "embedding_model_entry", ttk.Entry()).get(),
            "embedding_tokens": self.embedding_tokens_var.get(),
            "embedding_concurrency": self.embedding_并发数_var.get(),
            "embedding_batch_size": self.embedding_单次处理数_var.get(),
            
            # Index 设置
            "vector_path": self.向量路径变量.get(),
            "vector_name": self.向量名称变量.get(),
            "vector_quantization": self.vector_quantization_var.get(),
            "vector_block_size": self.vector_block_size_var.get(),
            "index_count": self.index_count_var.get(),
            
            # Other 设置
            "cache_path": self.缓存路径变量.get()
        }
        return config
    
    def _保存配置(self):
        """保存当前配置到config.json文件中的指定名称下"""
        config_name = self.config_var.get().strip()
        if not config_name:
            # 如果没有输入名称，使用默认名称
            config_name = "default"
        
        # 读取现有的所有配置
        config_file = "config.json"
        all_configs = {}
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    all_configs = json.load(f)
            except Exception:
                pass
        
        # 添加或更新当前配置
        all_configs[config_name] = self._获取当前配置()
        
        # 写回文件
        try:
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(all_configs, f, indent=4, ensure_ascii=False)
            
            # 重新加载配置列表
            self._加载配置列表()
            # 选中刚保存的配置
            self.config_combobox.set(config_name)
            
        except Exception as e:
            # 这里可以添加错误提示
            pass
    
    def _加载选中配置(self):
        """加载选中的配置"""
        config_name = self.config_var.get()
        if not config_name:
            return
        
        config_file = "config.json"
        if not os.path.exists(config_file):
            return
        
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                all_configs = json.load(f)
            
            if config_name not in all_configs:
                return
            config = all_configs[config_name]
            
            # 应用配置到UI
            # LLM API 设置
            if hasattr(self, "natural_language_processing_url_entry"):
                self.natural_language_processing_url_entry.delete(0, tk.END)
                self.natural_language_processing_url_entry.insert(0, config.get("llm_url", ""))
            if hasattr(self, "natural_language_processing_key_entry"):
                self.natural_language_processing_key_entry.delete(0, tk.END)
                self.natural_language_processing_key_entry.insert(0, config.get("llm_key", ""))
            if hasattr(self, "natural_language_processing_model_entry"):
                self.natural_language_processing_model_entry.delete(0, tk.END)
                self.natural_language_processing_model_entry.insert(0, config.get("llm_model", ""))
            
            self.llm_top_k_var.set(config.get("llm_top_k", 50))
            self.llm_top_p_var.set(config.get("llm_top_p", 0.7))
            self.llm_温度_var.set(config.get("llm_temperature", 0.65))
            self.llm_context_switch_var.set(config.get("llm_context_enabled", True))
            self.llm_上下文长度_var.set(config.get("llm_context_length", 16384))
            self.llm_并发数_var.set(config.get("llm_concurrency", 24))
            self.llm_单次处理数_var.set(config.get("llm_batch_size", 3))
            self.llm_提示词位置_var.set(config.get("llm_prompt_position", "system"))
            
            # Embedding API 设置
            if hasattr(self, "embedding_url_entry"):
                self.embedding_url_entry.delete(0, tk.END)
                self.embedding_url_entry.insert(0, config.get("embedding_url", ""))
            if hasattr(self, "embedding_key_entry"):
                self.embedding_key_entry.delete(0, tk.END)
                self.embedding_key_entry.insert(0, config.get("embedding_key", ""))
            if hasattr(self, "embedding_model_entry"):
                self.embedding_model_entry.delete(0, tk.END)
                self.embedding_model_entry.insert(0, config.get("embedding_model", ""))
            
            self.embedding_tokens_var.set(config.get("embedding_tokens", 512))
            self.embedding_并发数_var.set(config.get("embedding_concurrency", 8))
            self.embedding_单次处理数_var.set(config.get("embedding_batch_size", 2147483647))
            
            # Index 设置
            self.向量路径变量.set(config.get("vector_path", "./Vectors"))
            self.向量名称变量.set(config.get("vector_name", "Vectors"))
            self.vector_quantization_var.set(config.get("vector_quantization", "Q4_K_X"))
            self.vector_block_size_var.set(config.get("vector_block_size", 64))
            self.index_count_var.set(config.get("index_count", 3))
            
            # Other 设置
            self.缓存路径变量.set(config.get("cache_path", os.path.expanduser("~/AppData/Local/Temp")))
            
        except Exception as e:
            # 这里可以添加错误提示
            pass
    
    def _删除选中配置(self):
        """删除选中的配置"""
        config_name = self.config_var.get()
        if not config_name:
            return
        
        config_file = "config.json"
        if not os.path.exists(config_file):
            return
        
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                all_configs = json.load(f)
            
            if config_name in all_configs:
                del all_configs[config_name]
                
                # 写回文件
                with open(config_file, 'w', encoding='utf-8') as f:
                    json.dump(all_configs, f, indent=4, ensure_ascii=False)
            
            # 重新加载配置列表
            self._加载配置列表()
            # 如果还有其他配置，选中第一个
            if self.config_combobox['values']:
                self.config_combobox.set(self.config_combobox['values'][0])
            else:
                self.config_var.set("")
                
        except Exception as e:
            # 这里可以添加错误提示
            pass
    
    def _创建路径输入行(self, parent, label_text, variable, row, col, is_file):
        """创建路径输入框和浏览按钮 - 修复版"""
        frame = ttk.Frame(parent)
        frame.grid(row=row, column=col, sticky='nsew', padx=5, pady=5)
        
        # 配置内部三列：标签(0) | 输入框(1) | 按钮(2)
        frame.columnconfigure(0, weight=0)  # 标签列：固定宽度
        frame.columnconfigure(1, weight=1)  # 输入框列：可拉伸（关键！）
        frame.columnconfigure(2, weight=0)  # 按钮列：固定宽度
        
        label = ttk.Label(frame, text=label_text)
        label.grid(row=0, column=0, sticky='w', padx=(0, 5))
        
        entry = ttk.Entry(frame, textvariable=variable)
        entry.grid(row=0, column=1, sticky='ew', pady=(2, 0))  # 水平拉伸
        
        browse_btn = ttk.Button(frame, text="浏览", 
                            command=lambda: self._浏览路径(variable, is_file))
        browse_btn.grid(row=0, column=2, sticky='e', padx=(5, 0))
    
    def _浏览路径(self, variable, is_file):
        """打开文件或文件夹选择对话框"""
        
        if is_file:
            path = filedialog.askopenfilename()
        else:
            path = filedialog.askdirectory()
        if path:
            variable.set(path)
    
    def _创建语言输入行(self, parent, label_text, variable, row, col=0):
        """创建语言代码输入框"""
        frame = ttk.Frame(parent)
        frame.grid(row=row, column=col, sticky='ew', padx=5, pady=5)
        frame.columnconfigure(1, weight=1)
        
        label = ttk.Label(frame, text=label_text)
        label.grid(row=0, column=0, sticky='w')
        
        entry = ttk.Entry(frame, textvariable=variable)
        entry.grid(row=0, column=1, sticky='ew', padx=(5, 0))
    
    def _on_task_select(self, event):
        """任务列表选择事件处理"""
        selection = self.任务列表框.curselection()
        if selection:
            index = selection[0]
            task_name = self.任务列表框.get(index)
            self.current_task = task_name
            self._update_log_display(task_name)
    
    def _update_log_display(self, task_name):
        """更新日志显示区域"""
        log_content = self.tasks.get(task_name, "")
        self.日志文本.config(state='normal')
        self.日志文本.delete(1.0, tk.END)
        self.日志文本.insert(tk.END, log_content)
        self.日志文本.config(state='disabled')
        self.日志文本.see(tk.END)
    
    def _process_log_queue(self):
        """处理日志队列（线程安全）"""
        try:
            while True:
                task_name, message = self.log_queue.get_nowait()
                # 更新任务日志
                if task_name in self.tasks:
                    self.tasks[task_name] += message + "\n"
                else:
                    self.tasks[task_name] = message + "\n"
                
                # 如果当前显示的是这个任务，立即更新
                if self.current_task == task_name:
                    self._update_log_display(task_name)
        except queue.Empty:
            pass
        # 继续定期检查队列
        self.root.after(100, self._process_log_queue)
    
    def _create_task(self, task_type):
        """创建新任务的通用方法"""
        # 生成唯一任务名称
        task_name = f"{task_type}_{len(self.tasks) + 1}"
        
        # 添加到任务列表
        self.任务列表框.insert(tk.END, task_name)
        self.tasks[task_name] = ""
        
        # 自动切换到任务列表页并选中新任务
        self.标签页控件.select(self.任务列表框架)
        self.任务列表框.selection_clear(0, tk.END)
        self.任务列表框.selection_set(tk.END)
        self.任务列表框.see(tk.END)
        self.current_task = task_name
        self._update_log_display(task_name)
        
        return task_name
    
    def _run_background_task(self, task_name, task_func):
        """在后台线程中运行任务"""
        def worker():
            try:
                task_func(task_name)
            except Exception as e:
                self.log_queue.put((task_name, f"任务执行出错: {str(e)}"))
        
        thread = threading.Thread(target=worker, daemon=True)
        thread.start()
    
    def _翻译语言文件(self):
        task_name = self._create_task("翻译语言文件")
        self._run_background_task(task_name, self._execute_translation_task)
    
    def _翻译资源包文件(self):
        task_name = self._create_task("翻译资源包文件")
        self._run_background_task(task_name, self._execute_translation_task)
    
    def _翻译FTBQ任务文件夹(self):
        task_name = self._create_task("翻译FTBQ任务")
        self._run_background_task(task_name, self._execute_translation_task)
    
    def _翻译BQ任务文件夹(self):
        task_name = self._create_task("翻译BQ任务")
        self._run_background_task(task_name, self._execute_translation_task)
    
    def _导出ChatML数据集文件(self):
        task_name = self._create_task("导出ChatML")
        self._run_background_task(task_name, self._execute_translation_task)
        
    def _导出Alpaca数据集文件(self):
        task_name = self._create_task("导出Alpaca")
        self._run_background_task(task_name, self._execute_translation_task)
    
    def _导入参考词(self):
        task_name = self._create_task("导入参考词")
        self._run_background_task(task_name, self._execute_translation_task)
    
    def _导入Dict_Mini参考词(self):
        task_name = self._create_task("导入Dict_Mini")
        self._run_background_task(task_name, self._execute_translation_task)
    
    def _execute_translation_task(self, task_name):
        """执行实际的翻译任务并捕获tqdm进度"""

        # 保存原始stderr
        original_stderr = sys.stderr
        # 保存原始stdout
        original_stdout = sys.stdout
        
        # 创建线程安全的日志捕获对象
        log_capture = ThreadSafeLogCapture(self.log_queue, task_name)
        
        try:
            # 重定向stderr和stdout到自定义捕获对象
            sys.stderr = log_capture
            sys.stdout = log_capture
            
            # 获取当前配置
            config = self._获取当前配置()
            
            llm_api_url = config['llm_url']
            llm_api_key = config['llm_key']
            llm_model = config['llm_model']
            llm_prompt_location = config['llm_prompt_position']
            llm_contexts = config['llm_context_enabled']
            llm_contexts_length = config['llm_context_length']
            llm_max_workers = config['llm_concurrency']
            llm_max_batch = config['llm_batch_size']
            llm_k = config['llm_top_k']
            llm_p = config['llm_top_p']
            llm_t = config['llm_temperature']
            
            emb_api_url = config['embedding_url']
            emb_api_key = config['embedding_key']
            emb_model = config['embedding_model']
            emb_max_token = config['embedding_tokens']
            emb_max_batch = config['embedding_batch_size']
            emb_max_workers = config['embedding_concurrency']
            emb_file_name = config['vector_name']
            emb_file_path = config['vector_path']
            emb_file_quantization = config['vector_quantization']
            emb_file_block_size = config['vector_block_size']
            
            index_k = config['index_count']
            
            file0 = self.输入文件0变量.get()
            file1 = self.输入文件1变量.get()
            path0 = self.输入路径0变量.get()
            output_path = self.输出路径0变量.get()
            cache_path = config['cache_path']
            
            original_language = self.原始语言代码变量.get()
            target_language = self.目标语言代码变量.get()
            
            TranslatorLib.向量存储格式 = emb_file_quantization
            TranslatorLib.Q量化块大小 = emb_file_block_size
            if "翻译语言文件" in task_name:
                # 构建参数字典，仅包含非空值
                kwargs = {
                    'file0': file0,
                    'output_path': output_path,
                    'llm_api_url': llm_api_url,
                    'llm_api_key': llm_api_key,
                    'llm_model': llm_model,
                    'emb_api_url': emb_api_url,
                    'emb_api_key': emb_api_key,
                    'emb_model': emb_model,
                    'language': target_language,
                    'emb_max_token': emb_max_token,
                    'emb_max_batch': emb_max_batch,
                    'emb_max_workers': emb_max_workers,
                    'emb_file_name': emb_file_name,
                    'emb_file_path': emb_file_path,
                    'llm_prompt_location': llm_prompt_location,
                    'llm_contexts': llm_contexts,
                    'llm_contexts_length': llm_contexts_length,
                    'llm_max_workers': llm_max_workers,
                    'llm_max_batch': llm_max_batch,
                    'llm_t': llm_t,
                    'llm_p': llm_p,
                    'llm_k': llm_k,
                    'index_k': index_k
                }
                # 移除空字符串参数
                kwargs = {k: v for k, v in kwargs.items() if v != ""}
                if file1:  # 特殊处理file1，因为原逻辑中它可能为None
                    kwargs['file1'] = file1
                TranslatorLib.翻译语言文件(**kwargs)
            elif "翻译资源包文件" in task_name:
                kwargs = {
                    'file0': file0,
                    'llm_api_url': llm_api_url,
                    'llm_api_key': llm_api_key,
                    'llm_model': llm_model,
                    'emb_api_url': emb_api_url,
                    'emb_api_key': emb_api_key,
                    'emb_model': emb_model,
                    'cache_path': cache_path,
                    'output_path': output_path,
                    'original_language': original_language,
                    'target_language': target_language,
                    'emb_max_token': emb_max_token,
                    'emb_max_batch': emb_max_batch,
                    'emb_max_workers': emb_max_workers,
                    'emb_file_name': emb_file_name,
                    'emb_file_path': emb_file_path,
                    'llm_prompt_location': llm_prompt_location,
                    'llm_contexts': llm_contexts,
                    'llm_contexts_length': llm_contexts_length,
                    'llm_max_workers': llm_max_workers,
                    'llm_max_batch': llm_max_batch,
                    'llm_t': llm_t,
                    'llm_p': llm_p,
                    'llm_k': llm_k,
                    'index_k': index_k
                }
                kwargs = {k: v for k, v in kwargs.items() if v != ""}
                if file1:
                    kwargs['file1'] = file1
                TranslatorLib.翻译资源文件(**kwargs)
            elif "翻译FTBQ任务" in task_name:
                kwargs = {
                    'path': path0,
                    'llm_api_url': llm_api_url,
                    'llm_api_key': llm_api_key,
                    'llm_model': llm_model,
                    'emb_api_url': emb_api_url,
                    'emb_api_key': emb_api_key,
                    'emb_model': emb_model,
                    'language': target_language,
                    'emb_max_token': emb_max_token,
                    'emb_max_batch': emb_max_batch,
                    'emb_max_workers': emb_max_workers,
                    'emb_file_name': emb_file_name,
                    'emb_file_path': emb_file_path,
                    'llm_prompt_location': llm_prompt_location,
                    'llm_contexts': llm_contexts,
                    'llm_contexts_length': llm_contexts_length,
                    'llm_max_workers': llm_max_workers,
                    'llm_max_batch': llm_max_batch,
                    'llm_t': llm_t,
                    'llm_p': llm_p,
                    'llm_k': llm_k,
                    'index_k': index_k
                }
                kwargs = {k: v for k, v in kwargs.items() if v != ""}
                TranslatorLib.翻译FTB任务(**kwargs)
            elif "翻译BQ任务" in task_name:
                kwargs = {
                    'path': path0,
                    'llm_api_url': llm_api_url,
                    'llm_api_key': llm_api_key,
                    'llm_model': llm_model,
                    'emb_api_url': emb_api_url,
                    'emb_api_key': emb_api_key,
                    'emb_model': emb_model,
                    'language': target_language,
                    'emb_max_token': emb_max_token,
                    'emb_max_batch': emb_max_batch,
                    'emb_max_workers': emb_max_workers,
                    'emb_file_name': emb_file_name,
                    'emb_file_path': emb_file_path,
                    'llm_prompt_location': llm_prompt_location,
                    'llm_contexts': llm_contexts,
                    'llm_contexts_length': llm_contexts_length,
                    'llm_max_workers': llm_max_workers,
                    'llm_max_batch': llm_max_batch,
                    'llm_t': llm_t,
                    'llm_p': llm_p,
                    'llm_k': llm_k,
                    'index_k': index_k
                }
                kwargs = {k: v for k, v in kwargs.items() if v != ""}
                TranslatorLib.翻译BQ任务(**kwargs)
            elif "导出ChatML" in task_name:
                kwargs = {
                    'mode': "ChatML",
                    'file': output_path,
                    'emb_file_name': emb_file_name,
                    'emb_file_path': emb_file_path
                }
                kwargs = {k: v for k, v in kwargs.items() if v != ""}
                TranslatorLib.导出数据集(**kwargs)
            elif "导出Alpaca" in task_name:
                kwargs = {
                    'mode': "Alpaca",
                    'file': output_path,
                    'emb_file_name': emb_file_name,
                    'emb_file_path': emb_file_path
                }
                kwargs = {k: v for k, v in kwargs.items() if v != ""}
                TranslatorLib.导出数据集(**kwargs)
            elif "导入参考词" in task_name:
                kwargs = {
                    'path': path0,
                    'emb_api_url': emb_api_url,
                    'emb_api_key': emb_api_key,
                    'emb_model': emb_model,
                    'original_language': original_language,
                    'target_language': target_language,
                    'cache_path': cache_path,
                    'emb_max_token': emb_max_token,
                    'emb_max_batch': emb_max_batch,
                    'emb_max_workers': emb_max_workers,
                    'emb_file_name': emb_file_name,
                    'emb_file_path': emb_file_path
                }
                kwargs = {k: v for k, v in kwargs.items() if v != ""}
                TranslatorLib.导入参考词(**kwargs)
            elif "导入Dict_Mini" in task_name:
                kwargs = {
                    'file': file0,
                    'emb_api_url': emb_api_url,
                    'emb_api_key': emb_api_key,
                    'emb_model': emb_model,
                    'emb_max_token': emb_max_token,
                    'emb_max_batch': emb_max_batch,
                    'emb_max_workers': emb_max_workers,
                    'emb_file_name': emb_file_name,
                    'emb_file_path': emb_file_path
                }
                kwargs = {k: v for k, v in kwargs.items() if v != ""}
                TranslatorLib.导入DictMini参考词(**kwargs)
            
            # 任务完成提示
            self.log_queue.put((task_name, "\n当前线程工作完成"))
            
        except Exception as e:
            # 记录错误
            error_msg = f"任务执行出错: {str(e)}"
            self.log_queue.put((task_name, error_msg))
        finally:
            # 刷新并恢复原始stderr/stdout
            log_capture.flush()
            sys.stderr = original_stderr
            sys.stdout = original_stdout

if __name__ == "__main__":
    # 创建主窗口
    root = tk.Tk()
    app = TranslatorGUI(root)

    # 运行主循环
    root.mainloop()
