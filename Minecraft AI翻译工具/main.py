import json
import os
import shutil
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import requests
import threading

class TranslatorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("JSON/.lang 翻译工具")
        self.root.geometry("1280x720")
        
        # API配置区域
        self.api_frame = tk.LabelFrame(root, text="API配置", padx=5, pady=5)
        self.api_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # API URL
        tk.Label(self.api_frame, text="API URL:").grid(row=0, column=0, sticky=tk.W)
        self.api_url_entry = tk.Entry(self.api_frame, width=50)
        self.api_url_entry.insert(0, "http://127.0.0.1:1234/")
        self.api_url_entry.grid(row=0, column=1, padx=5, pady=2)
        
        # API密钥
        tk.Label(self.api_frame, text="API密钥:").grid(row=1, column=0, sticky=tk.W)
        self.api_key_entry = tk.Entry(self.api_frame, width=50, show="*")
        self.api_key_entry.grid(row=1, column=1, padx=5, pady=2)
        
        # 模型名称
        tk.Label(self.api_frame, text="模型名称:").grid(row=2, column=0, sticky=tk.W)
        self.model_var = tk.StringVar()
        self.model_combobox = ttk.Combobox(
            self.api_frame,
            textvariable=self.model_var,
            width=47,
            postcommand=self.update_model_list
        )
        self.model_combobox.grid(row=2, column=1, padx=5, pady=2)
        
        # Temperature值
        tk.Label(self.api_frame, text="Temperature:").grid(row=3, column=0, sticky=tk.W)
        self.temp_entry = tk.Entry(self.api_frame, width=50)
        self.temp_entry.insert(0, "0.7")
        self.temp_entry.grid(row=3, column=1, padx=5, pady=2)
        
        # 文件路径输入
        self.file_frame = tk.LabelFrame(root, text="文件配置", padx=5, pady=5)
        self.file_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(self.file_frame, text="文件路径:").grid(row=0, column=0, sticky=tk.W)
        self.file_path_entry = tk.Entry(self.file_frame, width=50)
        self.file_path_entry.grid(row=0, column=1, padx=5, pady=2)
        
        self.browse_button = tk.Button(self.file_frame, text="浏览", command=self.browse_file)
        self.browse_button.grid(row=0, column=2, padx=5)
        
        # 翻译按钮
        self.translate_button = tk.Button(root, text="开始翻译", command=self.start_translation)
        self.translate_button.pack(pady=20)
        
        # 状态显示
        self.status_label = tk.Label(root, text="准备就绪", relief=tk.SUNKEN, anchor=tk.W)
        self.status_label.pack(fill=tk.X, pady=5)
        
        # 翻译结果显示
        self.output_frame = tk.LabelFrame(root, text="翻译结果", padx=5, pady=5)
        self.output_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.output_text = tk.Text(self.output_frame, height=10, state='disabled')
        self.output_text.pack(fill=tk.BOTH, expand=True)
    
    def update_model_list(self):
        """从API获取可用模型列表"""
        try:
            base_url = self.api_url_entry.get().rstrip('/')
            if '/v1/chat/completions' in base_url:
                base_url = base_url.replace('/v1/chat/completions', '')
            models_url = f"{base_url}/api/v0/models"
            
            response = requests.get(models_url)
            response.raise_for_status()
            models = [model["id"] for model in response.json()["data"]]
            self.model_combobox["values"] = models
        except Exception as e:
            messagebox.showwarning("警告", f"获取模型列表失败: {str(e)}")

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
        
        self.translate_button.config(state='disabled')
        self.status_label.config(text="正在初始化翻译...")
        
        try:
            if file_path.endswith('.json'):
                thread = threading.Thread(target=self.translate_json, args=(file_path,))
            elif file_path.endswith('.lang'):
                thread = threading.Thread(target=self.translate_lang, args=(file_path,))
            else:
                messagebox.showerror("错误", "不支持的文件格式")
                return
            
            thread.daemon = True
            thread.start()
        except Exception as e:
            messagebox.showerror("错误", f"翻译失败: {str(e)}")
            self.translate_button.config(state='normal')
    
    def __init__(self, root):
        self.root = root
        self.root.title("JSON/.lang 翻译工具")
        self.root.geometry("600x450")
        self.stop_flag = False
        self.context_history = []  # 添加上下文历史记录
        
        # API配置区域
        self.api_frame = tk.LabelFrame(root, text="API配置", padx=5, pady=5)
        self.api_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # API URL
        tk.Label(self.api_frame, text="API URL:").grid(row=0, column=0, sticky=tk.W)
        self.api_url_entry = tk.Entry(self.api_frame, width=50)
        self.api_url_entry.insert(0, "http://127.0.0.1:1234/")
        self.api_url_entry.grid(row=0, column=1, padx=5, pady=2)
        
        # API密钥
        tk.Label(self.api_frame, text="API密钥:").grid(row=1, column=0, sticky=tk.W)
        self.api_key_entry = tk.Entry(self.api_frame, width=50, show="*")
        self.api_key_entry.grid(row=1, column=1, padx=5, pady=2)
        
        # 模型名称
        tk.Label(self.api_frame, text="模型名称:").grid(row=2, column=0, sticky=tk.W)
        self.model_var = tk.StringVar()
        self.model_combobox = ttk.Combobox(
            self.api_frame,
            textvariable=self.model_var,
            width=47,
            postcommand=self.update_model_list
        )
        self.model_combobox.grid(row=2, column=1, padx=5, pady=2)
        
        # Temperature值
        tk.Label(self.api_frame, text="Temperature:").grid(row=3, column=0, sticky=tk.W)
        self.temp_entry = tk.Entry(self.api_frame, width=50)
        self.temp_entry.insert(0, "0.7")
        self.temp_entry.grid(row=3, column=1, padx=5, pady=2)

        # 上下文翻译开关
        self.use_context = tk.BooleanVar(value=True)
        tk.Checkbutton(
            self.api_frame,
            text="启用上下文（高质量）",
            variable=self.use_context
        ).grid(row=4, columnspan=2, sticky=tk.W)
        
        # 文件路径输入
        self.file_frame = tk.LabelFrame(root, text="文件配置", padx=5, pady=5)
        self.file_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(self.file_frame, text="文件路径:").grid(row=0, column=0, sticky=tk.W)
        self.file_path_entry = tk.Entry(self.file_frame, width=50)
        self.file_path_entry.grid(row=0, column=1, padx=5, pady=2)
        
        self.browse_button = tk.Button(self.file_frame, text="浏览", command=self.browse_file)
        self.browse_button.grid(row=0, column=2, padx=5)
        
        # 翻译按钮
        self.translate_button = tk.Button(root, text="开始翻译", command=self.start_translation)
        self.translate_button.pack(pady=20)
        
        # 状态显示
        self.status_label = tk.Label(root, text="准备就绪", relief=tk.SUNKEN, anchor=tk.W)
        self.status_label.pack(fill=tk.X, pady=5)
        
        # 翻译结果显示
        self.output_frame = tk.LabelFrame(root, text="翻译结果", padx=5, pady=5)
        self.output_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.output_text = tk.Text(self.output_frame, height=10, state='disabled')
        self.output_text.pack(fill=tk.BOTH, expand=True)

    def translate_text(self, text):
        """调用LMStudio API进行翻译"""
        # 跳过空内容或仅空白字符的内容
        if not text or not text.strip():
            return text
            
        try:
            headers = {}
            api_key = self.api_key_entry.get()
            if api_key:
                headers["Authorization"] = f"Bearer {api_key}"
            
            base_url = self.api_url_entry.get().rstrip('/')
            if '/v1/chat/completions' not in base_url:
                base_url = f"{base_url}/v1/chat/completions"
                
            # 构建上下文消息
            messages = [
                {"role": "system", "content": "翻译为中文，仅输出翻译内容，领域：Minecraft我的世界模组、光影，若无法翻译则输出原文，只能输出一行严禁换行，仅进行翻译功能，遇到特殊符号需要保留"}
            ]
            
            # 如果启用上下文，添加上下文历史(最近3条)
            if self.use_context.get():
                for ctx in self.context_history[-3:]:
                    messages.append({"role": "user", "content": ctx["original"]})
                    messages.append({"role": "assistant", "content": ctx["translated"]})
            
            messages.append({"role": "user", "content": text})
            
            response = requests.post(
                base_url,
                headers=headers,
                json={
                    "model": self.model_var.get(),
                    "messages": messages,
                    "temperature": float(self.temp_entry.get())
                }
            )
            
            # 记录成功翻译的上下文
            translated_text = response.json()["choices"][0]["message"]["content"]
            self.context_history.append({
                "original": text,
                "translated": translated_text
            })
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]
        except Exception as e:
            raise Exception(f"API调用失败: {str(e)}")
    
    def translate_json(self, file_path):
        """翻译JSON文件"""
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        total = len(data)
        for i, (key, value) in enumerate(data.items()):
            self.status_label.config(text=f"正在翻译 {i+1}/{total}: {key}")
            self.output_text.config(state='normal')
            self.output_text.insert(tk.END, f"原文: {key}={value}\n")
            self.root.update()
            
            try:
                translated = self.translate_text(value)
                self.output_text.insert(tk.END, f"译文: {key}={translated}\n\n")
                self.output_text.see(tk.END)
                data[key] = translated
            except Exception as e:
                messagebox.showwarning("警告", f"翻译 {key} 失败: {str(e)}")
                continue
        
        # 保存翻译结果到临时文件
        temp_path = file_path + ".tmp"
        with open(temp_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        # 替换原文件
        os.replace(temp_path, file_path)
        
        if self.auto_rename.get():
            # 生成zh_cn文件名
            dirname = os.path.dirname(file_path)
            basename = os.path.basename(file_path)
            name, ext = os.path.splitext(basename)
            new_name = f"{name}_zh_cn{ext}"
            
            zh_cn_path = os.path.join(dirname, new_name)
            shutil.copy2(file_path, zh_cn_path)
            messagebox.showinfo("完成", f"翻译完成，结果已保存到:\n原文件: {file_path}\n中文文件: {zh_cn_path}")
        else:
            messagebox.showinfo("完成", f"翻译完成，结果已保存到原文件: {file_path}")
        self.status_label.config(text="翻译完成")
        self.translate_button.config(state='normal')
    
    def translate_lang(self, file_path):
        """翻译.lang文件"""
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        total = len(lines)
        results = []
        
        for i, line in enumerate(lines):
            line = line.rstrip('\n')
            if not line.strip() or line.startswith('#'):
                results.append(line)
                continue
            
            try:
                key, value = line.split('=', 1)
                self.status_label.config(text=f"正在翻译 {i+1}/{total}: {key}")
                self.output_text.config(state='normal')
                self.output_text.insert(tk.END, f"原文: {line}\n")
                self.root.update()
                
                translated = self.translate_text(value)
                results.append(f"{key}={translated}")
                self.output_text.insert(tk.END, f"译文: {key}={translated}\n\n")
                self.output_text.see(tk.END)
            except Exception as e:
                messagebox.showwarning("警告", f"翻译行 {i+1} 失败: {str(e)}")
                results.append(line)
                continue
        
        # 保存翻译结果到临时文件
        temp_path = file_path + ".tmp"
        with open(temp_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(results))
        
        # 替换原文件
        os.replace(temp_path, file_path)
        
        if self.auto_rename.get():
            # 生成zh_cn文件名
            dirname = os.path.dirname(file_path)
            basename = os.path.basename(file_path)
            name, ext = os.path.splitext(basename)
            new_name = f"{name}_zh_cn{ext}"
            
            zh_cn_path = os.path.join(dirname, new_name)
            shutil.copy2(file_path, zh_cn_path)
            messagebox.showinfo("完成", f"翻译完成，结果已保存到:\n原文件: {file_path}\n中文文件: {zh_cn_path}")
        else:
            messagebox.showinfo("完成", f"翻译完成，结果已保存到原文件: {file_path}")
        self.status_label.config(text="翻译完成")

if __name__ == "__main__":
    root = tk.Tk()
    app = TranslatorApp(root)
    root.mainloop()