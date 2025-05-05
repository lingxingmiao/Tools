import json
import os
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

        # API Key
        tk.Label(self.api_frame, text="API Key:").grid(row=1, column=0, sticky=tk.W)
        self.api_key_entry = tk.Entry(self.api_frame, width=50, show="*")
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
        
        # 模型详情按钮
        self.details_btn = tk.Button(
            self.api_frame,
            text="模型详情",
            command=self.show_model_details,
            width=10
        )
        self.details_btn.grid(row=2, column=2, padx=5)
        
        self.fetch_models()

    def fetch_models(self):
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
            print(f"{current_time}  [INFO] Returning {model_names}")
            
            self.model_combobox['values'] = model_names
            if model_names:
                self.model_var.set(model_names[0])
        except Exception as e:
            current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"{current_time}  [ERROR] Failed to fetch models: {str(e)}")

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
        self.config_frame1.pack(fill=tk.X, pady=(0,5))

        # 上下文开关
        self.use_context = tk.BooleanVar(value=True)
        self.context_cb = tk.Checkbutton(
            self.config_frame1,
            text="启用上下文（高质量 性能影响低）",
            variable=self.use_context
        )
        self.context_cb.pack(side=tk.LEFT, padx=5)

        # 上下文历史数量
        tk.Label(self.config_frame1, text="最大上下文:").pack(side=tk.LEFT)
        self.history_count = tk.Spinbox(
            self.config_frame1,
            from_=1,
            to=2147483647,
            width=12
        )
        self.history_count.delete(0, tk.END)
        self.history_count.insert(0, "131072")
        self.history_count.pack(side=tk.LEFT, padx=5)

        # 第二行配置
        self.config_frame2 = tk.Frame(self.config_main_frame)
        self.config_frame2.pack(fill=tk.X)

        # 启用思考按钮
        self.enable_think = tk.BooleanVar(value=False)
        self.think_cb = tk.Checkbutton(
            self.config_frame2,
            text="启用思考（超高质量 性能影响高 需要模型支持）",
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
        """调用LMStudio API进行翻译"""
        if not text or not text.strip():
            return text

        try:
            base_url = self.api_url_entry.get().rstrip('/')
            if '/v1/chat/completions' not in base_url:
                base_url = f"{base_url}/v1/chat/completions"

            system_content = """
翻译为中文，仅输出翻译内容（只能输出翻译后的内容，否则程序会报错）,遇到疑问句（或者其他）不要回答请继续翻译，翻译领域Minecraft光影，遇到特殊符号需要保留（列如§），遇到翻译不了的输出原文
参考：
profile.POTATO=§a土豆
profile.VERYLOW=§a非常低
profile.LOW=§a较低
profile.MEDIUM=§a中等
profile.HIGH=§e高（默认）
profile.VERYHIGH=§c非常高
profile.ULTRA=§4§l极限
profile.COMPLEMENTARY=§4§l§n§o互补
profile.comment=Shader配置文件更改性能设置，以最优化的视觉保真度与性能比率。 §e[*]§r建议使用这些配置文件来调整您的设置，除非您知道自己在做什么。 §e[*]§r所有受影响的设置都可以在"性能设置"或"重新思考体素设置"菜单中找到。

#Information
screen.INFORMATION=信息
screen.INFORMATION.comment=该部分包含仅用于提供信息的按钮。

option.info0=将鼠标悬停在按钮上。
value.info0.0=
option.info0.comment=该部分包含的按钮只用于提供信息。

option.info1=如何获得更高性能
value.info1.0=
option.info1.comment=性能在Minecraft中是一个复杂的话题，因为它受到许多因素的影响，但你可以尝试以下方法：减少渲染距离，理想情况下应在6和16之间适用于几乎每种设备。降低"Profile"着色器设置，这些设置已经过测试以获得最佳的视觉/性能比例。稍后将添加更多信息。

option.info2=最佳设置是：Render Distance 6 to 16, Profile Shader Settings: Normal.
value.info2.0=
option.info2.comment=最佳设置因人而异，但使用默认设置对于大多数人来说几乎是最好的。 默认设置经过多年的社区评估和反馈的打磨，同时非常注重视觉/性能比例。 不过你仍然可以随心所欲地调整并从中找到乐趣！

option.info3=Profile or Visual Style：可视化风格。
value.info3.0=
option.info3.comment="配置文件"设置改变了"性能设置"菜单中的设置，而不会影响任何基于偏好设置。 "视觉风格" 更改许多基于偏好的设置中的"默认样式"值，但它不会显著影响性能。
"""
            
            if not self.enable_think.get():
                system_content += "/no_think"
                
            messages = [{"role": "system", "content": system_content}]
            
            # 添加上下文历史(固定30条)
            if self.use_context.get():
                for ctx in self.context_history[-30:]:
                    messages.append({"role": "user", "content": ctx["original"]})
                    messages.append({"role": "assistant", "content": ctx["translated"]})

            messages.append({"role": "user", "content": text})

            response = requests.post(
                base_url,
                json={
                    "model": self.model_var.get(),
                    "messages": messages,
                    "temperature": 0.6
                }
            )
            response.raise_for_status()
            translated_text = response.json()["choices"][0]["message"]["content"]
            translated_text = re.sub(r'\n', '', translated_text)
            self.context_history.append({
                "original": text,
                "translated": translated_text
            })
            return translated_text
        except Exception as e:
            messagebox.showerror("错误", f"翻译失败: {str(e)}")
            return text

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
            self.output_text.insert(tk.END, f"原文: {key}={value}\n")
            self.status_label.config(text=f"正在翻译: {current}/{total}")
            translated = self.translate_text(value)
            self.output_text.insert(tk.END, f"译文: {key}={translated}\n\n")
            self.output_text.see(tk.END)
            data[key] = translated
            
            current += 1
            print(f"当前进度: {current}/{total}")  # 调试信息
            self.root.update()

        # 保存翻译结果
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        messagebox.showinfo("完成", "翻译完成")

    def translate_lang(self, file_path):
        """翻译.lang文件"""
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            print(f"读取到{len(lines)}行原始内容")  # 调试信息
            print(f"示例内容: {lines[:5]}")  # 调试前5行

        # 计算需要翻译的行数（非空且非注释行）
        translatable_lines = [l for l in lines if l.strip() and not l.startswith('#')]
        total = len(translatable_lines)
        print(f"可翻译行数: {total}")  # 调试信息
        self.output_text.insert(tk.END, f"可翻译行数: {total}\n")
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
                self.output_text.insert(tk.END, f"原文: {line}\n")
                self.status_label.config(text=f"正在翻译: {current}/{total}")
                translated = self.translate_text(value)
                results.append(f"{key}={translated}")
                self.output_text.insert(tk.END, f"译文: {key}={translated}\n\n")
                self.output_text.see(tk.END)
                
                current += 1
                self.root.update()
            except Exception as e:
                results.append(line)
                continue

        # 保存翻译结果
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(results))

        messagebox.showinfo("完成", "翻译完成")

    def create_styled_label(self, parent, text, font="Arial", font_size=12):
        return tk.Label(
            parent,
            text=text,
            font=(font, font_size),
            anchor='w',
            justify='left'
        ).pack(fill=tk.X, padx=4)

    def add_separator(self, parent, height=2, color="gray"):
        """添加水平分割线"""
        separator = tk.Frame(parent, height=height, bg=color)
        separator.pack(fill=tk.X, pady=5)
        return separator

    def show_model_details(self):
        details_window = tk.Toplevel(self.root)
        details_window.title("模型详情")
        details_window.geometry("480x720")
        details_window.resizable(False, False)
        self.create_styled_label(details_window, "Qwen架构：", font="微软雅黑", font_size=19)
        self.create_styled_label(details_window, "Qwen3系列：", font="微软雅黑", font_size=15)
        self.create_styled_label(details_window, "警告：此系列可能回导致无限回复", font="微软雅黑", font_size=11)
        self.create_styled_label(details_window, "模型推荐：Qwen3-30B-A3B(可禁用思考)", font="微软雅黑", font_size=11)
        self.create_styled_label(details_window, "量化推荐：Avg.Q6_K_L，Min.Q5_K_M", font="微软雅黑", font_size=11)
        self.create_styled_label(details_window, "Qwen2.5系列：", font="微软雅黑", font_size=15)
        self.create_styled_label(details_window, "警告：此系列可能回导致符号消失", font="微软雅黑", font_size=11)
        self.create_styled_label(details_window, "模型推荐：Qwen2.5-14B-Instruct", font="微软雅黑", font_size=11)
        self.create_styled_label(details_window, "量化推荐：Avg.Q4_1，Min.IQ3_XXS", font="微软雅黑", font_size=11)
        self.add_separator(details_window)
        self.create_styled_label(details_window, "Llama架构：", font="微软雅黑", font_size=19)
        self.create_styled_label(details_window, "警告：此架构可能回导致回答问题", font="微软雅黑", font_size=11)
        self.create_styled_label(details_window, "Llama4系列：", font="微软雅黑", font_size=15)
        self.create_styled_label(details_window, "模型推荐：Llama-4-Scout-17B-16E-Instruct", font="微软雅黑", font_size=11)
        self.create_styled_label(details_window, "量化推荐：Avg.Q4_0，Min.IQ3_XXS", font="微软雅黑", font_size=11)
        self.create_styled_label(details_window, "Llama3系列：", font="微软雅黑", font_size=15)
        self.create_styled_label(details_window, "模型推荐：Mistral-Small-3.1-24b-instruct-2503", font="微软雅黑", font_size=11)
        self.create_styled_label(details_window, "量化推荐：Avg.Q5_K_M，Min.Q4_1", font="微软雅黑", font_size=11)
        self.add_separator(details_window)
        self.create_styled_label(details_window, "Glm架构：", font="微软雅黑", font_size=19)
        self.create_styled_label(details_window, "Glm4系列：", font="微软雅黑", font_size=15)
        self.create_styled_label(details_window, "警告：此系列小概率回导致回答问题", font="微软雅黑", font_size=11)
        self.create_styled_label(details_window, "模型推荐：GLM-4-32B-0414", font="微软雅黑", font_size=11)




if __name__ == "__main__":
    root = tk.Tk()
    app = TranslatorApp(root)
    root.mainloop()