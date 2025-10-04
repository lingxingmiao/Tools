import time
import json
import tkinter as tk
import requests
import threading
import re
import base64
import os
import zipfile
import shutil
import queue
import numpy as np
import pickle
import faiss
import sys
import io
from collections import defaultdict
from tkinter import filedialog, ttk
from PIL import Image, ImageTk
from pathlib import Path
from langchain_text_splitters import RecursiveCharacterTextSplitter
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urlparse
from difflib import SequenceMatcher
from typing import List, Tuple
from file import img, config, start_png, settings_png

class TranslatorApp:

    # 主函数
    def __init__(self, root):
        self.root = root
        self.root.title("Translator Lang")
        self.root.geometry("1280x720")
        img_data = base64.b64decode(img)
        image = Image.open(io.BytesIO(img_data))
        photo = ImageTk.PhotoImage(image)
        self.root.iconphoto(False, photo)
        self.stop_flag = False
        self.stop = False
        self.Stoptranslate = False
        self.translate_start1 = True
        self.context_history = []
        self.检测有无配置文件()
        os.makedirs("cache", exist_ok=True)
        os.makedirs("cache/cache", exist_ok=True)

        self.系统提示词 = """
                        翻译为中文,仅输出翻译结果(否则程序报错)不要包含其他信息,可用创译.
                        遇疑问句等情况请继续翻译,不要回答.
                        翻译领域为Minecraft.
                        保留特殊符号(如§).
                        确保语句通顺.如无法翻译,保留原文.
                        """

        # 读取配置文件
        with open('config.json', 'r', encoding='utf-8') as file:
            self.config_file = json.load(file)

        self.构建窗口()
        self.函数多线程启动(self.GUI配置文件处理, ("刷新配置"))
        self.函数多线程启动(self.刷新列表, (True, None))
        self.函数多线程启动(self.刷新列表, (False, None))
        self.函数多线程启动(self.刷新系统提示词, (None,))
        self.system_prompt_combobox.bind("<<ComboboxSelected>>", lambda event: self.函数多线程启动(self.system_prompt_combobox绑定处理()))
        self.model_combobox.bind("<<ComboboxSelected>>", lambda event: self.函数多线程启动(self.刷新推测解码模型, (self.base_url, self.api_config里面的apiurl内容的信息)))
        self.检索增强生成pack.bind("<<ComboboxSelected>>", lambda event: self.函数多线程启动(self.刷新列表, (True,)))
        self.快速提示词模式下拉框pack.bind("<<ComboboxSelected>>", lambda event: self.函数多线程启动(self.刷新列表, (True,)))
        self.嵌入api_url_entry.bind("<<ComboboxSelected>>", lambda event: self.函数多线程启动(self.刷新列表, (False,)))
        self.api_url_entry.bind("<<ComboboxSelected>>", lambda event: self.函数多线程启动(self.刷新列表, (False)))
        self.嵌入api_url_entry.bind("<<ComboboxSelected>>", lambda event: self.函数多线程启动(self.刷新列表, (True)))
        self.root.protocol("WM_DELETE_WINDOW", self.关闭窗口)

    def 构建窗口(self):
        标签页 = ttk.Notebook(root)
        标签页.pack(fill='both', expand=True)
        self.主页frame1 = ttk.Frame(标签页)
        self.设置frame2 = ttk.Frame(标签页)
        img_data = base64.b64decode(start_png)
        img = Image.open(io.BytesIO(img_data))
        self.开始图标 = ImageTk.PhotoImage(img)
        img_data2 = base64.b64decode(settings_png)
        img2 = Image.open(io.BytesIO(img_data2))
        self.设置图标 = ImageTk.PhotoImage(img2)
        标签页.add(self.主页frame1, text='开始', compound = "left", image = self.开始图标)
        标签页.add(self.设置frame2, text='设置', compound = "left", image = self.设置图标)

        self.主页frame1.columnconfigure(1, weight=1)
        self.主页frame1.rowconfigure(2, weight=1)
        self.设置frame2.columnconfigure(1, weight=1)
        self.设置frame2.rowconfigure(2, weight=1)

        self.配置文件tk = tk.LabelFrame(self.设置frame2, text="配置文件", padx=5, pady=5)
        self.配置文件tk.grid(row=0, column=0, columnspan=2, sticky="ew", padx=5, pady=(5, 2))
        self.配置文件tk.grid_columnconfigure(3, weight=1)
        self.配置文件_加载 = tk.Button(self.配置文件tk,text="加载配置",command=lambda: self.函数多线程启动(self.GUI配置文件处理, ("加载配置")))
        self.配置文件_加载.grid(row=0, column=0, padx=0, pady=2, sticky="ew")
        self.配置文件_保存 = tk.Button(self.配置文件tk,text="保存配置",command=lambda: self.函数多线程启动(self.GUI配置文件处理, ("保存配置")))
        self.配置文件_保存.grid(row=0, column=1, padx=0, pady=2, sticky="ew")
        self.配置文件_删除 = tk.Button(self.配置文件tk,text="删除配置",command=lambda: self.函数多线程启动(self.GUI配置文件处理, ("删除配置")))
        self.配置文件_删除.grid(row=0, column=2, padx=0, pady=2, sticky="ew")
        self.配置文件_项 = tk.StringVar()
        self.配置文件_项 = ttk.Combobox(self.配置文件tk,textvariable=self.配置文件_项)
        self.配置文件_项.grid(row=0, column=3, padx=5, pady=2, sticky="ew")

        self.api_frame = tk.LabelFrame(self.设置frame2, text="API配置", padx=5, pady=5)
        self.api_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=(5, 2))
        tk.Label(self.api_frame, text="API URL:").grid(row=0, column=0, sticky=tk.W)
        self.apiurl内容 = tk.StringVar()
        self.api_url_entry = ttk.Combobox(self.api_frame,textvariable=self.apiurl内容,width=47)
        self.api_url_entry.grid(row=0, column=1, padx=5, pady=2, sticky=tk.W)
        self.API名称 = tk.Label(self.api_frame,text="")
        self.API名称.grid(row=1, column=2, padx=5, pady=2, sticky=tk.W)
        self.v1模式选项 = tk.BooleanVar(value=False)
        self.v1_mode_cb = tk.Checkbutton(self.api_frame,text="v1模式",variable=self.v1模式选项)
        self.v1_mode_cb.grid(row=0, column=2, padx=5, pady=2, sticky=tk.W)
        tk.Label(self.api_frame, text="API Key:").grid(row=1, column=0, sticky=tk.W)
        self.apikey内容 = tk.StringVar()
        self.api_key_entry = ttk.Combobox(self.api_frame,textvariable=self.apikey内容,width=47)
        self.api_key_entry.grid(row=1, column=1, padx=5, pady=2, sticky=tk.W)
        tk.Label(self.api_frame, text="语言模型:").grid(row=2, column=0, sticky=tk.W)
        self.模型名称内容 = tk.StringVar()
        self.model_combobox = ttk.Combobox(self.api_frame,textvariable=self.模型名称内容,width=47)
        self.model_combobox.grid(row=2, column=1, padx=5, pady=2, sticky=tk.W)
        self.refresh_button = tk.Button(self.api_frame,text="刷新列表",command=lambda: self.函数多线程启动(self.刷新列表, (False)))
        self.refresh_button.grid(row=2, column=2, padx=5, pady=2, sticky=tk.W)
        tk.Label(self.api_frame, text="API URL:").grid(row=3, column=0, sticky=tk.W)
        self.嵌入apiurl内容 = tk.StringVar()
        self.嵌入api_url_entry = ttk.Combobox(self.api_frame,textvariable=self.嵌入apiurl内容,width=47)
        self.嵌入api_url_entry.grid(row=3, column=1, padx=5, pady=2, sticky=tk.W)
        self.嵌入API名称 = tk.Label(self.api_frame,text="")
        self.嵌入API名称.grid(row=4, column=2, padx=5, pady=2, sticky=tk.W)
        self.嵌入v1模式选项 = tk.BooleanVar(value=False)
        self.嵌入v1_mode_cb = tk.Checkbutton(self.api_frame,text="v1模式",variable=self.嵌入v1模式选项)
        self.嵌入v1_mode_cb.grid(row=3, column=2, padx=5, pady=2, sticky=tk.W)
        tk.Label(self.api_frame, text="API Key:").grid(row=4, column=0, sticky=tk.W)
        self.嵌入apikey内容 = tk.StringVar()
        self.嵌入api_key_entry = ttk.Combobox(self.api_frame,textvariable=self.嵌入apikey内容,width=47)
        self.嵌入api_key_entry.grid(row=4, column=1, padx=5, pady=2, sticky=tk.W)
        tk.Label(self.api_frame, text="嵌入模型:").grid(row=5, column=0, sticky=tk.W)
        self.嵌入模型名称内容 = tk.StringVar()
        self.嵌入模型名称内容pack = ttk.Combobox(self.api_frame,textvariable=self.嵌入模型名称内容,width=47)
        self.嵌入模型名称内容pack.grid(row=5, column=1, padx=5, pady=2, sticky=tk.W)
        self.嵌入refresh_button = tk.Button(self.api_frame,text="刷新列表",command=lambda: self.函数多线程启动(self.刷新列表, (True)))
        self.嵌入refresh_button.grid(row=5, column=2, padx=5, pady=2, sticky=tk.W)
        self.函数多线程启动(self.api地址列表处理())

        self.config_main_frame = tk.LabelFrame(self.设置frame2, text="翻译配置", padx=5, pady=5)
        self.config_main_frame.grid(row=1, column=1, sticky="nsew", padx=5, pady=(5, 2))
        self.config_frame1 = tk.Frame(self.config_main_frame)
        self.config_frame1.pack(fill=tk.X)
        self.use_context = tk.BooleanVar(value=True)
        self.context_cb = tk.Checkbutton(self.config_frame1,text="（提高精度.中 降低性能.低）启用上下文",variable=self.use_context)
        self.context_cb.pack(side=tk.LEFT, padx=5)
        self.config_frame3 = tk.Frame(self.config_main_frame)
        self.config_frame3.pack(fill=tk.X)
        self.enable_key_value = tk.BooleanVar(value=True)
        self.key_value_cb = tk.Checkbutton(self.config_frame3,text="（提高精度.中 降低性能.低）启用键值输入",variable=self.enable_key_value)
        self.key_value_cb.pack(side=tk.LEFT, padx=5)
        self.config_frame2 = tk.Frame(self.config_main_frame)
        self.config_frame2.pack(fill=tk.X)
        self.enable_think = tk.BooleanVar(value=False)
        self.think_cb = tk.Checkbutton(self.config_frame2,text="（提高精度.中 降低性能.高）启用思考（需要模型支持）",variable=self.enable_think)
        self.think_cb.pack(side=tk.LEFT, padx=5)
        self.思考等级Text = tk.Label(self.config_frame2,text="思考等级:")
        self.思考等级Text.pack(side=tk.LEFT, padx=(0, 5))
        self.thinkingLevel = tk.IntVar(value=1)
        self.thinkingLevel1 = tk.Spinbox(self.config_frame2,from_=1,to=4,width=5,textvariable=self.thinkingLevel)
        self.thinkingLevel1.pack(side=tk.LEFT, padx=(0, 5))
        self.config_frame3 = tk.Frame(self.config_main_frame)
        self.config_frame3.pack(fill=tk.X)
        self.enable_quick_search_btn = tk.BooleanVar(value=True)
        self.quick_search_btn_cp = tk.Checkbutton(self.config_frame3,text="（提高精度.高 提高性能.高）启用快速提示词",variable=self.enable_quick_search_btn)
        self.quick_search_btn_cp.pack(side=tk.LEFT, padx=5)
        self.快速提示词数量Text = tk.Label(self.config_frame3,text="提示词数量:")
        self.快速提示词数量Text.pack(side=tk.LEFT, padx=(0, 5))
        self.retrieve_count = tk.IntVar(value=3)
        self.retrieve_spinbox = tk.Spinbox(self.config_frame3,from_=0,to=128,width=5,textvariable=self.retrieve_count)
        self.retrieve_spinbox.pack(side=tk.LEFT, padx=(0, 5))
        self.快速提示词模式Text = tk.Label(self.config_frame3,text="模式:")
        self.快速提示词模式Text.pack(side=tk.LEFT, padx=(0, 5))
        self.快速提示词模式下拉框 = tk.StringVar(value="检索增强生成")
        self.快速提示词模式下拉框pack = ttk.Combobox(self.config_frame3,width=12,textvariable=self.快速提示词模式下拉框,values=["检索增强生成", "系统提示词检索"])
        self.快速提示词模式下拉框pack.pack(side=tk.LEFT, padx=(0, 5))
        self.检索增强生成模式Text = tk.Label(self.config_frame3,text="检索增强生成模式:")
        self.检索增强生成模式Text.pack(side=tk.LEFT, padx=(0, 5))
        self.检索增强生成模式 = tk.StringVar(value="EM-2P")
        self.检索增强生成模式pack = ttk.Combobox(self.config_frame3,width=12,textvariable=self.检索增强生成模式,values=["EM-1P", "EM-2P"])
        self.检索增强生成模式pack.pack(side=tk.LEFT, padx=(0, 5))
        self.config_frame4 = tk.Frame(self.config_main_frame)
        self.config_frame4.pack(fill=tk.X)
        self.启用自定义模型温度系数 = tk.BooleanVar(value=True)
        self.启用自定义模型温度系数pack = tk.Checkbutton(self.config_frame4,text="（提高精度.低 提高性能.无）启用自定义模型",variable=self.启用自定义模型温度系数)
        self.启用自定义模型温度系数pack.pack(side=tk.LEFT, padx=5)
        self.温度系数Text = tk.Label(self.config_frame4,text="Temperature:")
        self.温度系数Text.pack(side=tk.LEFT, padx=(0, 5))
        self.温度系数 = tk.IntVar(value=0.3)
        self.温度系数pack = tk.Spinbox(self.config_frame4,from_=0.0,to=2.0,width=5,increment=0.1,textvariable=self.温度系数)
        self.温度系数pack.pack(side=tk.LEFT, padx=(0, 5))
        self.核心采样Text = tk.Label(self.config_frame4,text="Top_p:")
        self.核心采样Text.pack(side=tk.LEFT, padx=(0, 5))
        self.核心采样 = tk.IntVar(value=0.60)
        self.核心采样pack = tk.Spinbox(self.config_frame4,from_=0.00,to=1.00,width=5,increment=0.05,textvariable=self.核心采样)
        self.核心采样pack.pack(side=tk.LEFT, padx=(0, 5))
        self.config_frame5 = tk.Frame(self.config_main_frame)
        self.config_frame5.pack(fill=tk.X)
        self.启用推测解码 = tk.BooleanVar(value=True)
        self.启用推测解码pack = tk.Checkbutton(self.config_frame5,text="（降低精度.低 提高性能.高）启用推测解码（需要API支持）",variable=self.启用推测解码)
        self.启用推测解码pack.pack(side=tk.LEFT, padx=5)
        self.推测解码下拉框Text = tk.Label(self.config_frame5,text="推测解码模型:")
        self.推测解码下拉框Text.pack(side=tk.LEFT, padx=(0, 5))
        self.推测解码下拉框 = tk.StringVar()
        self.推测解码下拉框pack = ttk.Combobox(self.config_frame5,width=33,textvariable=self.推测解码下拉框)
        self.推测解码下拉框pack.pack(side=tk.LEFT, padx=(0, 5))
        self.config_frameX3 = tk.Frame(self.config_main_frame)
        self.config_frameX3.pack(fill=tk.X)
        self.向量嵌入生成并行数Text = tk.Label(self.config_frameX3,text="向量嵌入生成并行数:")
        self.向量嵌入生成并行数Text.pack(side=tk.LEFT, padx=(0, 5))
        self.向量嵌入生成并行数 = tk.IntVar(value=16)
        self.向量嵌入生成并行数pack = tk.Spinbox(self.config_frameX3,from_=4,to=1024,width=5,increment=4,textvariable=self.向量嵌入生成并行数)
        self.向量嵌入生成并行数pack.pack(side=tk.LEFT, padx=(0, 5))
        
        self.翻译缓存 = tk.LabelFrame(self.设置frame2, text="翻译缓存/系统提示词", padx=5, pady=5)
        self.翻译缓存.grid(row=2, column=1, sticky="new", padx=5, pady=(5, 2))
        self.config_frameW1_1 = tk.Frame(self.翻译缓存)
        self.config_frameW1_1.pack(fill=tk.X)
        self.替换翻译过的键值的值 = tk.BooleanVar(value=True)
        self.替换翻译过的键值 = tk.Checkbutton(self.config_frameW1_1,text="替换缓存中的键值",variable=self.替换翻译过的键值的值)
        self.替换翻译过的键值.pack(side=tk.LEFT, padx=5)
        self.记录翻译过的键值的值 = tk.BooleanVar(value=True)
        self.记录翻译过的键值 = tk.Checkbutton(self.config_frameW1_1,text="记录翻译过的键值",variable=self.记录翻译过的键值的值)
        self.记录翻译过的键值.pack(side=tk.LEFT, padx=5)
        self.导出包含键的值 = tk.BooleanVar(value=True)
        self.导出包含键 = tk.Checkbutton(self.config_frameW1_1,text="导出包含键",variable=self.导出包含键的值)
        self.导出包含键.pack(side=tk.LEFT, padx=5)
        self.config_frameW1_2 = tk.Frame(self.翻译缓存)
        self.config_frameW1_2.pack(fill=tk.X)
        self.清除缓存 = tk.Button(self.config_frameW1_2,text="清除翻译缓存",command=self.def清除缓存)
        self.清除缓存.pack(side=tk.LEFT, padx=5)
        self.导出ChatML数据集 = tk.Button(self.config_frameW1_2,text="导出ChatML数据集",command=lambda: self.函数多线程启动(self.def导出Jsonl, ("ChatML数据集")))
        self.导出ChatML数据集.pack(side=tk.LEFT, padx=5)
        self.导出Alpaca数据集 = tk.Button(self.config_frameW1_2,text="导出Alpaca数据集",command=lambda: self.函数多线程启动(self.def导出Jsonl, ("Alpaca数据集")))
        self.导出Alpaca数据集.pack(side=tk.LEFT, padx=5)
        self.从着色器包与模组导入 = tk.Button(self.config_frameW1_2,text="从模组或着色器包导入翻译缓存",command=lambda: self.函数多线程启动(self.def翻译缓存, ("导入")))
        self.从着色器包与模组导入.pack(side=tk.LEFT, padx=5)
        self.config_frameW1_3 = tk.Frame(self.翻译缓存)
        self.config_frameW1_3.pack(fill=tk.X)
        self.清除提示词 = tk.Button(self.config_frameW1_3,text="清除系统提示词",command=lambda: self.函数多线程启动(self.def默认提示词, ("清除")))
        self.清除提示词.pack(side=tk.LEFT, padx=5, pady=5)
        self.加载翻译缓存 = tk.Button(self.config_frameW1_3,text="加载翻译缓存到提示词",command=lambda: self.函数多线程启动(self.def默认提示词, ("加载")))
        self.加载翻译缓存.pack(side=tk.LEFT, padx=5, pady=5)

        self.其他框 = tk.LabelFrame(self.设置frame2, text="其他", padx=5, pady=5)
        self.其他框.grid(row=2, column=0, sticky="new", padx=5, pady=(5, 2))
        self.config_frameW2_1 = tk.Frame(self.其他框)
        self.config_frameW2_1.pack(fill=tk.X)
        self.自动滚动至底部的值 = tk.BooleanVar(value=True)
        self.自动滚动至底部 = tk.Checkbutton(self.config_frameW2_1,text="自动滚动至底部",variable=self.自动滚动至底部的值)
        self.自动滚动至底部.pack(side=tk.LEFT, padx=5)
        
        self.bottom_container = tk.Frame(self.主页frame1)
        self.bottom_container.grid(row=2, column=0, columnspan=2, sticky="nsew", padx=5)
        self.主页frame1.rowconfigure(2, weight=1)
        self.control_frame = tk.Frame(self.bottom_container)
        self.control_frame.pack(side=tk.LEFT, padx=5)
        self.translate_start = tk.Button(self.control_frame,text="开始翻译",command=self.translateStart)
        self.translate_start.pack(anchor=tk.W)
        self.translate_stop = tk.Button(self.control_frame,text="暂停翻译",command=self.translateStop)
        self.translate_stop.pack(anchor=tk.W)
        self.status_label = tk.Label(self.control_frame,text="准备就绪")
        self.status_label.pack(anchor=tk.W, pady=2)
        self.EstimatedTimeRequired1 = tk.Label(self.control_frame,text="")
        self.EstimatedTimeRequired1.pack(anchor=tk.W, pady=2)
        self.EstimatedTimeRequired2 = tk.Label(self.control_frame,text="")
        self.EstimatedTimeRequired2.pack(anchor=tk.W, pady=2)
        self.每秒输出词元文本 = tk.Label(self.control_frame,text="")
        self.每秒输出词元文本.pack(anchor=tk.W, pady=2)
        self.output_frame = tk.LabelFrame(self.bottom_container, text="日志", padx=5, pady=5)
        self.output_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        self.output_text = tk.Text(self.output_frame, height=5000)
        self.output_text.pack(fill=tk.BOTH, expand=True)

        提示词配置 = tk.LabelFrame(self.主页frame1, text="文件配置", padx=5, pady=5)
        提示词配置.grid(row=1, column=1, sticky="nsew", padx=5, pady=(2, 5))
        提示词配置.grid_columnconfigure(1, weight=1)
        tk.Label(提示词配置, text="系统提示词选择:").grid(row=0, column=0, sticky=tk.W)
        self.system_prompt_var = tk.StringVar()
        self.system_prompt_combobox = ttk.Combobox(提示词配置,textvariable=self.system_prompt_var,width=100)
        self.system_prompt_combobox.grid(row=0, column=1, padx=5, pady=2, sticky="ew")
        tk.Label(提示词配置, text="检索增强生成选择:").grid(row=1, column=0, sticky=tk.W)
        self.检索增强生成 = tk.StringVar()
        self.检索增强生成pack = ttk.Combobox(提示词配置,textvariable=self.检索增强生成,width=100)
        self.检索增强生成pack.grid(row=1, column=1, padx=5, pady=2, sticky="ew")

        self.file_frame = tk.LabelFrame(self.主页frame1, text="文件配置", padx=5, pady=5)
        self.file_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=(2, 5))
        tk.Label(self.file_frame, text="待处理文件路径:").grid(row=0, column=0, sticky=tk.W)
        self.file_path_entry = tk.Entry(self.file_frame, width=47)
        self.file_path_entry.grid(row=0, column=1, sticky="ew", padx=5, pady=2)
        self.browse_button = tk.Button(self.file_frame, text="浏览", command=lambda: self.browse_file(self.file_path_entry))
        self.browse_button.grid(row=0, column=2, padx=5, sticky=tk.W)
        tk.Label(self.file_frame, text="新版本文件路径:").grid(row=1, column=0, sticky=tk.W)
        self.新版本文件路径 = tk.Entry(self.file_frame, width=47)
        self.新版本文件路径.grid(row=1, column=1, sticky="ew", padx=5, pady=2)
        self.新版本文件路径browse_button = tk.Button(self.file_frame, text="浏览", command=lambda: self.browse_file(self.新版本文件路径))
        self.新版本文件路径browse_button.grid(row=1, column=2, padx=5, sticky=tk.W)

        self.函数多线程启动(self.日志滚动)

    def def翻译缓存(self, model, event=None):
        #预留多语言支持
        语言A = "en_us"
        语言B = "zh_cn"
        json_file = "original-translated-value.json"
        def 读取lang文件(file_path_or_content):
            result = {}
            if os.path.exists(file_path_or_content):
                with open(file_path_or_content, 'r', encoding='utf-8') as f:
                    content = f.read()
            else:
                content = file_path_or_content
            lines = content.splitlines()
            for line in lines:
                line = line.strip()
                if line and not line.startswith(('#', '//')) and '=' in line:
                    key, value = line.split('=', 1)
                    result[key] = value
            return result
        def 获取assets后路径(文件名):
            base_dir = Path(f"./cache/cache/{文件名}")
            for pattern in [f'{语言A}.lang', f'{语言A}.json']:
                for file_path in (base_dir / "assets").rglob(pattern):
                    return file_path.relative_to(base_dir).parent
        def 解压Zip文件(文件, 含缓存路径):
            start_time = time.time()
            self.output_text.insert(tk.END, f"[{time.strftime('%H:%M:%S', time.localtime())}][设置][INFO]:解压Jar文件中...\n")
            with zipfile.ZipFile(文件, 'r') as zip_ref:
                zip_ref.extractall(f"./cache/{含缓存路径}")
                zip_ref.close()
            self.output_text.insert(tk.END, f"[{time.strftime('%H:%M:%S', time.localtime())}][设置][INFO]:解压耗时{time.time() - start_time}秒\n")
        def 转换Lang(Json文件):
            with open(Json文件, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return "\n".join(f"{key}={value}" for key, value in data.items())
        def 导入至缓存(PathA, PathB):
            语言A内容 = 读取lang文件(PathA)
            语言B内容 = 读取lang文件(PathB)
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                existing_data = []
            existing_originals = {item['original'] for item in existing_data}
            共同键 = set(语言A内容.keys()) & set(语言B内容.keys())
            added_count = 0
            for key in 共同键:
                original_value = 语言A内容[key]
                translated_value = 语言B内容[key]
                if original_value not in existing_originals:
                    existing_data.append({"key": key, "original": original_value, "translated": translated_value})
                    existing_originals.add(original_value)
                    added_count += 1
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(existing_data, f, ensure_ascii=False, indent=2)
        def 导入(文件路径):
            文件名 = os.path.basename(文件路径) 
            名称, 格式 = os.path.splitext(文件名)
            解压Zip文件(文件路径, f"cache/{名称}")
            if 格式 == ".zip":
                PathA = f"./cache/cache/{名称}/shaders/lang/{语言A}.lang"
                PathB = f"./cache/cache/{名称}/shaders/lang/{语言B}.lang"
            elif 格式 == ".jar":
                assets后路径 = 获取assets后路径(名称)
                导入模式 = False
                if Path(f"./cache/cache/{名称}/{assets后路径}/{语言A}.lang").is_file():
                    PathA = f"./cache/cache/{名称}/{assets后路径}/{语言A}.lang"
                    if Path(f"./cache/cache/{名称}/{assets后路径}/{语言B}.lang").is_file():
                        PathB = f"./cache/cache/{名称}/{assets后路径}/{语言B}.lang"
                        导入模式 = True
                    else:
                        self.output_text.insert(tk.END, f"[{time.strftime('%H:%M:%S',time.localtime(time.time()))}][设置][ERROR]:无法找到{语言B}.lang\n")
                elif Path(f"./cache/cache/{名称}/{assets后路径}/{语言A}.json").is_file():
                    PathA = 转换Lang(f"./cache/cache/{名称}/{assets后路径}/{语言A}.json")
                    if Path(f"./cache/cache/{名称}/{assets后路径}/{语言B}.json").is_file():
                        PathB = 转换Lang(f"./cache/cache/{名称}/{assets后路径}/{语言B}.json")
                        导入模式 = True
                    else:
                        self.output_text.insert(tk.END, f"[{time.strftime('%H:%M:%S',time.localtime(time.time()))}][设置][ERROR]:无法找到{语言B}.json\n")
                else:
                    self.output_text.insert(tk.END, f"[{time.strftime('%H:%M:%S',time.localtime(time.time()))}][设置][ERROR]:无法找到{语言A}语言文件\n")
            if 导入模式:
                start_time1 = time.time()
                导入至缓存(PathA, PathB)
                self.output_text.insert(tk.END, f"[{time.strftime('%H:%M:%S',time.localtime(time.time()))}][设置][INFO]:单个文件导入完成耗时{time.time() - start_time1}秒\n")
            else:
                self.output_text.insert(tk.END, f"[{time.strftime('%H:%M:%S',time.localtime(time.time()))}][设置][ERROR]:无法成功找到两个语言文件\n")
        if model == "导入":
            file_path = filedialog.askopenfilenames(
                filetypes=[("Zip/Jar Files", "*.zip *.jar"), ("All Files", "*.*")]
            )
            if file_path:
                if len(file_path) == 1:
                    self.清理缓存文件夹(1)
                    导入(file_path[0])
                    self.output_text.insert(tk.END, f"[{time.strftime('%H:%M:%S',time.localtime(time.time()))}][设置][INFO]:文件导入完成\n")
                elif len(file_path) > 1:
                    start_time = time.time()
                    self.清理缓存文件夹(1)
                    for f in file_path:
                        导入(f)
                    self.清理缓存文件夹(1)
                    self.output_text.insert(tk.END, f"[{time.strftime('%H:%M:%S',time.localtime(time.time()))}][设置][INFO]:所有文件导入完成，耗时{time.time() - start_time}秒\n")

    def def默认提示词(self, model, event=None):
        if model == "清除":
            with open('./system_prompt/default.txt', 'w', encoding='utf-8') as f:
                f.write("")
        elif model == "加载":
            with open("original-translated-value.json", "r", encoding='utf-8') as f:
                data = json.load(f)
            默认提示词 = [f"{item['original']}={item['translated']}" for item in data]
            with open('./system_prompt/default.txt', 'w', encoding='utf-8') as f:
                f.write("\n".join(默认提示词))

    def GUI配置文件处理(self, model, event=None):
        print(model)
        def 读取文件():
            with open('config.json', 'r', encoding='utf-8') as file:
                return json.load(file)
        def 保存文件(数据):
            with open('config.json', 'w', encoding='utf-8') as f:
                json.dump(数据, f, ensure_ascii=False, indent=4)
        def 配置列表():
            return [item['name'] for item in 文件["预设"]]
        if model == "加载配置" and self.配置文件_项.get():
            文件 = 读取文件()
            选定配置 = next((item for item in 文件["预设"] if item["name"] == self.配置文件_项.get()), None)
            api_config_id = ["llm_api_url", "llm_api_key", "llm_api_model", "llm_api_v1", "emb_api_url", "emb_api_key", "emb_api_model", "emb_api_v1"]
            api_config_id_list = []
            for config_id in api_config_id:
                api_config_id_list.append(next((item['value'] for item in 选定配置['api_config'] if item['id'] == config_id), None))
            self.apiurl内容.set(api_config_id_list[0])
            self.apikey内容.set(api_config_id_list[1])
            self.模型名称内容.set(api_config_id_list[2])
            self.v1模式选项.set(api_config_id_list[3])
            self.嵌入apiurl内容.set(api_config_id_list[4])
            self.嵌入apikey内容.set(api_config_id_list[5])
            self.嵌入模型名称内容.set(api_config_id_list[6])
            self.嵌入v1模式选项.set(api_config_id_list[7])

            config_dict = {config["apiurl"]:config for config in self.config_file["api_config"]}
            if self.apiurl内容.get() in config_dict:
                api_config里面的apiurl内容的信息 = config_dict[self.apiurl内容.get()]
            self.API名称.config(text=f"{api_config里面的apiurl内容的信息['name']}")
            嵌入config_dict = {config["apiurl"]:config for config in self.config_file["api_config_embedding"]}
            if self.嵌入apiurl内容.get() in 嵌入config_dict:
                嵌入api_config里面的apiurl内容的信息 = 嵌入config_dict[self.嵌入apiurl内容.get()]
            self.嵌入API名称.config(text=f"{嵌入api_config里面的apiurl内容的信息['name']}")

            self.use_context.set(next((item['on'] for item in 选定配置['translator_config'] if item['id'] == "context"), None))
            self.enable_key_value.set(next((item['on'] for item in 选定配置['translator_config'] if item['id'] == "key_value_input"), None))
            self.enable_think.set(next((item['on'] for item in 选定配置['translator_config'] if item['id'] == "reasoning_mode"), None))
            self.thinkingLevel.set(next((item['value'] for item in 选定配置['translator_config'] if item['id'] == "reasoning_mode"), None))
            self.enable_quick_search_btn.set(next((item['on'] for item in 选定配置['translator_config'] if item['id'] == "quick_prompt"), None))
            self.retrieve_count.set(next((item['value'] for item in 选定配置['translator_config'] if item['id'] == "quick_prompt"), None))
            self.快速提示词模式下拉框.set(next((item['mode'] for item in 选定配置['translator_config'] if item['id'] == "quick_prompt"), None))
            self.检索增强生成模式.set(next((item['mode_rag'] for item in 选定配置['translator_config'] if item['id'] == "quick_prompt"), None))
            self.启用自定义模型温度系数.set(next((item['on'] for item in 选定配置['translator_config'] if item['id'] == "custom_parameters"), None))
            self.温度系数.set(next((item['temperature'] for item in 选定配置['translator_config'] if item['id'] == "custom_parameters"), None))
            self.核心采样.set(next((item['top_p'] for item in 选定配置['translator_config'] if item['id'] == "custom_parameters"), None))
            self.启用推测解码.set(next((item['on'] for item in 选定配置['translator_config'] if item['id'] == "speculative_encoding"), None))
            self.推测解码下拉框.set(next((item['model'] for item in 选定配置['translator_config'] if item['id'] == "speculative_encoding"), None))

        elif model == "刷新配置":
            文件 = 读取文件()
            配置列表 = 配置列表()
            self.配置文件_项['values'] = 配置列表
            if 配置列表:
                self.配置文件_项.set(配置列表[0])
            else:
                self.配置文件_项.set("")

        elif model == "保存配置" and self.配置文件_项.get():
            文件 = 读取文件()
            当前预设名 = self.配置文件_项.get().strip()
            目标预设 = None
            for 预设 in 文件["预设"]:
                if 预设["name"] == 当前预设名:
                    目标预设 = 预设
                    break
            新配置 = {
                "name": 当前预设名,
                "api_config": [
                    {"id": "llm_api_url",   "value": self.apiurl内容.get()},
                    {"id": "llm_api_key",   "value": self.apikey内容.get()},
                    {"id": "llm_api_model", "value": self.模型名称内容.get()},
                    {"id": "llm_api_v1",    "value": self.v1模式选项.get()},
                    {"id": "emb_api_url",   "value": self.嵌入apiurl内容.get()},
                    {"id": "emb_api_key",   "value": self.嵌入apikey内容.get()},
                    {"id": "emb_api_model", "value": self.嵌入模型名称内容.get()},
                    {"id": "emb_api_v1",    "value": self.嵌入v1模式选项.get()},
                ],
                "translator_config": [
                    {"id": "context","on": bool(self.use_context.get())},
                    {"id": "key_value_input","on": bool(self.enable_key_value.get())},
                    {"id": "reasoning_mode","on": bool(self.enable_think.get()),"value": int(self.thinkingLevel.get())},
                    {"id": "quick_prompt","on": bool(self.enable_quick_search_btn.get()),"value": int(self.retrieve_count.get()),"mode": self.快速提示词模式下拉框.get(),"mode_rag": self.检索增强生成模式.get()},
                    {"id": "custom_parameters","on": bool(self.启用自定义模型温度系数.get()),"temperature": float(self.温度系数.get()),"top_p": float(self.核心采样.get())},
                    {"id": "speculative_encoding","on": bool(self.启用推测解码.get()),"model": self.推测解码下拉框.get()}
                ]
            }

            if not 目标预设:
                文件["预设"].append(新配置)
            else:
                index = 文件["预设"].index(目标预设)
                文件["预设"][index] = 新配置

            保存文件(文件)
            self.配置文件_项['values'] = 配置列表()
        
        elif model == "删除配置" and self.配置文件_项.get():
            当前预设名 = self.配置文件_项.get().strip()
            文件 = 读取文件()
            文件["预设"] = [p for p in 文件["预设"] if p["name"] != 当前预设名]
            保存文件(文件)
            self.GUI配置文件处理("刷新配置")

    def def清除缓存(self):
        with open("original-translated-value.json", 'w', encoding='utf-8') as f:
            json.dump([], f, ensure_ascii=False, indent=4)

    def def导出Jsonl(self, 格式, event=None):
        now = time.localtime()
        系统提示词 = re.sub(r'\s', '', self.系统提示词)
        file_path = filedialog.asksaveasfilename(
            initialfile=f"{now.tm_year}年{now.tm_yday:03d}日{now.tm_hour:02d}时{now.tm_min:02d}分{now.tm_sec:02d}秒_{格式}_.jsonl",
            filetypes=[(格式, "*.jsonl")],
            defaultextension=".jsonl"
        )
        if file_path:
            with open("original-translated-value.json", 'r', encoding='utf-8') as f:
                data = json.load(f)
            data_list = []
            for i in range(len(data)):
                if self.导出包含键的值.get():
                    系统提示词 += f"键值输入{data[i]["key"]}"
                original = data[i]["original"]
                translated = data[i]["translated"]
                if 格式 == "ChatML数据集":
                    data_list.append({"messages": [{"role": "system", "content": 系统提示词}, {"role": "user", "content": original}, {"role": "assistant", "content": translated}]})
                elif 格式 == "Alpaca数据集":
                    data_list.append({"instruction": "翻译为 中文", "input": original, "output": translated, "system": 系统提示词})
            with open(file_path, 'w', encoding='utf-8') as f:
                for item in data_list:
                    f.write(json.dumps(item, ensure_ascii=False, separators=(',', ':')) + '\n')

    def 关闭窗口(self):
        self.stop_flag = True
        self.Stoptranslate = True
        self.stop = False
        self.root.destroy()
        sys.exit(0)
    # 从配置文件选择API地址
    def api地址列表处理(self):
        api地址列表 = [config["apiurl"] for config in self.config_file["api_config"]]
        嵌入api地址列表 = [config["apiurl"] for config in self.config_file["api_config_embedding"]]
        self.api_url_entry['values'] = api地址列表
        self.嵌入api_url_entry['values'] = 嵌入api地址列表
        if api地址列表:
            self.apiurl内容.set(api地址列表[0])
        else:
            self.apiurl内容.set("")
        if 嵌入api地址列表:
            self.嵌入apiurl内容.set(嵌入api地址列表[0])
        else:
            self.嵌入apiurl内容.set("")
        
    # 刷新列表
    def 刷新列表(self, 嵌入=False, event=None):
        config_dict = {config["apiurl"]:config for config in self.config_file["api_config"]}
        嵌入config_dict = {config["apiurl"]:config for config in self.config_file["api_config_embedding"]}
        if self.apiurl内容.get() in config_dict:
            api_config里面的apiurl内容的信息 = config_dict[self.apiurl内容.get()]
        if self.嵌入apiurl内容.get() in 嵌入config_dict:
            嵌入api_config里面的apiurl内容的信息 = 嵌入config_dict[self.嵌入apiurl内容.get()]
        self.api_config里面的apiurl内容的信息 = api_config里面的apiurl内容的信息
        base_url = self.api_url_entry.get().rstrip('/')
        base_url = self.extract_base_url(full_url=base_url)
        嵌入base_url = self.嵌入api_url_entry.get().rstrip('/')
        嵌入base_url = self.extract_base_url(full_url=嵌入base_url)
        self.base_url = base_url
        if not 嵌入:
            if api_config里面的apiurl内容的信息['model_search']:
                try:
                    if not api_config里面的apiurl内容的信息['name'] == "LMStudio":
                        v1模型列表地址 = f"{base_url}/v1/models"
                        response = requests.get(v1模型列表地址, timeout=0.1)
                        response.raise_for_status()
                        models = response.json()["data"]
                        model_names = [model["id"] for model in models]
                        self.model_combobox['values'] = model_names
                        if model_names:
                            self.模型名称内容.set(model_names[0])
                    else:
                        v1模型列表地址 = f"{base_url}/api/v0/models"
                        response = requests.get(v1模型列表地址, timeout=0.1)
                        response.raise_for_status()
                        models = response.json()["data"]
                        model_names = [model["id"] for model in models if model.get("type") in ["llm", "vlm"]]
                        self.model_combobox['values'] = model_names
                        if model_names:
                            self.模型名称内容.set(model_names[0])

                    self.api_key_entry['values'] = []
                    self.apikey内容.set('')
                    self.v1模式选项.set(api_config里面的apiurl内容的信息['v1_mode'])
                    self.API名称.config(text=f"{api_config里面的apiurl内容的信息['name']}")
                except Exception as e:
                    self.模型名称内容.set('')
            else:
                self.model_combobox['values'] = api_config里面的apiurl内容的信息['model_list']
                if api_config里面的apiurl内容的信息['model_list']:
                    self.模型名称内容.set(api_config里面的apiurl内容的信息['model_list'][0])
                else:
                    self.模型名称内容.set('')
                self.v1模式选项.set(api_config里面的apiurl内容的信息['v1_mode'])
                key列表 = [item["key"] for item in self.config_file["api_key"] if item["name"] == api_config里面的apiurl内容的信息['name']]
                self.api_key_entry['values'] = key列表
                self.API名称.config(text=f"{api_config里面的apiurl内容的信息['name']}")
                if key列表:
                    self.apikey内容.set(key列表[0])
                else:
                    self.apikey内容.set('')
            self.刷新推测解码模型(base_url, api_config里面的apiurl内容的信息)
        else:
            if 嵌入api_config里面的apiurl内容的信息['model_search']:
                try:
                    if not 嵌入api_config里面的apiurl内容的信息['name'] == "LMStudio":
                        v1模型列表地址 = f"{嵌入base_url}/v1/models"
                        response = requests.get(v1模型列表地址, timeout=0.1)
                        response.raise_for_status()
                        models = response.json()["data"]
                        model_names = [model["id"] for model in models]
                        self.嵌入模型名称内容pack['values'] = model_names
                        self.全局model_names = model_names  # 确保这里设置了全局model_names
                        if model_names:
                            self.嵌入模型名称内容.set(model_names[0])
                    else:
                        v1模型列表地址 = f"{嵌入base_url}/api/v0/models"
                        response = requests.get(v1模型列表地址, timeout=0.1)
                        response.raise_for_status()
                        models = response.json()["data"]
                        model_names = [model["id"] for model in models if model.get("type") in ["embeddings"]]
                        self.嵌入模型名称内容pack['values'] = model_names
                        self.全局model_names = model_names  # 确保这里设置了全局model_names
                        if model_names:
                            self.嵌入模型名称内容.set(model_names[0])

                    self.嵌入api_key_entry['values'] = []
                    self.嵌入apikey内容.set('')
                    self.嵌入v1模式选项.set(嵌入api_config里面的apiurl内容的信息['v1_mode'])
                    self.嵌入API名称.config(text=f"{嵌入api_config里面的apiurl内容的信息['name']}")
                    self.函数多线程启动(self.刷新检索增强生成, (None,))
                except Exception as e:
                    self.嵌入模型名称内容.set('')
                    print(e)
            else:
                self.嵌入模型名称内容pack['values'] = 嵌入api_config里面的apiurl内容的信息['model_list']
                if 嵌入api_config里面的apiurl内容的信息['model_list']:
                    self.嵌入模型名称内容.set(嵌入api_config里面的apiurl内容的信息['model_list'][0])
                    self.全局model_names = 嵌入api_config里面的apiurl内容的信息['model_list']
                else:
                    self.嵌入模型名称内容.set('')
                self.嵌入v1模式选项.set(嵌入api_config里面的apiurl内容的信息['v1_mode'])
                key列表 = [item["key"] for item in self.config_file["api_key_embedding"] if item["name"] == 嵌入api_config里面的apiurl内容的信息['name']]
                self.嵌入api_key_entry['values'] = key列表
                self.嵌入API名称.config(text=f"{嵌入api_config里面的apiurl内容的信息['name']}")
                if key列表:
                    self.嵌入apikey内容.set(key列表[0])
                else:
                    self.嵌入apikey内容.set('')
        

    def 刷新推测解码模型(self, url, name):
        try:
            if name['name'] == 'LMStudio':
                当前模型详细信息 = requests.get(f"{url}/api/v0/models/{self.模型名称内容.get()}")
                所有模型详细信息 = requests.get(f"{url}/api/v0/models")
                当前模型详细信息.raise_for_status()
                所有模型详细信息.raise_for_status()
                当前模型详细信息 = 当前模型详细信息.json()
                所有模型详细信息 = 所有模型详细信息.json()
                所有模型数据 = 所有模型详细信息["data"]
                可用模型列表 = []
                if "arch" in 当前模型详细信息:
                    当前模型架构 = 当前模型详细信息["arch"]
                    if re.search('qwen', 当前模型架构):
                        if re.search('moe', 当前模型架构):
                            当前模型架构 = 当前模型架构.removesuffix('moe')
                        elif re.search('vl', 当前模型架构):
                            当前模型架构 = 当前模型架构.removesuffix('vl')
                    for i in range(len(所有模型数据)):
                        if "arch" in 所有模型数据[i]:
                            if (所有模型数据[i]["arch"] == 当前模型架构 and 所有模型数据[i].get("type") in ["llm", "vlm"]):
                                可用模型列表.append(所有模型数据[i]["id"])
                self.推测解码下拉框pack['values'] = 可用模型列表
                if 可用模型列表:
                    self.推测解码下拉框.set(可用模型列表[0])
                    self.启用推测解码.set(True)
                else:
                    self.推测解码下拉框pack['values'] = []
                    self.推测解码下拉框.set("")
                    self.启用推测解码.set(False)
            else:
                self.推测解码下拉框pack['values'] = []
                self.推测解码下拉框.set("")
                self.启用推测解码.set(False)
        except Exception as e:
            # 其他异常处理
            self.推测解码下拉框pack['values'] = []
            self.推测解码下拉框.set("")
            self.启用推测解码.set(False)
        
    def system_prompt_combobox绑定处理(self):
        self.刷新系统提示词()
        self.刷新列表(True)
    def 函数多线程启动(self, def_, args=None):
        if args is None:
            args = ()
        elif not isinstance(args, (list, tuple)):
            args = (args,)
        
        thread = threading.Thread(target=def_, args=args)
        thread.daemon = True
        thread.start()
    # 检测有无配置文件
    def 检测有无配置文件(self):
        for i in range(2):
            if i == 0:
                if os.path.isfile("config.json"):
                    continue
                decoded_data = base64.b64decode(config)
                json_data = json.loads(decoded_data.decode('utf-8'))
                with open("config.json", 'w', encoding='utf-8') as f:
                    json.dump(json_data, f, ensure_ascii=False, indent=4)
            if i == 1:
                if os.path.isfile("original-translated-value.json"):
                    with open("original-translated-value.json", 'r', encoding='utf-8') as f:
                        content = f.read().strip()
                    if content:
                        continue
                    else:
                        with open("original-translated-value.json", 'w', encoding='utf-8') as f:
                            json.dump([], f, ensure_ascii=False, indent=4)
                else:
                    with open("original-translated-value.json", 'w', encoding='utf-8') as f:
                        json.dump([], f, ensure_ascii=False, indent=4)

    def format_bytes(self, bytes_value):
        units = ['B', 'kB', 'MB', 'GB', 'TB']
        size = float(bytes_value)
        unit_index = 0
        while size >= 1024.0 and unit_index < len(units) - 1:
            size /= 1024.0
            unit_index += 1
        if size.is_integer():
            return f"{int(size)} {units[unit_index]}"
        else:
            return f"{size:.2f} {units[unit_index]}"
    def 刷新检索增强生成(self, event=None):
        if self.快速提示词模式下拉框.get() == "检索增强生成":
            提示词名称 = Path(self.system_prompt_var.get()).stem
            检索增强生成列表 = []
            for file_path in Path("./system_prompt").glob(f"{提示词名称 + '——'}*.npy"):
                if file_path.is_file():
                    file_size = self.format_bytes(file_path.stat().st_size)
                    检索增强生成列表.append(f"{file_path.name}   {file_size}")
            self.检索增强生成pack['values'] = 检索增强生成列表
            if 检索增强生成列表:
                if 检索增强生成列表 and not self.检索增强生成.get():
                    self.检索增强生成.set(检索增强生成列表[0])
                name, data = self.检索增强生成.get().split("   ", 1)
                name, data = name.split("———", 1)
                data1, name = name.split("——", 1)
                
                if 检索增强生成列表 and not (提示词名称 == data1):
                    self.检索增强生成.set(检索增强生成列表[0])
                self.嵌入模型名称内容.set(name)
            else:
                self.检索增强生成.set("")
                # 添加保护，确保 self.全局model_names 存在且不为空
                if hasattr(self, '全局model_names') and self.全局model_names:
                    self.嵌入模型名称内容.set(self.全局model_names[0])
                # 如果全局model_names不存在或为空，尝试从嵌入模型列表中获取第一个
                elif self.嵌入模型名称内容pack['values']:
                    self.嵌入模型名称内容.set(self.嵌入模型名称内容pack['values'][0])
        else:
            self.检索增强生成pack['values'] = []
            self.检索增强生成.set("")


    def 刷新系统提示词(self, event=None):
        os.makedirs(r'.\system_prompt', exist_ok=True)
        with open(f'./system_prompt/default.txt', 'w+', encoding='utf-8') as f:
            f.close()
        self.system_prompt_combobox['values'] = [
            f for f in os.listdir(r'.\system_prompt')
            if os.path.isfile(os.path.join(r'.\system_prompt', f)) and f.endswith('.txt')
        ]
        if self.system_prompt_var and not self.system_prompt_var.get():
            self.system_prompt_combobox.current(0)
        self.函数多线程启动(self.刷新检索增强生成())

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

    def 日志滚动(self):
        while True:
            if self.自动滚动至底部的值.get():
                self.output_text.see(tk.END)
                time.sleep(0.25)
    # 剩余时长处理
    def EstimatedTimeRequired(self, arr):
        if self.enable_quick_search_btn.get():
            if self.快速提示词模式下拉框.get() == "系统提示词检索":
                basicNumericalValue = 3
            elif self.快速提示词模式下拉框.get() == "检索增强生成":
                basicNumericalValue = 2
        else:
            basicNumericalValue = 1
        try:
            返回内容 = round(sum(arr) / len(arr) * basicNumericalValue * self.lang_lines / 60, 2)
        except Exception as e:
            返回内容 = 0
        return 返回内容

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
        with open(f'./system_prompt/{self.system_prompt_var.get()}', 'r', encoding='utf-8') as file:
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
            self.每秒输出词元文本.config(text="")
            return True
        else:
            return False
        
    def 清理缓存文件夹(self, model=0):
        if model == 0:
            self.output_text.insert(tk.END, f"[{time.strftime('%H:%M:%S', time.localtime())}][INFO]:清理缓存文件夹中...\n")
            start_time = time.time()
            for item in os.listdir(f"./cache"):
                item_path = os.path.join("./cache", item)
                if os.path.isfile(item_path):
                    os.remove(item_path)
                elif os.path.isdir(item_path):
                    shutil.rmtree(item_path)
            self.output_text.insert(tk.END, f"[{time.strftime('%H:%M:%S', time.localtime())}][INFO]:清理耗时{time.time() - start_time}秒\n")
        elif model == 1:
            self.output_text.insert(tk.END, f"[{time.strftime('%H:%M:%S', time.localtime())}][设置][INFO]:清理缓存文件夹中...\n")
            start_time = time.time()
            for item in os.listdir(f"./cache/cache"):
                item_path = os.path.join("./cache/cache", item)
                if os.path.isfile(item_path):
                    os.remove(item_path)
                elif os.path.isdir(item_path):
                    shutil.rmtree(item_path)
            self.output_text.insert(tk.END, f"[{time.strftime('%H:%M:%S', time.localtime())}][设置][INFO]:清理耗时{time.time() - start_time}秒\n")

        
    # 比较两个语言文件
    def 比较两个语言文件(self, en_us_content: str, zh_cn_content: str):
        def parse_to_dict(text: str) -> dict:
            result = {}
            for line in text.splitlines():
                line = line.strip()
                if '=' in line and not line.startswith('#'):
                    key, value = line.split('=', 1)
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
    
    def get_embedding(self, url, texts):
        is_single_input = isinstance(texts, str)
        if is_single_input:
            input_data = texts
        else:
            input_data = texts
        data = {
            "input": input_data,
            "model": self.嵌入模型名称内容.get()
        }
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.嵌入apikey内容}"
        }
        try:
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            result = response.json()
            embeddings_data = result.get("data", [])
            if is_single_input:
                if embeddings_data and "embedding" in embeddings_data[0]:
                    return embeddings_data[0]["embedding"]
                else:
                    print(f"[ERROR] API 返回格式不正确或无数据 (单个输入)")
                    return None
            else:
                vectors = []
                for item in embeddings_data:
                     if "embedding" in item:
                         vectors.append(item["embedding"])
                     else:
                         vectors.append(None)
                         print(f"[WARNING] API 返回中缺少某个文本的 embedding")
                return vectors
        except requests.exceptions.RequestException as e:
            error_msg = f"[ERROR] 请求嵌入向量失败: {e}"
            print(error_msg)
            self.output_text.insert(tk.END, f"[{time.strftime('%H:%M:%S')}]{error_msg}\n")
            
        except KeyError as e:
            error_msg = f"[ERROR] 解析 API 响应失败 (缺少键 {e}): {result}"
            print(error_msg)
            self.output_text.insert(tk.END, f"[{time.strftime('%H:%M:%S')}]{error_msg}\n")
            
        except Exception as e:
            error_msg = f"[ERROR] 生成嵌入向量时发生未知错误: {e}"
            print(error_msg)
            self.output_text.insert(tk.END, f"[{time.strftime('%H:%M:%S')}]{error_msg}\n")
            
        if is_single_input:
            return None
        else:
            return [None] * len(input_data if isinstance(input_data, list) else [input_data])

    def get_embeddings(self, url, text_list, max_workers=4):
        n_texts = len(text_list)
        vectors = [None] * n_texts
        ui_queue = queue.Queue()
        start_time = time.time()
        self.总计Token数 = 0
        self.TimeConsuming = []

        def worker(index, text):
            if hasattr(text, 'page_content'):
                text_content = text.page_content
            else:
                text_content = text
            vector = self.get_embedding(url, text_content)
            ui_queue.put(('update_status', index, n_texts))
            if vector is not None:
                ui_queue.put(('vector', index, vector))
            else:
                ui_queue.put(('error', index))
            return index, vector

        def check_ui_queue():
            try:
                while True:
                    message = ui_queue.get_nowait()
                    msg_type = message[0]
                    if msg_type == 'update_status':
                        idx, total = message[1], message[2]
                        elapsed_time = time.time() - start_time
                        speed = (idx + 1) / elapsed_time if elapsed_time > 0 else 0
                        if speed > 0:
                            estimated_total_time = total / speed
                            remaining_time = estimated_total_time - elapsed_time
                            self.EstimatedTimeRequired1.config(text=f"预计耗时\n {round(estimated_total_time, 2)}秒")
                            self.EstimatedTimeRequired2.config(text=f"剩余时长\n {round(remaining_time, 2)}秒")
                        self.每秒输出词元文本.config(text=f"Emb/S\n {round(speed, 4)}")
                        self.status_label.config(text=f"向量嵌入\n{idx+1}/{total}")
                    elif msg_type == 'vector':
                        pass
                    elif msg_type == 'error':
                        idx = message[1]
                        print(f"跳过第 {idx+1} 个文本")
            except queue.Empty:
                pass
            self.root.after(50, check_ui_queue) 

        def process_results(futures_list):
            success_count = 0
            for future in as_completed(futures_list):
                idx, vector = future.result()
                if vector is not None:
                    vectors[idx] = vector
                    success_count += 1
                else:
                    print(f"跳过第 {idx+1} 个文本")
            return success_count
        self.root.after(100, check_ui_queue)
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [
                executor.submit(worker, i, text)
                for i, text in enumerate(text_list)
            ]
            process_results(futures)
        total_time = time.time() - start_time
        self.output_text.insert(tk.END, f"[{time.strftime('%H:%M:%S')}][INFO]:向量嵌入耗时{round(total_time, 2)}秒\n")
        
        return np.array(vectors)

    def retrieve_similar_texts(self, url, index, chunks, query, k=3):
        query_vector = self.get_embedding(url, query)
        if query_vector is None:
            return []
        query_vector = np.array([query_vector]).astype("float32")
        distances, indices = index.search(query_vector, k)
        results = []
        for idx in indices[0]:
            if idx != -1:
                chunk = chunks[idx]
                text = chunk.page_content if hasattr(chunk, 'page_content') else chunk
                results.append(text)
        return results
    # 翻译主函数
    def translate_text(self, text, 键值输入):
        def 生成向量嵌入():
            with open(f"./system_prompt/{self.system_prompt_var.get()}", "r", encoding="utf-8") as f:
                if self.检索增强生成模式.get() == "EM-2P":
                    documents = [line.split("=", 1)[0].strip() for line in f.readlines() if line.strip() and "=" in line.strip()]
                elif self.检索增强生成模式.get() == "EM-1P":
                    documents = [line.strip() for line in f.readlines() if line.strip()]
                text_splitter = RecursiveCharacterTextSplitter(
                    chunk_size=200,
                    chunk_overlap=50,
                    length_function=len,
                )
                self.chunks = text_splitter.create_documents(documents)
                prompttime = time.time()
                self.vectors = self.get_embeddings(嵌入url, self.chunks, self.向量嵌入生成并行数.get()) # 第三个是线程数
                self.output_text.insert(tk.END, f"[{time.strftime('%H:%M:%S',time.localtime(time.time()))}][INFO]:向量嵌入处理耗时：{time.time() - prompttime}秒\n")
                嵌入模型名称内容 = self.嵌入模型名称内容.get()
                self.output_text.insert(tk.END, f"[{time.strftime('%H:%M:%S',time.localtime(time.time()))}][INFO]:正在保存向量嵌入\n")
                prompttime = time.time()
                if not Path(f"./system_prompt/{提示词文件名称}——{嵌入模型名称内容}———{self.检索增强生成模式.get()}.npy").is_file():
                    np.save(f"./system_prompt/{提示词文件名称}——{嵌入模型名称内容}———{self.检索增强生成模式.get()}.npy", self.vectors)
                if not Path(f"./system_prompt/{提示词文件名称}———{self.检索增强生成模式.get()}.pkl").is_file():
                    with open(f"./system_prompt/{提示词文件名称}———{self.检索增强生成模式.get()}.pkl", "wb") as f:
                        pickle.dump(self.chunks, f)
                self.output_text.insert(tk.END, f"[{time.strftime('%H:%M:%S',time.localtime(time.time()))}][INFO]:向量嵌入保存耗时：{time.time() - prompttime}秒\n")
                self.检索增强生成.set(f"{提示词文件名称}——{嵌入模型名称内容}———{self.检索增强生成模式.get()}.npy   {self.format_bytes(Path(f'./system_prompt/{提示词文件名称}——{嵌入模型名称内容}———{self.检索增强生成模式.get()}.npy').stat().st_size)}")
                self.刷新检索增强生成()
  
        while True:
            try:
                with open('original-translated-value.json', 'r', encoding='utf-8') as f:
                    缓存的键值 = json.load(f)

                base_url = self.api_url_entry.get().rstrip('/')
                嵌入url = self.嵌入api_url_entry.get().rstrip('/')

                if not re.search(r'/chat/completions$', base_url):
                    if self.v1模式选项.get():
                        
                        base_url = f"{base_url}/v1/chat/completions"
                    else:
                        base_url = f"{base_url}/chat/completions"
                if not re.search(r'/embeddings$', 嵌入url):
                    if self.嵌入v1模式选项.get():
                        嵌入url = f"{嵌入url}/v1/embeddings"
                    else:
                        嵌入url = f"{嵌入url}/embeddings"

                start_time = time.time()
                if self.替换翻译过的键值的值.get():
                    for item in 缓存的键值:
                        if item["original"] == text:
                            self.context_history.append({
                                "original": text,
                                "translated": item["translated"]
                            })
                            self.output_text.insert(tk.END, f"[{time.strftime('%H:%M:%S',time.localtime(time.time()))}][INFO]:词条被跳过\n")                            
                            return item["translated"]


                with open(f'./system_prompt/{self.system_prompt_var.get()}', "r", encoding="utf-8") as file:

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

                    system_content += self.系统提示词
                    system_content = re.sub(r'\s', '', system_content)

                    if not self.enable_quick_search_btn.get():
                        system_content += file.read()
                    else:
                        if self.快速提示词模式下拉框.get() == "系统提示词检索":
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
                        elif self.快速提示词模式下拉框.get() == "检索增强生成":
                            提示词文件名称 = Path(self.system_prompt_var.get()).stem
                            if not hasattr(self, 'vectors') or not hasattr(self, 'chunks') or self.vectors is None or self.chunks is None:
                                if self.检索增强生成.get():
                                    npy文件, aaa = self.检索增强生成.get().split("   ", 1)
                                    模型, RAG模式npy = npy文件.split("———", 1)
                                    文件RAG模式 = re.sub(r'\.npy$', '', RAG模式npy)
                                    模型 = 模型.join(".npy")
                                    aaa, 模型npy = npy文件.split("——", 1)
                                    npy模型名称, aaa = 模型npy.split(".np", 1)
                                    if os.path.isfile(f"./system_prompt/{提示词文件名称 + '——' + 模型npy}") and self.嵌入模型名称内容.get() == npy模型名称:        
                                        self.vectors = np.load(f"./system_prompt/{提示词文件名称 + '——' + 模型npy}")
                                        with open(f"./system_prompt/{提示词文件名称}———{self.检索增强生成模式.get()}.pkl", "rb") as f:
                                            self.chunks = pickle.load(f)
                                    else:
                                        if 文件RAG模式 == self.检索增强生成模式.get():
                                            if os.path.isfile(f"./system_prompt/{提示词文件名称 + '——' + self.嵌入模型名称内容.get() + '———' + self.检索增强生成模式.get()}.npy"):
                                                文件大小 = self.format_bytes(Path(f'./system_prompt/{提示词文件名称 + "——" + self.嵌入模型名称内容.get() + "———" + self.检索增强生成模式.get()}.npy').stat().st_size)
                                                self.检索增强生成.set(f"{提示词文件名称 + '——' + self.嵌入模型名称内容.get() + '———' + self.检索增强生成模式.get()}.npy   {文件大小}")
                                                self.vectors = np.load(f"./system_prompt/{提示词文件名称 + '——' + self.嵌入模型名称内容.get() + '———' + self.检索增强生成模式.get()}.npy")
                                                with open(f"./system_prompt/{提示词文件名称}———{self.检索增强生成模式.get()}.pkl", "rb") as f:
                                                    self.chunks = pickle.load(f)
                                            else:
                                                self.output_text.insert(tk.END, f"[{time.strftime('%H:%M:%S')}][INFO]:.npy文件模型与所选模型不相同\n")
                                                self.output_text.insert(tk.END, f"[{time.strftime('%H:%M:%S')}][INFO]:正在重新生成向量嵌入...\n")
                                                
                                                生成向量嵌入()
                                        else:
                                            self.output_text.insert(tk.END, f"[{time.strftime('%H:%M:%S')}][INFO]:.npy文件检索增强生成模式与所选检索增强生成模式不相同\n")
                                            self.output_text.insert(tk.END, f"[{time.strftime('%H:%M:%S')}][INFO]:正在重新生成向量嵌入...\n")
                                            
                                            生成向量嵌入()
                                else:
                                    self.output_text.insert(tk.END, f"[{time.strftime('%H:%M:%S')}][INFO]:未检测到.npy文件\n")
                                    self.output_text.insert(tk.END, f"[{time.strftime('%H:%M:%S')}][INFO]:正在生成向量嵌入...\n")
                                    
                                    生成向量嵌入()
                            prompttime = time.time()
                            dimension = self.vectors.shape[1]
                            index = faiss.IndexFlatL2(dimension)
                            index.add(self.vectors)
                            relevant_texts = self.retrieve_similar_texts(嵌入url, index, self.chunks, text, k=self.retrieve_count.get())
                            print(relevant_texts)
                            results = []
                            if self.检索增强生成模式.get() == "EM-2P":
                                key_values = defaultdict(list)
                                for i in relevant_texts:
                                    with open(f"./system_prompt/{提示词文件名称}.txt", 'r', encoding='utf-8') as f:
                                        for line_num, line in enumerate(f, 1):
                                            line = line.strip()
                                            if line and '=' in line:
                                                key, value = line.split('=', 1)
                                                key = key.strip()
                                                if key == i:
                                                    key_values[key].append(value)
                                for key, values in key_values.items():
                                    unique_values = list(dict.fromkeys(values))
                                    if len(unique_values) == 1:
                                        results.append(f"({key}={unique_values[0]}),")
                                    else:
                                        results.append(f"({key}={'='.join(unique_values)}),")
                            elif self.检索增强生成模式.get() == "EM-1P":
                                results = relevant_texts
                            self.output_text.insert(tk.END, f"[{time.strftime('%H:%M:%S',time.localtime(time.time()))}][INFO]:知识库检索耗时：{time.time() - prompttime}秒\n")
                            self.TimeConsuming.append(time.time() - prompttime)
                            system_content += "参考输入按照优先级排序[" + "".join(str(text) for text in results) + "]"
                                    


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

                request_data = {
                        "model": self.模型名称内容.get(),
                        "messages": messages,
                    }
                
                if self.启用推测解码.get():
                    request_data["draft_model"] = self.推测解码下拉框.get()
                
                # 模型温度系数处理
                if self.启用自定义模型温度系数.get():
                    request_data["temperature"] = self.温度系数.get()
                    request_data["top_p"] = self.核心采样.get()

                response = requests.post(
                    base_url,
                    headers=headers,
                    json=request_data
                )

                self.output_text.insert(tk.END, f"[{time.strftime('%H:%M:%S',time.localtime(time.time()))}][INFO]:本词条翻译耗时：{time.time() - start_time}秒\n")
                self.TimeConsuming.append(time.time() - start_time)

                response.raise_for_status()
                translated_text = response.json()["choices"][0]["message"]["content"]
                translated_text = re.sub(r'\n', '', translated_text)

                self.总计耗时 += time.time() - start_time
                self.总计Token数 += response.json()["usage"]["completion_tokens"]
                self.当前Token数 = response.json()["usage"]["total_tokens"]

                self.output_text.insert(tk.END, f"[{time.strftime('%H:%M:%S',time.localtime(time.time()))}][INFO]:当前Token长度：{self.当前Token数}Token\n")
                self.每秒输出词元文本.config(text=f"Token/S\n {round((self.总计Token数 / sum(self.TimeConsuming)), 4)}")

                self.context_history.append({
                    "original": text,
                    "translated": translated_text
                })

                if self.记录翻译过的键值的值.get():
                    已有缓存的值 = False
                    for item in 缓存的键值:
                        if item["original"] == text:
                            已有缓存的值 = True
                            break
                    if not 已有缓存的值:
                        缓存的键值.append({"key": 键值输入, "original": text, "translated": translated_text})
                        with open("original-translated-value.json", 'w', encoding='utf-8') as f:
                            json.dump(缓存的键值, f, ensure_ascii=False, indent=4)

                return translated_text

            except Exception as e:
                self.TimeConsuming = self.TimeConsuming[:-3]
                self.output_text.insert(tk.END, f"[{time.strftime('%H:%M:%S',time.localtime(time.time()))}][ERROR]:{e}\n")
                self.output_text.insert(tk.END, f"[{time.strftime('%H:%M:%S',time.localtime(time.time()))}][INFO]:重试中...\n")
                if self.enable_quick_search_btn.get():
                    if self.快速提示词模式下拉框.get() == "系统提示词检索":
                        basicNumericalValue = 3
                    elif self.快速提示词模式下拉框.get() == "检索增强生成":
                        basicNumericalValue = 2
                else:
                    basicNumericalValue = 1
                self.TimeConsuming = self.TimeConsuming[:-basicNumericalValue]
                self.TimeConsuming.append(0)
                if not self.Stoptranslate:
                    time.sleep(3)
                    self.start_time -= 3
                    while self.stop:
                        time.sleep(0.02)
                        self.start_time -= 0.02
                else:
                    return text
            
    def parse_lang_content(self, content):
        """智能解析 .lang 文件内容，支持多行值"""
        entries = []
        current_key = None
        current_value_lines = []

        for line_num, line in enumerate(content.splitlines(), 1):
            if not line.strip() or line.startswith('#') or line.startswith('//'):
                continue

            if '=' in line:
                if current_key is not None:
                    full_value = '\n'.join(current_value_lines)
                    entries.append((current_key, full_value))
                    current_value_lines = []

                parts = line.split('=', 1)
                current_key = parts[0].strip()
                value_part = parts[1] if len(parts) > 1 else ""
                current_value_lines = [value_part]
            else:
                if current_key is not None:
                    current_value_lines.append(line)
                else:
                    print(f"[警告] 第{line_num}行: 没有键的值: {line}")

        if current_key is not None:
            full_value = '\n'.join(current_value_lines)
            entries.append((current_key, full_value))

        return entries

    # Lang翻译处理
    def translate_lang(self, file_path, 读取文件=1, 输出处理=1):
        self.status_label.config(text=f"正在处理")
        self.总计耗时 = 0
        self.总计Token数 = 0
        self.start_time = time.time()
        if 读取文件 == 1:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = [line.rstrip('\n') for line in f.readlines()]
        elif 读取文件 == 2:
            if isinstance(file_path, str):
                lines = file_path.splitlines()
            elif isinstance(file_path, list):
                lines = [line.rstrip('\n') for line in file_path]
            else:
                lines = []
        else:
            if isinstance(file_path, str):
                lines = file_path.splitlines()
            else:
                lines = []

        self.lang_lines = len(lines)
        total = 0
        for line in lines:
            stripped = line.strip()
            if not stripped or stripped.startswith('#') or stripped.startswith('//'):
                continue
            if '=' in line:
                key, value = line.split('=', 1)
                if value.strip():
                    total += 1

        self.status_label.config(text=f"翻译进度\n 0/{total}")
        current = 0
        self.stop_time = 0
        results = []

        # === 步骤3: 逐行处理 ===
        for line in lines:
            stripped_line = line.strip()
            if not stripped_line or stripped_line.startswith('#') or stripped_line.startswith('//'):
                results.append(line)
                continue
            if '=' in line:
                parts = line.split('=', 1)
                key = parts[0]
                value = parts[1] if len(parts) > 1 else ""
                if not value.strip():
                    results.append(line)
                    continue
                try:
                    translated = self.translate_text(value, key)
                    new_line = f"{key}={translated}"
                    results.append(new_line)
                    current += 1
                    self.status_label.config(text=f"正在翻译\n {current}/{total}")
                    self.output_text.insert(tk.END, f"[{time.strftime('%H:%M:%S')}][INFO]:{key}\n")
                    self.output_text.insert(tk.END, f"[{time.strftime('%H:%M:%S')}][INFO]:{value}={translated}\n")
                    if self.翻译暂停结束处理():
                        return False
                    预计耗时 = self.EstimatedTimeRequired(self.TimeConsuming)
                    if 预计耗时 > 0:
                        self.EstimatedTimeRequired1.config(text=f"预计耗时\n {预计耗时}分")
                        self.EstimatedTimeRequired2.config(text=f"剩余时长\n {round(预计耗时 - ((time.time() - self.start_time - self.stop_time) / 60), 2)}分")
                except Exception as e:
                    self.output_text.insert(tk.END, f"[{time.strftime('%H:%M:%S')}][ERROR]:翻译 {key} 时出错: {e}\n")
                    results.append(line)
            else:
                results.append(line)
        self.output_text.insert(tk.END, f"[{time.strftime('%H:%M:%S')}][INFO]:翻译总耗时：{time.time() - self.start_time}秒\n")
        self.output_text.insert(tk.END, f"[{time.strftime('%H:%M:%S')}][INFO]:总计输出Token：{self.总计Token数}Token\n")
        final_content = "\n".join(results)
        if 输出处理 == 1:
            with open(file_path, 'w', encoding='utf-8') as f:
                original_no_newlines = "\n".join(lines)
                processed = self.Lang模板文件处理(original_no_newlines, final_content)
                f.write(processed)
            self.stop_flag = False
            return True
        elif 输出处理 == 2:
            with open('./cache/zh_cn.lang', 'w+', encoding='utf-8') as f:
                f.write(final_content)
            return True
        else:
            return final_content

    # Json翻译处理
    def translate_json(self, file_path, 读取文件=True, 输出处理=1):
        self.status_label.config(text=f"正在处理")
        if 读取文件:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                f.close()
        else:
            data = file_path
        result_lines = []
        for key, value in data.items():
            result_lines.append(f"{key}={value}")
            result_enus = "\n".join(result_lines)
        print(result_enus)
        result = self.translate_lang(result_enus, 读取文件=3, 输出处理=3)
        if result:
            result = self.Lang模板文件处理(result_enus, result)
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
                    self.stop_flag = False
                return True
            elif 输出处理 == 2:
                with open(f'./cache/zh_cn.json', 'w+', encoding='utf-8') as f:
                    f.write(result_json_str)
                return True
            else:
                return result_json_str
        else:
            if 输出处理 == 1:
                self.stop_flag = False
            else:
                return False



    # Zip光影包处理
    def translate_zip(self, Zip文件, 新Zip文件=None):
        self.status_label.config(text=f"正在处理")
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
                zh_cn_lang = (self.translate_lang(未翻译的zh_cn缺少键值, 读取文件=2, 输出处理=3))
                if zh_cn_lang:
                    zh_cn = '\n' + zh_cn_lang
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
            Stop = self.translate_lang(file_path, 输出处理=2)
            if not Stop:
                self.清理缓存文件夹()
                return
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

    # Jar模组处理（谁写的，看不懂）
    def translate_jar(self, Jar文件, 新Jar文件=None):
        self.status_label.config(text=f"正在处理")
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
            if Path(f'./cache/{en_us文件名}/{file_path}/en_us.json').is_file():
                if os.path.isfile(f'./cache/{Jar文件名}/{file_path}/zh_cn.json'):
                    def 转换Lang(Json文件):
                        with open(Json文件, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                        return "\n".join(f"{key}={value}" for key, value in data.items())
                    未翻译的zh_cn缺少键值 = self.比较两个语言文件(转换Lang(f'./cache/{en_us文件名}/{file_path}/en_us.json'), 转换Lang(f'./cache/{Jar文件名}/{file_path}/zh_cn.json'))
                    if 未翻译的zh_cn缺少键值:
                        json转换的zh_cn_lang = 转换Lang(f'./cache/{Jar文件名}/{file_path}/zh_cn.json')
                        self.output_text.insert(tk.END, f"[{time.strftime('%H:%M:%S', time.localtime())}][INFO]:检测到有zh_cn.json启动部分翻译\n")
                        zh_cn_lang = (self.translate_lang(未翻译的zh_cn缺少键值, 读取文件=2, 输出处理=3))
                        if zh_cn_lang:
                            json转换的zh_cn_lang += '\n' + zh_cn_lang
                            json转换的zh_cn_lang = self.Lang模板文件处理(转换Lang(f'./cache/{en_us文件名}/{file_path}/en_us.json'), json转换的zh_cn_lang)
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
                            self.清理缓存文件夹()
                            return
                    else:
                        self.output_text.insert(tk.END, f"[{time.strftime('%H:%M:%S', time.localtime())}][WAENING]:没有需要翻译的项或键值相同\n")
                        self.清理缓存文件夹()
                        self.stop_flag = False
                        return
                else:
                    self.output_text.insert(tk.END, f"[{time.strftime('%H:%M:%S', time.localtime())}][INFO]:检测到无zh_cn.json启动全部翻译\n")
                    Stop = self.translate_json(f'./cache/{en_us文件名}/{file_path}/en_us.json', 输出处理=2)
                    if Stop:
                        shutil.copy('./cache/zh_cn.json', f'./cache/{en_us文件名}/{file_path}/zh_cn.json')
                    else:
                        self.清理缓存文件夹()
                        return
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
                        zh_cn_lang = (self.translate_lang(未翻译的zh_cn缺少键值, 读取文件=2, 输出处理=3))
                        if zh_cn_lang:
                            zh_cn += '\n' + zh_cn_lang
                            result_lang_str = self.Lang模板文件处理(en_us, zh_cn)
                            with open(f'./cache/zh_cn.lang', 'w+', encoding='utf-8') as f:
                                f.write(result_lang_str)
                            shutil.copy('./cache/zh_cn.lang', f'./cache/{en_us文件名}/{file_path}')
                        else:
                            self.清理缓存文件夹()
                            return
                    else:
                        self.output_text.insert(tk.END, f"[{time.strftime('%H:%M:%S', time.localtime())}][WAENING]:没有需要翻译的项或键值相同\n")
                        self.清理缓存文件夹()
                        self.stop_flag = False
                        return
                else:
                    self.output_text.insert(tk.END, f"[{time.strftime('%H:%M:%S', time.localtime())}][INFO]:检测到无zh_cn.lang启动全部翻译\n")
                    Stop = self.translate_lang(f'./cache/{en_us文件名}/{file_path}/en_us.lang', 输出处理=2)
                    if Stop:
                        shutil.copy('./cache/zh_cn.lang', f'./cache/{en_us文件名}/{file_path}')
                    else:
                        self.清理缓存文件夹()
                        return
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
                self.output_text.insert(tk.END, f"[{time.strftime('%H:%M:%S', time.localtime())}][ERROR]:无法替换{e}\n")
                self.output_text.insert(tk.END, f"[{time.strftime('%H:%M:%S', time.localtime())}][INFO]:重试中...\n")
                
                time.sleep(3)
        self.output_text.insert(tk.END, f"[{time.strftime('%H:%M:%S', time.localtime())}][INFO]:Jar文件已覆盖至{Jar文件}\n")
        if 新Jar文件布尔值:
            self.output_text.insert(tk.END, f"[{time.strftime('%H:%M:%S', time.localtime())}][WARNING]:新版本文件被复制至待处理文件路径，请检查是否有同一模组不同版本的模组文件\n")
        self.清理缓存文件夹()
        self.stop_flag = False
        
if __name__ == "__main__":
    root = tk.Tk()
    app = TranslatorApp(root)
    root.mainloop()