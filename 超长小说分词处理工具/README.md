# 超长小说分词处理工具
超长小说分词处理工具 是一个为大批量文本进行分词的一个工具。<br/>
其内部包含 分词 模拟器必剪文本脚本 *视频合并 工具。<br/>
推荐使用模型：Qwen3-Plus。<br/>
测试版不代表最总品质。



<img width="1282" height="752" alt="image" src="https://github.com/user-attachments/assets/6c5512a8-c100-4c59-8a8c-02ec1f8870b9" /><br/>
<img width="1252" height="661" alt="f7842c91ce0165c94f6204bfafa8f534" src="https://github.com/user-attachments/assets/5d2c66f9-2358-45d8-8098-a12d681dd694" /><br/>
<img width="556" height="772" alt="image" src="https://github.com/user-attachments/assets/6f54fbeb-3969-48e9-be1f-5dc53b04e004" /><br/>
[《意外变故：我成福瑞了??!》第19篇——上山](https://www.bilibili.com/opus/1125448299663327270)版权归[莱阳航天](https://space.bilibili.com/3537122694793391)所有。


## 使用
### 分词器设置
#### 文件路径
- 文件路径填写文本文档文件路径；
#### 分词字数
- 这个参数并不是一次给 AI 输入多少文本。
- x默认为0，y默认为1；
- 从 x 到 分词符号乘y 检索 分词符号，如果没检索到符号则x-1，直到找打符号，如果还是没找到那就从 x+分词符号 然后 x 到 分词符号乘y，如果没检索到符号则 x-1 循环往复。
#### 分词下一个符号
- 我也忘了做什么的，反正就是有用。

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
- Pico （RP2040）
![2b179b3cb3fa99a30e6f96df3bcc17e3_720](https://github.com/user-attachments/assets/535574c0-8774-401f-82b5-10d06d97b522)

#### 安装
1. 下载[MicroPython](https://micropython.org/download/RPI_PICO)，把.uf文件扔到开发板根目录，然后等一会儿；
2. 下载[Adafruit_CircuitPython_HID](https://github.com/adafruit/Adafruit_CircuitPython_HID)，把adafruit _hid整个文件夹扔到开发板的lib目录；
3. 下载这里的 code.py，然后扔到根目录。

### 日志
#### 八月中旬
- 创建 main4_2.py；
- 添加 稍微可用的纠错算法；
- 添加 脚本功能。
