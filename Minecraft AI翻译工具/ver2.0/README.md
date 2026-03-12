# Translator Minecraft
Translator Minecraft 是 Translator Lang 的神经续作（第一个版本维护不动了）。
## 功能
### 移植
- 翻译 lang 与 json 格式的语言文件
- 翻译 zip 资源包、光影包 与 jar 模组
- RAG检索 EM-2P
- 并发并行向量生成 与 并发翻译生成
- 导出数据集功能
### 否决
- 推测解码
- 思考等级

# 推荐配置
- 中央处理器：CPU-Z多核3000分以上的64位处理器
- 计算加速器：NVIDIA支持CUDA Toolkit 12.0的Maxwell以上架构 8GB内存（非必须）
- 内存：4GB（按向量大小）
- 存储：4GB（按向量大小）

## 编译/环境设置
```powershell
conda create -n Translator_Minecraft python=3.12 -y
conda activate Translator_Minecraft
pip install numpy faiss-cpu tqdm requests pyhocon
# 向量处理 向量索引 进度显示* 网络请求* FTB任务snbt编解码
pip install -U "sentence-transformers[onnx]" # 或 pip install -U "sentence-transformers[onnx-gpu]"
pip install einops
pip install uninstall torch
pip install torch==2.9.1 torchvision==0.24.1 torchaudio==2.9.1 --index-url https://download.pytorch.org/whl/cu128
# 内置向量生成
conda install anaconda::cupy
# 向量处理加速

pip install pyinstaller
pyinstaller -w --hidden-import=requests "TranslatorGui.py"

conda deactivate
conda env remove -n Translator_Minecraft
```
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

### Release.1.2 Bata.1
- 添加 自动汉化更新 的 I18n词典 导入参考词功能（[Dict-Mini.json](https://github.com/CFPATools/i18n-dict)）
- 添加 向量索引缓存功能（SHA3-256校验 .pkl 与 .npy 文件，生成 .faiss-sha3 与 .faiss 文件）
- 更改 向量存储的格式从 .npy 改为 .npz，格式可选:
    - Float32
    - Float16_S1M15
    - Uint8+Float16
    - Uint4+Float16
- 修复 FTBQ 与 BQ 任务翻译无法传入的问题
- 删除 额外依赖 ujson

### Release.1.2 Bata.2
- 修复 单次多词 翻译键值映射问题
- 更改 单次多词 格式

### Release.1.2
- 添加 已安装的整合包翻译支持 ×
- 添加 GUI（纯AI编写）
- 更改 分离Argparse

### Release.1.3 Bata.1
- 大量修改传入方式
- 添加 IndexRefineFlat 方法
- 添加 翻译资源文件 单文件传入键值自动补全
- 添加 模糊匹配语言代码
- 添加 日志功能（目前只有 翻译资源文件、翻译语言文件、生成翻译 有写入日志）
- 更改 向量存储的格式从 Int4/8 量化的 块缩放 格式从 Float16 改为 Float16_S1M15：
    - Uint8+Float16_S1M15(99.99827147%)
    - Uint4+Float16_S1M15(99.49955940%)
- 修复 GUI 开始多文件无法传入（忘写了）

### Release.1.3 Bata.2（便秘中）
开始便秘，随机添加一些构思功能
- 添加 翻译解析/向量生成 错误重试功能
- 添加 CuPy 加速支持
- 添加 SentenceTransformer 自动加载模型（ONNX、Safetensors）
- 添加 更改 单个词语 翻译为 字符串 而不是 列表
- 添加 I18n词典 导出 数据集 功能（[Dict-Mini.json](https://github.com/CFPATools/i18n-dict)）
- 添加 分离语言文件更新 与 合并语言文件更新（手动翻译使用）
- 添加 翻译缓存替换，并支持 I18n词典 导入（[Dict-Mini.json](https://github.com/CFPATools/i18n-dict)）（未完成）
- 添加 向量存储格式:
    - Float16
    - BFloat16
    - Uint6+Float16_S1M15
    - Uint3+Float16_S1M15
    - Uint2+Float16_S1M15
- 修复 Json 语言文件解析错误
- 修复 单次多词 参考词仅传入一个的问题
- 修复 增加向量 时发生的错误
- 修改 拆分 Config 类与 Quantization 类到两个新的文件
- 修改 Lib 部分函数分离至一个新的文件（Module） 
- 修改 翻译资源文件 合并至 翻译语言文件
- 删除 Lib函数 删除 导出数据集 函数


| RMSE/余弦相似度损失 | [-1, 1] | [-32, 31] | [-131072, 131071] | 压缩率 | 原生支持 |
| - | - | - | - | - | - |
| Float32 | 0/0 | 0/0 | 0/0 | 1:1 | √ |
| Float16 | 1.07E-4/0 | 3.41E-5/0 | inf/nan | 2:1 | √ |
| BFloat16 | 1.3E-3/1E-6 | 5.46E-2/1E-6 | 223.45/1E-6 | 2:1 | × |
| Float16_S1M15 | 9E-6/0 | inf/nan | inf/nan | 2:1 | × |
| Uint8+Float16_S1M15 | 2.32E-3/8E-6 | 7.11E-2/8E-6 | 7.56E+4/1.2E-4 | 3.88:1 | × |
| Uint6+Float16_S1M15 | 9E-3/1.2E-4 | 0.32/1.35E-4 | 7.57E+4/2.31E-4 | 5.12:1 | × |
| Uint4+Float16_S1M15 | 3.76E-2/2.1E-3 | 12.18/2.21E-3 | 7.57E+4/2.21E-3 | 7.53:1 | × |
| Uint3+Float16_S1M15 | 8.1E-2/9.37E-3 | 16.41/9.48E-3 | 7.57E+4/9.48E-3 | 9.85:1 | × |
| Uint2+Float16_S1M15 | 0.19/4.37E-2 | 17.56/4.37E-2 | 7.57E+4/4.37E-2 | 14.22:1 | × |

