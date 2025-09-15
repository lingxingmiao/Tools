<p align="center"><img width="96" height="96" alt="image" src="https://github.com/user-attachments/assets/5c5f8e4f-a64e-4925-aa9a-6e3ab62322f0" /></p>

# Translator Lang

Translator Lang 是一个用来翻译.lang格式与.json格式的翻译工具。

Translator Lang 对于 LMStudio API 有完整的兼容性。

## 文件列表

### main/main3_1

翻译核心文件（.lang/.json）
<p align="center"><img width="1282" height="752" alt="image" src="https://github.com/user-attachments/assets/57179691-160a-4147-aed4-a48f3f09b19e" /></p>
<p align="center"><img width="1282" height="752" alt="image" src="https://github.com/user-attachments/assets/8f8497b7-10a2-4784-82b8-dfbaa0c99c4b" /></p>
<p align="center"><img width="1282" height="752" alt="image" src="https://github.com/user-attachments/assets/609f272a-b8c3-44ef-a93e-7115a5a1dcba" /></p>


## 如何使用

### 前提紧要
- 必须在第一个 API URL 填入大语言模型；
- 如果启用 RAG 功能，则必须在第二个 API URL 填入嵌入模型。

### 翻译相关配置
#### 系统提示词
- 下拉框内容来源于程序目录下的 system_prompt 文件夹里面的 Text源文件；
#### 翻译配置内
1. ##### 翻译过的键值相关
- 记录翻译过的值；并在下一次翻译直接读取上一次的值并添加上下文而不进行翻译，适用于 着色器包（可能重复的内容） 或新旧版本的 Jar模组（先前翻译）。
- 替换翻译过的键值——查找 original-translated-value.json 有没有先前启用 记录翻译过的键值 的内容，如果值匹配就会直接替换。
- 记录翻译过的键值——记录翻译的内容，以便下次启用 替换翻译过的键值 来跳过词条。
2. ##### 启用上下文
- 顾名思义，启用大语言模型的上下文功能。
3. ##### 启用键值输入
- 在翻译该 键值对 的时候从 系统提示词 中加入 键。
- 可以有效防止无上午的情况。
4. ##### 启用思考
- 启用大语言模型的思考功能，启用以及禁用都需要模型的支持。
- 目前采用在 系统提示词 前面加入 /no_thinking Reasoning: Low 等。
- 后面的数字框用于 GPT-OSS 模型，值越高，思考等级越高。
5. ##### 快速提示词
- 有 检索增强生成（RAG） 和 系统提示词检索 两种模式。
- 检索增强生成（RAG）适合有嵌入模型或者想获得更高翻译质量的用户；
- 系统提示词检索 适合手头紧张（电脑性能不足）的用户。
6. ##### Temperature
- 该值会直接传入API。
- 低的值输出较为严谨，高的值较为奔放。
- 不建议该值超过 0.6。
7. ##### Top_p
- 该值会直接传入API。
- 低的值输出较为死板，高的值会发癫，
- 不建议该值超过 0.95。
8. ##### 推测编码
- 该值会直接传入API。
- 填入一个比主模型小的模型可以有效提升速度；
- 但是可能导致质量下降。
- Qwen3-2504 与 Qwen-2507 不兼容。
9. ##### 检索增强生成选择
- 需要启用 快速提示词 并且模式为 检索增强生成（RAG）。
- 格式：<提示词名称>——<嵌入模型名称>.npy   <.npy文件大小>。
- .npy文件大小会影响输出质量。
- 如果没有发现与嵌入模型匹配的文件会重新以 16并行（Min.4 Max.1024） 重新生成。

### 文件配置
#### 翻译Lang格式语言文件
- 填写 待处理文件路径 即可开始翻译；
- 稍后会自动保存（覆盖写入）至原文件。
#### 翻译Json格式语言文件
- 填写 待处理文件路径 即可开始翻译；
- 稍后会自动保存（覆盖写入）至原文件。
#### 翻译Zip格式光影包
1. #### 仅翻译Zip格式光影包
- 填写 待处理文件路径 开始翻译即可；
- 如果已有 zh_cn.lang 会比较 en_us.lang 是否有缺失的键值，否则直接退出翻译；
- 翻译完成后会直接覆盖写入 新版本文件。
2. #### 合并翻译Zip光影包
- 填写待处理文件路径（旧的）与 新版本文件路径（新的）即可开始翻译（反过来会炸）；
- 程序首先会检测新的光影包里的 en_us.lang 文件与旧的 zh_cn.lang 文件进行比较；
- 如果新的 zh_cn.lang 包含了 en_us.lang 所有的键值会直接退出翻译，如果旧的光影包在 zh_cn.lang 里面缺少键值会比较新的 en_us.lang 然后仅翻译新增的键值；
- 翻译完成的 zh_cn.lang 会与新的 en_us.lang 进行排序，以便维护；
- 翻译完成后会直接覆盖写入 新版本文件。
#### 翻译Jar格式模组
1. #### 仅翻译Jar格式模组
- 填写 待处理文件路径 开始翻译即可；
- 如果已有 zh_cn.lang/.json 会比较 en_us.lang/.json 是否有缺失的键值，否则直接退出翻译；
- 翻译完成后会直接覆盖写入 新版本文件。
1. #### 合并翻译Jar格式模组
- 填写待处理文件路径（旧的）与 新版本文件路径（新的）即可开始翻译（反过来会炸，我不说是谁更新的版本删除了 zh_cn.json）；
- 程序首先会检测新的模组里的 en_us.lang/.json 文件与旧的 zh_cn.lang/.json 文件进行比较；
- 如果新的 zh_cn.lang/.json 包含了 en_us.lang/.json 所有的键值会直接退出翻译，如果旧的模组在 zh_cn.lang/.json 里面缺少键值会比较新的 en_us.lang/.json 然后仅翻译新增的键值；
- 翻译完成的 zh_cn.lang 会与新的 en_us.lang 进行排序，以便维护；
- 翻译完成后会直接覆盖写入 新版本文件。

### 配置文件
- 配置文件是用来存储密钥、API URL以及模型名称的主要方式。
#### 格式
- 以下内容非标注Json格式：
<pre style="white-space: pre-wrap; word-wrap: break-word;">
{
    "api_config": [ #这里是翻译模型（LLM）的API
        {
            "apiurl": "http://127.0.0.1:1234/", #这里是API URL
            "name": "LMStudio", #这里是提供商的名称
            "model_search": true, #这里是模型名称下拉框是否由API提供，关的话要加"model_list": []
            "v1_mode": true #这里是V1模式的开关，部分API（例如GPT的）需要启用这个功能
        },{
            "apiurl": "http://127.0.0.1:11434/", 
            "name": "Ollama", 
            "model_search": true, 
            "v1_mode": false
        },{
            "apiurl": "https://api.deepseek.com/", 
            "name": "DeepSeek", 
            "model_search": false, 
            "v1_mode": false, 
            "model_list": [
                "deepseek-chat", 
                "deepseek-reasoner"
        ]},{
            "apiurl": "https://api.minimaxi.com/", #MiniMax的另一个API没做兼容 “https://api.minimaxi.com/v1/text/chatcompletion_v2” 之前想做兼容的（json在加一个项），但是想了想又没做，一般API不会这么抽象
            "name": "MiniMax", 
            "model_search": false, 
            "v1_mode": true, 
            "model_list": [
                "MiniMax-M1", 
                "MiniMax-Text-01"
        ]},{
            "apiurl": "https://dashscope.aliyuncs.com/compatible-mode/", #这里是API URL
            "name": "阿里云百炼", #这里是提供商的名称
            "model_search": false, #这里是模型名称下拉框是否由API提供，关的话要加"model_list": []
            "v1_mode": true, #这里是V1模式的开关，部分API（例如GPT的）需要启用这个功能
            "model_list": [ #这里就是模型名称的列表了
                "qwen-max", 
                "qwen-max-latest", 
                "qwen-plus", 
                "qwen-plus-latest", 
                "qwen-flash", 
                "deepseek-r1",
                "deepseek-v3",
                "deepseek-r1-distill-qwen-14b",
                "deepseek-r1-distill-qwen-32b",
                "deepseek-r1-distill-llama-70b",
                "Moonshot-Kimi-K2-Instruct",
                "glm-4.5",
                "glm-4.5-air"
        ]}
    ],
    "api_key": [
        {
          "name": "DeepSeek",  #这里必须和api_config里面的name一致
          "key":"sk-你猜" #这里填密钥
        },{
          "name": "MiniMax",
          "key":"你猜"
        }
    ],
    "api_embedding": [ #这里是嵌入模型的选项，基本与以上相同
        {
            "apiurl": "http://127.0.0.1:1234/", 
            "name": "LMStudio", 
            "model_search": true, 
            "v1_mode": true
        }
    ],
    "api_key_embedding": [
        {
            "name": "阿里云百炼",
            "key": "sk-*************de0dc35fa441ae"
        }
    ],
    "预设": [ #这里存储软件预设
        {
            "name": "aaa",
            "api_config": [
                {
                    "id": "llm_api_url",
                    "value": "https://api.deepseek.com/"
                },
                {
                    "id": "llm_api_key",
                    "value": "sk-*************de0dc35fa441ae"
                },
                {
                    "id": "llm_api_model",
                    "value": "deepseek-chat"
                },
                {
                    "id": "llm_api_v1",
                    "value": false
                },
                {
                    "id": "emb_api_url",
                    "value": "https://dashscope.aliyuncs.com/compatible-mode/"
                },
                {
                    "id": "emb_api_key",
                    "value": "sk-*************e0dc35fa441ae"
                },
                {
                    "id": "emb_api_model",
                    "value": ""
                },
                {
                    "id": "emb_api_v1",
                    "value": true
                }
            ],
            "translator_config": [
                {
                    "id": "context",
                    "on": true
                },
                {
                    "id": "key_value_input",
                    "on": true
                },
                {
                    "id": "reasoning_mode",
                    "on": false,
                    "value": 1
                },
                {
                    "id": "quick_prompt",
                    "on": true,
                    "value": 3,
                    "mode": "检索增强生成"
                },
                {
                    "id": "custom_parameters",
                    "on": true,
                    "temperature": 0.0,
                    "top_p": 0.0
                },
                {
                    "id": "speculative_encoding",
                    "on": false,
                    "model": ""
                }
            ]
        }
    ]
}
</pre>


#### 更新日志

##### 2025年3月

- 创建该文件。

##### 2025年7月

- 修复 API Ked 无法使用的问题；
- 修复 正在翻译 进度在结尾总是少1的问题；
- 改进 GUI内输出格式；
- 改进 翻译失败后重试；
- 添加 模型列表 刷新功能；
- 添加 键值输入 功能；
- 添加 v1模式 功能；
- 移除 模型介绍；
- 移除 最大上下文。

##### 2025年8月初

- 修复 API URL 不正确 模型列表 刷新后依旧显示的问题；
- 修复 API URL 非仅基础地址 模型列表 无法刷新的问题；
- 修复 当前翻译未完成却可以启动下一个翻译的问题；
- 修复 启用上下文 无法使用的问题；
- 修复 无 system_prompt.txt 导致崩溃的问题；
- 改进 将 翻译列表 改为 日志；
- 改进 GUI界面布局；
- 添加 暂停翻译 功能，并添加一些BUG；
- 添加 停止翻译 功能，并添加一些BUG；
- 添加 翻译耗时 提示词处理耗时 提示词比较耗时 功能；
- 添加 软件图标；
- 添加 启用快速提示词 功能；
  - 缓解 API 费用过高；
  - 修复 完整输入错误率过高的问题；
  - 修复 提示词Token数量大于模型Token数量 导致的问题。

##### 2025年8月末

- 修复 部分 暂停翻译 导致的问题；
- 修复 正在翻译 无法检测斜杆的问题；
- 修复 键值输入 可能导致的输出内容包含键值；
- 改进 Json翻译函数；
- 改进 GUI界面布局；
- 改进 API Key 以及 模型名称 可以从配置文件自动选择；
- 改进 键值输入的系统提示词；
- 改进 API URL 下拉框自动刷新列表；
- 添加 Zip格式光影 以及 Jar格式模组 翻译（自动检测zh_cn缺失键值来减少翻译次数）；
- 添加 新版本文件处理 功能（用于与 Zip格式光影 以及 Jar格式模组 结合）；
- 添加 词条翻译耗时 功能；
- 添加 预计耗时 与 剩余时长 功能；
- 添加 思考等级 功能（用于兼容 GPT-OSS ）；
- 添加 系统提示词选择 功能；
- 添加 API名称展示 功能；
- 添加 配置文件 功能（存储密钥以及模型名称）。

##### 2025年9月初

- 修复 下拉框替换 API URL 部分不会替换 API Key 的问题；
- 修复 如果翻译出现错误 剩余时长 依旧会计时的问题；
- 修复 Jar翻译 无法替换 与 重试中... {e} 写反的问题；
- 修复 翻译Jar文件时把 json 格式识别成 lang 格式（下次可能识别成 json）；
- 修复 停止翻译 是 self.translate_lang 返回 列表 导致程序红温的问题；
- 修复 Jar翻译 json 格式覆盖至 en_us.json 的问题；
- 修复 Lang翻译 注释报错的问题；
- 改进 Jar翻译 json 格式不会排序的问题；
- 改进 键值对 中的 值 为空时跳过翻译；
- 改进 翻译配置 性能影响以及质量影响的文本；
- 改进 GUI 启动耗时；
- 添加 Token/S、当前Token数、总计Token数 功能；
- 添加 自定义模型 Temperature Top_p 功能（先前删除的功能，未记录在更新日志）；
- 添加 推测解码 功能（目前仅发现 [LMStudio](https://lmstudio.ai/) 可用使用）；
- 添加 检索增强生成（RAG） 功能（必须启用快速提示词）.

##### 下次

- 修复 嵌入 API URL 更换时 API Key 不会更新的问题；
- 修复 更改 API URL 时非从 API URL 获取模型地址时且模型列表没有填写不会自动替换为空的问题；
- 修复 重新生成向量嵌入完成不会自动选择到新的 .npy 文件导致的 API 报错；
- 修复 检索增强生成选择列表 已有与 嵌入模型 相同的文件，但未选择导致的重新生成；
- 修复 \n 导致等于号离奇失踪；
- 改进 图标从磁盘缓存改为内存缓存；
- 改进 GUI界面布局；
- 添加 预设设置配置文件；
- 添加 替换翻译过的键值的值 与 记录翻译过的键值的值 功能。

### main2/main3_2

提示词合并工具，输入en_us与xx_xx来合并提示词（.lang）

#### 更新日志

##### 7月

- 新增 关闭相似度检测按钮。

### main3/main3_3

键值检索工具，用来检索哪个文件缺少键值（.lang）

### main4/main3_4

整理工具，使用一个模板来整理键值排序（.lang）
