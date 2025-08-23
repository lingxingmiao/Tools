<p align="center"><img width="96" height="96" alt="image" src="https://github.com/user-attachments/assets/5c5f8e4f-a64e-4925-aa9a-6e3ab62322f0" /></p>

# Translator Lang

Translator Lang 是一个用来翻译.lang格式与.json格式的翻译工具。

Translator Lang 初衷是用来给光影包翻译的，最早的版本只能翻译.lang和.json，并且纯AI写BUG连连。

## 文件列表

### main/main3_1

翻译核心文件（.lang/.json）
<p align="center"><img width="1282" height="752" alt="image" src="https://github.com/user-attachments/assets/9029434c-ce7f-4c29-b1ea-01a6fc923fad" /></p>

## 如何使用

### 前提紧要
- 必须填入 API URL 以及 模型名称，否则程序无法运行！！！
- API ULR 必须是大语言模型！！
- 可直接填写 API URL 或者从配置文件读取 API URL 以及相关数据。

### 翻译相关配置
#### 系统提示词
- 下拉框内容来源于程序目录下的 system_prompt 文件夹里面的 Text源文件；
#### 翻译配置内
1. ##### 启用上下文
- 顾名思义，启用大语言模型的上下文功能。
2. ##### 启用键值输入
- 在翻译该 键值对 的时候从 系统提示词 中加入 键。
- 可以有效防止无上午的情况。
3. ##### 启用思考
- 启用大语言模型的思考功能，启用以及禁用都需要模型的支持。
- 目前采用在 系统提示词 前面加入 /no_thinking Reasoning: Low 等。
- 后面的数字框用于 GPT-OSS 模型，值越高，思考等级越高。
4. ##### 快速提示词
- 功能类似于 RAG 功能。
- 但考虑到 RAG 还需要一个嵌入式模型所以使用匹配文本相似度方法（好吧其实是我RAG功能不会做）。
- 程序会先检测当前 键值对 中的 值 与 系统提示词内的 值进行匹配，相似度越高，就越靠前。
- 数字框为匹配输入 键值对 中的 值 的个数，一般情况 1-2 之间尚可。
- 关闭该功能会将整个 系统提示词文件 输入到 系统提示词！

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
    "api_config": [
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
            "apiurl": "https://api.minimaxi.com/", #MiNiMax的另一个API没做兼容 “https://api.minimaxi.com/v1/text/chatcompletion_v2” 之前想做兼容的（json在加一个项），但是想了想又没做，一般API不会这么抽象
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

### main2/main3_2

提示词合并工具，输入en_us与xx_xx来合并提示词（.lang）

#### 更新日志

##### 7月

- 新增 关闭相似度检测按钮。

### main3/main3_3

键值检索工具，用来检索哪个文件缺少键值（.lang）

### main4/main3_4

整理工具，使用一个模板来整理键值排序（.lang）
