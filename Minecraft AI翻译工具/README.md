# MinecraftAl翻译工具

MinecraftAl翻译工具 是一个用来翻译.lang格式与.json格式的翻译工具；

MinecraftAl翻译工具 默认使用LM Studio软件作为API。

## 文件列表

### main/main3_1

翻译核心文件（.lang/.json）

#### 更新日志

##### 3月

- 创建该文件。

##### 7月

- 修复 API Ked无法使用；
- 修复 正在翻译 进度在结尾总是少1；
- 更改 GUI内输出格式；
- 更改 翻译失败后重试；
- 新增 键值输入 功能；
- 新增 v1模式 功能；
- 删除 模型介绍；
- 删除 最大上下文。

main2/main3_2

提示词合并工具，输入en_us与xx_xx来合并提示词（.lang）

main3/main3_3

键值检索工具，用来检索哪个文件缺少键值（.lang）

main4/main3/4

整理工具，使用一个模板来整理文件排序（.lang）
