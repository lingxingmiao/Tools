import time
import json
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import requests
import threading
import datetime
import re

class TranslatorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("JSON/.lang 翻译工具")
        self.root.geometry("1280x720")
        self.stop_flag = False
        self.context_history = []

        # API配置区域
        self.api_frame = tk.LabelFrame(root, text="API配置", padx=5, pady=5)
        self.api_frame.pack(fill=tk.X, padx=10, pady=5)

        # API URL
        tk.Label(self.api_frame, text="API URL:").grid(row=0, column=0, sticky=tk.W)
        self.api_url_entry = tk.Entry(self.api_frame, width=50)
        self.api_url_entry.insert(0, "http://127.0.0.1:1234/")
        self.api_url_entry.grid(row=0, column=1, padx=5, pady=2)

        self.v1_mode_var = tk.BooleanVar(value=False)
        self.v1_mode_cb = tk.Checkbutton(
            self.api_frame,
            text="v1模式",
            variable=self.v1_mode_var
        )
        self.v1_mode_cb.grid(row=0, column=2, padx=5, pady=2, sticky="w")

        # API Key
        tk.Label(self.api_frame, text="API Key:").grid(row=1, column=0, sticky=tk.W)
        self.api_key_entry = tk.Entry(self.api_frame, width=50)
        self.api_key_entry.grid(row=1, column=1, padx=5, pady=2)

        # 模型名称
        tk.Label(self.api_frame, text="模型名称:").grid(row=2, column=0, sticky=tk.W)
        self.model_var = tk.StringVar()
        self.model_combobox = ttk.Combobox(
            self.api_frame,
            textvariable=self.model_var,
            width=47
        )
        self.model_combobox.grid(row=2, column=1, padx=5, pady=2)

        self.api_button_click()

        self.refresh_button = tk.Button(
            self.api_frame,
            text="刷新列表",
            command=self.api_button_click
        )
        self.refresh_button.grid(row=2, column=2, padx=5, pady=2)
        
        self.fetch_models()

    def api_button_click(self):
        """从API获取可用模型列表"""
        try:
            base_url = self.api_url_entry.get().rstrip('/')
            
            if '/v1/models' not in base_url:
                base_url = f"{base_url}/v1/models"
            
            response = requests.get(base_url)
            response.raise_for_status()
            
            models = response.json()["data"]
            model_names = [model["id"] for model in models]
            
            current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            self.model_combobox['values'] = model_names
            if model_names:
                self.model_var.set(model_names[0])
        except Exception as e:
            current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"{current_time}  [ERROR] Failed to fetch models: {str(e)}")

    def fetch_models(self):

        # 控制面板区域
        self.control_frame = tk.Frame(root)
        self.control_frame.pack(fill=tk.X, padx=10, pady=5)


        # 文件路径输入
        self.file_frame = tk.LabelFrame(root, text="文件配置", padx=5, pady=5)
        self.file_frame.pack(fill=tk.X, padx=10, pady=5)

        # 翻译配置区域
        # 翻译配置主框架
        self.config_main_frame = tk.LabelFrame(root, text="翻译配置", padx=5, pady=5)
        self.config_main_frame.pack(fill=tk.X, padx=10, pady=5)

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

        tk.Label(self.file_frame, text="文件路径:").grid(row=0, column=0, sticky=tk.W)
        self.file_path_entry = tk.Entry(self.file_frame, width=50)
        self.file_path_entry.grid(row=0, column=1, padx=5, pady=2)


        self.browse_button = tk.Button(
            self.file_frame, 
            text="浏览", 
            command=self.browse_file
        )
        self.browse_button.grid(row=0, column=2, padx=5)

        # 翻译按钮
        self.translate_button = tk.Button(
            root,
            text="开始翻译",
            command=self.start_translation
        )
        self.translate_button.pack(pady=10)

        # 进度显示
        self.status_label = tk.Label(root, text="准备就绪")
        self.status_label.pack()

        # 翻译结果显示
        self.output_frame = tk.LabelFrame(root, text="翻译结果", padx=5, pady=5)
        self.output_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.output_text = tk.Text(self.output_frame, height=10)
        self.output_text.pack(fill=tk.BOTH, expand=True)

    def browse_file(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("JSON/Lang Files", "*.json *.lang"), ("All Files", "*.*")]
        )
        if file_path:
            self.file_path_entry.delete(0, tk.END)
            self.file_path_entry.insert(0, file_path)

    def start_translation(self):
        file_path = self.file_path_entry.get()
        if not file_path:
            messagebox.showerror("错误", "请选择要翻译的文件")
            return

        if file_path.endswith('.json'):
            thread = threading.Thread(target=self.translate_json, args=(file_path,))
        elif file_path.endswith('.lang'):
            thread = threading.Thread(target=self.translate_lang, args=(file_path,))
        else:
            messagebox.showerror("错误", "不支持的文件格式")
            return

        thread.daemon = True
        thread.start()
    def translate_text(self, text):
        """调用API进行翻译，失败后无限重试"""
        if not text or not text.strip():
            return text

        while True:  # 无限重试循环
            try:
                base_url = self.api_url_entry.get().rstrip('/')

                if not re.search(r'/chat/completions$', base_url):
                    if self.v1_mode_var.get():
                        base_url = f"{base_url}/v1/chat/completions"
                    else:
                        base_url = f"{base_url}/chat/completions"

                with open("./system_prompt.txt", "r", encoding="utf-8") as file:
                    system_content = """
                    翻译为中文，仅输出翻译内容（只能输出翻译后的内容，否则程序会报错），可以实用创译，
                    输入若含键值输出请不要包含键值，
                    遇到疑问句（或者其他）不要回答请继续翻译，
                    翻译领域Minecraft光影、模组，
                    遇到特殊符号需要保留（例如§），
                    需要保证语句通畅，
                    遇到翻译不了的输出原文参考：""" + file.read()

                if not self.enable_think.get():
                    system_content += "/no_thinking"

                messages = [{"role": "system", "content": system_content}]

                for ctx in self.context_history:
                    messages.append({"role": "user", "content": ctx["original"]})
                    messages.append({"role": "assistant", "content": ctx["translated"]})

                messages.append({"role": "user", "content": text})

                api_key = self.api_key_entry.get()

                headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {api_key}"
                }

                response = requests.post(
                    base_url,
                    headers=headers,
                    json={
                        "model": self.model_var.get(),
                        "messages": messages,
                    }
                )
                response.raise_for_status()
                translated_text = response.json()["choices"][0]["message"]["content"]
                translated_text = re.sub(r'\n', '', translated_text)

                self.context_history.append({
                    "original": text,
                    "translated": translated_text
                })

                return translated_text  # 成功翻译，退出循环

            except Exception as e:
                # 记录错误信息
                print(f"[翻译失败] 错误: {e}，正在重试...")
                self.output_text.insert(tk.END, f"重试中...\n")

                # 可选：等待一段时间再重试（防止API限流）
                time.sleep(3)  # 每次失败后等待2秒再重试

    def translate_json(self, file_path):
        """翻译JSON文件"""
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        total = len(data)
        current = 0
        print(f"开始翻译JSON文件，共{total}项")  # 调试信息
        self.output_text.insert(tk.END, f"开始翻译JSON文件，共{total}项\n")
        self.status_label.config(text=f"正在翻译: 0/{total}")
        
        for key, value in data.items():
            self.status_label.config(text=f"正在翻译: {current}/{total}")
            if self.enable_key_value.get():
                value_input = key + value
            else:
                value_input = value
            translated = self.translate_text(value_input)
            self.output_text.insert(tk.END, f"{key}\n")
            self.output_text.insert(tk.END, f"{value}={translated}\n\n")
            self.output_text.see(tk.END)
            data[key] = translated
            
            current += 1
            self.root.update()

        # 保存翻译结果
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        self.on_click()

    def translate_lang(self, file_path):
        """翻译.lang文件"""
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            print(f"读取到{len(lines)}行原始内容")  # 调试信息

        # 计算需要翻译的行数（非空且非注释行）
        translatable_lines = [l for l in lines if l.strip() and not l.startswith('#')]
        total = len(translatable_lines)
        print(f"可翻译行数: {total}")  # 调试信息
        self.status_label.config(text=f"正在翻译: 0/{total}")
        current = 0
        results = []
        for line in lines:
            line = line.rstrip('\n')
            if not line.strip() or line.startswith('#'):
                results.append(line)
                continue

            try:
                key, value = line.split('=', 1)
                if self.enable_key_value.get():
                    value_input = line
                else:
                    value_input = value
                self.status_label.config(text=f"正在翻译: {current}/{total}")
                translated = self.translate_text(value_input)
                results.append(f"{key}={translated}")
                self.output_text.insert(tk.END, f"{key}\n")
                self.output_text.insert(tk.END, f"{value}={translated}\n\n")
                self.output_text.see(tk.END)
                
            except Exception as e:
                results.append(line)
                continue

            current += 1
            self.status_label.config(text=f"正在翻译: {current}/{total}")
            self.root.update()

        # 保存翻译结果
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(results))




if __name__ == "__main__":
    root = tk.Tk()
    app = TranslatorApp(root)
    root.mainloop()
