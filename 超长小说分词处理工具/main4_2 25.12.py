from gradio_client import Client, handle_file
from tkinter import filedialog, ttk
from pydub import AudioSegment
from pydub.silence import *
from datetime import timedelta
from tqdm import tqdm
import keyboard
import threading
import numpy as np
import librosa
import pysrt
import tkinter as tk
import threading
import json
import pyperclip
import pyautogui
import requests
import serial
import time
import re
import os

class 小说剪辑:
    def __init__(self, root):
        self.root = root
        self.root.title("新建项目（10）")
        self.root.geometry("1280x720")
        self.构建窗口()
    
    def 构建窗口(self):
        标签页 = ttk.Notebook(root)
        标签页.pack(fill='both', expand=True)
        self.日志frame1 = ttk.Frame(标签页)
        self.脚本frame2 = ttk.Frame(标签页)
        self.分词器frame2 = ttk.Frame(标签页)
        self.视频生成frame2 = ttk.Frame(标签页)
        self.手动纠错frame3 = ttk.Frame(标签页)
        标签页.add(self.日志frame1, text='日志', compound = "left")
        标签页.add(self.脚本frame2, text='脚本', compound = "left")
        标签页.add(self.分词器frame2, text='分词器', compound = "left")
        标签页.add(self.视频生成frame2, text='音频字幕生成', compound = "left")
        标签页.add(self.手动纠错frame3, text='手动分词纠错', compound = "left")

        self.日志frame1.columnconfigure(1, weight=1)
        self.日志frame1.rowconfigure(1, weight=1)
        self.脚本frame2.columnconfigure(1, weight=1)
        self.脚本frame2.rowconfigure(2, weight=1)
        self.分词器frame2.columnconfigure(1, weight=1)
        self.分词器frame2.rowconfigure(2, weight=1)
        self.手动纠错frame3.columnconfigure(1, weight=1)
        self.手动纠错frame3.rowconfigure(2, weight=1)

        self.脚本文件容器 = tk.LabelFrame(self.脚本frame2, text="文件配置", padx=5, pady=5)
        self.脚本文件容器.grid(row=0, column=0, sticky="nsew", padx=5, pady=(2, 5))
        tk.Label(self.脚本文件容器, text="文件路径:").grid(row=0, column=0, sticky=tk.W)
        self.脚本文件路径 = tk.Entry(self.脚本文件容器, width=47)
        self.脚本文件路径.grid(row=0, column=1, sticky="ew", padx=5, pady=2)
        self.脚本文件浏览按钮 = tk.Button(self.脚本文件容器, text="浏览", command=lambda: self.浏览文件按钮(self.脚本文件路径, ("JSON 文件", "*.json")))
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
        self.视频生成开始 = tk.Button(self.视频生成frame2, text="音频字幕生成开始", command=lambda: self.函数多线程启动(self.视频生成开始处理))
        self.视频生成开始.grid(row=100, column=0, padx=5, pady=5)
        self.手动纠错开始 = tk.Button(self.手动纠错frame3, text="手动分词纠错开始", command=lambda: self.函数多线程启动(self.手动分词纠错开始处理))
        self.手动纠错开始.grid(row=100, column=0, padx=5, pady=5)

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
        self.APIKEY内容 = tk.StringVar(value="sk-f7a7ca5feafa44839727a5c739411501")
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
        self.分词文件浏览按钮 = tk.Button(self.分词文件容器, text="浏览", command=lambda: self.浏览文件按钮(self.分词文件路径, ("Text 源文件", "*.txt")))
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
        
        self.分词器导出设置容器 = tk.LabelFrame(self.分词器frame2, text="导出设置", padx=5, pady=5)
        self.分词器导出设置容器.grid(row=2, column=0, sticky="new", padx=5, pady=(5, 2))
        self.分词器导出设置第1行 = tk.Frame(self.分词器导出设置容器)
        self.分词器导出设置第1行.pack(fill=tk.X)
        tk.Label(self.分词器导出设置第1行,text="Json项间隔:").pack(side=tk.LEFT, padx=(0, 5))
        self.分词器json项间隔 = tk.IntVar(value=300)
        self.分词器json项间隔框架 = tk.Spinbox(self.分词器导出设置第1行,from_=100,to=100000,width=35,increment=50,textvariable=self.分词器json项间隔)
        self.分词器json项间隔框架.pack(side=tk.LEFT, padx=(0, 5))
        self.分词器导出设置第2行 = tk.Frame(self.分词器导出设置容器)
        self.分词器导出设置第2行.pack(fill=tk.X)
        tk.Label(self.分词器导出设置第2行, text="输出路径:").pack(side=tk.LEFT)
        self.分词器输出文件夹 = tk.Entry(self.分词器导出设置第2行, width=47)
        self.分词器输出文件夹.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        tk.Button(self.分词器导出设置第2行, text="浏览", command=lambda: self.浏览文件按钮(self.分词器输出文件夹, (), True)).pack(side=tk.LEFT, padx=5)
        self.分词器导出设置第3行 = tk.Frame(self.分词器导出设置容器)
        self.分词器导出设置第3行.pack(fill=tk.X)
        tk.Label(self.分词器导出设置第3行, text="输出名称:").pack(side=tk.LEFT)
        self.分词器输出名称 = tk.StringVar(value="")
        self.分词器输出名称框架 = tk.Entry(self.分词器导出设置第3行, width=47, textvariable=self.分词器输出名称)
        self.分词器输出名称框架.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        self.视频生成API容器 = tk.LabelFrame(self.视频生成frame2, text="语音生成API配置（Index-TTS v2.0）", padx=5, pady=5)
        self.视频生成API容器.grid(row=0, column=0, sticky="nsew", padx=5, pady=(5, 2))
        tk.Label(self.视频生成API容器, text="API URL:").grid(row=0, column=0, sticky=tk.W)
        self.视频生成APIURL内容 = tk.StringVar(value="http://127.0.0.1:7860")
        self.视频生成APIURL内容框架 = ttk.Combobox(self.视频生成API容器,textvariable=self.视频生成APIURL内容,width=47)
        self.视频生成APIURL内容框架.grid(row=0, column=1, padx=5, pady=2, sticky=tk.W)
        tk.Label(self.视频生成API容器, text="参考音频:").grid(row=1, column=0, sticky=tk.W)
        self.视频生成参考音频 = tk.Entry(self.视频生成API容器, width=47)
        self.视频生成参考音频.grid(row=1, column=1, sticky="ew", padx=5, pady=2)
        tk.Button(self.视频生成API容器, text="浏览", command=lambda: self.浏览文件按钮(self.视频生成参考音频, ("WAV/MP3 - Audio Files", "*.wav *.mp3"))).grid(row=1, column=2, padx=5, sticky=tk.W)

        self.视频生成文件容器 = tk.LabelFrame(self.视频生成frame2, text="文件配置", padx=5, pady=5)
        self.视频生成文件容器.grid(row=1, column=0, sticky="nsew", padx=5, pady=(5, 2))
        tk.Label(self.视频生成文件容器, text="文件路径:").grid(row=0, column=0, sticky=tk.W)
        self.视频生成文件路径 = tk.Entry(self.视频生成文件容器, width=47)
        self.视频生成文件路径.grid(row=0, column=1, sticky="ew", padx=5, pady=2)
        self.视频生成文件浏览按钮 = tk.Button(self.视频生成文件容器, text="浏览", command=lambda: self.浏览文件按钮(self.视频生成文件路径, ("JSON 文件", "*.json")))
        self.视频生成文件浏览按钮.grid(row=0, column=2, padx=5, sticky=tk.W)

        self.视频生成模型设置容器 = tk.LabelFrame(self.视频生成frame2, text="模型设置", padx=5, pady=5)
        self.视频生成模型设置容器.grid(row=2, column=0, sticky="nsew", padx=5, pady=(5, 2))
        tk.Label(self.视频生成模型设置容器, text="top_p").grid(row=0, column=0, sticky=tk.W)
        self.视频生成top_p = tk.DoubleVar(value=0.9)
        self.视频生成top_p框架 = tk.Spinbox(self.视频生成模型设置容器,from_=0,to=1,width=35,increment=0.1,textvariable=self.视频生成top_p)
        self.视频生成top_p框架.grid(row=0, column=1, padx=5, pady=2, sticky=tk.W)
        tk.Label(self.视频生成模型设置容器, text="top_k").grid(row=1, column=0, sticky=tk.W)
        self.视频生成top_k = tk.IntVar(value=50)
        self.视频生成top_k框架 = tk.Spinbox(self.视频生成模型设置容器,from_=0,to=100,width=35,increment=1,textvariable=self.视频生成top_k)
        self.视频生成top_k框架.grid(row=1, column=1, padx=5, pady=2, sticky=tk.W)
        tk.Label(self.视频生成模型设置容器, text="温度").grid(row=2, column=0, sticky=tk.W)
        self.视频生成温度 = tk.DoubleVar(value=1.0)
        self.视频生成温度框架 = tk.Spinbox(self.视频生成模型设置容器,from_=0,to=1,width=35,increment=0.1,textvariable=self.视频生成温度)
        self.视频生成温度框架.grid(row=2, column=1, padx=5, pady=2, sticky=tk.W)
        tk.Label(self.视频生成模型设置容器, text="长度惩罚").grid(row=3, column=0, sticky=tk.W)
        self.视频生成长度惩罚 = tk.DoubleVar(value=0)
        self.视频生成长度惩罚框架 = tk.Spinbox(self.视频生成模型设置容器,from_=0,to=10,width=35,increment=0.1,textvariable=self.视频生成长度惩罚)
        self.视频生成长度惩罚框架.grid(row=3, column=1, padx=5, pady=2, sticky=tk.W)
        tk.Label(self.视频生成模型设置容器, text="束数").grid(row=4, column=0, sticky=tk.W)
        self.视频生成束数 = tk.IntVar(value=6)
        self.视频生成束数框架 = tk.Spinbox(self.视频生成模型设置容器,from_=0,to=10,width=35,increment=1,textvariable=self.视频生成束数)
        self.视频生成束数框架.grid(row=4, column=1, padx=5, pady=2, sticky=tk.W)
        tk.Label(self.视频生成模型设置容器, text="重复惩罚").grid(row=5, column=0, sticky=tk.W)
        self.视频生成重复惩罚 = tk.DoubleVar(value=10)
        self.视频生成重复惩罚框架 = tk.Spinbox(self.视频生成模型设置容器,from_=0,to=10,width=35,increment=0.1,textvariable=self.视频生成重复惩罚)
        self.视频生成重复惩罚框架.grid(row=5, column=1, padx=5, pady=2, sticky=tk.W)
        tk.Label(self.视频生成模型设置容器, text="最大梅尔令牌数").grid(row=6, column=0, sticky=tk.W)
        self.视频生成最大梅尔令牌数 = tk.IntVar(value=1500)
        self.视频生成最大梅尔令牌数框架 = tk.Spinbox(self.视频生成模型设置容器,from_=0,to=10000,width=35,increment=1,textvariable=self.视频生成最大梅尔令牌数)
        self.视频生成最大梅尔令牌数框架.grid(row=6, column=1, padx=5, pady=2, sticky=tk.W)
        
        self.视频生成导出设置容器 = tk.LabelFrame(self.视频生成frame2, text="导出设置", padx=5, pady=5)
        self.视频生成导出设置容器.grid(row=3, column=0, sticky="nsew", padx=5, pady=(5, 2))
        tk.Label(self.视频生成导出设置容器, text="输出路径:").grid(row=0, column=0, sticky=tk.W)
        self.输出文件夹 = tk.Entry(self.视频生成导出设置容器, width=47)
        self.输出文件夹.grid(row=0, column=1, sticky="ew", padx=5, pady=2)
        tk.Button(self.视频生成导出设置容器, text="浏览", command=lambda: self.浏览文件按钮(self.输出文件夹, (), True)).grid(row=0, column=2, padx=5, sticky=tk.W)
        tk.Label(self.视频生成导出设置容器, text="输出名称:").grid(row=1, column=0, sticky=tk.W)
        self.输出名称=tk.StringVar(value="")
        self.输出名称框架 = tk.Entry(self.视频生成导出设置容器, width=47, textvariable=self.输出名称)
        self.输出名称框架.grid(row=1, column=1, sticky="ew", padx=5, pady=2)

        self.视频生成处理设置容器 = tk.LabelFrame(self.视频生成frame2, text="处理设置", padx=5, pady=5)
        self.视频生成处理设置容器.grid(row=0, column=1, sticky="nsew", padx=5, pady=(5, 2))
        tk.Label(self.视频生成处理设置容器, text="处理并行量:").grid(row=0, column=0, sticky=tk.W)
        self.视频生成处理次数 = tk.IntVar(value=2)
        self.视频生成处理次数框架 = tk.Spinbox(self.视频生成处理设置容器,from_=1,to=2,width=35,increment=1,textvariable=self.视频生成处理次数)
        self.视频生成处理次数框架.grid(row=0, column=1, padx=5, pady=2, sticky=tk.W)
        tk.Label(self.视频生成处理设置容器, text="空隙纠错量:").grid(row=1, column=0, sticky=tk.W)
        self.视频生成空隙纠错量 = tk.DoubleVar(value=4)
        self.视频生成空隙纠错量框架 = tk.Spinbox(self.视频生成处理设置容器,from_=2,to=128,width=35,increment=1,textvariable=self.视频生成空隙纠错量)
        self.视频生成空隙纠错量框架.grid(row=1, column=1, padx=5, pady=2, sticky=tk.W)
        tk.Label(self.视频生成处理设置容器, text="并行最短空隙长度").grid(row=2, column=0, sticky=tk.W)
        self.视频生成并行最短空隙长度 = tk.IntVar(value=0.1)
        self.视频生成并行最短空隙长度框架 = tk.Spinbox(self.视频生成处理设置容器,from_=0.1,to=0.5,width=35,increment=0.001,textvariable=self.视频生成并行最短空隙长度)
        self.视频生成并行最短空隙长度框架.grid(row=2, column=1, padx=5, pady=2, sticky=tk.W)
        tk.Label(self.视频生成处理设置容器, text="删除生成空隙长度").grid(row=3, column=0, sticky=tk.W)
        self.视频生成删除生成空隙长度 = tk.IntVar(value=0.090)
        self.视频生成删除生成空隙长度框架 = tk.Spinbox(self.视频生成处理设置容器,from_=0.00,to=0.299,width=35,increment=0.001,textvariable=self.视频生成删除生成空隙长度)
        self.视频生成删除生成空隙长度框架.grid(row=3, column=1, padx=5, pady=2, sticky=tk.W)
        
        self.手动纠错文件容器 = tk.LabelFrame(self.手动纠错frame3, text="文件配置", padx=5, pady=5)
        self.手动纠错文件容器.grid(row=0, column=0, sticky="nsew", padx=5, pady=(5, 2))
        tk.Label(self.手动纠错文件容器, text="A文件路径:").grid(row=0, column=0, sticky=tk.W)
        self.手动纠错A文件路径 = tk.Entry(self.手动纠错文件容器, width=47)
        self.手动纠错A文件路径.grid(row=0, column=1, sticky="ew", padx=5, pady=2)
        self.手动纠错A文件浏览按钮 = tk.Button(self.手动纠错文件容器, text="浏览", command=lambda: self.浏览文件按钮(self.手动纠错A文件路径, ("JSON 文件", "*.json")))
        self.手动纠错A文件浏览按钮.grid(row=0, column=2, padx=5, sticky=tk.W)
        tk.Label(self.手动纠错文件容器, text="B文件路径:").grid(row=1, column=0, sticky=tk.W)
        self.手动纠错B文件路径 = tk.Entry(self.手动纠错文件容器, width=47)
        self.手动纠错B文件路径.grid(row=1, column=1, sticky="ew", padx=5, pady=2)
        self.手动纠错B文件浏览按钮 = tk.Button(self.手动纠错文件容器, text="浏览", command=lambda: self.浏览文件按钮(self.手动纠错B文件路径, ("JSON 文件", "*.json")))
        self.手动纠错B文件浏览按钮.grid(row=1, column=2, padx=5, sticky=tk.W)
        tk.Label(self.手动纠错文件容器, text="输出名称:").grid(row=2, column=0, sticky=tk.W)
        self.手动纠错输出名称 = tk.StringVar(value="")
        self.手动纠错输出名称框架 = tk.Entry(self.手动纠错文件容器, width=47, textvariable=self.手动纠错输出名称)
        self.手动纠错输出名称框架.grid(row=2, column=1, sticky="ew", padx=5, pady=2)
        
        
        self.手动纠错主容器 = tk.LabelFrame(self.手动纠错frame3, text="处理", padx=5, pady=5)
        self.手动纠错主容器.grid(row=1, column=0, sticky="nsew", padx=5, pady=(5, 2), columnspan=2)
        self.手动纠错主容器.columnconfigure(0, weight=1)
        self.手动纠错显示 = tk.Text(self.手动纠错主容器, height=2)
        self.手动纠错显示.grid(row=0, column=0, sticky="ew", padx=5, pady=2)
        self.手动纠错输入 = tk.Entry(self.手动纠错主容器, width=47)
        self.手动纠错输入.grid(row=1, column=0, sticky="ew", padx=5, pady=2)
        self.手动纠错输入.bind('<Return>', lambda e: print("回车键"))
        

    def 手动分词纠错开始处理(self):
        with open(self.手动纠错A文件路径.get(), "r", encoding="utf-8") as f:
            A = json.load(f)
            if isinstance(A, dict):
                sorted_items = sorted(A.items(), key=lambda x: int(x[0]) if x[0].isdigit() else x[0])
                A = [value for key, value in sorted_items]
        with open(self.手动纠错B文件路径.get(), "r", encoding="utf-8") as f:
            B = json.load(f)
            if isinstance(B, dict):
                sorted_items = sorted(B.items(), key=lambda x: int(x[0]) if x[0].isdigit() else x[0])
                B = [value for key, value in sorted_items]
        错误数量 = 0
        for index0, index1 in zip(A, B):
            if index0 != index1:
                错误数量 += 1
        self.手动纠错显示.delete(1.0, tk.END)
        self.手动纠错显示.insert(tk.END, f"输入 A 时保存 A 的内容，输入 B 时保存 B 的内容，输入 自定义内容 保存 自定义内容 内容\n输入 退出 结束任务，输入 开始 启动任务，按下 回车键 确认输入。共计错误{错误数量}")
        while True:
            while True:
                if self.等待回车键():
                    break
            if self.手动纠错输入.get() == "开始":
                break
            if self.手动纠错输入.get() == "退出":
                return
        json列表 = A.copy()
        for index, (index0, index1) in enumerate(zip(A, B)):
            if index0 != index1:
                self.手动纠错显示.delete(1.0, tk.END)
                self.手动纠错输入.delete(0, tk.END)
                self.手动纠错显示.insert(tk.END, f"A:{index0}\nB:{index1}")
                while True:
                    time.sleep(0.01)
                    if self.等待回车键():
                        break
                if self.手动纠错输入.get() == "A" or self.手动纠错输入.get() == "a":
                    值 = index0
                elif self.手动纠错输入.get() == "B" or self.手动纠错输入.get() == "b":
                    值 = index1
                elif self.手动纠错输入.get() == "" or self.手动纠错输入.get() == "":
                    值 = index0
                elif self.手动纠错输入.get() == "退出":
                    return
                else:
                    值 = self.手动纠错输入.get()
                json列表[index] = 值
                print(值, index)
        self.手动纠错显示.delete(1.0, tk.END)
        self.手动纠错显示.insert(tk.END, f"完成\n文件已保存：{os.path.dirname(self.手动纠错A文件路径.get())}/{self.手动纠错输出名称.get()}_手动纠错.json")
        with open(f"{os.path.dirname(self.手动纠错A文件路径.get())}/{self.手动纠错输出名称.get()}_手动纠错.json", "w", encoding="utf-8") as f:
            json.dump({str(i): item for i, item in enumerate(json列表)}, f, ensure_ascii=False, indent=2)
            
    def 等待回车键(self):
        while not keyboard.is_pressed('enter'):
            time.sleep(0.01)
        while keyboard.is_pressed('enter'):
            time.sleep(0.01)
        return True
        
        
        
    def 视频生成开始处理(self):

        def 音频生成(text):
            client = Client(self.视频生成APIURL内容.get())
            result = client.predict(
                    emo_control_method="与音色参考音频相同",
                    prompt=handle_file(self.视频生成参考音频.get()),
                    text=text,
                    emo_ref_path=handle_file(self.视频生成参考音频.get()),
                    emo_weight=0.8,
                    vec1=0,
                    vec2=0,
                    vec3=0,
                    vec4=0,
                    vec5=0,
                    vec6=0,
                    vec7=0,
                    vec8=0,
                    emo_text="",
                    emo_random=False,
                    max_text_tokens_per_sentence=600,
                    param_16=True,
                    param_17=self.视频生成top_p.get(),
                    param_18=self.视频生成top_k.get(),
                    param_19=self.视频生成温度.get(),
                    param_20=self.视频生成长度惩罚.get(),
                    param_21=self.视频生成束数.get(),
                    param_22=self.视频生成重复惩罚.get(),
                    param_23=self.视频生成最大梅尔令牌数.get(),
                    api_name="/gen_single"
            )
            return result
        def 截取有效音频(input_path, output_path, silence_thresh=-50.0, min_silence_len=1000, keep_silence=200):
            audio = AudioSegment.from_file(input_path)
            nonsilent_ranges = detect_nonsilent(
                audio,
                min_silence_len=min_silence_len,
                silence_thresh=silence_thresh
            )
            if not nonsilent_ranges:
                print("未检测到非静音部分，请检查音频文件或调整参数。")
                return
            start_time = max(0, nonsilent_ranges[0][0] - keep_silence)
            end_time = min(len(audio), nonsilent_ranges[-1][1] + keep_silence)
            trimmed_audio = audio[start_time:end_time]
            trimmed_audio.export(output_path, format="WAV")
            return output_path
        
        def 统计音频长度(file_path):
            return len(AudioSegment.from_file(file_path)) / 1000.0
        
        def 音频空隙识别(audio_path, num_segments=5, silence_threshold_db=-40, min_silence_duration=0.1):
            try:
                num_segments = int(num_segments)
                y, sr = librosa.load(audio_path, sr=None)
                silence_threshold = librosa.db_to_amplitude(silence_threshold_db)
                frame_length = 2048
                hop_length = 512
                S = np.abs(librosa.stft(y, n_fft=frame_length, hop_length=hop_length))
                rms = librosa.feature.rms(S=S, hop_length=1)[0]
                hop_length = int(hop_length)
                times = librosa.frames_to_time(np.arange(len(rms)), sr=sr, hop_length=hop_length)
                silent_frames = rms < silence_threshold
                silence_segments = []
                start_idx = None
                for i, is_silent in enumerate(silent_frames):
                    if is_silent and start_idx is None:
                        start_idx = i
                    elif not is_silent and start_idx is not None:
                        start_time = float(times[start_idx])
                        end_time = float(times[i])
                        duration = end_time - start_time
                        if duration >= min_silence_duration:
                            silence_segments.append((start_time, end_time, duration))
                        start_idx = None
                if start_idx is not None:
                    start_time = float(times[start_idx])
                    end_time = float(times[-1])
                    duration = end_time - start_time
                    if duration >= min_silence_duration:
                        silence_segments.append((start_time, end_time, duration))
                silence_segments.sort(key=lambda x: x[2], reverse=True)
                result = silence_segments[:num_segments]
                return result
            except FileNotFoundError:
                print(f"错误：找不到音频文件 '{audio_path}'")
                return []
            except Exception as e:
                print(f"处理音频文件时发生错误: {e}")
                import traceback
                traceback.print_exc()
                return []
            
        with open(self.视频生成文件路径.get(), "r", encoding="utf-8") as f:
            data = json.load(f)
            start_time = time.time()

        total_characters = 0
        for value in data.values():
            if isinstance(value, str):
                total_characters += len(value)

        视频时间索引位置 = 0
        字幕列表 = pysrt.SubRipFile()
        音频列表 = AudioSegment.silent(duration=int(total_characters * 1000 / 2))
        items_list = list(data.items())
        批处理次数 = self.视频生成处理次数.get()
        for index in tqdm(range(0, len(items_list), 批处理次数), desc="音频字幕生成"):
            key = ""
            value = ""
            for i in range(批处理次数):
                if index + i < len(items_list):
                    key_for, value_for = items_list[index + i]
                    if key:
                        key += "。" + key_for
                    else:
                        key = key_for
                    if value:
                        value += "。" + value_for
                    else:
                        value = value_for
            for_start_time = time.time()
            有效音频路径 = 音频生成(value)['value']
            print("有效音频路径", time.time() - for_start_time)
            #有效音频路径 = 截取有效音频(有效音频路径, f"./缓存/{key}.WAV")
            有效音频时长 = 统计音频长度(有效音频路径)
            print("有效音频时长", time.time() - for_start_time)
            if 批处理次数 == 2:
                #索引方法 1代-3代
                # 音频空隙 = sorted(音频空隙识别(有效音频路径, num_segments=批处理次数-1), key=lambda x: x[0])
                # 音频空隙 = sorted(音频空隙识别(有效音频路径, num_segments=self.视频生成空隙纠错量.get(), min_silence_duration=self.视频生成并行最短空隙长度.get()), key=lambda x: abs(x[1] - 有效音频时长/2))
                音频空隙 = sorted(音频空隙识别(有效音频路径, num_segments=self.视频生成空隙纠错量.get(), min_silence_duration=self.视频生成并行最短空隙长度.get()), key=lambda x: abs(x[1] - ((有效音频时长) * (len(items_list[index:index + 批处理次数][0][1]) / len(value)))))
                aaaaa = time.time()
                for i in range(批处理次数-1):
                    try:
                        字幕数据 = pysrt.SubRipItem()
                        字幕数据.start = timedelta(seconds=round(视频时间索引位置+0.01, 3))
                        字幕数据.end = timedelta(seconds=round(视频时间索引位置+音频空隙[i][1], 3))
                        key_for, value_for = items_list[index+i]
                        字幕数据.text = value_for
                        字幕列表.append(字幕数据)
                        if i == 批处理次数-2:
                            字幕数据 = pysrt.SubRipItem()
                            字幕数据.start = timedelta(seconds=round(视频时间索引位置+音频空隙[i][1]+0.01, 3))
                            字幕数据.end = timedelta(seconds=round(视频时间索引位置+有效音频时长-self.视频生成删除生成空隙长度.get(), 3))
                            key_for, value_for = items_list[index+i+1]
                            字幕数据.text = value_for
                            字幕列表.append(字幕数据)
                    except IndexError as e:
                        pass
                print("if", time.time()-aaaaa)
            else:
                aaaaa = time.time()
                字幕数据 = pysrt.SubRipItem()
                字幕数据.start = timedelta(seconds=视频时间索引位置)
                字幕数据.end = timedelta(seconds=视频时间索引位置+有效音频时长)
                字幕数据.text = value
                字幕列表.append(字幕数据)
                print("else", time.time()-aaaaa)
            aaaaa = time.time()
            音频列表 = 音频列表.overlay(AudioSegment.from_file(有效音频路径), position=视频时间索引位置*1000)
            print("音频列表", time.time()-aaaaa)
            视频时间索引位置 += 有效音频时长 - self.视频生成删除生成空隙长度.get()
            self.日志.insert(tk.END, f"[{time.strftime('%H:%M:%S',time.localtime(time.time()))}][信息]:添加音频字幕：进度:{index+1:0{len(str(len(data)))}d}/{len(data):0{len(str(len(data)))}d} {((index+1)/len(data))*100:05.3f}%   耗时:{(time.time()-for_start_time):05.3f}秒   项:{value}   {有效音频时长}   {((有效音频时长) * (len(items_list[index:index + 批处理次数][0][1]) / len(value)))}\n") 
        输出路径 = self.输出文件夹.get() if self.输出文件夹.get() else "./"
        输出名称 = self.输出名称.get() if self.输出名称.get() else "output"
        音频列表.export(f"{输出路径}/{输出名称}.WAV", format="wav")
        截取有效音频(f"{输出路径}/{输出名称}.WAV", f"{输出路径}/{输出名称}.WAV")
        字幕列表.save(f"{输出路径}/{输出名称}.srt")

        with open(f"{输出路径}/{输出名称}.srt", 'r', encoding='utf-8') as file:
            content = file.read()
        content = content.replace('000', '').replace('\n0:', '\n00:').replace(' 0:', ' 00:').replace('.', ',').replace('00:00:00', '00:00:00,000').replace(',000,', ',')
        with open(f"{输出路径}/{输出名称}.srt", 'w', encoding='utf-8') as file:
            file.write(content)

        self.日志.insert(tk.END, f"[{time.strftime('%H:%M:%S',time.localtime(time.time()))}][信息]:音频字幕处理耗时：{time.time() - start_time}秒\n") 

    def 浏览文件按钮(self, file_type, type_name, 文件夹=False):
        if 文件夹:
            file_path = filedialog.askdirectory()
        else:
            file_path = filedialog.askopenfilename(
                filetypes=[type_name]
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
                        文本分词，严格执行一下操作：内容不要改变，不要过多的杂碎，按照意识流分词，每行最多20字，标点符号需要正确处理，尾部符号也需要正确处理（不能添加符号，不能更改符号，尾部不需要除顿号省略号感叹号问号以外的符号）"""
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
                "enable_thinking": False,
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
        
        未纠错lines = lines.copy()
        词条成功计数 = 0
        for i in lines:
            纠错匹配 = i
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
        输出路径 = self.分词器输出文件夹.get() if self.分词器输出文件夹.get() else "./"
        输出名称 = self.分词器输出名称.get() if self.分词器输出名称.get() else "output"
        for index, index2 in zip(["已纠错", "未纠错"], [lines, 未纠错lines]):
            分词列表 = {str(i + 1): line for i, line in enumerate(index2)}
            with open(f"{输出路径}/{输出名称}_{index}.json", "w", encoding="utf-8") as f:
                json.dump(分词列表, f, ensure_ascii=False, indent=2)
            当前数据集份数 = (int(len(index2) / self.分词器json项间隔.get()) + 1)
            for batch_index in range(当前数据集份数):
                列表 = index2[batch_index * self.分词器json项间隔.get():(batch_index + 1) * self.分词器json项间隔.get()]
                分词列表 = {str(i + 1): line for i, line in enumerate(列表)}
                with open(f"{输出路径}/{输出名称}_{index}_{batch_index}.json", "w", encoding="utf-8") as f:
                    json.dump(分词列表, f, ensure_ascii=False, indent=2)



if __name__ == "__main__":
    root = tk.Tk()
    app = 小说剪辑(root)
    root.mainloop()