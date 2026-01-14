import requests
import threading as mt
import time
import json
import pickle
from pathlib import Path
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed

import faiss
import numpy as np

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
    请求结果 = 请求结果.json()
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
        for index in texts:
            原文 = index[0]
            if not 原文 in 检索词:
                待处理文本.append([原文, index[1]])
    if 待处理文本:
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
                messages.extend(上下文)
    请求文本 = "\n".join(texts)
    if system_prompt_location == "user":
        messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": 请求文本 + 额外内容})
    elif system_prompt_location == "system":
        messages.append({"role": "system", "content": system_prompt + 额外内容})
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
    请求结果 = response.json()
    请求结果 = 请求结果["choices"][0]["message"]["content"]
    返回结果 = []
    返回的请求结果 = 请求结果.strip().split("\n")
    for index in range(len(texts)):
        返回结果.append([other_input[0][0], texts[index], 返回的请求结果[index]])
    if contexts:
        with 线程锁:
            if system_prompt_location == "user":
                上下文.append({"role": "user", "content": 请求文本 + 额外内容})
            elif system_prompt_location == "system": pass
            上下文.append({"role": "assistant", "content": 请求结果})
    return 返回结果
def 索引文本(texts, input_texts, index, index_vector, original_text, k):
    请求内容 = f"{input_texts[1][0][index]}"
    其他内容 = [input_texts[1][1][index], f"键:{input_texts[1][1][index]}|参考:"]
    索引向量 = np.array([input_texts[0][index]]).astype(np.float32)
    索引结果向量 = index_vector.search(索引向量, k)[1]
    for index2 in 索引结果向量[0]:
        索引结果列表 = original_text[index2]
        for index3, index4 in enumerate(texts):
            if 索引结果列表 == index4[0]:
                其他内容[1] += f"{texts[index3]}|"
    return 请求内容, 其他内容
    
def 翻译语言列表(
    texts: list,
    llm_api_url: str, llm_api_key: str, llm_model: str,
    emb_api_url: str, emb_api_key: str, emb_model: str,
    language: str = "简体中文",
    emb_max_token: int = 512, emb_max_batch: int = 2147483647, emb_max_workers: int = 16,
    emb_file_name: str = "vectors", emb_file_path: str = ".",
    llm_system_prompt: list = [], llm_prompt_location: str = "system", llm_contexts: bool = False,
    llm_max_workers: int = 3, llm_max_batch: int = 1,
    llm_t: float = 0.65, llm_p: float = 0.7, llm_k: int = 50,
    index_max_workers: int = 128, index_k: int = 3,
    ) -> list:
    输入列表 = [[b, a] for a, b in texts]
    向量文件, 文本文件 = 参考词预处理(llm_system_prompt, emb_api_url, emb_api_key, emb_model, emb_max_token, emb_max_batch, emb_max_workers, emb_file_name, emb_file_path)
    if 文本文件:
        输入列表 = 并行生成向量(输入列表, emb_api_url, emb_api_key, emb_model, emb_max_token, emb_max_batch, emb_max_workers)
        向量索引 = faiss.IndexFlatL2(向量文件.shape[1])
        向量索引.add(向量文件)
        原文索引列表 = [pair[0] for pair in 文本文件]
        返回请求内容 = []
        返回其他内容 = []
        with ThreadPoolExecutor(max_workers=index_max_workers) as 执行器:
            未来任务映射 = {
                执行器.submit(
                    索引文本,
                    texts = 文本文件,
                    input_texts = 输入列表,
                    index = index,
                    index_vector = 向量索引,
                    original_text = 原文索引列表,
                    k = index_k
                ): index
                for index in range(len(输入列表[0]))
            }
            for 单个任务 in tqdm(as_completed(未来任务映射), total=len(未来任务映射), desc="索引文本"):
                请求内容, 其他内容 = 单个任务.result()
                返回请求内容.append(请求内容)
                返回其他内容.append(其他内容)
    else:
        返回请求内容 = [row[1] for row in texts]
        返回其他内容 = [[row[0], f"键值:{row[0]}"] for row in texts]
    其他列表 = [返回其他内容[i:i + llm_max_batch] for i in range(0, len(返回其他内容), llm_max_batch)]
    请求列表 = [返回请求内容[i:i + llm_max_batch] for i in range(0, len(返回请求内容), llm_max_batch)]
    返回列表 = []
    system_prompt = f"/no_thinking 1.仅输出原文翻译内容，不得包含解释、参考、键、额外内容（如“以下是翻译：”或“翻译如下：”等）,即使是单个符号也要翻译,注意不需要翻译上文，也不要额外解释\n2.返回结构为一个输出内容一个换行,输出行数必须与输入一致,中间不能有多余的空行\n3.返回的译文数量与输出格式必须一致\n4.翻译为{language}语言"
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
                system_prompt_location = llm_prompt_location,
            ): index
            for index, index2 in zip(请求列表, 其他列表)
        }
        for 单个任务 in tqdm(as_completed(未来任务映射), total=len(未来任务映射), desc="生成翻译"):
            返回列表.extend(单个任务.result())
    参考词预处理([sublist[1:] for sublist in 返回列表], emb_api_url, emb_api_key, emb_model, emb_max_token, emb_max_batch, emb_max_workers, emb_file_name, emb_file_path)
    return 返回列表

def 翻译语言文件(
    file0: str, output_path: str,
    llm_api_url: str, llm_api_key: str, llm_model: str,
    emb_api_url: str, emb_api_key: str, emb_model: str,
    file1: str = "",
    language: str = "简体中文",
    emb_max_token: int = 512, emb_max_batch: int = 2147483647, emb_max_workers: int = 16,
    emb_file_name: str = "vectors", emb_file_path: str = ".",
    llm_system_prompt: list = [], llm_prompt_location: str = "system", llm_contexts: bool = False,
    llm_max_workers: int = 3, llm_max_batch: int = 1,
    llm_t: float = 0.65, llm_p: float = 0.7, llm_k: int = 50,
    index_max_workers: int = 128, index_k: int = 3,
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
        for index, index1 in enumerate(可翻译源文件):
            if index1 not in 参考文件:
                去翻译列表.append(参考文件[index])
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
        llm_contexts=llm_contexts, llm_max_workers=llm_max_workers, llm_max_batch=llm_max_batch,
        llm_t=llm_t, llm_p=llm_p, llm_k=llm_k,
        index_max_workers=index_max_workers, index_k=index_k
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
    
            
            
    
    
    
if __name__ == "__main__":
    start_time = time.time()
    with open("output.lang", "r", encoding="utf-8") as f:
        参考词 = [line.split('=', 1) for line in f.read().strip().splitlines()]
    参考词预处理(参考词, "http://127.0.0.1:25564/v1/embeddings", "", "text-embedding-nomic-embed-text-v1.5-embedding", 2048)
    翻译语言文件(r"C:\Users\FengMang\Desktop\Translator Minecraft\en_US.lang", "abab.json",
        "http://127.0.0.1:25564/v1/chat/completions", "", "hy-mt1.5-7b",
        "http://127.0.0.1:25564/v1/embeddings", "", "text-embedding-nomic-embed-text-v1.5-embedding",
        r"dtyhmdfgngnrf.lang")
    """
    
    with open("en_US.lang", "r", encoding="utf-8") as f:
        lines = f.read().splitlines()
        有效行 = []
        for line in lines:
            stripped = line.strip()
            if not stripped or stripped.startswith('#') or stripped.startswith('//'):
                continue
            有效行.append(line)
        阿巴阿巴 = [line.split('=', 1) for line in '\n'.join(有效行).strip().splitlines()]
    阿巴阿巴 = 翻译语言文件(阿巴阿巴,
        "http://127.0.0.1:25564/v1/embeddings", "", "text-embedding-nomic-embed-text-v1.5-embedding",
        "http://127.0.0.1:25564/v1/chat/completions", "", "hy-mt1.5-7b", llm_contexts=False)"""
    #print(阿巴阿巴)
    #参考词预处理(参考词, "http://127.0.0.1:25564/v1/embeddings", "", "text-embedding-nomic-embed-text-v1.5@f32", 2048, 100000, 16)
    #print(文本生成向量(["hello world", "abcd"], "http://127.0.0.1:25564/v1/embeddings", "", "text-embedding-all-minilm-l6-v2-embedding"))
    #LM生成交互(["测试"], "输出20个项，都要是中文", "http://127.0.0.1:25564/v1/chat/completions", "", "qwen3-30b-a3b-instruct-2507")
    #LLM生成交互(["测试啊哈哈哈哈哈哈哈哈哈哈哈哈哈哈哈哈哈"], "输出20个项，都要是中文", "http://127.0.0.1:25564/v1/chat/completions", "", "qwen3-30b-a3b-instruct-2507")
    print(time.time() - start_time)
    
            
