import tkinter as tk
from tkinter import filedialog, ttk
import threading
import json
import pyperclip
import pyautogui
import requests
import serial
import time
import re

class 小说剪辑:
    def __init__(self, root):
        self.root = root
        self.root.title("请输入文本")
        self.root.geometry("1280x720")
        self.构建窗口()
    
    def 构建窗口(self):
        标签页 = ttk.Notebook(root)
        标签页.pack(fill='both', expand=True)
        self.日志frame1 = ttk.Frame(标签页)
        self.脚本frame2 = ttk.Frame(标签页)
        self.分词器frame2 = ttk.Frame(标签页)
        标签页.add(self.日志frame1, text='日志', compound = "left")
        标签页.add(self.脚本frame2, text='脚本', compound = "left")
        标签页.add(self.分词器frame2, text='分词器', compound = "left")

        self.日志frame1.columnconfigure(1, weight=1)
        self.日志frame1.rowconfigure(1, weight=1)
        self.脚本frame2.columnconfigure(1, weight=1)
        self.脚本frame2.rowconfigure(2, weight=1)
        self.分词器frame2.columnconfigure(1, weight=1)
        self.分词器frame2.rowconfigure(2, weight=1)

        self.脚本文件容器 = tk.LabelFrame(self.脚本frame2, text="文件配置", padx=5, pady=5)
        self.脚本文件容器.grid(row=0, column=0, sticky="nsew", padx=5, pady=(2, 5))
        tk.Label(self.脚本文件容器, text="文件路径:").grid(row=0, column=0, sticky=tk.W)
        self.脚本文件路径 = tk.Entry(self.脚本文件容器, width=47)
        self.脚本文件路径.grid(row=0, column=1, sticky="ew", padx=5, pady=2)
        self.脚本文件浏览按钮 = tk.Button(self.脚本文件容器, text="浏览", command=lambda: self.浏览文件按钮(self.脚本文件路径))
        self.脚本文件浏览按钮.grid(row=0, column=2, padx=5, sticky=tk.W)

        self.脚本设置 = tk.LabelFrame(self.脚本frame2, text="脚本设置", padx=5, pady=5)
        self.脚本设置.grid(row=1, column=0, sticky="nsew", padx=5, pady=(2, 5))
        tk.Label(self.脚本设置, text="新增页位置:").grid(row=0, column=0, sticky=tk.W)
        tk.Label(self.脚本设置, text="模拟器位置:").grid(row=1, column=0, sticky=tk.W)
        tk.Label(self.脚本设置, text="张贴硬件端口:").grid(row=2, column=0, sticky=tk.W)
        self.新增页位置的值 = tk.StringVar(value="440 1014")
        self.新增页位置 = tk.Entry(self.脚本设置, width=25, textvariable=self.新增页位置的值)
        self.新增页位置.grid(row=0, column=1, sticky="ew", padx=5, pady=2)
        self.模拟器位置的值 = tk.StringVar(value="173 29")
        self.模拟器位置 = tk.Entry(self.脚本设置, width=25, textvariable=self.模拟器位置的值)
        self.模拟器位置.grid(row=1, column=1, sticky="ew", padx=5, pady=2)
        self.张贴硬件端口的值 = tk.StringVar(value="COM13")
        self.张贴硬件端口 = tk.Entry(self.脚本设置, width=25, textvariable=self.张贴硬件端口的值)
        self.张贴硬件端口.grid(row=2, column=1, sticky="ew", padx=5, pady=2)

        self.脚本开始 = tk.Button(self.脚本frame2, text="脚本开始", command=lambda: self.函数多线程启动(self.脚本开始处理))
        self.脚本开始.grid(row=100, column=0, padx=5, pady=5)
        self.分词开始 = tk.Button(self.分词器frame2, text="分词开始", command=lambda: self.函数多线程启动(self.分词开始处理))
        self.分词开始.grid(row=100, column=0, padx=5, pady=5)

        self.日志大容器 = tk.Frame(self.日志frame1)
        self.日志大容器.grid(row=1, column=0, columnspan=3, sticky="nsew", padx=5)
        self.日志容器 = tk.LabelFrame(self.日志大容器, text="日志", padx=5, pady=5)
        self.日志容器.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        self.日志 = tk.Text(self.日志容器, height=2000)
        self.日志.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.API配置 = tk.LabelFrame(self.分词器frame2, text="API配置", padx=5, pady=5)
        self.API配置.grid(row=0, column=0, sticky="nsew", padx=5, pady=(5, 2))
        tk.Label(self.API配置, text="API URL:").grid(row=0, column=0, sticky=tk.W)
        tk.Label(self.API配置, text="API Key:").grid(row=1, column=0, sticky=tk.W)
        tk.Label(self.API配置, text="文本模型:").grid(row=2, column=0, sticky=tk.W)
        self.APIURL内容 = tk.StringVar(value="https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions")
        self.APIURL内容框架 = ttk.Combobox(self.API配置,textvariable=self.APIURL内容,width=47)
        self.APIURL内容框架.grid(row=0, column=1, padx=5, pady=2, sticky=tk.W)
        self.APIKEY内容 = tk.StringVar(value="sk-***")
        self.APIKEY内容框架 = ttk.Combobox(self.API配置,textvariable=self.APIKEY内容,width=47)
        self.APIKEY内容框架.grid(row=1, column=1, padx=5, pady=2, sticky=tk.W)
        self.模型名称内容 = tk.StringVar(value="qwen-plus")
        self.模型名称内容框架 = ttk.Combobox(self.API配置,textvariable=self.模型名称内容,width=47)
        self.模型名称内容框架.grid(row=2, column=1, padx=5, pady=2, sticky=tk.W)

        self.分词文件容器 = tk.LabelFrame(self.分词器frame2, text="文件配置", padx=5, pady=5)
        self.分词文件容器.grid(row=1, column=0, sticky="nsew", padx=5, pady=(5, 2))
        tk.Label(self.分词文件容器, text="文件路径:").grid(row=0, column=0, sticky=tk.W)
        self.分词文件路径 = tk.Entry(self.分词文件容器, width=47)
        self.分词文件路径.grid(row=0, column=1, sticky="ew", padx=5, pady=2)
        self.分词文件浏览按钮 = tk.Button(self.分词文件容器, text="浏览", command=lambda: self.浏览文件按钮(self.分词文件路径))
        self.分词文件浏览按钮.grid(row=0, column=2, padx=5, sticky=tk.W)

        self.分词器设置 = tk.LabelFrame(self.分词器frame2, text="分词器设置", padx=5, pady=5)
        self.分词器设置.grid(row=0, column=1, sticky="nsew", padx=5, pady=(5, 2))
        self.分词器设置第1行 = tk.Frame(self.分词器设置)
        self.分词器设置第1行.pack(fill=tk.X)
        tk.Label(self.分词器设置第1行,text="分词字数:").pack(side=tk.LEFT, padx=(0, 5))
        self.分词字数 = tk.IntVar(value=180)
        self.分词字数框架 = tk.Spinbox(self.分词器设置第1行,from_=20,to=800,width=35,increment=50,textvariable=self.分词字数)
        self.分词字数框架.pack(side=tk.LEFT, padx=(0, 5))
        self.分词器设置第2行 = tk.Frame(self.分词器设置)
        self.分词器设置第2行.pack(fill=tk.X)
        tk.Label(self.分词器设置第2行,text="分词符号:").pack(side=tk.LEFT, padx=(0, 5))
        self.分词符号 = tk.StringVar(value="。.？?！!")
        self.分词符号框架 = tk.Entry(self.分词器设置第2行, width=35,textvariable=self.分词符号)
        self.分词符号框架.pack(side=tk.LEFT, padx=(0, 5))
        self.分词器设置第3行 = tk.Frame(self.分词器设置)
        self.分词器设置第3行.pack(fill=tk.X)
        tk.Label(self.分词器设置第3行,text="分词下一个符号:").pack(side=tk.LEFT, padx=(0, 5))
        self.分词下一个符号 = tk.StringVar(value='"”“')
        self.分词下一个符号框架 = tk.Entry(self.分词器设置第3行, width=35,textvariable=self.分词下一个符号)
        self.分词下一个符号框架.pack(side=tk.LEFT, padx=(0, 5))
        self.分词器设置第4行 = tk.Frame(self.分词器设置)
        self.分词器设置第4行.pack(fill=tk.X)
        tk.Label(self.分词器设置第4行,text="Json项间隔:").pack(side=tk.LEFT, padx=(0, 5))
        self.json项间隔 = tk.IntVar(value=300)
        self.json项间隔框架 = tk.Spinbox(self.分词器设置第4行,from_=100,to=100000,width=35,increment=50,textvariable=self.json项间隔)
        self.json项间隔框架.pack(side=tk.LEFT, padx=(0, 5))


    def 浏览文件按钮(self, file_type):
        file_path = filedialog.askopenfilename(
            filetypes=[("JSON/TXT Files", "*.json *.txt")]
        )
        if file_path:
                file_type.delete(0, tk.END)
                file_type.insert(0, file_path)

    def 函数多线程启动(self, def_, args=None):
        if args is None:
            args = ()
        elif not isinstance(args, (list, tuple)):
            args = (args,)
        
        thread = threading.Thread(target=def_, args=args)
        thread.daemon = True
        thread.start()

    def 脚本开始处理(self):
        with open(self.脚本文件路径.get(), "r", encoding="utf-8") as f:
            data = json.load(f)
        ser = serial.Serial(f"{self.张贴硬件端口.get()}", 115200, timeout=1)
        print(f"{self.张贴硬件端口.get()}")
        pos1 = self.新增页位置.get().strip()
        pos2 = self.模拟器位置.get().strip()
        a1, b1 = map(int, pos1.split())
        a2, b2 = map(int, pos2.split())
        pyautogui.click(a2, b2)
        time.sleep(0.15)
        for key, value in data.items():
            try:
                self.日志.insert(tk.END, f"[{time.strftime('%H:%M:%S',time.localtime(time.time()))}][INFO]]:正在处理：{value}") 
                print("1")
                pyperclip.copy(value)
                print(value)
                pyautogui.click(a1, b1)
                print("2")
                time.sleep(0.4)
                ser.write(b"paste\n")
                print("3")
                time.sleep(0.4)
                self.日志.insert(tk.END, f"，成功！\n") 
            except ValueError as e:
                self.日志.insert(tk.END, f"[{time.strftime('%H:%M:%S',time.localtime(time.time()))}][ERROR]:坐标错误\n") 
        ser.close()

    def 分词开始处理(self):
        system_content = """
                        文本分词，严格执行一下操作：内容不要改变，不要过多的杂碎，按照意识流分词，每行最多25字，平均20字，标点符号需要正确处理，尾部符号也需要正确处理（不能添加符号，不能更改符号，尾部不需要除顿号省略号感叹号问号以外的符号）"""
        messages = [{"role": "system", "content": system_content}]

        def 分词(输入):
            messages.append({"role": "user", "content": 输入})
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.APIKEY内容.get()}"
            }
            data_json = {
                "model": self.模型名称内容.get(),
                "messages": messages,
            }
            response = requests.post(self.APIURL内容.get(), headers=headers, json=data_json)
            输出 = response.json()["choices"][0]["message"]["content"]
            messages.append({"role": "assistant", "content": 输出})
            return 输出
        
        def 分词器(data):
            start_time = time.time()
            self.日志.insert(tk.END, f"[{time.strftime('%H:%M:%S',time.localtime(time.time()))}][信息]:初步分词启动\n") 
            每次分词字数 = self.分词字数.get()
            处理到的分词位置 = 每次分词字数
            分割的符号 = list(self.分词符号.get())
            分割下一位符号 = list(self.分词下一个符号.get())
            上次处理位置 = 1
            循环次数 = 1
            内容 = []
            while True:
                if not 处理到的分词位置 >= len(data):
                    if not data[处理到的分词位置] in 分割的符号:
                        if 处理到的分词位置 <= 上次处理位置:
                            循环次数 += 1
                            处理到的分词位置 = 上次处理位置 + 每次分词字数 * 循环次数
                        else:
                            处理到的分词位置 -= 1
                    else:
                        if data[处理到的分词位置+1] in 分割下一位符号:
                            待处理的字符 = data[上次处理位置-1:处理到的分词位置+2]
                            上次处理位置 = 处理到的分词位置 + 3
                            处理到的分词位置
                        else:
                            待处理的字符 = data[上次处理位置-1:处理到的分词位置+1]
                            上次处理位置 = 处理到的分词位置 + 2
                        处理到的分词位置 = 上次处理位置 + 每次分词字数
                        循环次数 = 1
                        内容.append(待处理的字符)
                else:
                    待处理的字符 = data[上次处理位置:len(data)]
                    内容.append(待处理的字符)
                    self.日志.insert(tk.END, f"[{time.strftime('%H:%M:%S',time.localtime(time.time()))}][信息]:初步分词结束，耗时{time.time() - start_time}秒\n") 
                    return 内容
        def 重复项检索(列表: list) -> bool:
            return len(列表) != len(set(列表))
                
        def 字数统计(data):
            if isinstance(data, list):
                data = ''.join(str(item) for item in data)
            elif not isinstance(data, str):
                data = str(data)
            标点模式 = r'[，。！？；：,.!?;:“”’‘"]'
            return len(re.sub(标点模式, '', data))
        
        with open(self.分词文件路径.get(), "r", encoding="utf-8") as f:
            data = f.read()

        分词结果 = ""
        初步分词结果数组 = 分词器(data)
        分词计数 = 0
        start_time = time.time()
        for i in 初步分词结果数组:
            self.日志.insert(tk.END, f"[{time.strftime('%H:%M:%S',time.localtime(time.time()))}][信息]:分词正在处理{分词计数}/{len(初步分词结果数组)}，字数{字数统计(i)}\n") 
            单次分词结果 = 分词(i)
            分词计数 += 1
            分词结果 += 单次分词结果 + "\n"
        self.日志.insert(tk.END, f"[{time.strftime('%H:%M:%S',time.localtime(time.time()))}][信息]:分词处理完成，耗时{time.time() - start_time}秒\n")
        lines = [line.strip() for line in 分词结果.splitlines() if line.strip()]

        self.日志.insert(tk.END, f"[{time.strftime('%H:%M:%S',time.localtime(time.time()))}][信息]:处理前字数：{字数统计(data)}，处理后字数：{字数统计(lines)}\n")
        self.日志.insert(tk.END, f"[{time.strftime('%H:%M:%S',time.localtime(time.time()))}][警告]:输出含有重复项\n\n") if 重复项检索(lines) else ""
        
        
        词条成功计数 = 0
        for i in lines:
            self.写入i = i
            if i in data:
                词条成功计数 += 1
            else:
                self.日志.insert(tk.END, f"[{time.strftime('%H:%M:%S',time.localtime(time.time()))}][警告]:匹配失败位置：{i}\n")
                if not (lines.index(i) - 1) < 0:
                    错误前一位字符串位置 = data.find(lines[(lines.index(i) - 1)])
                    if 错误前一位字符串位置 != -1:
                        错误位置 = (错误前一位字符串位置 + len(lines[(lines.index(i) - 1)]) + 1)
                        匹配最后x位 = 2
                        错误的最后一位 = i[-匹配最后x位:]
                        相对终止位置 = 0
                        完成纠错 = False
                        重试向后次数 = 100
                        符号纠错匹配不包含符号 = ["，", "。", "！", "？", "“", "”"]
                        data = re.sub(r'\r\n|\n|\r', '。', data)
                        for i in range(len(i) + 重试向后次数):
                            if len(data) - 错误位置 >= 重试向后次数:
                                if data[错误位置 + i - 匹配最后x位:错误位置 + i] in [错误的最后一位]:
                                    if (data[错误位置 - 1]) in ["，", "。", "！", "？", "、"]:
                                        相对终止位置 = i
                                        完成纠错 = True
                                        break
                                    else:
                                        相对终止位置 = i + 1
                                        错误位置 -= 1
                                        完成纠错 = True
                                        break
                            else:
                                break
                        if not 完成纠错:
                            for i in range(错误位置 + len(self.写入i) + 20):
                                if data[错误位置 + i] in ["，", "。", "！", "？"]:
                                    if (data[错误位置 - 1]) in ["，", "。", "！", "？"]:
                                        相对终止位置 = i
                                        完成纠错 = True
                                    else:
                                        相对终止位置 = i + 1
                                        错误位置 -= 1
                                        完成纠错 = True
                                二次处理 = False
                                if 完成纠错:
                                    写入i不含符号字数 = len(self.写入i.translate(str.maketrans('', '', ''.join(符号纠错匹配不包含符号))))
                                    纠错匹配不含符号字数 = len(data[错误位置:错误位置 + 相对终止位置].translate(str.maketrans('', '', ''.join(符号纠错匹配不包含符号))))
                                    if 写入i不含符号字数 > 纠错匹配不含符号字数:
                                        if 写入i不含符号字数 - 纠错匹配不含符号字数 > 3:
                                            尝试重试次数 = 1
                                            while True:
                                                纠错匹配 = data[错误位置:错误位置 + 相对终止位置]
                                                无符号纠错匹配字数 = len(纠错匹配.translate(str.maketrans('', '', ''.join(符号纠错匹配不包含符号))))
                                                无符号全局写入i = len(self.写入i.translate(str.maketrans('', '', ''.join(符号纠错匹配不包含符号))))
                                                if 无符号全局写入i == 无符号纠错匹配字数:
                                                    if data[错误位置:错误位置 + 相对终止位置 + 1][-1] in ["，", "。", "！", "？"]:
                                                        相对终止位置 += 1
                                                    break
                                                if 尝试重试次数 >= 200:
                                                    break
                                                尝试重试次数 += 1
                                                相对终止位置 += 1
                                        else:
                                            break
                                    else:
                                        break
                        纠错匹配 = data[错误位置:错误位置 + 相对终止位置]
                        lines[lines.index(self.写入i)] = 纠错匹配
                        self.日志.insert(tk.END, f"[{time.strftime('%H:%M:%S',time.localtime(time.time()))}][警告]:失败替换成功：{纠错匹配}\n\n")
                else:
                    self.日志.insert(tk.END, f"[{time.strftime('%H:%M:%S',time.localtime(time.time()))}][警告]:失败替换失败：{lines.index(i)}位置无项\n\n")
                    
        self.日志.insert(tk.END, f"[{time.strftime('%H:%M:%S',time.localtime(time.time()))}][信息]:字符串词条数：{len(lines)}，匹配成功的字符串词条数：{词条成功计数}\n")
        json文件份数 = (int(len(lines) / self.json项间隔.get()) + 1)
        分词列表 = {str(i + 1): line for i, line in enumerate(lines)}
        with open(f"output_.json", "w", encoding="utf-8") as f:
            json.dump(分词列表, f, ensure_ascii=False, indent=2)
        for i in range(json文件份数):
            列表 = lines[i * self.json项间隔.get():(i + 1) * self.json项间隔.get()]
            分词列表 = {str(i + 1): line for i, line in enumerate(列表)}
            with open(f"output_{i}.json", "w", encoding="utf-8") as f:
                json.dump(分词列表, f, ensure_ascii=False, indent=2)



if __name__ == "__main__":
    root = tk.Tk()
    app = 小说剪辑(root)
    root.mainloop()