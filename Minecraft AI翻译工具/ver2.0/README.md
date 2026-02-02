# Translator Minecraft
Translator Minecraft 是 Translator Lang 的神经续作（第一个版本维护不动了）。
## 功能
### 移植的功能
- 翻译 lang 与 json 格式的语言文件
- 翻译 zip 资源包、光影包 与 jar 模组
- RAG检索 EM-2P
- 并发并行向量生成 与 并发翻译生成
- 导出数据集功能
### 不做的功能
- GUI
- 推测解码
- 思考等级
## 如何使用
先按照 编译 进行构建
<pre><code class="language-PowerShell">& "TranslatorLib Release.1.exe" TranslatorLang --file0 "en_us.lang" --output-path "zh_cn.json" --llm-api-url "http://127.0.0.1:25564/v1/chat/completions" --llm-model "千问3-30b-a3b-动态量化-iq3_m" --emb-api-url "http://127.0.0.1:25564/v1/embeddings" --emb-model  "text-embedding-nomic-embed-text-v1.5-embedding"

& "TranslatorLib Release.1.exe" TranslatorPack --file0 "zbgt-0.16.2.jar" --llm-api-url "http://127.0.0.1:25564/v1/chat/completions" --llm-model "千问3-30b-a3b-动态量化-iq3_m" --emb-api-url "http://127.0.0.1:25564/v1/embeddings" --emb-model  "text-embedding-nomic-embed-text-v1.5-embedding"
    
& "TranslatorLib Release.1.exe" ExportJsonl --mode "Alpaca"
    
& "TranslatorLib Release.1.exe" ImportPrompt --path "C:\Users\FengMang\Desktop\Translator Minecraft\测试" --emb-api-url "http://127.0.0.1:25564/v1/embeddings" --emb-model "text-embedding-nomic-embed-text-v1.5-embedding"
</code></pre>
TranslatorLang方法 输入 Lang、Json 语言文件 输出 输出路径文件格式 语言文件</br>
TranslatorPack方法 输入 模组、资源包 输出 资源包，输入 光影包 输出 光影包</br>
ImportPrompt方法 导入所有文件夹下的 模组、光影包、Translator Minecraft生成的pkl文件</br>
ExportJsonl方法 导出 ChatML、Alpaca 数据集 来训练模型</br>
TranslatorFTBQ方法 输入 config文件夹下的ftbquests文件夹 输出覆盖原有文件夹，请手动备份</br>
TranslatorBQ方法 输入 config文件夹下的betterquesting文件夹 输出覆盖原有文件夹，请手动备份</br>
ImportPromptI18n方法 输入 [Dict.json](https://github.com/VM-Chinese-translate-group/i18n-Dict-Extender)</br>

## API来源
通用/英伟达/AMD：[LM Studio](https://lmstudio.ai/)
英特尔：[Ollama](https://github.com/ipex-llm/ipex-llm/releases/tag/v2.2.0)
#### 推荐模型
##### 嵌入模型
- [NomicEmbed文本嵌入v2专家混合8*227M 768维](https://hf-mirror.com/nomic-ai/nomic-embed-text-v2-moe-GGUF/tree/main)（推荐 Q8_0 Q4_K_S，缺点只支持 512 Tokens）（Q8_0 参考速度：133）
- [通义千问嵌入0.6B 1024维](https://hf-mirror.com/Casual-Autopsy/Qwen3-Embedding-0.6B-GGUFs/tree/main)（推荐 Q4_K_S，这个上下文长度巨吃显存）（Q4_0 参考速度：137）
##### 翻译模型
- [通义千问3 80B-A3B](https://hf-mirror.com/unsloth/Qwen3-Next-80B-A3B-Instruct-GGUF/tree/main)（我V100 16G显存不够我用的 UD-Q2_K_XL）（UD-Q2_K_XL 砖家权重加载到CPU参考速度：14+ Tokens）
- [通义千问3 30B-A3B](https://hf-mirror.com/mradermacher/Qwen3-30B-A3B-Instruct-2507-i1-GGUF/tree/main)（推荐 IQ3_M，还算不错）（IQ3_M 参考速度：50+ Tokens）
- [通义千问2.5 14B](https://hf-mirror.com/Mungert/Qwen2.5-14B-Instruct-1M-GGUF/tree/main)（推荐 Q5_K_S IQ3_M，这个一直很稳定的，但是费电，显存不够用这个）（F16-Q4 参考速度：47+ Tokens）
## 编译
<pre><code class="language-PowerShell">conda create -n Translator_Minecraft python=3.12 -y
conda activate Translator_Minecraft
pip install pyinstaller numpy faiss-cpu tqdm requests pyhocon ujson orjson
# 构建EXE 向量存储 向量索引 进度显示* 网络请求* FTB任务snbt编解码 .json()优化 I18n词典导入优化
pyinstaller -F --hidden-import=requests "TranslatorLib Release.1.py"
conda deactivate
conda env remove -n Translator_Minecraft
</code></pre>
## 更新日志
### Release.1 Alpha.1
- 添加 语言文件 翻译支持
- 添加 IndexFlatL2方法RAG检索
- 添加 额外依赖 numpy faiss-cpu
### Release.1 Bata.1
- 添加 资源包 翻译支持 （光影，模组，资源包）
- 添加 导出数据集功能
- 添加 导入参考词功能
### Release.1 Bata.2
- 修复 上下文 system 位置
- 修复 系统提示词为 system 时不会添加 user 的问题
- 添加 最大历史上下文
### Release.1
- 添加 文件传入参数 （如何使用 这一栏）
### Release.1.1 Bata.1
- 添加 FTBQ任务 翻译支持
- 更改 IndexFlatL2索引 改为 IndexHNSWSQ索引(SQ8)
- 更改 ThreadPoolExecutor索引并发 改为 Faiss并行
- 添加 额外依赖 pyhocon
### Release.1.1 Bata.2
- ~~修复了一些已知的问题。~~
- 修复 IndexHNSWSQ索引 没有训练就构建的错误
- 添加 BQ任务 翻译支持
- 添加 思考模型支持（仅为强制思考模型做支持）
### Release.1.1
- 修复 翻译语言文件 双文件无法正确处理
- 修复 无法传入上下文开关参数
- 添加 FTB任务 翻译支持 （选定版本 1.12.2 1.20.1）
- 添加 BQ任务 翻译支持 （选定版本 1.7.10 1.12.2）
- 添加 思考模型支持
- 添加 额外依赖 ujson
### Release.1.2 （计划）
- 添加 已安装的整合包翻译支持
- 添加 自动汉化更新 的 I18n词典 导入参考词功能（Dict DictMini） √
- 添加 向量索引缓存功能（SHA3-256校验 .pkl 与 .npy 文件，生成 .faiss-sha3 与 .faiss 文件） √
- 更改 存储的格式从 .npy 改为 .npz，格式可选: √
    - Float32(100%)
    - Float16_S1M15(99.99999237%)
    - Int8+Float16(98.4445%)
    - Int4+Float16(96.8631%)
- 修复 FTBQ 与 BQ 任务翻译无法传入的问题
- 添加 额外依赖 orjson
