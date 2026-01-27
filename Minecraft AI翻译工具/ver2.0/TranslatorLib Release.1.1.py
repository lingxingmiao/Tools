import multiprocessing as mp
import threading as mt
import random
import json
import pickle
import os
import re
import argparse
import zipfile
from functools import partial
from collections import defaultdict
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

import faiss
import numpy as np
import ujson
from pyhocon import ConfigFactory, HOCONConverter


import requests
from tqdm import tqdm

def 文本生成向量(
    text: str | list,
    api_url: str,
    api_key: str,
    model: str,
    outputs: str | list = None
    ) -> np.float32:
    请求文本 = text
    if isinstance(text, str):
        请求文本 = [text]
    额外返回 = outputs
    if outputs:
        if isinstance(outputs, str):
            额外返回 = [outputs]
    else:
        额外返回 = [None] * len(请求文本)
    请求结果 = requests.post(
        url=api_url,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        },
        json={
            "input": 请求文本,
            "model": model
        },
    )
    请求结果 = ujson.loads(请求结果.content)
    向量列表 = []
    for index in range(len(请求文本)):
        向量列表.append(请求结果['data'][index]['embedding'])
    if isinstance(text, str):
        向量列表 = 向量列表[0]
    向量列表 = np.array(向量列表).astype(np.float32)
    return [向量列表, [请求文本, 额外返回]]
def 并行生成向量(
    texts: list,
    api_url: str,
    api_key: str,
    model: str,
    max_token: int = 2048,
    max_batch: int = 2147483647,
    max_workers: int = 16,
    ) -> list:
    if texts:
        最大字符数 = 1.5 * max_token
        分组结果 = []
        当前组 = []
        当前总长 = 0.0
        for index in texts:
            首字符串 = index[0]
            长度 = len(首字符串)
            if 当前总长 + 长度 > 最大字符数 or len(当前组) >= max_batch:
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
        with ThreadPoolExecutor(max_workers=max_workers) as 执行器:
            未来任务映射 = {
                执行器.submit(
                    文本生成向量,
                    text=原文组,
                    api_url=api_url,
                    api_key=api_key,
                    model=model,
                    outputs=额外输出
                ): 原文组
                for 原文组, 额外输出 in zip(待处理文本列表原文, 待处理文本列表额外输出)
            }
            for 单个任务 in tqdm(as_completed(未来任务映射), total=len(未来任务映射), desc="处理向量"):
            #for 单个任务 in as_completed(未来任务映射):
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

def 参考词预处理(
    texts: list = None,
    api_url: str = None,
    api_key: str = None,
    model: str = None,
    max_token: int = 2048,
    max_batch: int = 2147483647,
    max_workers: int = 16,
    file_name: str = "vectors",
    file_path: str = "."
    ) -> tuple[np.ndarray, list]:
    检索词 = []
    pkl文件内容 = []
    待处理文本 = []
    if texts:
        if Path(f"{file_path}/{file_name}.pkl").is_file():
            with open(f"{file_path}/{file_name}.pkl", "rb") as f:
                pkl文件内容.extend(pickle.load(f))
                for index in pkl文件内容:
                    检索词.append(index[0])
        #for index in texts:
        #    原文 = index[0]
        #    if not 原文 in 检索词:
        #        待处理文本.append([原文, index[1]])
        检索词_set = set(检索词)
        待处理文本 = [index for index in texts if index[0] not in 检索词_set]
    if 待处理文本 and api_url and model:
        向量结果列表 = []
        文本结果列表 = []
        返回内容向量 = 并行生成向量(待处理文本, api_url, api_key, model, max_token, max_batch, max_workers)
        for index in range(len(返回内容向量[0])):
            向量结果列表.append(返回内容向量[0][index])
            文本结果列表.append([返回内容向量[1][0][index], 返回内容向量[1][1][index]])
        if Path(f"{file_path}/{file_name}.npy").is_file():
            向量文件 = np.load(f"{file_path}/{file_name}.npy", allow_pickle=True)
            向量文件 = np.concatenate((向量文件, 向量结果列表), axis=0)
            np.save(f"{file_path}/{file_name}.npy", 向量文件)
        else:
            np.save(f"{file_path}/{file_name}.npy", 向量结果列表)
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
            with open(f"{file_path}/{file_name}.npy", "rb") as f:
                向量文件 = np.load(f, allow_pickle=True)
            with open(f"{file_path}/{file_name}.pkl", "rb") as f:
                文本文件 = pickle.load(f)
        except Exception:
            return False, False
    return 向量文件, 文本文件
上下文 = []
线程锁 = mt.Lock()
def LLM生成交互(
    texts: list,
    system_prompt: str,
    other_input: str,
    api_url: str,
    api_key: str,
    model: str,
    contexts: bool = True,
    contexts_length: int = 16,
    top_p: int = 50,
    top_k: float = 0.7,
    temperature: float = 0.65,
    system_prompt_location = "user",
    ):
    额外内容 = f"以下是提示内容，请不要输出（{other_input[0][1]}）"
    global 上下文
    messages = []
    if contexts:
        with 线程锁:
            if 上下文:
                messages.extend(上下文[-contexts_length*2:])
    请求文本 = "\n".join(texts)
    if system_prompt_location == "user":
        messages.insert(0, {"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": 请求文本 + 额外内容})
    elif system_prompt_location == "system":
        messages.insert(0, {"role": "system", "content": system_prompt + 额外内容})
        messages.append({"role": "user", "content": 请求文本})
    json = {
        "model": model,
        "messages": messages,
        "top_p": top_p,
        "top_k": top_k,
        "temperature": temperature,
        "stream": False,
    }
    response = requests.post(
        url=api_url,
        headers={
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
        },
        json=json
    )
    请求结果 = ujson.loads(response.content)
    请求结果 = 请求结果["choices"][0]["message"]["content"]
    请求结果 = re.sub(r'<think>.*?</think>\s*', '', 请求结果, flags=re.DOTALL)
    返回结果 = []
    返回的请求结果 = 请求结果.strip().split("\n")
    for index in range(len(texts)):
        返回结果.append([other_input[0][0], texts[index], 返回的请求结果[index]])
    if contexts:
        with 线程锁:
            if system_prompt_location == "user":
                上下文.append({"role": "user", "content": 请求文本 + 额外内容})
            elif system_prompt_location == "system":
                上下文.append({"role": "user", "content": 请求文本 })
            上下文.append({"role": "assistant", "content": 请求结果})
    return 返回结果

def 翻译语言列表(
    texts: list,
    llm_api_url: str, llm_api_key: str, llm_model: str,
    emb_api_url: str, emb_api_key: str, emb_model: str,
    language: str = "zh_cn",
    emb_max_token: int = 2048, emb_max_batch: int = 2147483647, emb_max_workers: int = 16,
    emb_file_name: str = "vectors", emb_file_path: str = ".",
    llm_system_prompt: list = [], llm_prompt_location: str = "system",
    llm_contexts: bool = True, llm_contexts_length: int = 16,
    llm_max_workers: int = 8, llm_max_batch: int = 1,
    llm_t: float = 0.65, llm_p: float = 0.7, llm_k: int = 50,
    index_k: int = 3, input_key: bool = True
    ) -> list:
    输入列表 = [[b, a] for a, b in texts]
    向量文件, 文本文件 = 参考词预处理(llm_system_prompt, emb_api_url, emb_api_key, emb_model, emb_max_token, emb_max_batch, emb_max_workers, emb_file_name, emb_file_path)
    if 文本文件:
        输入列表 = 并行生成向量(输入列表, emb_api_url, emb_api_key, emb_model, emb_max_token, emb_max_batch, emb_max_workers)
        向量索引 = faiss.IndexHNSWSQ(向量文件.shape[1], faiss.ScalarQuantizer.QT_8bit, 80)
        向量索引.hnsw.efConstruction = 480
        向量索引.hnsw.efSearch = 480
        向量列表 = np.array(输入列表[0]).astype(np.float32)
        for _ in tqdm(range(1), desc="训练索引"):
            向量索引.train(向量文件)
        for _ in tqdm(range(1), desc="构建索引"):
            向量索引.add(向量文件)
        for _ in tqdm(range(1), desc="近邻索引"):
            索引结果矩阵 = 向量索引.search(向量列表, index_k)[1]
        返回请求内容 = []
        返回其他内容 = []
        文本索引 = {index2[0]: index for index, index2 in enumerate(文本文件)}
        原文文本文件 = [index[0] for index in 文本文件]
        for index in range(len(向量列表)):
            请求内容 = 输入列表[1][0][index]
            键 = 输入列表[1][1][index]
            前缀 = f"键:{键}|参考:" if input_key else "参考:"
            其他内容 = [键, 前缀]
            for index2 in 索引结果矩阵[index]:
                原文 = 原文文本文件[index2]
                if 原文 in 文本索引:
                    其他内容[1] += f"{文本文件[文本索引[原文]]}|"
            返回请求内容.append(请求内容)
            返回其他内容.append(其他内容)
    else:
        返回请求内容 = [row[1] for row in texts]
        返回其他内容 = [[row[0], f"键值:{row[0]}"] for row in texts]
    其他列表 = [返回其他内容[i:i + llm_max_batch] for i in range(0, len(返回其他内容), llm_max_batch)]
    请求列表 = [返回请求内容[i:i + llm_max_batch] for i in range(0, len(返回请求内容), llm_max_batch)]
    返回列表 = []
    system_prompt = f"/no_thinking【任务内容】1.仅输出原文翻译内容，不得包含解释、参考、键、额外内容(如“以下是翻译：”或“翻译如下：”等),即使是单个符号也要翻译(遇到&或§需要保留后面一个符号),注意不需要翻译上文,也不要额外解释\n2.返回结构为一个输出内容一个换行,输出行数必须与输入一致,中间不能有多余的空行\n3.返回的译文数量与输出格式必须一致\n4.翻译为{language}语言\n5.翻译领域为Minecraft游戏"
    with ThreadPoolExecutor(max_workers=llm_max_workers) as 执行器:
        未来任务映射 = {
            执行器.submit(
                LLM生成交互,
                texts = index,
                system_prompt = system_prompt,
                other_input = index2,
                api_url = llm_api_url,
                api_key = llm_api_key,
                model = llm_model,
                top_p = llm_p,
                top_k = llm_k,
                temperature = llm_t,
                contexts = llm_contexts,
                contexts_length = llm_contexts_length,
                system_prompt_location = llm_prompt_location,
            ): index
            for index, index2 in zip(请求列表, 其他列表)
        }
        for 单个任务 in tqdm(as_completed(未来任务映射), total=len(未来任务映射), desc="生成翻译"):
            返回列表.extend(单个任务.result())
    #参考词预处理([sublist[1:] for sublist in 返回列表], emb_api_url, emb_api_key, emb_model, emb_max_token, emb_max_batch, emb_max_workers, emb_file_name, emb_file_path)
    return 返回列表

def 翻译语言文件(
    file0: str, output_path: str,
    llm_api_url: str, llm_api_key: str, llm_model: str,
    emb_api_url: str, emb_api_key: str, emb_model: str,
    file1: str = "",
    language: str = "zh_cn",
    emb_max_token: int = 2048, emb_max_batch: int = 2147483647, emb_max_workers: int = 16,
    emb_file_name: str = "vectors", emb_file_path: str = ".",
    llm_system_prompt: list = [], llm_prompt_location: str = "system",
    llm_contexts: bool = True, llm_contexts_length: int = 16,
    llm_max_workers: int = 8, llm_max_batch: int = 1,
    llm_t: float = 0.65, llm_p: float = 0.7, llm_k: int = 50,
    index_k: int = 3,
    ):
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
        参考字典 = {item[0]: item[1] for item in 参考文件}
        for index1 in 可翻译源文件:
            key = index1[0]
            if key in 参考字典:
                去翻译列表.append([key, 参考字典[key]])
            else:
                翻译列表.append(index1)
    else:
        翻译列表 = 可翻译源文件.copy()
    
    翻译列表 = 翻译语言列表(
        翻译列表,
        llm_api_url=llm_api_url, llm_api_key=llm_api_key, llm_model=llm_model,
        emb_api_url=emb_api_url, emb_api_key=emb_api_key,emb_model=emb_model,
        language=language,
        emb_max_token=emb_max_token, emb_max_batch=emb_max_batch, emb_max_workers=emb_max_workers,
        emb_file_name=emb_file_name, emb_file_path=emb_file_path,
        llm_system_prompt=llm_system_prompt, llm_prompt_location=llm_prompt_location,
        llm_contexts=llm_contexts, llm_contexts_length=llm_contexts_length,
        llm_max_workers=llm_max_workers, llm_max_batch=llm_max_batch,
        llm_t=llm_t, llm_p=llm_p, llm_k=llm_k,
        index_k=index_k
    )
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
    with open(output_path, "w+", encoding="utf-8") as f:
        if Path(output_path).suffix == ".lang":
            f.write("\n".join(翻译输出列表))
        elif Path(output_path).suffix == ".json":
            翻译输出列表 = [line for line in 翻译输出列表   if line.strip()   and '=' in line   and not line.lstrip().startswith(('//', '#'))]
            json文件 = {line.split('=', 1)[0]: line.split('=', 1)[1] for line in 翻译输出列表}
            f.write(json.dumps(json文件, ensure_ascii=False, indent=4))
    
def 随机16进制字符串(length: int):
    return '-'.join([f'{random.randint(0, 0xFFFF):04X}' for _ in range(length)])

def 读取压缩文件(file_path: str, cache_path: str, original_language: str = "en_us", target_language: str = "zh_cn"):
    with zipfile.ZipFile(file_path, 'r') as f:
        可用文件列表 = [False]
        文件列表 = f.namelist()
        文件路径 = f"{cache_path}/{随机16进制字符串(1)}_{Path(file_path).stem}"
        if any(name.startswith("shaders") for name in 文件列表):
            可用文件列表 = [True]
            f.extractall(文件路径)
        for index in [original_language, target_language]:
            for index1 in 文件列表:
                index1文件名 = os.path.splitext(index1.split('/')[-1])[0]
                if index1文件名 == index:
                    f.extract(index1, path=文件路径)
                    可用文件列表.append([index, f"{文件路径}/{index1}"])
    f.close()
    return 可用文件列表

def 翻译资源文件(
    file0: str,
    llm_api_url: str, llm_api_key: str, llm_model: str,
    emb_api_url: str, emb_api_key: str, emb_model: str,
    file1: str = "", cache_path: str = r"./cache/", output_path: str = "./",
    original_language: str = "en_us", target_language: str = "zh_cn",
    emb_max_token: int = 2048, emb_max_batch: int = 2147483647, emb_max_workers: int = 16,
    emb_file_name: str = "vectors", emb_file_path: str = ".",
    llm_system_prompt: list = [], llm_prompt_location: str = "system",
    llm_contexts: bool = True, llm_contexts_length: int = 16,
    llm_max_workers: int = 8, llm_max_batch: int = 1,
    llm_t: float = 0.65, llm_p: float = 0.7, llm_k: int = 50,
    index_k: int = 3,
    ):
    cache_dir = f"{cache_path}/{随机16进制字符串(4)}"
    file2 = 读取压缩文件(file0, cache_dir, original_language, target_language)
    file3 = 读取压缩文件(file1, cache_dir, original_language, target_language) if file1 else []
    if not any(isinstance(item, list) and len(item) > 0 and item[0] == original_language for item in file2[1:]): raise FileNotFoundError("文件0中没有原语言文件")
    if file1 and not any(isinstance(item, list) and len(item) > 0 and item[0] == target_language for item in file3[1:]): raise FileNotFoundError("文件1中没有目标语言文件")
    for index in file2[1:]:
        if index[0] == original_language:
            源文件 = index[1]
    目标文件 = ""
    for index in file3[1:]:
        if index[0] == target_language:
            目标文件 = index[1]
    输出路径 = f"{Path(源文件).parent}/{target_language}{Path(源文件).suffix}"
    翻译语言文件(file0=源文件, output_path=输出路径,
        llm_api_url=llm_api_url, llm_api_key=llm_api_key, llm_model=llm_model,
        emb_api_url=emb_api_url, emb_api_key=emb_api_key,emb_model=emb_model,
        file1=目标文件,
        language=target_language,
        emb_max_token=emb_max_token, emb_max_batch=emb_max_batch, emb_max_workers=emb_max_workers,
        emb_file_name=emb_file_name, emb_file_path=emb_file_path,
        llm_system_prompt=llm_system_prompt, llm_prompt_location=llm_prompt_location,
        llm_contexts=llm_contexts, llm_contexts_length=llm_contexts_length,
        llm_max_workers=llm_max_workers, llm_max_batch=llm_max_batch,
        llm_t=llm_t, llm_p=llm_p, llm_k=llm_k,
        index_k=index_k)
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
                
def 导出数据集(
    mode: str, file: str = "dataset.jsonl",
    emb_file_name: str = "vectors", emb_file_path: str = ".",
    ):
    with open(f"{emb_file_path}/{emb_file_name}.pkl", "rb") as f:
        文本文件 = pickle.load(f)
    导出列表 = []
    for index in 文本文件:
        if mode == "ChatML":
            导出列表.append({"messages": [{"role": "system", "content": "将下列文本翻译为目标语言"}, {"role": "user", "content": index[0]}, {"role": "assistant", "content": index[1]}]})
        elif mode == "Alpaca":
            导出列表.append({"instruction": "翻译为目标语言", "input": index[0], "output": index[1], "system": "将下列文本翻译为目标语言"})
    with open(file, 'w', encoding='utf-8') as f:
        for item in 导出列表:
            f.write(json.dumps(item, ensure_ascii=False, separators=(',', ':')) + '\n')
    
def 导入参考词(
    path: str, emb_api_url: str, emb_api_key: str, emb_model: str,
    original_language: str = "en_us", target_language: str = "zh_cn", cache_path: str = r"./cache/",
    emb_max_token: int = 2048, emb_max_batch: int = 2147483647, emb_max_workers: int = 16,
    emb_file_name: str = "vectors", emb_file_path: str = ".",):
    def 打开文件(file: str):
        with open(file, "r", encoding="utf-8") as f:
            if Path(file).suffix == ".lang":
                文件 = f.read().splitlines()
            elif Path(file).suffix == ".json":
                文件 = "[" + ",".join(f"{k}={v}" for k, v in json.load(f).items()) + "]"
            文件 = [line.split('=', 1)   for line in 文件   if (stripped := line.strip()) and not stripped.startswith('#') and not stripped.startswith('//')]
        f.close()
        return 文件
    待处理列表 = []
    for index in ["*.jar", "*.zip", "*.pkl"]:
        for 文件路径 in list(Path(path).rglob(index)):
            文件路径 = str(文件路径)
            cache_dir = f"{cache_path}/{随机16进制字符串(4)}"
            if Path(文件路径).suffix == ".pkl":
                with open(文件路径, "rb") as f:
                    待处理列表.extend(pickle.load(f))
            else:
                处理列表 = []
                文件列表 = 读取压缩文件(文件路径, cache_dir, original_language, target_language)
                if not any(isinstance(item, list) and len(item) > 0 and item[0] == original_language for item in 文件列表[1:]): continue
                if not any(isinstance(item, list) and len(item) > 0 and item[0] == target_language for item in 文件列表[1:]): continue
                for index1 in 文件列表[1:]:
                    if index1[0] == original_language:
                        原文文件 = index1[1]
                    if index1[0] == target_language:
                        目标文件 = index1[1]
                原文文件, 目标文件 = 打开文件(原文文件), 打开文件(目标文件)
                目标映射 = {item[0]: item[1] for item in 目标文件}
                处理列表.extend([[原文[1], 目标映射[原文[0]]] for 原文 in 原文文件 if 原文[0] in 目标映射])
                待处理列表 += 处理列表
    参考词预处理(texts=待处理列表, api_url=emb_api_url, api_key=emb_api_key, model=emb_model, max_token=emb_max_token, max_batch=emb_max_batch, max_workers=emb_max_workers, file_name=emb_file_name, file_path=emb_file_path)

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

def 翻译FTB任务(
    path: str,
    llm_api_url: str, llm_api_key: str, llm_model: str,
    emb_api_url: str, emb_api_key: str, emb_model: str,
    language: str = "zh_cn",
    emb_max_token: int = 2048, emb_max_batch: int = 2147483647, emb_max_workers: int = 16,
    emb_file_name: str = "vectors", emb_file_path: str = ".",
    llm_system_prompt: list = [], llm_prompt_location: str = "system",
    llm_contexts: bool = True, llm_contexts_length: int = 16,
    llm_max_workers: int = 8, llm_max_batch: int = 1,
    llm_t: float = 0.65, llm_p: float = 0.7, llm_k: int = 50,
    index_k: int = 3,):
    def 请求翻译语言列表(texts: list):
        return 翻译语言列表(texts=texts,
            llm_api_url=llm_api_url, llm_api_key=llm_api_key, llm_model=llm_model,
            emb_api_url=emb_api_url, emb_api_key=emb_api_key, emb_model=emb_model,
            language=language,
            emb_max_token=emb_max_token, emb_max_batch=emb_max_batch, emb_max_workers=emb_max_workers,
            emb_file_name=emb_file_name, emb_file_path=emb_file_path,
            llm_system_prompt=llm_system_prompt, llm_prompt_location=llm_prompt_location,
            llm_contexts=llm_contexts, llm_contexts_length=llm_contexts_length,
            llm_max_workers=llm_max_workers, llm_max_batch=llm_max_batch,
            llm_t=llm_t, llm_p=llm_p, llm_k=llm_k,
            index_k=index_k, input_key=False
        )
    翻译列表 = []
    snbt文件 = [str(index) for index in Path(path).rglob("*.snbt")]
    with mp.Pool(processes=int(mp.cpu_count() / 2 if mp.cpu_count() / 2 > 1 else 1)) as 解释器:
        任务结果 = 解释器.imap(读取单个FTBQ_Snbt文件, snbt文件)
        for 单个任务 in tqdm(任务结果, total=len(snbt文件), desc="读取文件"):
            翻译列表.extend(单个任务)
    翻译列表 = [[index[0], index[2]] for index in 请求翻译语言列表(翻译列表)]
    分组 = defaultdict(list)
    for item in 翻译列表:
        key = item[0][0]
        分组[key].append(item)
    翻译列表 = [分组[k] for k in sorted(分组.keys())]
    with mp.Pool(processes=1) as 解释器:
        任务结果 = 解释器.imap(partial(应用FTBQ翻译, mode=("H" if os.path.isdir(os.path.join(path, "quests")) else "L")), 翻译列表)
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
    
    
    
    
    
    
def 翻译BQ任务(
    path: str,
    llm_api_url: str, llm_api_key: str, llm_model: str,
    emb_api_url: str, emb_api_key: str, emb_model: str,
    language: str = "zh_cn",
    emb_max_token: int = 2048, emb_max_batch: int = 2147483647, emb_max_workers: int = 16,
    emb_file_name: str = "vectors", emb_file_path: str = ".",
    llm_system_prompt: list = [], llm_prompt_location: str = "system",
    llm_contexts: bool = True, llm_contexts_length: int = 16,
    llm_max_workers: int = 8, llm_max_batch: int = 1,
    llm_t: float = 0.65, llm_p: float = 0.7, llm_k: int = 50,
    index_k: int = 3,):
    def 请求翻译语言列表(texts: list):
        return 翻译语言列表(texts=texts,
            llm_api_url=llm_api_url, llm_api_key=llm_api_key, llm_model=llm_model,
            emb_api_url=emb_api_url, emb_api_key=emb_api_key, emb_model=emb_model,
            language=language,
            emb_max_token=emb_max_token, emb_max_batch=emb_max_batch, emb_max_workers=emb_max_workers,
            emb_file_name=emb_file_name, emb_file_path=emb_file_path,
            llm_system_prompt=llm_system_prompt, llm_prompt_location=llm_prompt_location,
            llm_contexts=llm_contexts, llm_contexts_length=llm_contexts_length,
            llm_max_workers=llm_max_workers, llm_max_batch=llm_max_batch,
            llm_t=llm_t, llm_p=llm_p, llm_k=llm_k,
            index_k=index_k, input_key=False
        )
    翻译列表 = []
    nbt文件 = [str(index) for index in Path(path).rglob("*.json")]
    with mp.Pool(processes=int(mp.cpu_count() / 2 if mp.cpu_count() / 2 > 1 else 1)) as 解释器:
        任务结果 = 解释器.imap(读取单个BQ_Json文件, nbt文件)
        for 单个任务 in tqdm(任务结果, total=len(nbt文件), desc="读取文件"):
            翻译列表.extend(单个任务)
    翻译列表 = [[index[0], index[2]] for index in 请求翻译语言列表(翻译列表)]
    分组 = defaultdict(list)
    for item in 翻译列表:
        key = item[0][0]
        分组[key].append(item)
    翻译列表 = [分组[k] for k in sorted(分组.keys())]
    with mp.Pool(processes=1) as 解释器:
        任务结果 = 解释器.imap(partial(应用BQ翻译), 翻译列表)
        for 单个任务 in tqdm(任务结果, total=len(翻译列表), desc="应用翻译"): pass
    
        


if __name__ == "__main__":
    解释器0 = argparse.ArgumentParser()
    解释器1 = 解释器0.add_subparsers(dest="mode")
    TranslatorLang = 解释器1.add_parser("TranslatorLang", help="翻译语言文件")
    TranslatorPack = 解释器1.add_parser("TranslatorPack", help="翻译资源包文件")
    TranslatorFTBQ = 解释器1.add_parser("TranslatorFTBQ", help="翻译FTBQ任务文件夹")
    TranslatorBQ = 解释器1.add_parser("TranslatorBQ", help="翻译BQ任务文件夹")
    TranslatorLang.add_argument("--index-k", type=int, default=3, help="检索结果数")
    ExportJsonl = 解释器1.add_parser("ExportJsonl", help="导出JSONL数据集文件")
    ImportPrompt = 解释器1.add_parser("ImportPrompt", help="从文件夹里的所有模组光影资源包导入参考词文件")
    TranslatorLang.add_argument("--file0", type=str, required=True, help="输入文件0路径")
    TranslatorLang.add_argument("--output-path", type=str, required=True, help="输出目录路径")
    TranslatorLang.add_argument("--llm-api-url", type=str, required=True, help="LLM API 地址")
    TranslatorLang.add_argument("--llm-api-key", type=str, default="", help="LLM API 密钥")
    TranslatorLang.add_argument("--llm-model", type=str, required=True, help="LLM 模型名称")
    TranslatorLang.add_argument("--emb-api-url", type=str, required=True, help="Embedding API 地址")
    TranslatorLang.add_argument("--emb-api-key", type=str, default="", help="Embedding API 密钥")
    TranslatorLang.add_argument("--emb-model", type=str, required=True, help="Embedding 模型名称")
    TranslatorLang.add_argument("--file1", type=str, default="", help="输入文件1路径")
    TranslatorLang.add_argument("--language", type=str, default="zh_cn", help="语言代码")
    TranslatorLang.add_argument("--emb-max-token", type=int, default=2048, help="Embedding 最大 token 数")
    TranslatorLang.add_argument("--emb-max-batch", type=int, default=2147483647, help="Embedding 最大批大小")
    TranslatorLang.add_argument("--emb-max-workers", type=int, default=16, help="Embedding 最大并发数")
    TranslatorLang.add_argument("--emb-file-name", type=str, default="vectors", help="向量文件名（不含扩展名）")
    TranslatorLang.add_argument("--emb-file-path", type=str, default=".", help="向量文件保存路径")
    TranslatorLang.add_argument("--llm-system-prompt", nargs="*", default=[], help="额外系统提示词列表")
    TranslatorLang.add_argument("--llm-prompt-location", type=str, default="system", help="提示位置(system | user)")
    TranslatorLang.add_argument("--llm-contexts", type=bool, default=True, help="是否启用上下文")
    TranslatorLang.add_argument("--llm-contexts-length", type=int, default=6, help="上下文长度")
    TranslatorLang.add_argument("--llm-max-workers", type=int, default=8, help="LLM 最大并发数")
    TranslatorLang.add_argument("--llm-max-batch", type=int, default=1, help="LLM 最大批大小")
    TranslatorLang.add_argument("--llm-t", type=float, default=0.65, help="采样温度 (temperature)")
    TranslatorLang.add_argument("--llm-p", type=float, default=0.7, help="Top-p 值")
    TranslatorLang.add_argument("--llm-k", type=int, default=50, help="Top-k 值")
    TranslatorPack.add_argument("--file0", type=str, required=True, help="输入文件0路径")
    TranslatorPack.add_argument("--llm-api-url", type=str, required=True, help="LLM API 地址")
    TranslatorPack.add_argument("--llm-api-key", type=str, default="", help="LLM API 密钥")
    TranslatorPack.add_argument("--llm-model", type=str, required=True, help="LLM 模型名称")
    TranslatorPack.add_argument("--emb-api-url", type=str, required=True, help="Embedding API 地址")
    TranslatorPack.add_argument("--emb-api-key", type=str, default="", help="Embedding API 密钥")
    TranslatorPack.add_argument("--emb-model", type=str, required=True, help="Embedding 模型名称")
    TranslatorPack.add_argument("--file1", type=str, default="", help="输入文件1路径")
    TranslatorPack.add_argument("--cache-path", type=str, default="./cache/", help="缓存目录")
    TranslatorPack.add_argument("--output-path", type=str, default="./", help="输出目录路径")
    TranslatorPack.add_argument("--original-language", type=str, default="en_us", help="原始语言代码")
    TranslatorPack.add_argument("--target-language", type=str, default="zh_cn", help="目标语言代码")
    TranslatorPack.add_argument("--emb-max-token", type=int, default=2048, help="Embedding 最大 token 数")
    TranslatorPack.add_argument("--emb-max-batch", type=int, default=2147483647, help="Embedding 最大批大小")
    TranslatorPack.add_argument("--emb-max-workers", type=int, default=16, help="Embedding 最大并发数")
    TranslatorPack.add_argument("--emb-file-name", type=str, default="vectors", help="向量文件名（不含扩展名）")
    TranslatorPack.add_argument("--emb-file-path", type=str, default=".", help="向量文件保存路径")
    TranslatorPack.add_argument("--llm-system-prompt", nargs="*", default=[], help="额外系统提示词列表")
    TranslatorPack.add_argument("--llm-prompt-location", type=str, default="system", help="提示位置(system | user)")
    TranslatorPack.add_argument("--llm-contexts", type=bool, default=True, help="是否启用上下文")
    TranslatorPack.add_argument("--llm-contexts-length", type=int, default=6, help="上下文长度")
    TranslatorPack.add_argument("--llm-max-workers", type=int, default=8, help="LLM 最大并发数")
    TranslatorPack.add_argument("--llm-max-batch", type=int, default=1, help="LLM 最大批大小")
    TranslatorPack.add_argument("--llm-t", type=float, default=0.65, help="采样温度 (temperature)")
    TranslatorPack.add_argument("--llm-p", type=float, default=0.7, help="Top-p 值")
    TranslatorPack.add_argument("--llm-k", type=int, default=50, help="Top-k 值")
    TranslatorPack.add_argument("--index-k", type=int, default=3, help="检索结果数")
    ExportJsonl.add_argument("--mode", type=str, required=True, help="导出格式(ChatML | Alpaca)")
    ExportJsonl.add_argument("--file", type=str, default="dataset.jsonl", help="输出文件路径")
    ExportJsonl.add_argument("--emb-file-name", type=str, default="vectors", help="向量文件名（不含扩展名）")
    ExportJsonl.add_argument("--emb-file-path", type=str, default=".", help="向量文件保存路径")
    ImportPrompt.add_argument("--path", type=str, required=True, help="输入文件夹路径")
    ImportPrompt.add_argument("--emb-api-url", type=str, required=True, help="Embedding API 地址")
    ImportPrompt.add_argument("--emb-api-key", type=str, default="", help="Embedding API 密钥")
    ImportPrompt.add_argument("--emb-model", type=str, required=True, help="Embedding 模型名称")
    ImportPrompt.add_argument("--original-language", type=str, default="en_us", help="原始语言代码")
    ImportPrompt.add_argument("--target-language", type=str, default="zh_cn", help="目标语言代码")
    ImportPrompt.add_argument("--cache-path", type=str, default="./cache/", help="缓存目录")
    ImportPrompt.add_argument("--emb-max-token", type=int, default=2048, help="Embedding 最大 token 数")
    ImportPrompt.add_argument("--emb-max-batch", type=int, default=2147483647, help="Embedding 最大批大小")
    ImportPrompt.add_argument("--emb-max-workers", type=int, default=16, help="Embedding 最大并发数")
    ImportPrompt.add_argument("--emb-file-name", type=str, default="vectors", help="向量文件名（不含扩展名）")
    ImportPrompt.add_argument("--emb-file-path", type=str, default=".", help="向量文件保存路径")
    TranslatorFTBQ.add_argument("--path", type=str, required=True, help="FTB任务文件夹路径")
    TranslatorFTBQ.add_argument("--llm-api-url", type=str, required=True, help="LLM API 地址")
    TranslatorFTBQ.add_argument("--llm-api-key", type=str, default="", help="LLM API 密钥")
    TranslatorFTBQ.add_argument("--llm-model", type=str, required=True, help="LLM 模型名称")
    TranslatorFTBQ.add_argument("--emb-api-url", type=str, required=True, help="Embedding API 地址")
    TranslatorFTBQ.add_argument("--emb-api-key", type=str, default="", help="Embedding API 密钥")
    TranslatorFTBQ.add_argument("--emb-model", type=str, required=True, help="Embedding 模型名称")
    TranslatorFTBQ.add_argument("--language", type=str, default="zh_cn", help="语言代码")
    TranslatorFTBQ.add_argument("--emb-max-token", type=int, default=2048, help="Embedding 最大 token 数")
    TranslatorFTBQ.add_argument("--emb-max-batch", type=int, default=2147483647, help="Embedding 最大批大小")
    TranslatorFTBQ.add_argument("--emb-max-workers", type=int, default=16, help="Embedding 最大并发数")
    TranslatorFTBQ.add_argument("--emb-file-name", type=str, default="vectors", help="向量文件名（不含扩展名）")
    TranslatorFTBQ.add_argument("--emb-file-path", type=str, default=".", help="向量文件保存路径")
    TranslatorFTBQ.add_argument("--llm-system-prompt", nargs="*", default=[], help="额外系统提示词列表")
    TranslatorFTBQ.add_argument("--llm-prompt-location", type=str, default="system", help="提示位置(system | user)")
    TranslatorFTBQ.add_argument("--llm-contexts", type=bool, default=True, help="是否启用上下文")
    TranslatorFTBQ.add_argument("--llm-contexts-length", type=int, default=6, help="上下文长度")
    TranslatorFTBQ.add_argument("--llm-max-workers", type=int, default=8, help="LLM 最大并发数")
    TranslatorFTBQ.add_argument("--llm-max-batch", type=int, default=1, help="LLM 最大批大小")
    TranslatorFTBQ.add_argument("--llm-t", type=float, default=0.65, help="采样温度 (temperature)")
    TranslatorFTBQ.add_argument("--llm-p", type=float, default=0.7, help="Top-p 值")
    TranslatorFTBQ.add_argument("--llm-k", type=int, default=50, help="Top-k 值")
    TranslatorFTBQ.add_argument("--index-k", type=int, default=3, help="检索结果数")
    TranslatorBQ.add_argument("--path", type=str, required=True, help="BQ任务文件夹路径")
    TranslatorBQ.add_argument("--llm-api-url", type=str, required=True, help="LLM API 地址")
    TranslatorBQ.add_argument("--llm-api-key", type=str, default="", help="LLM API 密钥")
    TranslatorBQ.add_argument("--llm-model", type=str, required=True, help="LLM 模型名称")
    TranslatorBQ.add_argument("--emb-api-url", type=str, required=True, help="Embedding API 地址")
    TranslatorBQ.add_argument("--emb-api-key", type=str, default="", help="Embedding API 密钥")
    TranslatorBQ.add_argument("--emb-model", type=str, required=True, help="Embedding 模型名称")
    TranslatorBQ.add_argument("--language", type=str, default="zh_cn", help="语言代码")
    TranslatorBQ.add_argument("--emb-max-token", type=int, default=2048, help="Embedding 最大 token 数")
    TranslatorBQ.add_argument("--emb-max-batch", type=int, default=2147483647, help="Embedding 最大批大小")
    TranslatorBQ.add_argument("--emb-max-workers", type=int, default=16, help="Embedding 最大并发数")
    TranslatorBQ.add_argument("--emb-file-name", type=str, default="vectors", help="向量文件名（不含扩展名）")
    TranslatorBQ.add_argument("--emb-file-path", type=str, default=".", help="向量文件保存路径")
    TranslatorBQ.add_argument("--llm-system-prompt", nargs="*", default=[], help="额外系统提示词列表")
    TranslatorBQ.add_argument("--llm-prompt-location", type=str, default="system", help="提示位置(system | user)")
    TranslatorBQ.add_argument("--llm-contexts", type=bool, default=True, help="是否启用上下文")
    TranslatorBQ.add_argument("--llm-contexts-length", type=int, default=6, help="上下文长度")
    TranslatorBQ.add_argument("--llm-max-workers", type=int, default=8, help="LLM 最大并发数")
    TranslatorBQ.add_argument("--llm-max-batch", type=int, default=1, help="LLM 最大批大小")
    TranslatorBQ.add_argument("--llm-t", type=float, default=0.65, help="采样温度 (temperature)")
    TranslatorBQ.add_argument("--llm-p", type=float, default=0.7, help="Top-p 值")
    TranslatorBQ.add_argument("--llm-k", type=int, default=50, help="Top-k 值")
    TranslatorBQ.add_argument("--index-k", type=int, default=3, help="检索结果数")
    参数 = 解释器0.parse_args()
    if 参数.mode == "TranslatorLang":
        翻译语言文件(
            file0=参数.file0,
            output_path=参数.output_path,
            llm_api_url=参数.llm_api_url,
            llm_api_key=参数.llm_api_key,
            llm_model=参数.llm_model,
            emb_api_url=参数.emb_api_url,
            emb_api_key=参数.emb_api_key,
            emb_model=参数.emb_model,
            file1=参数.file1,
            language=参数.language,
            emb_max_token=参数.emb_max_token,
            emb_max_batch=参数.emb_max_batch,
            emb_max_workers=参数.emb_max_workers,
            emb_file_name=参数.emb_file_name,
            emb_file_path=参数.emb_file_path,
            llm_system_prompt=参数.llm_system_prompt,
            llm_prompt_location=参数.llm_prompt_location,
            llm_contexts=参数.llm_contexts,
            llm_contexts_length=参数.llm_contexts_length,
            llm_max_workers=参数.llm_max_workers,
            llm_max_batch=参数.llm_max_batch,
            llm_t=参数.llm_t,
            llm_p=参数.llm_p,
            llm_k=参数.llm_k,
            index_k=参数.index_k
        )
    elif 参数.mode == "TranslatorPack":
        翻译资源文件(
            file0=参数.file0,
            llm_api_url=参数.llm_api_url,
            llm_api_key=参数.llm_api_key,
            llm_model=参数.llm_model,
            emb_api_url=参数.emb_api_url,
            emb_api_key=参数.emb_api_key,
            emb_model=参数.emb_model,
            file1=参数.file1,
            cache_path=参数.cache_path,
            output_path=参数.output_path,
            original_language=参数.original_language,
            target_language=参数.target_language,
            emb_max_token=参数.emb_max_token,
            emb_max_batch=参数.emb_max_batch,
            emb_max_workers=参数.emb_max_workers,
            emb_file_name=参数.emb_file_name,
            emb_file_path=参数.emb_file_path,
            llm_system_prompt=参数.llm_system_prompt,
            llm_prompt_location=参数.llm_prompt_location,
            llm_contexts=参数.llm_contexts,
            llm_contexts_length=参数.llm_contexts_length,
            llm_max_workers=参数.llm_max_workers,
            llm_max_batch=参数.llm_max_batch,
            llm_t=参数.llm_t,
            llm_p=参数.llm_p,
            llm_k=参数.llm_k,
            index_k=参数.index_k
        )
    elif 参数.mode == "ExportJsonl":
        导出数据集(
            mode=参数.mode,
            file=参数.file,
            emb_file_name=参数.emb_file_name,
            emb_file_path=参数.emb_file_path
        )
    elif 参数.mode == "ImportPrompt":
        导入参考词(
            path=参数.path,
            emb_api_url=参数.emb_api_url,
            emb_api_key=参数.emb_api_key,
            emb_model=参数.emb_model,
            original_language=参数.original_language,
            target_language=参数.target_language,
            cache_path=参数.cache_path,
            emb_max_token=参数.emb_max_token,
            emb_max_batch=参数.emb_max_batch,
            emb_max_workers=参数.emb_max_workers,
            emb_file_name=参数.emb_file_name,
            emb_file_path=参数.emb_file_path
        )
    elif 参数 == "TranslatorFTBQ":
        翻译FTB任务(
            path=参数.path,
            llm_api_url=参数.llm_api_url,
            llm_api_key=参数.llm_api_key,
            llm_model=参数.llm_model,
            emb_api_url=参数.emb_api_url,
            emb_api_key=参数.emb_api_key,
            emb_model=参数.emb_model,
            language=参数.language,
            emb_max_token=参数.emb_max_token,
            emb_max_batch=参数.emb_max_batch,
            emb_max_workers=参数.emb_max_workers,
            emb_file_name=参数.emb_file_name,
            emb_file_path=参数.emb_file_path,
            llm_system_prompt=参数.llm_system_prompt,
            llm_prompt_location=参数.llm_prompt_location,
            llm_contexts=参数.llm_contexts,
            llm_contexts_length=参数.llm_contexts_length,
            llm_max_workers=参数.llm_max_workers,
            llm_max_batch=参数.llm_max_batch,
            llm_t=参数.llm_t,
            llm_p=参数.llm_p,
            llm_k=参数.llm_k,
            index_k=参数.index_k
        )
    elif 参数 == "TranslatorBQ":
        翻译BQ任务(
            path=参数.path,
            llm_api_url=参数.llm_api_url,
            llm_api_key=参数.llm_api_key,
            llm_model=参数.llm_model,
            emb_api_url=参数.emb_api_url,
            emb_api_key=参数.emb_api_key,
            emb_model=参数.emb_model,
            language=参数.language,
            emb_max_token=参数.emb_max_token,
            emb_max_batch=参数.emb_max_batch,
            emb_max_workers=参数.emb_max_workers,
            emb_file_name=参数.emb_file_name,
            emb_file_path=参数.emb_file_path,
            llm_system_prompt=参数.llm_system_prompt,
            llm_prompt_location=参数.llm_prompt_location,
            llm_contexts=参数.llm_contexts,
            llm_contexts_length=参数.llm_contexts_length,
            llm_max_workers=参数.llm_max_workers,
            llm_max_batch=参数.llm_max_batch,
            llm_t=参数.llm_t,
            llm_p=参数.llm_p,
            llm_k=参数.llm_k,
            index_k=参数.index_k
        )
    else:
        解释器0.print_help()