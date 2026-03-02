import multiprocessing as mp
import threading as mt
import hashlib
import zipfile
import random
import pickle
import time
import json
import ast
import os
import re

from functools import partial
from collections import defaultdict
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

import faiss
import numpy as np
from pyhocon import ConfigFactory, HOCONConverter

import requests
from tqdm import tqdm

class Config:
    LANGUAGE_INPUT = "en_us"
    LANGUAGE_OUTPUT = "zh_cn"
    
    LLM_API_URL = ""
    LLM_API_KEY = ""
    LLM_API_MODEL = ""
    LLM_TOP_K = 60
    LLM_TOP_P = 0.70
    LLM_TEMP = 0.00
    LLM_PROMPT_LOCATION = "system"
    LLM_CONTEXTS = True
    LLM_CONTEXTS_LENGTH = 65536
    LLM_MAX_WORKERS = 24
    LLM_MAX_BATCH = 3
    LLM_SYSTEM_PROMPT = f"""
        /no_thinking
        【任务内容】
        1.仅输出原文翻译内容，不得包含解释、参考、键、额外内容(如“以下是翻译：”或“翻译如下：”等)
        2.单个符号需要翻译(遇到&或§或%需要保留后面一个符号)
        3.注意不需要翻译上文,也不要额外解释
        4.输入为列表，输出必须严格符合Python标准列表格式，如['翻译1', '翻译2']
        5.返回的译文数量与输出格式必须一致
        6.翻译为{LANGUAGE_OUTPUT}语言
        7.翻译领域为Minecraft游戏
        8.输入遇到【以下是翻译任务提示，请不要输出】请不要输出这段内容与后面的内容
    """

    EMB_API_URL = ""
    EMB_API_KEY = ""
    EMB_API_MODEL = ""
    EMB_MAX_TOKENS = 512
    EMB_MAX_WORKERS = 24

    VEC_FILE_PATH = r"./Vectors"
    VEC_FILE_NAME = "Vectors"
    VEC_QUANTIZATION = "Q4_K_X" # string: Float32, Float16_S1M15, Q8_K_X, Q4_K_X
    VEC_QUANTIZATION_BLOCK_SIZE = 64 # int: 2的倍数 最小1 最大256 默认64

    PATH_CACHE = r"./CACHE"
    LOGS_FILE_PATH = r"./logs/"
    LOGS_FILE_NAME = "logs.log"

    INDEX_K = 3
    INDEX_MODE = "RefineFlat" # HNSWSQ RefineFlat
    INDEX_HNSW_M = 128
    INDEX_HNSW_CONSTRUCTION = 720
    INDEX_HNSW_SEARCH = 480
    INDEX_REFINEFLAT_K_FACTOR = 2.0
Path(Config.VEC_FILE_PATH).mkdir(parents=True, exist_ok=True)
Path(Config.PATH_CACHE).mkdir(parents=True, exist_ok=True)
Path(Config.LOGS_FILE_PATH).mkdir(parents=True, exist_ok=True)

def 写入日志(text: str, info_level: int = 0):
    with open(f"{Config.LOGS_FILE_PATH}/{Config.LOGS_FILE_NAME}", "a+", encoding="utf-8") as f:
        时间 = time.strftime("[%Y-%m-%d %H:%M:%S]", time.localtime())
        with open(f"{Config.LOGS_FILE_PATH}/{Config.LOGS_FILE_NAME}", "a+", encoding="utf-8") as f:
            if info_level == 0:
                f.write(f"{时间}[INFO]{text}\n")
            elif info_level == 1:
                f.write(f"{时间}[WARNING]{text}\n")
            elif info_level == 2:
                f.write(f"{时间}[ERROR]{text}\n")
            elif info_level == 3:
                f.write(f"{时间}[FATAL]{text}\n")
    
    
class Quantization:
    def F32编码Q8_K_X(输入数组): #Qwen3-Max编写
        for _ in tqdm(range(1), desc="量化向量"):
            块大小 = Config.VEC_QUANTIZATION_BLOCK_SIZE
            输入数组 = np.asarray(输入数组, dtype=np.float32)
            原始形状 = 输入数组.shape
            扁平化 = 输入数组.flatten()
            填充长度 = (-len(扁平化)) % 块大小
            填充后数组 = np.pad(扁平化, (0, 填充长度), mode='constant')
            块数量 = len(填充后数组) // 块大小
            块视图 = 填充后数组.reshape(块数量, 块大小)
            块最大绝对值 = np.abs(块视图).max(axis=1)
            缩放因子 = np.where(块最大绝对值 > 1e-8, 块最大绝对值 / 127.0, 1.0).astype(np.float32)
            缩放因子编码 = Quantization.F32编码F16_S1M15(缩放因子)
            量化块 = np.clip(np.round(块视图 / 缩放因子[:, None]), -127, 127).astype(np.int8)
            量化结果 = 量化块.flatten()[:len(扁平化)]
        return 量化结果.reshape(原始形状), 缩放因子编码
    def Q8_K_X解码F32(量化数据, 缩放因子编码): #Qwen3-Max编写
        for _ in tqdm(range(1), desc="反量化向量"):
            块大小 = Config.VEC_QUANTIZATION_BLOCK_SIZE
            量化数据 = np.asarray(量化数据, dtype=np.int8)
            原始形状 = 量化数据.shape
            扁平化量化 = 量化数据.flatten()
            填充长度 = (-len(扁平化量化)) % 块大小
            填充后量化 = np.pad(扁平化量化, (0, 填充长度), mode='constant')
            块数量 = len(填充后量化) // 块大小
            块视图 = 填充后量化.reshape(块数量, 块大小)
            缩放因子 = Quantization.F16_S1M15解码F32(缩放因子编码).astype(np.float32)
            反量化块 = 块视图.astype(np.float32) * 缩放因子[:, None]
            反量化结果 = 反量化块.flatten()[:len(扁平化量化)]
        return 反量化结果.reshape(原始形状)
    def F32编码Q4_K_X(输入数组): #Qwen3-Max编写
        for _ in tqdm(range(1), desc="量化向量"):
            块大小 = Config.VEC_QUANTIZATION_BLOCK_SIZE
            输入数组 = np.asarray(输入数组, dtype=np.float32)
            原始形状 = 输入数组.shape
            扁平化 = 输入数组.flatten()
            填充长度 = (-len(扁平化)) % 块大小
            填充后数组 = np.pad(扁平化, (0, 填充长度), mode='constant')
            块数量 = len(填充后数组) // 块大小
            打包长度 = (len(填充后数组) + 1) // 2
            打包数据 = np.zeros(打包长度, dtype=np.uint8)
            块视图 = 填充后数组.reshape(块数量, 块大小)
            块最大值 = np.abs(块视图).max(axis=1)
            缩放因子 = np.where(块最大值 > 1e-8, (2.0 * 块最大值) / 15.0, 2.0 / 15.0).astype(np.float32)
            缩放因子编码 = Quantization.F32编码F16_S1M15(缩放因子)
            缩放因子广播 = 缩放因子[:, None].astype(np.float32)
            块最大值广播 = 块最大值[:, None]
            量化值 = np.clip(
                np.round((块视图 + 块最大值广播) / 缩放因子广播),
                0, 15
            ).astype(np.uint8)
            高四位 = 量化值[:, 0::2] << 4
            低四位 = 量化值[:, 1::2]
            打包二维 = 高四位 | 低四位
            打包数据[:打包二维.size] = 打包二维.flatten()
            实际打包长度 = (len(扁平化) + 1) // 2
        return 打包数据[:实际打包长度], 缩放因子编码, 原始形状
    def Q4_K_X解码F32(打包数据, 缩放因子编码, 原始形状): #Qwen3-Max编写
        for _ in tqdm(range(1), desc="反量化向量"):
            块大小 = Config.VEC_QUANTIZATION_BLOCK_SIZE
            总元素数 = np.prod(原始形状)
            填充后元素数 = ((总元素数 + 块大小 - 1) // 块大小) * 块大小
            块数量 = 填充后元素数 // 块大小
            完整打包长度 = (填充后元素数 + 1) // 2
            完整打包 = np.zeros(完整打包长度, dtype=np.uint8)
            完整打包[:len(打包数据)] = 打包数据
            高四位 = (完整打包[:, None] >> 4) & 0xF
            低四位 = 完整打包[:, None] & 0xF
            解包数据 = np.concatenate([高四位, 低四位], axis=1).flatten()[:填充后元素数]
            解包块 = 解包数据.reshape(块数量, 块大小)
            缩放因子 = Quantization.F16_S1M15解码F32(缩放因子编码).astype(np.float32)
            缩放因子_广播 = 缩放因子[:, np.newaxis]
            块最大值_广播 = (缩放因子 * 7.5)[:, np.newaxis]
            反量化块 = 解包块.astype(np.float32) * 缩放因子_广播 - 块最大值_广播
            反量化扁平 = 反量化块.flatten()[:总元素数]
        return 反量化扁平.reshape(原始形状)
    def F32编码F16_S1M15(浮点数组): #Qwen3-Max编写
        for _ in tqdm(range(1), desc="量化向量"):
            浮点数组 = np.clip(浮点数组, -1.0, 1.0 - 2**-15)
            整型数值 = np.round(浮点数组 * 32768.0).astype(np.int16)
        return 整型数值.view(np.uint16)
    def F16_S1M15解码F32(编码数组): #Qwen3-Max编写
        for _ in tqdm(range(1), desc="反量化向量"):
            整型数值 = 编码数组.view(np.int16)
        return 整型数值.astype(np.float32) / 32768.0
    def 解码向量(向量文件):
        if Config.VEC_QUANTIZATION == "Q8_K_X":
            向量文件 = Quantization.Q8_K_X解码F32(向量文件[0], 向量文件[1])
        elif Config.VEC_QUANTIZATION == "Q4_K_X":
            向量文件 = Quantization.Q4_K_X解码F32(向量文件[0], 向量文件[1], 向量文件[2])
        elif Config.VEC_QUANTIZATION == "Float16_S1M15":
            向量文件 = Quantization.F16_S1M15解码F32(向量文件)
        return 向量文件.astype(np.float32)
class Translator:
    def 文本生成向量(text: list, outputs: list = None) -> np.float32:
        请求结果 = requests.post(
            url=Config.EMB_API_URL,
            headers={"Content-Type": "application/json","Authorization": f"Bearer {Config.EMB_API_KEY}"},
            json={"input": text,"model": Config.EMB_API_MODEL},
        ).json()
        向量列表 = []
        for index in range(len(text)):
            向量列表.append(请求结果['data'][index]['embedding'])
        if isinstance(text, str):
            向量列表 = 向量列表[0]
        向量列表 = np.array(向量列表).astype(np.float32)
        return [向量列表, [text, outputs]]
    def 并行生成向量(texts: list,) -> list:
        if texts:
            最大字符数 = 2.0 * Config.EMB_MAX_TOKENS
            分组结果 = []
            当前组 = []
            当前总长 = 0.0
            for index in texts:
                首字符串 = index[0]
                长度 = len(首字符串)
                if 当前总长 + 长度 > 最大字符数:
                    分组结果.append(当前组)
                    当前组 = []
                    当前总长 = 0.0
                当前组.append(index)
                当前总长 += 长度
            if 当前组:
                分组结果.append(当前组)
            待处理文本列表原文 = [[item[0] for item in group] for group in 分组结果]
            待处理文本列表额外输出 = [[item[1] for item in group] for group in 分组结果]
            返回内容向量 = []
            with ThreadPoolExecutor(max_workers=Config.EMB_MAX_WORKERS) as 执行器:
                未来任务映射 = {
                    执行器.submit(
                        Translator.文本生成向量,
                        text=原文组,
                        outputs=额外输出
                    ): 原文组
                    for 原文组, 额外输出 in zip(待处理文本列表原文, 待处理文本列表额外输出)
                }
                for 单个任务 in tqdm(as_completed(未来任务映射), total=len(未来任务映射), desc="生成向量"):
                    返回内容向量.append(单个任务.result())
        if 返回内容向量:
            合并向量 = []
            合并请求文本 = []
            合并额外返回 = []
            for 结果 in 返回内容向量:
                if isinstance(结果[0], np.ndarray):
                    if len(结果[0].shape) == 1:
                        合并向量.append(结果[0])
                    else:
                        合并向量.extend(结果[0])
                合并请求文本.extend(结果[1][0])
                合并额外返回.extend(结果[1][1])
            return [np.array(合并向量).astype(np.float32), [合并请求文本, 合并额外返回]]
        return []

    def 参考词预处理(texts: list = None,) -> tuple[np.ndarray, list]:
        检索词 = []
        pkl文件内容 = []
        待处理文本 = []
        file_path = Config.VEC_FILE_PATH
        file_name = Config.VEC_FILE_NAME
        if texts:
            if Path(f"{file_path}/{file_name}.pkl").is_file():
                with open(f"{file_path}/{file_name}.pkl", "rb") as f:
                    pkl文件内容.extend(pickle.load(f))
                    for index in pkl文件内容:
                        检索词.append(index[0])
            检索词_set = set(检索词)
            待处理文本 = [index for index in texts if index[0] not in 检索词_set]
        if 待处理文本 and Config.EMB_API_URL and Config.EMB_API_MODEL:
            返回内容向量 = Translator.并行生成向量(待处理文本)
            向量结果列表 = 返回内容向量[0]
            文本结果列表 = [[返回内容向量[1][0][i], 返回内容向量[1][1][i]] for i in range(len(返回内容向量[1][0]))]
                
            for _ in tqdm(range(1), desc="存储向量"):
                if Config.VEC_QUANTIZATION == "Q8_K_X":
                    Int8数据, 块缩放 = Quantization.F32编码Q8_K_X(向量结果列表)
                    if Path(f"{file_path}/{file_name}.npz").is_file():
                        Int8数据向量文件, 块缩放向量文件 = np.load(f"{file_path}/{file_name}.npz", allow_pickle=True)
                        Int8数据向量文件 = np.concatenate((Int8数据向量文件, Int8数据), axis=0)
                        块缩放向量文件 = np.concatenate((块缩放向量文件, 块缩放), axis=0)
                        np.savez_compressed(f"{file_path}/{file_name}.npz", 向量=Int8数据向量文件, 块缩放=块缩放向量文件)
                    else:
                        np.savez_compressed(f"{file_path}/{file_name}.npz", 向量=Int8数据, 块缩放=块缩放)
                        向量文件 = [Int8数据, 块缩放]
                elif Config.VEC_QUANTIZATION == "Q4_K_X":
                    Int8数据, 块缩放, 原始形状 = Quantization.F32编码Q4_K_X(向量结果列表)
                    if Path(f"{file_path}/{file_name}.npz").is_file():
                        Int8数据向量文件, 块缩放向量文件, 原始形状 = np.load(f"{file_path}/{file_name}.npz", allow_pickle=True)
                        Int8数据向量文件 = np.concatenate((Int8数据向量文件, Int8数据), axis=0)
                        块缩放向量文件 = np.concatenate((块缩放向量文件, 块缩放), axis=0)
                        最新形状 = (np.prod(原始形状) + np.prod(向量结果列表.shape),)
                        np.savez_compressed(f"{file_path}/{file_name}.npz", 向量=Int8数据向量文件, 块缩放=块缩放向量文件, 形状=最新形状)
                    else:
                        np.savez_compressed(f"{file_path}/{file_name}.npz", 向量=Int8数据, 块缩放=块缩放, 形状=原始形状)
                        向量文件 = [Int8数据, 块缩放, 原始形状]
                elif Config.VEC_QUANTIZATION == "Float16_S1M15":
                    向量结果列表 = Quantization.F32编码F16_S1M15(向量结果列表)
                if Config.VEC_QUANTIZATION not in ["Q8_K_X", "Q4_K_X"]:
                    if Path(f"{file_path}/{file_name}.npz").is_file():
                        向量文件 = np.load(f"{file_path}/{file_name}.npz", allow_pickle=True)
                        向量文件 = np.concatenate((向量文件, 向量结果列表), axis=0)
                        np.savez_compressed(f"{file_path}/{file_name}.npz", 向量=向量文件)
                    else:
                        np.savez_compressed(f"{file_path}/{file_name}.npz", 向量=向量结果列表)
                        向量文件 = np.array(向量结果列表).astype(np.float32)

                if Path(f"{file_path}/{file_name}.pkl").is_file():
                    with open(f"{file_path}/{file_name}.pkl", "rb") as f:
                        文本文件 = pickle.load(f)
                    文本文件.extend(文本结果列表)
                    with open(f"{file_path}/{file_name}.pkl", "wb") as f:
                        pickle.dump(文本文件, f)
                else:
                    with open(f"{file_path}/{file_name}.pkl", "wb") as f:
                        pickle.dump(文本结果列表, f)
                    文本文件 = 文本结果列表
        else:
            try:
                if Config.VEC_QUANTIZATION == "Q8_K_X":
                    with open(f"{file_path}/{file_name}.npz", "rb") as f:
                        向量文件 = np.load(f, allow_pickle=True)
                        向量文件 = [向量文件["向量"], 向量文件["块缩放"]]
                elif Config.VEC_QUANTIZATION == "Q4_K_X":
                    with open(f"{file_path}/{file_name}.npz", "rb") as f:
                        向量文件 = np.load(f, allow_pickle=True)
                        向量文件 = [向量文件["向量"], 向量文件["块缩放"], 向量文件["形状"]]
                else:
                    with open(f"{file_path}/{file_name}.npz", "rb") as f:
                        向量文件 = np.load(f, allow_pickle=True)
                        向量文件 = 向量文件["向量"]
                with open(f"{file_path}/{file_name}.pkl", "rb") as f:
                    文本文件 = pickle.load(f)
            except Exception:
                return False, False
        return 向量文件, 文本文件
    上下文 = []
    线程锁 = mt.Lock()
    def 生成翻译(texts: list, system_prompt: str, other_input: str,):
        额外内容 = f"\n【以下是翻译任务提示，严禁输出】({other_input[0][1]})"
        messages = []
        if Config.LLM_CONTEXTS:
            with Translator.线程锁:
                if Translator.上下文:
                    messages.extend(Translator.上下文[-Config.LLM_CONTEXTS_LENGTH*2:])
        请求文本 = str(texts)
        if Config.LLM_PROMPT_LOCATION == "user":
            messages.insert(0, {"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": 请求文本 + 额外内容})
        elif Config.LLM_PROMPT_LOCATION == "system":
            messages.insert(0, {"role": "system", "content": system_prompt + 额外内容})
            messages.append({"role": "user", "content": 请求文本})
        
        json = {
            "model": Config.LLM_API_MODEL,
            "messages": messages,
            "top_p": Config.LLM_TOP_P,
            "top_k": Config.LLM_TOP_K,
            "temperature": Config.LLM_TEMP,
            "stream": False,
        }
        请求结果 = requests.post(
            url=Config.LLM_API_URL,
            headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {Config.LLM_API_KEY}"
            },
            json=json
        ).json()
        try:
            请求结果 = 请求结果["choices"][0]["message"]["content"]
            添加上下文结果 = 请求结果
            请求结果 = re.sub(r'<think>.*?</think>\s*', '', 请求结果, flags=re.DOTALL)
            返回的请求结果 = ast.literal_eval(请求结果)
        except Exception as e:
            写入日志(f"[生成翻译] 解析大语言模型翻译结果出现错误: {e}, {请求结果}", info_level=2)
            返回结果 = [[other_input[index][0], texts[index], texts[index]] for index in range(len(texts))]
            return 返回结果
        返回结果 = []
        for index in range(len(texts)):
            返回结果.append([other_input[index][0], texts[index], 返回的请求结果[index]])
        if Config.LLM_CONTEXTS:
            with Translator.线程锁:
                if Config.LLM_PROMPT_LOCATION == "user":
                    Translator.上下文.append({"role": "user", "content": 请求文本 + 额外内容})
                elif Config.LLM_PROMPT_LOCATION == "system":
                    Translator.上下文.append({"role": "user", "content": 请求文本 })
                Translator.上下文.append({"role": "assistant", "content": 添加上下文结果})
        return 返回结果
    def 构建索引(向量文件):
        if Config.INDEX_MODE == "HNSWSQ":
            向量索引 = faiss.IndexHNSWSQ(向量文件.shape[1], faiss.ScalarQuantizer.QT_8bit, Config.INDEX_HNSW_M)
            向量索引.hnsw.efConstruction = Config.INDEX_HNSW_CONSTRUCTION
            向量索引.hnsw.efSearch = Config.INDEX_HNSW_SEARCH
            for _ in tqdm(range(1), desc="训练索引"):
                向量索引.train(向量文件)
            for _ in tqdm(range(1), desc="构建索引"):
                向量索引.add(向量文件)
        elif Config.INDEX_MODE == "RefineFlat":
            向量索引 = faiss.IndexRefineFlat(faiss.IndexFlatL2(向量文件.shape[1]))
            向量索引.k_factor = Config.INDEX_REFINEFLAT_K_FACTOR
            for _ in tqdm(range(1), desc="构建索引"):
                向量索引.add(向量文件)
        return 向量索引
    def 缓存索引(向量文件, 文本文件):
        参考词哈希 = hashlib.sha3_256(pickle.dumps((向量文件, 文本文件, Config.INDEX_MODE))).hexdigest()
        emb_file_path = Config.VEC_FILE_PATH
        emb_file_name = Config.VEC_FILE_NAME
        if Path(f"{emb_file_path}/{emb_file_name}.faiss-sha3").is_file():
            with open(f"{emb_file_path}/{emb_file_name}.faiss-sha3", "r") as f:
                参考词哈希文件 = f.read()
            if 参考词哈希文件 == 参考词哈希:
                for _ in tqdm(range(1), desc="读取索引"):
                    向量索引 = faiss.read_index(f"{emb_file_path}/{emb_file_name}.faiss")
            else:
                向量索引 = Translator.构建索引(向量文件)
                for _ in tqdm(range(1), desc="存储索引"):
                    with open(f"{emb_file_path}/{emb_file_name}.faiss-sha3", "w+") as f:
                        f.write(参考词哈希)
                    faiss.write_index(向量索引, f"{emb_file_path}/{emb_file_name}.faiss")
        else:
            向量索引 = Translator.构建索引(向量文件)
            for _ in tqdm(range(1), desc="存储索引"):
                with open(f"{emb_file_path}/{emb_file_name}.faiss-sha3", "w+") as f:
                    f.write(参考词哈希)
                faiss.write_index(向量索引, f"{emb_file_path}/{emb_file_name}.faiss")
        return 向量索引
    def 翻译语言列表(texts: list,) -> list:
        输入列表 = [[b, a] for a, b in texts]
        向量文件, 文本文件 = Translator.参考词预处理()
        向量文件 = Quantization.解码向量(向量文件)
        if 文本文件:
            向量索引 = Translator.缓存索引(向量文件, 文本文件)
            输入列表 = Translator.并行生成向量(输入列表)
            向量列表 = np.array(输入列表[0]).astype(np.float32)
            for _ in tqdm(range(1), desc="近邻索引"):
                索引结果矩阵 = 向量索引.search(向量列表, Config.INDEX_K)[1]
            返回请求内容 = []
            返回其他内容 = []
            文本索引 = {index2[0]: index for index, index2 in enumerate(文本文件)}
            原文文本文件 = [index[0] for index in 文本文件]
            for index in range(len(向量列表)):
                请求内容 = 输入列表[1][0][index]
                键 = 输入列表[1][1][index]
                其他内容 = [键, f"键:{键}|参考:"]
                for index2 in 索引结果矩阵[index]:
                    原文 = 原文文本文件[index2]
                    if 原文 in 文本索引:
                        其他内容[1] += f"{文本文件[文本索引[原文]]}|"
                返回请求内容.append(请求内容)
                返回其他内容.append(其他内容)
        else:
            返回请求内容 = [row[1] for row in texts]
            返回其他内容 = [[row[0], f"键值:{row[0]}"] for row in texts]
        llm_max_batch = Config.LLM_MAX_BATCH
        其他列表 = [返回其他内容[i:i + llm_max_batch] for i in range(0, len(返回其他内容), llm_max_batch)]
        请求列表 = [返回请求内容[i:i + llm_max_batch] for i in range(0, len(返回请求内容), llm_max_batch)]
        返回列表 = []
        with ThreadPoolExecutor(max_workers=Config.LLM_MAX_WORKERS) as 执行器:
            未来任务映射 = {
                执行器.submit(
                    Translator.生成翻译,
                    texts = index,
                    system_prompt = Config.LLM_SYSTEM_PROMPT,
                    other_input = index2,
                ): index
                for index, index2 in zip(请求列表, 其他列表)
            }
            for 单个任务 in tqdm(as_completed(未来任务映射), total=len(未来任务映射), desc="生成翻译"):
                返回列表.extend(单个任务.result())
        return 返回列表
    def 翻译语言文件(file0: str,  file1: str = "", output_path: str = ".",):
        翻译列表 = []
        去翻译列表 = []
        翻译输出列表 = []
        with open(file0, "r", encoding="utf-8") as f:
            if Path(file0).suffix == ".lang":
                源文件 = f.read().splitlines()
            elif Path(file0).suffix == ".json":
                源文件 = "[" + ",".join(f"{k}={v}" for k, v in json.load(f).items()) + "]"
            可翻译源文件 = [line.split('=', 1)   for line in 源文件   if (stripped := line.strip()) and not stripped.startswith('#') and not stripped.startswith('//')]
        if file1:
            with open(file1, "r", encoding="utf-8") as f:
                if Path(file1).suffix == ".lang":
                    参考文件 = f.read().splitlines()
                elif Path(file1).suffix == ".json":
                    参考文件 = "[" + ",".join(f"{k}={v}" for k, v in json.load(f).items()) + "]"
                参考文件 = [line.split('=', 1)   for line in 参考文件   if (stripped := line.strip()) and not stripped.startswith('#') and not stripped.startswith('//')]
            参考字典 = {}
            for item in 参考文件:
                try:
                    参考字典[item[0]] = item[1]
                except Exception as e:
                    写入日志(f"[翻译语言文件] 解析参考文件出现错误: {e}, {item}", info_level=2)
                    pass
            for index1 in 可翻译源文件:
                key = index1[0]
                if key in 参考字典:
                    去翻译列表.append([key, 参考字典[key]])
                else:
                    翻译列表.append(index1)
        else:
            翻译列表 = 可翻译源文件.copy()
        翻译列表 = Translator.翻译语言列表(翻译列表)
        翻译列表 = [[a, c] for a, b, c in 翻译列表]
        所有翻译结果 = 翻译列表 + 去翻译列表
        for index in 源文件:
            if index.strip().startswith(('#', '//')):
                翻译输出列表.append(index)
            else:
                索引成功 = False
                for index1 in 所有翻译结果:
                    if index.split('=', 1)[0] == index1[0]:
                        翻译输出列表.append(f"{index1[0]}={index1[1]}")
                        索引成功 = True
                        break
                if not 索引成功:
                    翻译输出列表.append(index)
        if not Path(output_path).suffix:
            output_path = str(Path(f"{output_path}/{Config.LANGUAGE_OUTPUT}{Path(file0).suffix}"))
        with open(output_path, "w+", encoding="utf-8") as f:
            if Path(output_path).suffix == ".lang":
                f.write("\n".join(翻译输出列表))
            elif Path(output_path).suffix == ".json":
                翻译输出列表 = [line for line in 翻译输出列表   if line.strip()   and '=' in line   and not line.lstrip().startswith(('//', '#'))]
                json文件 = {line.split('=', 1)[0]: line.split('=', 1)[1] for line in 翻译输出列表}
                f.write(json.dumps(json文件, ensure_ascii=False, indent=4))
        print(f"导出路径：{output_path}")
    def 随机16进制字符串(length: int):
        return '-'.join([f'{random.randint(0, 0xFFFF):04X}' for _ in range(length)])
    def 读取压缩文件(file_path: str, cache_path: str, original_language: str, target_language: str):
        with zipfile.ZipFile(file_path, 'r') as f:
            可用文件列表 = [False]
            文件列表 = f.namelist()
            文件路径 = f"{cache_path}/{Translator.随机16进制字符串(1)}_{Path(file_path).stem}"
            if any(name.startswith("shaders") for name in 文件列表):
                可用文件列表 = [True]
                f.extractall(文件路径)
            for index in [original_language, target_language]:
                for index1 in 文件列表:
                    index1文件名 = os.path.splitext(index1.split('/')[-1])[0]
                    if index1文件名 == index.lower():
                        f.extract(index1, path=文件路径)
                        可用文件列表.append([index, f"{文件路径}/{index1}"])
        f.close()
        return 可用文件列表
    def 翻译资源文件(file0: str, file1: str = "", output_path: str = "./",):
        target_language = Config.LANGUAGE_OUTPUT
        original_language = Config.LANGUAGE_INPUT
        cache_dir = f"{Config.PATH_CACHE}/{Translator.随机16进制字符串(4)}"
        file2 = Translator.读取压缩文件(file0, cache_dir, original_language, target_language)
        file3 = Translator.读取压缩文件(file1, cache_dir, original_language, target_language) if file1 else []
        if not any(isinstance(item, list) and len(item) > 0 and item[0] == original_language for item in file2[1:]):
            写入日志("[翻译资源文件] file0中没有原语言文件", info_level=3)
            raise FileNotFoundError("[翻译资源文件] file0: 没有原始语言文件")
        if file1 and not any(isinstance(item, list) and len(item) > 0 and item[0] == target_language for item in file3[1:]):
            写入日志("[翻译资源文件] file1中没有目标语言文件", info_level=3)
            raise FileNotFoundError("[翻译资源文件] file1: 没有目标语言文件")
        for index in file2[1:]:
            if index[0] == original_language.lower():
                源文件 = index[1]
        目标文件 = ""
        if file3:
            for index in file3[1:]:
                if index[0] == target_language.lower():
                    目标文件 = index[1]
        else:
            for index in file2[1:]:
                if index[0] == target_language.lower():
                    目标文件 = index[1]
        #输出路径 = f"{Path(源文件).parent}/{target_language}{Path(源文件).suffix}"
        输出路径 = f"{Path(源文件).parent}"
        Translator.翻译语言文件(file0=源文件, output_path=输出路径, file1=目标文件)
        压缩文件夹Path = Path(源文件).parent.parent.parent
        if file2[0] == False:
            压缩文件夹Path = 压缩文件夹Path.parent
            with open(f"{str(压缩文件夹Path)}/pack.mcmeta", "w+", encoding="utf-8") as f:
                f.write(json.dumps({"pack": {"description": f"{Path(file0).stem}的{target_language}语言资源包\n由青茫制作","pack_format": 9999,"supported_formats": [0, 9999],"min_format": 0,"max_format": 9999}}, ensure_ascii=False, indent=4))
        压缩文件夹 = str(压缩文件夹Path)
        with zipfile.ZipFile(f"{output_path}/{Path(file0).stem}-{target_language}.zip", 'w', zipfile.ZIP_DEFLATED) as f:
            for 压缩文件 in 压缩文件夹Path.rglob('*'):
                if 压缩文件.is_file():
                    f.write(压缩文件, arcname=压缩文件.relative_to(压缩文件夹))
        print(f"导出路径：{output_path}/{Path(file0).stem}-{target_language}.zip")
    def 导出数据集(mode: str, file: str = "dataset.jsonl"):
        with open(f"{Config.VEC_FILE_PATH}/{Config.VEC_FILE_NAME}.pkl", "rb") as f:
            文本文件 = pickle.load(f)
        导出列表 = []
        for index in tqdm(文本文件, desc="正在编码"):
            if mode == "ChatML":
                导出列表.append({"messages": [{"role": "system", "content": "将下列文本翻译为目标语言"}, {"role": "user", "content": index[0]}, {"role": "assistant", "content": index[1]}]})
            elif mode == "Alpaca":
                导出列表.append({"instruction": "翻译为目标语言", "input": index[0], "output": index[1], "system": "将下列文本翻译为目标语言"})
        with open(file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(json.dumps(item, ensure_ascii=False, separators=(',', ':')) for item in tqdm(导出列表, desc="正在序列化")))
        print(f"导出路径：{file}")
    def 导入参考词(path: str):
        def 打开文件(file: str):
            with open(file, "r", encoding="utf-8") as f:
                if Path(file).suffix == ".lang":
                    文件 = f.read().splitlines()
                elif Path(file).suffix == ".json":
                    文件 = "[" + ",".join(f"{k}={v}" for k, v in json.load(f).items()) + "]"
                文件 = [line.split('=', 1)   for line in 文件   if (stripped := line.strip()) and not stripped.startswith('#') and not stripped.startswith('//')]
            f.close()
            return 文件
        target_language = Config.LANGUAGE_OUTPUT
        original_language = Config.LANGUAGE_INPUT
        待处理列表 = []
        for index in ["*.jar", "*.zip", "*.pkl"]:
            for 文件路径 in list(Path(path).rglob(index)):
                文件路径 = str(文件路径)
                cache_dir = f"{Config.PATH_CACHE}/{Translator.随机16进制字符串(4)}"
                if Path(文件路径).suffix == ".pkl":
                    with open(文件路径, "rb") as f:
                        待处理列表.extend(pickle.load(f))
                else:
                    处理列表 = []
                    文件列表 = Translator.读取压缩文件(文件路径, cache_dir, original_language, target_language)
                    if not any(isinstance(item, list) and len(item) > 0 and item[0] == original_language for item in 文件列表[1:]): continue
                    if not any(isinstance(item, list) and len(item) > 0 and item[0] == target_language for item in 文件列表[1:]): continue
                    for index1 in 文件列表[1:]:
                        if index1[0] == original_language:
                            原文文件 = index1[1]
                        if index1[0] == target_language:
                            目标文件 = index1[1]
                    原文文件, 目标文件 = 打开文件(原文文件), 打开文件(目标文件)
                    目标映射 = {}
                    for item in 目标文件:
                        if len(item) >= 2:
                            目标映射[item[0]] = item[1]
                    处理列表.extend([[原文[1], 目标映射[原文[0]]] for 原文 in 原文文件 if 原文[0] in 目标映射])
                    待处理列表 += 处理列表
        Translator.参考词预处理(待处理列表)
    def 读取单个FTBQ_Snbt文件(index: str):
        文本列表 = []
        SNBT文件 = ConfigFactory.parse_file(index)
        if "description" in SNBT文件:
            if isinstance(SNBT文件["description"], str):
                文本列表.append([[index, ["description"]], SNBT文件["description"]])
            elif isinstance(SNBT文件["description"], list):
                for index2q, index2 in enumerate(SNBT文件["description"]):
                    文本列表.append([[index, ["description", index2q]], index2])
        if "rewards" in SNBT文件:
            for index2q, index2 in enumerate(SNBT文件["rewards"]):
                if "title" in index2:
                    文本列表.append([[index, ["rewards", index2q], ["title"]], index2["title"]])
        if "subtitle" in SNBT文件:
            文本列表.append([[index, ["subtitle"]], SNBT文件["subtitle"]])
        if "title" in SNBT文件:
            文本列表.append([[index, ["title"]], SNBT文件["title"]])
        if "tasks" in SNBT文件:
            for index1q, index1 in enumerate(SNBT文件["tasks"]):
                if "items" in index1:
                    for index2q, index2 in enumerate(index1["items"]):
                        if "tag" in index2:
                            if "pages" in index2["tag"]:
                                for index3q, index3 in enumerate(index2["tag"]["pages"]):
                                    文本列表.append([[index, ["tasks", index1q], ["items", index2q], ["tag"], ["pages", index3q]], index3])
                            if "title" in index2["tag"]:
                                文本列表.append([[index, ["tasks", index1q], ["items", index2q], ["tag"], ["title"]], index3])
                            if "display" in index2["tag"]:
                                if "Lore" in index2["tag"]["display"]:
                                    for index3q, index3 in enumerate(index2["tag"]["display"]["Lore"]):
                                        文本列表.append([[index, ["tasks", index1q], ["items", index2q], ["tag", "display"], ["Lore", index3q]], index3])
                                if "Name" in index2["tag"]["display"]:
                                    文本列表.append([[index, ["tasks", index1q], ["items", index2q], ["tag", "display"], ["Name"]], index2["tag"]["display"]["Name"]])
                if "title" in index1:
                    文本列表.append([[index, ["tasks", index1q], ["title"]], index1["title"]])
        if "rewards" in SNBT文件:
            for index1q, index1 in enumerate(SNBT文件["rewards"]):
                if "item" in index1:
                    if isinstance(index1["item"], dict) and "tag" in index1["item"]:
                        if "pages" in index1["item"]["tag"]:
                            for index3q, index3 in enumerate(index1["item"]["tag"]["pages"]):
                                文本列表.append([[index, ["rewards", index1q], ["item", "tag"], ["pages", index3q]], index3])
                        if "title" in index1["item"]["tag"]:
                            文本列表.append([[index, ["rewards", index1q], ["item", "tag"], ["title"]], index3])
                        if "display" in index1["item"]["tag"]:
                            if "Lore" in index1["item"]["tag"]["display"]:
                                for index3q, index3 in enumerate(index1["item"]["tag"]["display"]["Lore"]):
                                    文本列表.append([[index, ["rewards", index1q], ["item", "tag", "display"], ["Lore", index3q]], index3])
                            if "Name" in index1["item"]["tag"]["display"]:
                                文本列表.append([[index, ["rewards", index1q], ["item", "tag", "display"], ["Name"]], index1["item"]["tag"]["display"]["Name"]])
                if "title" in index1:
                    文本列表.append([[index, ["rewards", index1q], ["title"]], index1["title"]])
        if "text" in SNBT文件:
            for index1q, index1 in enumerate(SNBT文件["text"]):
                文本列表.append([[index, ["text", index1q]], index1])
        if "quests" in SNBT文件:
            for index1q, index1 in enumerate(SNBT文件["quests"]):
                if "description" in index1:
                    for index2q, index2 in enumerate(index1["description"]):
                        文本列表.append([[index, ["quests", index1q], ["description", index2q]], index2])
                if "rewards" in index1:
                    for index2q, index2 in enumerate(index1["rewards"]):
                        if "title" in index2:
                            文本列表.append([[index, ["quests", index1q], ["rewards", index2q], ["title"]], index2["title"]])
                if "subtitle" in index1:
                    文本列表.append([[index, ["quests", index1q], ["subtitle"]], index1["subtitle"]])
                if "title" in index1:
                    文本列表.append([[index, ["quests", index1q], ["title"]], index1["title"]])
                if "tasks" in index1:
                    for index2q, index2 in enumerate(index1["tasks"]):
                        if "title" in index2:
                            文本列表.append([[index, ["quests", index1q], ["tasks", index2q], ["title"]], index2["title"]])
        if "chapter_groups" in SNBT文件:
            for index1q, index1 in enumerate(SNBT文件["chapter_groups"]):
                文本列表.append([[index, ["chapter_groups", index1q]], index["title"]])
        return 文本列表
    def 应用FTBQ翻译(index: list, mode: str):
        SNBT文件 = ConfigFactory.parse_file(index[0][0][0])
        for index1p, index1 in enumerate(index):
            层数 = len(index[index1p][0][1:])
            位置 = index1[0][1:]
            if 层数 == 1:
                if len(位置[0]) == 1:
                    SNBT文件[位置[0][0]] = index1[1]
                else:
                    列表 = SNBT文件[位置[0][0]]
                    列表[位置[0][1]] = index1[1]
                    SNBT文件[位置[0][0]] = 列表
            elif 层数 == 2:
                if len(位置[1]) == 1:
                    SNBT文件[位置[0][0]][位置[0][1]][位置[1][0]] = index1[1]
                else:
                    列表 = SNBT文件[位置[0][0]][位置[0][1]][位置[1][0]]
                    列表[位置[1][1]] = index1[1]
                    SNBT文件[位置[0][0]][位置[0][1]][位置[1][0]] = 列表
            elif 层数 == 3:
                if not isinstance(位置[1][1], str):
                    if len(位置[2]) == 1:
                        SNBT文件[位置[0][0]][位置[0][1]][位置[1][0]][位置[1][1]][位置[2][0]] = index1[1]
                    else:
                        列表 = SNBT文件[位置[0][0]][位置[0][1]][位置[1][0]][位置[1][1]][位置[2][0]]
                        列表[位置[2][1]] = index1[1]
                        SNBT文件[位置[0][0]][位置[0][1]][位置[1][0]][位置[1][1]][位置[2][0]] = 列表
                else:
                    if len(位置[1]) == 2:
                        if len(位置[2]) == 1:
                            SNBT文件[位置[0][0]][位置[0][1]][位置[1][0]][位置[1][1]][位置[2][0]] = index1[1]
                        else:
                            列表 = SNBT文件[位置[0][0]][位置[0][1]][位置[1][0]][位置[1][1]][位置[2][0]]
                            列表[位置[2][1]] = index1[1]
                            SNBT文件[位置[0][0]][位置[0][1]][位置[1][0]][位置[1][1]][位置[2][0]] = 列表
                    elif len(位置[1]) == 3:
                        if len(位置[2]) == 1:
                            SNBT文件[位置[0][0]][位置[0][1]][位置[1][0]][位置[1][1]][位置[1][2]][位置[2][0]] = index1[1]
                        else:
                            列表 = SNBT文件[位置[0][0]][位置[0][1]][位置[1][0]][位置[1][1]][位置[1][2]][位置[2][0]]
                            列表[位置[2][1]] = index1[1]
                            SNBT文件[位置[0][0]][位置[0][1]][位置[1][0]][位置[1][1]][位置[1][2]][位置[2][0]] = 列表
            elif 层数 == 4:
                if len(位置[2]) == 1:
                    if len(位置[3]) == 1:
                        SNBT文件[位置[0][0]][位置[0][1]][位置[1][0]][位置[1][1]][位置[2][0]][位置[3][0]] = index1[1]
                    elif len(位置[3]) == 2:
                        列表 = SNBT文件[位置[0][0]][位置[0][1]][位置[1][0]][位置[1][1]][位置[2][0]][位置[3][0]]
                        列表[位置[3][1]] = index1[1]
                        SNBT文件[位置[0][0]][位置[0][1]][位置[1][0]][位置[1][1]][位置[2][0]][位置[3][0]] = 列表
                elif len(位置[2]) == 2:
                    if len(位置[3]) == 1:
                        SNBT文件[位置[0][0]][位置[0][1]][位置[1][0]][位置[1][1]][位置[2][0]][位置[2][1]][位置[3][0]] = index1[1]
                    elif len(位置[3]) == 2:
                        列表 = SNBT文件[位置[0][0]][位置[0][1]][位置[1][0]][位置[1][1]][位置[2][0]][位置[2][1]][位置[3][0]]
                        列表[位置[3][1]] = index1[1]
                        SNBT文件[位置[0][0]][位置[0][1]][位置[1][0]][位置[1][1]][位置[2][0]][位置[2][1]][位置[3][0]] = 列表

        with open(index[0][0][0], "w", encoding="utf-8") as f:
            json文件 = HOCONConverter.to_json(SNBT文件, indent=4).splitlines()
            if mode ==  "H":
                去逗号json文件 = []
                for index in json文件:
                    if index.endswith(","):
                        index = index[:-1]
                    去逗号json文件.append(index)
                json文件 = 去逗号json文件
            for index1p, index1 in enumerate(json文件):
                index1 = re.sub(r'":\s*"([+-]?\d+\.?\d*[bdL])"',r'": \1',index1)
                #index1 = re.sub(r'"([^"]+)":', r'\1:', index1)
                index1 = re.sub(r'"([a-zA-Z_][a-zA-Z0-9_]*)":', r'\1:', index1)
                json文件[index1p] = index1
            f.write("\n".join(json文件))
    def 翻译FTB任务(path: str):
        翻译列表 = []
        snbt文件 = [str(index) for index in Path(path).rglob("*.snbt")]
        with mp.Pool(processes=int(mp.cpu_count() / 2 if mp.cpu_count() / 2 > 1 else 1)) as 解释器:
            任务结果 = 解释器.imap(Translator.读取单个FTBQ_Snbt文件, snbt文件)
            for 单个任务 in tqdm(任务结果, total=len(snbt文件), desc="读取文件"):
                翻译列表.extend(单个任务)
        翻译列表 = [[index[0], index[2]] for index in Translator.翻译语言列表(翻译列表)]
        分组 = defaultdict(list)
        for item in 翻译列表:
            key = item[0][0]
            分组[key].append(item)
        翻译列表 = [分组[k] for k in sorted(分组.keys())]
        with mp.Pool(processes=int(mp.cpu_count() / 2 if mp.cpu_count() / 2 > 1 else 1)) as 解释器:
            任务结果 = 解释器.imap(partial(Translator.应用FTBQ翻译, mode=("H" if os.path.isdir(os.path.join(path, "quests")) else "L")), 翻译列表)
            for 单个任务 in tqdm(任务结果, total=len(翻译列表), desc="应用翻译"): pass
    def 读取单个BQ_Json文件(index: str):
        文件列表 = []
        with open(index, "r", encoding="utf-8") as f:
            NBT文件 = json.load(f)
        if "properties:10" in NBT文件:
            if "betterquesting:10" in NBT文件["properties:10"]:
                if "name:8" in NBT文件["properties:10"]["betterquesting:10"]:
                    文件列表.append([[index, ["properties:10", "betterquesting:10"], ["name:8"]], NBT文件["properties:10"]["betterquesting:10"]["name:8"]])
                if "desc:8" in NBT文件["properties:10"]["betterquesting:10"]:
                    文件列表.append([[index, ["properties:10", "betterquesting:10"], ["desc:8"]], NBT文件["properties:10"]["betterquesting:10"]["desc:8"]])
        if "questDatabase:9" in NBT文件:
            for index1 in NBT文件["questDatabase:9"]:
                if "properties:10" in NBT文件["questDatabase:9"][index1]:
                    if "betterquesting:10" in NBT文件["questDatabase:9"][index1]["properties:10"]:
                        if "name:8" in NBT文件["questDatabase:9"][index1]["properties:10"]["betterquesting:10"]:
                            文件列表.append([[index, ["questDatabase:9", index1, "properties:10", "betterquesting:10"], ["name:8"]], NBT文件["questDatabase:9"][index1]["properties:10"]["betterquesting:10"]["name:8"]])
                        if "desc:8" in NBT文件["questDatabase:9"][index1]["properties:10"]["betterquesting:10"]:
                            文件列表.append([[index, ["questDatabase:9", index1, "properties:10", "betterquesting:10"], ["desc:8"]], NBT文件["questDatabase:9"][index1]["properties:10"]["betterquesting:10"]["desc:8"]])
        if "questLines:9" in NBT文件:
            for index1 in NBT文件["questLines:9"]:
                if "properties:10" in NBT文件["questLines:9"][index1]:
                    if "betterquesting:10" in NBT文件["questLines:9"][index1]["properties:10"]:
                        if "name:8" in NBT文件["questLines:9"][index1]["properties:10"]["betterquesting:10"]:
                            文件列表.append([[index, ["questLines:9", index1, "properties:10", "betterquesting:10"], ["name:8"]], NBT文件["questDatabase:9"][index1]["properties:10"]["betterquesting:10"]["name:8"]])
                        if "desc:8" in NBT文件["questLines:9"][index1]["properties:10"]["betterquesting:10"]:
                            文件列表.append([[index, ["questLines:9", index1, "properties:10", "betterquesting:10"], ["desc:8"]], NBT文件["questDatabase:9"][index1]["properties:10"]["betterquesting:10"]["desc:8"]])
        return 文件列表
    def 应用BQ翻译(index: list):
        with open(index[0][0][0], "r", encoding="utf-8") as f:
            NBT文件 = json.load(f)
        for index1 in index:
            位置 = index1[0][1:]
            if len(位置[0]) == 2:
                NBT文件[位置[0][0]][位置[0][1]][位置[1][0]] = index1[1]
            if len(位置[0]) == 4:
                NBT文件[位置[0][0]][位置[0][1]][位置[0][2]][位置[0][3]][位置[1][0]] = index1[1]
        with open(index[0][0][0], "w+", encoding="utf-8") as f:
            json.dump(NBT文件, f, ensure_ascii=False, indent=2)
    def 翻译BQ任务(path: str):
        翻译列表 = []
        nbt文件 = [str(index) for index in Path(path).rglob("*.json")]
        with mp.Pool(processes=int(mp.cpu_count() / 2 if mp.cpu_count() / 2 > 1 else 1)) as 解释器:
            任务结果 = 解释器.imap(Translator.读取单个BQ_Json文件, nbt文件)
            for 单个任务 in tqdm(任务结果, total=len(nbt文件), desc="读取文件"):
                翻译列表.extend(单个任务)
        翻译列表 = [[index[0], index[2]] for index in Translator.翻译语言列表(翻译列表)]
        分组 = defaultdict(list)
        for item in 翻译列表:
            key = item[0][0]
            分组[key].append(item)
        翻译列表 = [分组[k] for k in sorted(分组.keys())]
        with mp.Pool(processes=int(mp.cpu_count() / 2 if mp.cpu_count() / 2 > 1 else 1)) as 解释器:
            任务结果 = 解释器.imap(partial(Translator.应用BQ翻译), 翻译列表)
            for 单个任务 in tqdm(任务结果, total=len(翻译列表), desc="应用翻译"): pass
    def 导入DictMini参考词(file: str):
        待处理列表 = []
        for _ in tqdm(range(1), desc="读取文件"):
            with open(file, "rb") as f:
                Dict文件 = json.load(f)
        for index in tqdm(Dict文件, desc="处理文件"):
            待处理列表.append([index, ", ".join(Dict文件[index])])
        Translator.参考词预处理(待处理列表)