# 超长小说分词处理工具
超长小说分词处理工具 是一个为大批量文本进行分词的一个工具。<br/>
其内部包含 分词 模拟器必剪文本脚本 语音字幕生成 工具。<br/>
推荐使用分词使用语言模型：Qwen3-Plus、Qwen3-Max<br/>
推荐（唯一）使用语音合成模型：Index TTS v2.0
测试版不代表最终品质。



<img width="1282" height="752" alt="image" src="https://github.com/user-attachments/assets/6c5512a8-c100-4c59-8a8c-02ec1f8870b9" /><br/>
<img width="1252" height="661" alt="f7842c91ce0165c94f6204bfafa8f534" src="https://github.com/user-attachments/assets/5d2c66f9-2358-45d8-8098-a12d681dd694" /><br/>
<img width="1282" height="752" alt="image" src="https://github.com/user-attachments/assets/63ec820f-b119-4723-9a6e-445649d58484" /><br/>
图2 [《意外变故：我成福瑞了??!》第19篇——上山](https://www.bilibili.com/opus/1125448299663327270)版权归[莱阳航天](https://space.bilibili.com/3537122694793391)所有。


## 使用
### 分词器
#### 文件路径
- 文件路径填写文本文档文件路径；
#### 分词字数
- 这个参数并不是一次给 AI 输入多少文本。
- x默认为0，y默认为1；
- 从 x 到 分词符号乘y 检索 分词符号，如果没检索到符号则x-1，直到找打符号，如果还是没找到那就从 x+分词符号 然后 x 到 分词符号乘y，如果没检索到符号则 x-1 循环往复。
#### 分词下一个符号
- 我也忘了做什么的，反正就是有用。
<br/><br/>
### 视频字幕生成
#### 语音生成API配置
##### API URL
- 填入 Index TTS v2.0 整合包的 API 地址（Gradio）
##### 参考音频
- Index TTS v2.0 使用的参考音频
#### 文件配置
##### 文件路径
- 填入由 分词器 生成的 JSON文件
#### 模型设置
- 参考 Gradio Web UI 中的设置。
- 描述：束数 控制质量，值为 6 是需要 16G 显卡内存
#### 导出设置
##### 输出路径
- 字面意思，输出路径，选择一个输出文件夹，SRT文件 与 WAV文件 会生成在次路径下
##### 输出名称
- 字面意思，控制 SRT文件 与 WAV文件 的名称，不填会变成滚木
#### 处理设置
##### 并行处理
- 一次生成 JSON文件 中值的数量
- 1 为字幕百分比与音频对其
- 2 为 1 的加速方法（平均加速55%），
- 测试：空隙纠错量 为 [3] 的情况下平均错误率小于 [6%]
##### 空隙纠错量
- 并行处理 为 2 是查找 JSON文件 第一个值以及第二个值的分割位置
- 值过大可能导致性能不佳与字幕位置错误
- 值过小可能导致字幕位置错误（没有）
<br/><br/>
### 脚本
#### 文件路径
- 文件路径填写分词器输出的output_x.json文件；
#### 新增页位置
- 这个选择 电脑模拟器上的必剪 文字视频 文字编辑 右下角的 新增页位置（我用PixPin获取的位置）；
#### 模拟器位置
- 顾名思义，这里填模拟器窗口位置；
#### 张贴硬件端口
- 这个是在 Ctrl+V 文本时使用的硬件端口（我用Thonny获取的端口）。

### 硬件需要
- Pico （RP2040）（庆祝我烧了两块板子）
#### 安装
1. 下载[MicroPython](https://micropython.org/download/RPI_PICO)，把.uf文件扔到开发板根目录，然后等一会儿；
2. 下载[Adafruit_CircuitPython_HID](https://github.com/adafruit/Adafruit_CircuitPython_HID)，把adafruit _hid整个文件夹扔到开发板的lib目录；
3. 下载这里的 code.py，然后扔到根目录。

### 日志
#### 十月中旬
- 创建 main4_2.py；
- 添加 稍微可用的纠错算法；
- 添加 脚本功能。
#### 下次
- 添加 音频字幕生成。
