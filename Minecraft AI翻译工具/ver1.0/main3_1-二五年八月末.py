import time
import json
import tkinter as tk
from tkinter import filedialog, ttk
import requests
import threading
import datetime
import re
from urllib.parse import urlparse
from difflib import SequenceMatcher
from typing import List, Tuple
import base64
from file import img, config
import os
import zipfile
import shutil
from pathlib import Path

class TranslatorApp:

    # 主函数
    def __init__(self, root):
        self.root = root
        self.root.title("Translator Lang")
        self.root.geometry("1280x720")
        tmp = open("tmp.ico","wb+")
        tmp.write(base64.b64decode(img))
        tmp.close()
        self.root.iconbitmap('tmp.ico')
        os.remove("tmp.ico")
        self.stop_flag = False
        self.stop = False
        self.Stoptranslate = False
        self.translate_start1 = True
        self.context_history = []
        self.检测有无配置文件()
        os.makedirs("cache", exist_ok=True)

        # 主容器框架
        self.main_container = tk.Frame(root)
        self.main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # 配置 self.main_container 的行列权重
        self.main_container.columnconfigure(0, weight=1)   # 左侧窄
        self.main_container.columnconfigure(1, weight=3)   # 右侧宽
        self.main_container.columnconfigure(0, weight=1)      # 上半行
        self.main_container.columnconfigure(1, weight=2)      # 下半行（可调整比例）

        # API配置区域
        self.api_frame = tk.LabelFrame(self.main_container, text="API配置", padx=5, pady=5)
        self.api_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=(5, 2))
        self.api_frame.columnconfigure(1, weight=1)
        self.api_frame.columnconfigure(0, weight=0)
        self.api_frame.columnconfigure(1, weight=0)
        self.api_frame.columnconfigure(2, weight=0)

        # 读取配置文件
        with open('config.json', 'r', encoding='utf-8') as file:
            self.config_file = json.load(file)
        
        # API URL
        tk.Label(self.api_frame, text="API URL:").grid(row=0, column=0, sticky=tk.W)
        self.apiurl内容 = tk.StringVar()
        self.api_url_entry = ttk.Combobox(
            self.api_frame,
            textvariable=self.apiurl内容,
            width=47
        )
        self.api_url_entry.grid(row=0, column=1, padx=5, pady=2, sticky=tk.W)
        self.api_url_entry.bind("<<ComboboxSelected>>", self.刷新列表)
        
        self.API名称 = tk.Label(
            self.api_frame,
            text=""
        )
        self.API名称.grid(row=1, column=2, padx=5, pady=2, sticky=tk.W)
        self.api地址列表处理()

        self.v1模式选项 = tk.BooleanVar(value=False)
        self.v1_mode_cb = tk.Checkbutton(
            self.api_frame,
            text="v1模式",
            variable=self.v1模式选项
        )
        self.v1_mode_cb.grid(row=0, column=2, padx=5, pady=2, sticky=tk.W)

        # API Key
        tk.Label(self.api_frame, text="API Key:").grid(row=1, column=0, sticky=tk.W)
        self.apikey内容 = tk.StringVar()
        self.api_key_entry = ttk.Combobox(
            self.api_frame,
            textvariable=self.apikey内容,
            width=47
        )
        self.api_key_entry.grid(row=1, column=1, padx=5, pady=2, sticky=tk.W)

        # 模型名称
        tk.Label(self.api_frame, text="模型名称:").grid(row=2, column=0, sticky=tk.W)
        self.模型名称内容 = tk.StringVar()
        self.model_combobox = ttk.Combobox(
            self.api_frame,
            textvariable=self.模型名称内容,
            width=47
        )
        self.model_combobox.grid(row=2, column=1, padx=5, pady=2, sticky=tk.W)

        self.刷新列表()

        self.refresh_button = tk.Button(
            self.api_frame,
            text="刷新列表",
            command=self.刷新列表
        )
        self.refresh_button.grid(row=2, column=2, padx=5, pady=2, sticky=tk.W)
        self.fetch_models()

    # 从配置文件选择API地址
    def api地址列表处理(self):
        api地址列表 = [config["apiurl"] for config in self.config_file["api_config"]]
        self.api_url_entry['values'] = api地址列表
        if api地址列表:
            self.apiurl内容.set(api地址列表[0])
        
    # 刷新列表
    def 刷新列表(self, event=None):
        config_dict = {config["apiurl"]:config for config in self.config_file["api_config"]}
        if self.apiurl内容.get() in config_dict:
            api_config里面的apiurl内容的信息 = config_dict[self.apiurl内容.get()]
        self.api_config里面的apiurl内容的信息 = api_config里面的apiurl内容的信息
        if api_config里面的apiurl内容的信息['model_search']:
            try:
                base_url = self.api_url_entry.get().rstrip('/')
                base_url = self.extract_base_url(full_url=base_url)
                base_url = f"{base_url}/v1/models"

                response = requests.get(base_url)
                response.raise_for_status()
                
                models = response.json()["data"]
                model_names = [model["id"] for model in models]
                
                current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                self.model_combobox['values'] = model_names
                if model_names:
                    self.模型名称内容.set(model_names[0])
                self.v1模式选项.set(api_config里面的apiurl内容的信息['v1_mode'])
                self.api_key_entry['values'] = []
                self.apikey内容.set('')
                self.API名称.config(text=f"{api_config里面的apiurl内容的信息['name']}")
            except Exception as e:
                self.模型名称内容.set('')
                current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                print(f"{current_time}  [ERROR] Failed to fetch models: {str(e)}")
        else:
            self.model_combobox['values'] = api_config里面的apiurl内容的信息['model_list']
            if api_config里面的apiurl内容的信息['model_list']:
                    self.模型名称内容.set(api_config里面的apiurl内容的信息['model_list'][0])
            self.v1模式选项.set(api_config里面的apiurl内容的信息['v1_mode'])
            key列表 = [item["key"] for item in self.config_file["api_key"] if item["name"] == api_config里面的apiurl内容的信息['name']]
            self.api_key_entry['values'] = key列表
            self.API名称.config(text=f"{api_config里面的apiurl内容的信息['name']}")
            if key列表:
                    self.apikey内容.set(key列表[0])
    # 副GUI函数
    def fetch_models(self):
        # 文件路径输入
        self.file_frame = tk.LabelFrame(self.main_container, text="文件配置", padx=5, pady=5)
        self.file_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=(2, 5))  # 左下
        self.file_frame.columnconfigure(1, weight=1)
        self.file_frame.columnconfigure(0, weight=0)
        self.file_frame.columnconfigure(1, weight=0)
        self.file_frame.columnconfigure(2, weight=0)

        tk.Label(self.file_frame, text="待处理文件路径:").grid(row=0, column=0, sticky=tk.W)
        self.file_path_entry = tk.Entry(self.file_frame)
        self.file_path_entry.grid(row=0, column=1, sticky="ew", padx=5, pady=2)

        self.browse_button = tk.Button(
            self.file_frame, 
            text="浏览", 
            command=lambda: self.browse_file(self.file_path_entry)
        )
        self.browse_button.grid(row=0, column=2, padx=5, sticky=tk.W)

        tk.Label(self.file_frame, text="新版本文件路径:").grid(row=1, column=0, sticky=tk.W)
        self.新版本文件路径 = tk.Entry(self.file_frame)
        self.新版本文件路径.grid(row=1, column=1, sticky="ew", padx=5, pady=2)

        self.新版本文件路径browse_button = tk.Button(
            self.file_frame, 
            text="浏览", 
            command=lambda: self.browse_file(self.新版本文件路径)
        )
        self.新版本文件路径browse_button.grid(row=1, column=2, padx=5, sticky=tk.W)

        tk.Label(self.file_frame, text="系统提示词选择:").grid(row=3, column=0, sticky=tk.W)
        self.system_prompt_var = tk.StringVar()
        self.system_prompt_combobox = ttk.Combobox(
            self.file_frame,
            textvariable=self.system_prompt_var,
            width=47
        )
        self.system_prompt_combobox.grid(row=3, column=1, padx=5, pady=2, sticky=tk.W)
        os.makedirs(r'.\system_prompt', exist_ok=True)
        if not [f for f in os.listdir('.\system_prompt') if f.lower().endswith('.txt') and os.path.isfile(os.path.join('.\system_prompt', f))]:
            open('.\system_prompt\default_prompt.txt', 'w').close()
        self.system_prompt_combobox['values'] = [
            f for f in os.listdir(r'.\system_prompt')
            if os.path.isfile(os.path.join(r'.\system_prompt', f)) and f.endswith('.txt')
        ]
        if self.system_prompt_var:
            self.system_prompt_combobox.current(0)

        # 翻译配置区域
        # 翻译配置主框架
        self.config_main_frame = tk.LabelFrame(self.main_container, text="翻译配置", padx=5, pady=5)
        self.config_main_frame.grid(
            row=0, column=1,           # 放在右上角
            rowspan=2,                 # 跨两行（覆盖左上 + 左下）
            sticky="nsew",             # 填满空间
            padx=5, pady=5
        )
        # 允许内部组件伸展
        self.config_main_frame.columnconfigure(0, weight=1)
        self.config_main_frame.rowconfigure(1, weight=1)
        self.config_main_frame.rowconfigure(3, weight=1)

        # 第一行配置
        self.config_frame1 = tk.Frame(self.config_main_frame)
        self.config_frame1.pack(fill=tk.X)

        # 上下文开关
        self.use_context = tk.BooleanVar(value=True)
        self.context_cb = tk.Checkbutton(
            self.config_frame1,
            text="启用上下文（高精度 性能影响低）",
            variable=self.use_context
        )
        self.context_cb.pack(side=tk.LEFT, padx=5)

        # 第二行配置
        self.config_frame3 = tk.Frame(self.config_main_frame)
        self.config_frame3.pack(fill=tk.X)

        # 启用键值输入按钮
        self.enable_key_value = tk.BooleanVar(value=True)
        self.key_value_cb = tk.Checkbutton(
            self.config_frame3,
            text="启用键值输入（高精度 性能影响低）",
            variable=self.enable_key_value
        )
        self.key_value_cb.pack(side=tk.LEFT, padx=5)

        # 第三行配置
        self.config_frame2 = tk.Frame(self.config_main_frame)
        self.config_frame2.pack(fill=tk.X)

        # 启用思考按钮
        self.enable_think = tk.BooleanVar(value=False)
        self.think_cb = tk.Checkbutton(
            self.config_frame2,
            text="启用思考（超高精度 性能影响高 需要模型支持）",
            variable=self.enable_think
        )
        self.think_cb.pack(side=tk.LEFT, padx=5)

        # 思考等级
        self.thinkingLevel = tk.IntVar(value=1)
        self.thinkingLevel1 = tk.Spinbox(
            self.config_frame2,
            from_=1,
            to=4,
            width=5,
            textvariable=self.thinkingLevel
        )
        self.thinkingLevel1.pack(side=tk.LEFT, padx=(0, 5))

        # 第四行配置
        self.config_frame3 = tk.Frame(self.config_main_frame)
        self.config_frame3.pack(fill=tk.X)

        self.enable_quick_search_btn = tk.BooleanVar(value=True)
        self.quick_search_btn_cp = tk.Checkbutton(
            self.config_frame3,
            text="启用快速提示词（超高精度 性能影响中）",
            variable=self.enable_quick_search_btn
        )
        self.quick_search_btn_cp.pack(side=tk.LEFT, padx=5)

        # 快速提示词数量
        self.retrieve_count = tk.IntVar(value=3)
        self.retrieve_spinbox = tk.Spinbox(
            self.config_frame3,
            from_=0,
            to=128,
            width=5,
            textvariable=self.retrieve_count
        )
        self.retrieve_spinbox.pack(side=tk.LEFT, padx=(0, 5))

        # 第三行配置
        self.config_root = tk.Frame(root)
        self.config_root.pack(side=tk.LEFT, padx=5)

        # 翻译按钮
        self.translate_start = tk.Button(
            self.config_root,
            text="开始翻译",
            command=self.translateStart
        )
        self.translate_start.pack()

        # 暂停翻译按钮
        self.translate_stop = tk.Button(
            self.config_root,
            text="暂停翻译",
            command=self.translateStop
        )
        self.translate_stop.pack()

        # 进度显示
        self.status_label = tk.Label(
            self.config_root,
            text="准备就绪"
        )
        self.status_label.pack()

        # 预计耗时
        self.EstimatedTimeRequired1 = tk.Label(
            self.config_root,
            text=""
        )
        self.EstimatedTimeRequired1.pack()

        # 剩余时长
        self.EstimatedTimeRequired2 = tk.Label(
            self.config_root,
            text=""
        )
        self.EstimatedTimeRequired2.pack()


        # 显示日志
        self.output_frame = tk.LabelFrame(root, text="日志", padx=5, pady=5)
        self.output_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.output_text = tk.Text(self.output_frame, height=5000)
        self.output_text.pack(fill=tk.BOTH, expand=True)

    # 检测有无配置文件
    def 检测有无配置文件(self):
        if os.path.isfile("config.json"):
            return
        decoded_data = base64.b64decode(config)
        json_data = json.loads(decoded_data.decode('utf-8'))
        with open("config.json", 'w', encoding='utf-8') as f:
            json.dump(json_data, f, ensure_ascii=False, indent=4)

    # 启动翻译处理
    def translateStart(self):
        if self.translate_start1:
            self.start_translation()
            self.TimeConsuming = []
        else:
            self.translateStop()
            self.output_text.insert(tk.END, f"[{time.strftime('%H:%M:%S',time.localtime(time.time()))}][INFO]:正在停止翻译...\n")
            self.Stoptranslate = True

    # 暂停结束继续翻译按钮处理
    def translateStop(self):
        if self.stop_flag:
            if self.stop:
                self.translate_stop.config(text=f"暂停翻译")
                self.translate_start.config(text=f"开始翻译")
                self.output_text.insert(tk.END, f"[{time.strftime('%H:%M:%S',time.localtime(time.time()))}][INFO]:翻译继续\n")
                self.translate_start1 = True
            else:
                self.translate_stop.config(text=f"继续翻译")
                self.translate_start.config(text=f"结束翻译")
                self.output_text.insert(tk.END, f"[{time.strftime('%H:%M:%S',time.localtime(time.time()))}][INFO]:正在暂停翻译...\n")
                self.translate_start1 = False
            self.stop = False if self.stop else True

    # 剩余时长处理
    def EstimatedTimeRequired(self, arr):
        if self.enable_quick_search_btn.get():
            basicNumericalValue = 3
        else:
            basicNumericalValue = 1
        return round(sum(arr) / len(arr) * basicNumericalValue * self.lang_lines / 60, 2)

    # URL粗处理
    def extract_base_url(self, full_url):
        parsed_url = urlparse(full_url)
        base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
        return base_url

    # 提示词比较
    def find_top_similar_strings_with_index(self, target: str, string_array: List[str], top_x: int) -> List[Tuple[int, str, float, int]]:
        promptcompare = time.time()
        similarities = []
        for index, string in enumerate(string_array):
            matcher = SequenceMatcher(None, target, string, autojunk=False)
            similarity = matcher.ratio()
            similarities.append((index, string, similarity))
        similarities.sort(key=lambda x: x[2], reverse=True)
        top_results = similarities[:top_x]
        result = [(idx, s, sim, len(s)) for idx, s, sim in top_results]
        self.output_text.insert(tk.END, f"[{time.strftime('%H:%M:%S',time.localtime(time.time()))}][INFO]:提示词比较耗时：{time.time() - promptcompare}秒\n")
        self.TimeConsuming.append(time.time() - promptcompare)
        return result
    
    # 提示词处理
    def extract_english_templates(self, full_line):
        prompttime = time.time()
        result_list = []
        with open(f'./system_prompt\{self.system_prompt_var.get()}', 'r', encoding='utf-8') as file:
            for line in file:
                line = line.strip()
                if line:
                    if full_line:
                        result_list.append(line)
                    else:
                        equal_sign_index = line.find('=')
                        if equal_sign_index != -1:
                            template = line[:equal_sign_index].strip()
                            if template:
                                result_list.append(template)
        self.output_text.insert(tk.END, f"[{time.strftime('%H:%M:%S',time.localtime(time.time()))}][INFO]:提示词处理耗时：{time.time() - prompttime}秒\n")
        self.TimeConsuming.append(time.time() - prompttime)
        return result_list

    # 待处理文件浏览
    def browse_file(self, file_type):
        file_path = filedialog.askopenfilename(
            filetypes=[("JSON/Lang/Zip/Jar Files", "*.json *.lang *.zip *.jar"), ("All Files", "*.*")]
        )
        if file_path:
                file_type.delete(0, tk.END)
                file_type.insert(0, file_path)

    # 启动翻译检测
    def start_translation(self):
        if not self.stop_flag:
            待处理文件路径 = self.file_path_entry.get()
            新版本文件路径 = self.新版本文件路径.get()
            if not 待处理文件路径:
                self.output_text.insert(tk.END, f"[{time.strftime('%H:%M:%S',time.localtime(time.time()))}][ERROR]:请选择要翻译的文件\n")
                return
            if 待处理文件路径.endswith('.json'):
                thread = threading.Thread(target=self.translate_json, args=(待处理文件路径,))
            elif 待处理文件路径.endswith('.lang'):
                thread = threading.Thread(target=self.translate_lang, args=(待处理文件路径,))
            elif 待处理文件路径.endswith('.zip'):
                if 新版本文件路径:
                    if 新版本文件路径.endswith('.zip'):
                        thread = threading.Thread(target=self.translate_zip, args=(待处理文件路径, 新版本文件路径,))
                    else:
                        self.output_text.insert(tk.END, f"[{time.strftime('%H:%M:%S',time.localtime(time.time()))}][ERROR]:新版本文件与待处理文件格式不相同\n")
                        return
                else:
                    thread = threading.Thread(target=self.translate_zip, args=(待处理文件路径,))
            elif 待处理文件路径.endswith('.jar'):
                if 新版本文件路径:
                    if 新版本文件路径.endswith('.jar'):
                        thread = threading.Thread(target=self.translate_jar, args=(待处理文件路径, 新版本文件路径,))
                    else:
                        self.output_text.insert(tk.END, f"[{time.strftime('%H:%M:%S',time.localtime(time.time()))}][ERROR]:新版本文件与待处理文件格式不相同\n")
                        return
                else:
                    thread = threading.Thread(target=self.translate_jar, args=(待处理文件路径,))
            else:
                self.output_text.insert(tk.END, f"[{time.strftime('%H:%M:%S',time.localtime(time.time()))}][ERROR]:不支持的文件格式\n")
                return
            thread.daemon = True
            self.stop_flag = True
            thread.start()
        else:
            self.output_text.insert(tk.END, f"[{time.strftime('%H:%M:%S',time.localtime(time.time()))}][ERROR]:无法启动多个翻译\n")
    
    def 翻译暂停结束处理(self):
        if self.stop:
                self.output_text.insert(tk.END, f"[{time.strftime('%H:%M:%S',time.localtime(time.time()))}][INFO]:翻译暂停\n")

        while self.stop:
            time.sleep(0.02)
            self.stop_time += 0.02

        if self.Stoptranslate:
            self.Stoptranslate = False
            self.translate_start1 = True
            self.status_label.config(text=f"准备就绪")
            self.output_text.insert(tk.END, f"[{time.strftime('%H:%M:%S',time.localtime(time.time()))}][INFO]:翻译停止\n")
            self.stop_flag = False
            self.EstimatedTimeRequired1.config(text="")
            self.EstimatedTimeRequired2.config(text="")
            return True
        else:
            return False
        
    def 清理缓存文件夹(self):
        self.output_text.insert(tk.END, f"[{time.strftime('%H:%M:%S', time.localtime())}][INFO]:清理缓存文件夹中...\n")
        start_time = time.time()
        for item in os.listdir(f"./cache"):
            item_path = os.path.join("./cache", item)
            if os.path.isfile(item_path):
                os.remove(item_path)
            elif os.path.isdir(item_path):
                shutil.rmtree(item_path)
        self.output_text.insert(tk.END, f"[{time.strftime('%H:%M:%S', time.localtime())}][INFO]:清理耗时{time.time() - start_time}秒\n")
        
    # 比较两个语言文件
    def 比较两个语言文件(self, en_us_content: str, zh_cn_content: str):
        def parse_to_dict(text: str) -> dict:
            result = {}
            for line in text.splitlines():
                line = line.strip()
                if '=' in line and not line.startswith('#'):
                    key, value = line.split('=', 1)  # 只分割第一个 '='
                    result[key.strip()] = value.strip()
            return result
        en_dict = parse_to_dict(en_us_content)
        zh_dict = parse_to_dict(zh_cn_content)
        missing_entries = []
        for key, value in en_dict.items():
            if key not in zh_dict:
                missing_entries.append(f"{key}={value}")
        return missing_entries
    def Lang模板文件处理前置(self, content: str):
        entries = {}
        lines = []
        for line in content.splitlines():
            lines.append(line)
            stripped = line.strip()
            if stripped and not stripped.startswith('#') and '=' in stripped:
                key = stripped.split('=', 1)[0].strip()
                entries[key] = line
        return entries, lines

    def Lang模板文件处理(self, 模板文件: str, 目标文件: str) -> str:
        template_entries, template_lines = self.Lang模板文件处理前置(模板文件)
        target_entries, target_lines = self.Lang模板文件处理前置(目标文件)
        result = []
        used_keys = set()
        for line in template_lines:
            stripped = line.strip()
            if not stripped or stripped.startswith('#'):
                result.append(line)
            elif '=' in stripped:
                key = stripped.split('=', 1)[0].strip()
                if key in target_entries:
                    result.append(target_entries[key])
                    used_keys.add(key)
                else:
                    result.append(line)
        return '\n'.join(result)
    # 翻译主函数
    def translate_text(self, text, 键值输入):
        while True:
            try:
                base_url = self.api_url_entry.get().rstrip('/')

                if not re.search(r'/chat/completions$', base_url):
                    if self.v1模式选项.get():
                        base_url = f"{base_url}/v1/chat/completions"
                    else:
                        base_url = f"{base_url}/chat/completions"


                with open(f'./system_prompt\{self.system_prompt_var.get()}', "r", encoding="utf-8") as file:

                    # 启用思考处理
                    if not self.enable_think.get():
                        system_content = "/no_thinking Reasoning: Low"
                    elif self.thinkingLevel.get() == 1:
                        system_content = "Reasoning: Low"
                    elif self.thinkingLevel.get() == 2:
                        system_content = "Reasoning: Medium"
                    elif self.thinkingLevel.get() == 3:
                        system_content = "Reasoning: High"
                    else:
                        system_content = ""

                    system_content += """
                        翻译为中文,仅输出翻译结果(否则程序报错)不要包含其他信息,可用创译.
                        遇疑问句等情况请继续翻译,不要回答.
                        翻译领域为Minecraft.
                        保留特殊符号(如§).
                        确保语句通顺.如无法翻译,保留原文."""
                    system_content = re.sub(r'\s', '', system_content)
                    if not self.enable_quick_search_btn.get():
                        system_content += file.read()
                    else:
                        input_full = self.extract_english_templates(full_line=True) 
                        i = self.find_top_similar_strings_with_index(
                            text, 
                            input_full,
                            self.retrieve_count.get()
                        )
                        system_content += "参考输入按照优先级排序["
                        for idx, string, similarity, length in i: 
                            system_content += "{" + f"{input_full[idx]}" + "}"
                        system_content += "]"
                    if self.enable_key_value.get():
                        system_content += f"键值输入{键值输入},"
                        
                messages = [{"role": "system", "content": system_content}]
                print(system_content)

                if self.use_context.get():
                    for ctx in self.context_history:
                        messages.append({"role": "user", "content": ctx["original"]})
                        messages.append({"role": "assistant", "content": ctx["translated"]})
                messages.append({"role": "user", "content": text})

                api_key = self.api_key_entry.get()

                headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {api_key}"
                }

                start_time = time.time()
                response = requests.post(
                    base_url,
                    headers=headers,
                    json={
                        "model": self.模型名称内容.get(),
                        "messages": messages,
                    }
                )
                self.output_text.insert(tk.END, f"[{time.strftime('%H:%M:%S',time.localtime(time.time()))}][INFO]:本词条翻译耗时：{time.time() - start_time}秒\n")
                self.TimeConsuming.append(time.time() - start_time)

                response.raise_for_status()
                translated_text = response.json()["choices"][0]["message"]["content"]
                translated_text = re.sub(r'\n', '', translated_text)

                self.context_history.append({
                    "original": text,
                    "translated": translated_text
                })

                return translated_text

            except Exception as e:
                self.TimeConsuming = self.TimeConsuming[:-3]
                self.output_text.insert(tk.END, f"[{time.strftime('%H:%M:%S',time.localtime(time.time()))}][ERROR]:{e}\n")
                self.output_text.insert(tk.END, f"[{time.strftime('%H:%M:%S',time.localtime(time.time()))}][INFO]:重试中...\n")
                self.TimeConsuming = self.TimeConsuming[:-3]
                self.TimeConsuming.append(0)
                if not self.Stoptranslate:
                    time.sleep(3)
                    while self.stop:
                        time.sleep(0.02)
                else:
                    return text
            
    # Lang翻译处理
    def translate_lang(self, file_path, 读取文件=1, 输出处理=1):
        start_time = time.time()
        if 读取文件 == 1:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                f.close()
        elif 读取文件 == 2:
            lines = file_path
        else:
            lines = file_path.splitlines()
        self.lang_lines = len(lines)

        # 计算需要翻译的行数（非空且非注释行）
        translatable_lines = [l for l in lines if l.strip() and not l.startswith('#') and not l.startswith('//')]
        total = len(translatable_lines)
        self.status_label.config(text=f"翻译进度\n 0/{total}")
        current = 0
        self.stop_time = 0
        results = []
        for line in lines:
            line = line.rstrip('\n')
            if not line.strip() or line.startswith('#')  or line.startswith('//'):
                results.append(line)
                continue
            try:
                key, value = line.split('=', 1)
                self.status_label.config(text=f"正在翻译\n {current}/{total}")
                translated = self.translate_text(value, key)
                results.append(f"{key}={translated}")
                self.output_text.insert(tk.END, f"[{time.strftime('%H:%M:%S',time.localtime(time.time()))}][INFO]:{key}\n")
                self.output_text.insert(tk.END, f"[{time.strftime('%H:%M:%S',time.localtime(time.time()))}][INFO]:{value}={translated}\n")
                self.output_text.see(tk.END)
                
            except Exception as e:
                results.append(line)
                continue

            current += 1
            self.status_label.config(text=f"正在翻译\n {current}/{total}")

            if self.翻译暂停结束处理():
                return results
            
            self.EstimatedTimeRequired1.config(text=f"预计耗时\n {self.EstimatedTimeRequired(self.TimeConsuming)}分")
            self.EstimatedTimeRequired2.config(text=f"剩余时长\n {round(self.EstimatedTimeRequired(self.TimeConsuming) - ((time.time() - start_time - self.stop_time) / 60), 2)}分")
        self.output_text.insert(tk.END, f"[{time.strftime('%H:%M:%S',time.localtime(time.time()))}][INFO]:翻译总耗时：{time.time() - start_time}秒\n")

        # 保存翻译结果
        if 输出处理 == 1:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(results))
                self.stop_flag = False
        elif 输出处理 == 2:
            with open(f'./cache/zh_cn.lang', 'w+', encoding='utf-8') as f:
                f.write('\n'.join(results))
        else:
            return '\n'.join(results)

    # Json翻译处理
    def translate_json(self, file_path, 读取文件=True, 输出处理=1):
        if 读取文件:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                f.close()
        else:
            data = file_path
        result_lines = []
        for key, value in data.items():
            result_lines.append(f"{key}={value}")
            result = "\n".join(result_lines)
        result = self.translate_lang(result, 读取文件=3, 输出处理=3)
        lines = result.split('\n')
        result_dict = {}
        for line in lines:
            line = line.strip()
            if line and '=' in line:
                key, value = line.split('=', 1)
                result_dict[key.strip()] = value.strip()
        result = json.dumps(result_dict, ensure_ascii=False, indent=4)
        result_json_str = json.dumps(result_dict, ensure_ascii=False, indent=2)
        if 输出处理 == 1:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(result_json_str)
        elif 输出处理 == 2:
            with open(f'./cache/zh_cn.json', 'w+', encoding='utf-8') as f:
                f.write(result_json_str)
        else:
            self.stop_flag = False
            return result_json_str

    # Zip光影包处理
    def translate_zip(self, Zip文件, 新Zip文件=None):
        self.清理缓存文件夹()
        新Zip文件布尔值 = False
        def 解压Zip文件(文件, 含缓存路径):
            with zipfile.ZipFile(文件, 'r') as zip_ref:
                zip_ref.extractall(f"./cache/{含缓存路径}")
                zip_ref.close()
        if 新Zip文件:
            新Zip文件布尔值 = True
            新Zip文件名 = os.path.basename(新Zip文件).replace('.zip', '')
        覆盖路径 = 新Zip文件 if 新Zip文件布尔值 else Zip文件
        Zip文件名 = os.path.basename(Zip文件).replace('.zip', '')
        start_time = time.time()
        self.output_text.insert(tk.END, f"[{time.strftime('%H:%M:%S', time.localtime())}][INFO]:解压Zip文件中...\n")
        解压Zip文件(Zip文件, Zip文件名)
        if 新Zip文件布尔值:
            解压Zip文件(新Zip文件, 新Zip文件名)
        self.output_text.insert(tk.END, f"[{time.strftime('%H:%M:%S', time.localtime())}][INFO]:解压耗时{time.time() - start_time}秒\n")
        if 新Zip文件布尔值:
            en_us文件名 = 新Zip文件名
        else:
            en_us文件名 = Zip文件名
        if os.path.isfile(f'./cache/{Zip文件名}/shaders/lang/zh_cn.lang'):
            with open(f'./cache/{Zip文件名}/shaders/lang/zh_cn.lang', 'r', encoding='utf-8') as f:
                zh_cn = f.read()
                f.close()
            with open(f'./cache/{en_us文件名}/shaders/lang/en_us.lang', 'r', encoding='utf-8') as f:
                en_us = f.read()
                f.close()
            未翻译的zh_cn缺少键值 = self.比较两个语言文件(en_us, zh_cn)
            if 未翻译的zh_cn缺少键值:
                self.output_text.insert(tk.END, f"[{time.strftime('%H:%M:%S', time.localtime())}][INFO]:检测到有zh_cn.lang启动部分翻译\n")
                zh_cn += '\n' + (self.translate_lang(未翻译的zh_cn缺少键值, 读取文件=2, 输出处理=3))
                result_lang_str = self.Lang模板文件处理(en_us, zh_cn)
                with open(f'./cache/zh_cn.lang', 'w+', encoding='utf-8') as f:
                    f.write(result_lang_str)
            else:
                self.output_text.insert(tk.END, f"[{time.strftime('%H:%M:%S', time.localtime())}][WAENING]:没有需要翻译的项或键值相同\n")
                self.清理缓存文件夹()
                self.stop_flag = False
                return
        else:
            self.output_text.insert(tk.END, f"[{time.strftime('%H:%M:%S', time.localtime())}][INFO]:检测到无zh_cn.lang启动全部翻译\n")
            self.translate_lang(file_path, 输出处理=2)
        shutil.copy('./cache/zh_cn.lang', f'./cache/{en_us文件名}/shaders/lang/zh_cn.lang')
        with zipfile.ZipFile(f'./cache/{en_us文件名}.zip', 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(f'./cache/{en_us文件名}'):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, start=f'./cache/{en_us文件名}')
                    zipf.write(file_path, arcname)
        while True:
            try:
                shutil.copy(f'./cache/{en_us文件名}.zip', os.path.dirname(self.file_path_entry.get()))
                break
            except Exception as e:
                self.output_text.insert(tk.END, f"[{time.strftime('%H:%M:%S', time.localtime())}][ERROR]:无法替换{e}\n")
                self.output_text.insert(tk.END, f"[{time.strftime('%H:%M:%S', time.localtime())}][INFO]:重试中...{e}\n")
                time.sleep(3)
        self.output_text.insert(tk.END, f"[{time.strftime('%H:%M:%S', time.localtime())}][INFO]:Zip文件已覆盖至{Zip文件}\n")
        self.清理缓存文件夹()
        self.stop_flag = False

    # Jar模组处理
    def translate_jar(self, Jar文件, 新Jar文件=None):
        self.清理缓存文件夹()
        新Jar文件布尔值 = False
        def 获取assets后路径(文件名):
            base_dir = Path(f"./cache/{文件名}")
            for pattern in ['en_us.lang', 'en_us.json']:
                for file_path in (base_dir / "assets").rglob(pattern):
                    return file_path.relative_to(base_dir).parent
        def 解压Zip文件(文件, 含缓存路径):
            with zipfile.ZipFile(文件, 'r') as zip_ref:
                zip_ref.extractall(f"./cache/{含缓存路径}")
                zip_ref.close()
        if 新Jar文件:
            新Jar文件布尔值 = True
            新Jar文件名 = os.path.basename(新Jar文件).replace('.zip', '')
        覆盖路径 = 新Jar文件 if 新Jar文件布尔值 else Jar文件
        Jar文件名 = os.path.basename(Jar文件).replace('.jar', '')
        self.output_text.insert(tk.END, f"[{time.strftime('%H:%M:%S', time.localtime())}][INFO]:解压Jar文件中...\n")
        start_time = time.time()
        解压Zip文件(Jar文件, Jar文件名)
        if 新Jar文件布尔值:
            解压Zip文件(新Jar文件, 新Jar文件名)
            
        self.output_text.insert(tk.END, f"[{time.strftime('%H:%M:%S', time.localtime())}][INFO]:解压耗时{time.time() - start_time}秒\n")
        if 新Jar文件布尔值:
            en_us文件名 = 新Jar文件名
        else:
            en_us文件名 = Jar文件名
        file_path = 获取assets后路径(Jar文件名)
        found = False

        if Path(f'./cache/{en_us文件名}/{file_path}/en_us.json').is_file() or Path(f'./cache/{en_us文件名}/{file_path}/en_us.lang').is_file():
            found = True
            if Path(Jar文件).suffix.lower() == '.json':
                if os.path.isfile(f'./cache/{Jar文件名}/{file_path}/zh_cn.json'):
                    def 转换Lang(Json文件):
                        with open(Json文件, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            f.close()
                        result_lines = []
                        for key, value in data.items():
                            result_lines.append(f"{key}={value}")
                        return "\n".join(result_lines)
                    未翻译的zh_cn缺少键值 = self.比较两个语言文件(转换Lang(f'./cache/{en_us文件名}/{file_path}/en_us.json'), 转换Lang(f'./cache/{Jar文件名}/{file_path}/zh_cn.json'))
                    if 未翻译的zh_cn缺少键值:
                        json转换的zh_cn_lang = 转换Lang(f'./cache/{Jar文件名}/{file_path}/zh_cn.json')
                        self.output_text.insert(tk.END, f"[{time.strftime('%H:%M:%S', time.localtime())}][INFO]:检测到有zh_cn.json启动部分翻译\n")
                        json转换的zh_cn_lang += '\n' + (self.translate_lang(未翻译的zh_cn缺少键值, 读取文件=2, 输出处理=3))
                        result_dict = {}
                        for line in json转换的zh_cn_lang.split('\n'):
                            line = line.strip()
                            if line and '=' in line:
                                key, value = line.split('=', 1)
                                result_dict[key.strip()] = value.strip()
                        result_json_str = json.dumps(result_dict, ensure_ascii=False, indent=2)
                        with open(f'./cache/zh_cn.json', 'w+', encoding='utf-8') as f:
                            f.write(result_json_str)
                        shutil.copy('./cache/zh_cn.json', f'./cache/{en_us文件名}/{file_path}')
                    else:
                        self.output_text.insert(tk.END, f"[{time.strftime('%H:%M:%S', time.localtime())}][WAENING]:没有需要翻译的项或键值相同\n")
                        self.清理缓存文件夹()
                        self.stop_flag = False
                        return
                else:
                    self.output_text.insert(tk.END, f"[{time.strftime('%H:%M:%S', time.localtime())}][INFO]:检测到无zh_cn.json启动全部翻译\n")
                    self.translate_json(f'./cache/{en_us文件名}/{file_path}/en_us.json', 输出处理=2)
                    shutil.copy('./cache/zh_cn.json', f'./cache/{en_us文件名}/{file_path}/en_us.json')
            else:
                if os.path.isfile(f'./cache/{Jar文件名}/{file_path}/zh_cn.lang'):
                    with open(f'./cache/{Jar文件名}/{file_path}/zh_cn.lang', 'r', encoding='utf-8') as f:
                        zh_cn = f.read()
                        f.close()
                    with open(f'./cache/{en_us文件名}/{file_path}/en_us.lang', 'r', encoding='utf-8') as f:
                        en_us = f.read()
                        f.close()
                    未翻译的zh_cn缺少键值 = self.比较两个语言文件(en_us, zh_cn)
                    if 未翻译的zh_cn缺少键值:
                        self.output_text.insert(tk.END, f"[{time.strftime('%H:%M:%S', time.localtime())}][INFO]:检测到有zh_cn.lang启动部分翻译\n")
                        zh_cn += '\n' + (self.translate_lang(未翻译的zh_cn缺少键值, 读取文件=2, 输出处理=3))
                        result_lang_str = self.Lang模板文件处理(en_us, zh_cn)
                        with open(f'./cache/zh_cn.lang', 'w+', encoding='utf-8') as f:
                            f.write(result_lang_str)
                        shutil.copy('./cache/zh_cn.lang', f'./cache/{en_us文件名}/{file_path}')
                    else:
                        self.output_text.insert(tk.END, f"[{time.strftime('%H:%M:%S', time.localtime())}][WAENING]:没有需要翻译的项或键值相同\n")
                        self.清理缓存文件夹()
                        self.stop_flag = False
                        return
                else:
                    self.output_text.insert(tk.END, f"[{time.strftime('%H:%M:%S', time.localtime())}][INFO]:检测到无zh_cn.lang启动全部翻译\n")
                    self.translate_lang(f'./cache/{en_us文件名}/{file_path}/en_us.lang', 输出处理=2)
                    shutil.copy('./cache/zh_cn.lang', f'./cache/{en_us文件名}/{file_path}')
        if not found:
            self.output_text.insert(tk.END, f"[{time.strftime('%H:%M:%S', time.localtime())}][ERROR]:Jar模组内未包含或不支持的语言文件\n")
            self.stop_flag = False
        with zipfile.ZipFile(f'./cache/{en_us文件名}.jar', 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(f'./cache/{en_us文件名}'):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, start=f'./cache/{en_us文件名}')
                    zipf.write(file_path, arcname)
        while True:
            try:
                shutil.copy(f'./cache/{en_us文件名}.jar', os.path.dirname(self.file_path_entry.get()))
                break
            except Exception as e:
                self.output_text.insert(tk.END, f"[{time.strftime('%H:%M:%S', time.localtime())}][ERROR]:无法替换\n")
                self.output_text.insert(tk.END, f"[{time.strftime('%H:%M:%S', time.localtime())}][INFO]:重试中...{e}\n")
                time.sleep(3)
        self.output_text.insert(tk.END, f"[{time.strftime('%H:%M:%S', time.localtime())}][INFO]:Jar文件已覆盖至{Jar文件}\n")
        self.清理缓存文件夹()
        self.stop_flag = False
        
if __name__ == "__main__":
    root = tk.Tk()
    app = TranslatorApp(root)
    root.mainloop()
