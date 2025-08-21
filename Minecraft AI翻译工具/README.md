<p align="center"><img width="96" height="96" alt="image" src="https://github.com/user-attachments/assets/5c5f8e4f-a64e-4925-aa9a-6e3ab62322f0" /></p>

# Translator Lang

Translator Lang 是一个用来翻译.lang格式与.json格式的翻译工具；

Translator Lang 默认使用LM Studio软件作为API。

## 文件列表

### main/main3_1

翻译核心文件（.lang/.json）
<p align="center"><img width="1282" height="752" alt="image" src="https://github.com/user-attachments/assets/69b597b5-bf54-4fff-bd08-a7786f20d6e5" /></p>

#### 更新日志

##### 3月

- 创建该文件。

##### 7月

- 修复 API Ked 无法使用的问题；
- 修复 正在翻译 进度在结尾总是少1的问题；
- 改进 GUI内输出格式；
- 改进 翻译失败后重试；
- 添加 模型列表 刷新功能；
- 添加 键值输入 功能；
- 添加 v1模式 功能；
- 移除 模型介绍；
- 移除 最大上下文。

##### 8月

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

##### 下次

- 修复 部分 暂停翻译 导致的BUG；
- 改进 GUI界面布局；
- 改进 API Key 以及 模型名称 可以从配置文件自动选择；
- 添加 词条翻译耗时 功能；
- 添加 预计耗时 与 剩余时长 功能；
- 添加 思考等级 功能（用于兼容GPT-OSS）；
- 添加 系统提示词选择 功能；
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
