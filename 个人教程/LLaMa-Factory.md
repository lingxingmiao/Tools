原始协议：Apache-2.0 license

# LLaMa-Factory
- 本教程截取 https://zhuanlan.zhihu.com/p/695287607 https://github.com/hiyouga/LLaMA-Factory/blob/main/README_zh.md
- 以防以后的自己看不懂所写的

1. 安装虚拟环境以及Git<br>
- 虚拟环境Miniconda：`https://www.anaconda.com/download/success`<br>
- Git：`https://git-scm.com/downloads/win`<br>
2. 添加环境变量<br>
- 右键计算机→属性→设置右边或者下边的高级系统设置→在系统属性选择高级→在高级底部选择环境变量→在环境变量中找到系统变量中选择Path点编辑→右边点新建→添加以下内容<br>
- `C:\ProgramData\miniconda3`<br>
- `C:\ProgramData\miniconda3\Scripts`<br>
- `C:\ProgramData\miniconda3\Library\bin`<br>
- 恭喜你完成环境变量安装了<br>
3. 安装LLaMa-Factory<br>
- 打开开始菜单（Win键）→在 W 那一栏找到 Windows PowerShell 选→打开它<br>
- 选择一个你喜欢的目录：`cd <路径>`<br>
- 复制LLaMa-Factory到自己的电脑上：`git clone https://github.com/hiyouga/LLaMA-Factory.git`<br>
- 创建虚拟环境：`conda create -n llama_factory python=3.10`<br>
- 进入虚拟环境：`conda activate llama_factory`<br>
- 进入LLaMa-Factory目录：`cd LLaMA-Factory`<br>
- 安装LLaMa-Factory需要的第三方库：`pip install -e '.[torch,metrics]'`<br>
- 重新安装需要的第三方库：`pip uninstall torch torchvision torchaudio` `pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu126`<br>
- 检测刚刚安装的第三方库：`python -c "import torch; print(torch.cuda.is_available())"` 输出True就是没有问题的<br>
非必要别用：
- 退出虚拟环境：`conda deactivate`
- 删除虚拟环境：`conda remove -n LLaMA-Factory --all`
4. 启动微调
- 下载需要微调的模型
- 比如我要下载 [Qwen2.5-3B](https://hf-mirror.com/Qwen/Qwen2.5-3B) 这个网站右边有一个大大的蓝色按钮，旁边有竖着的三个点，点他，点Clone repository，然后HTTPS找到第二行 `git clone https://hf-mirror.com/Qwen/Qwen2.5-3B`，执行这个就可以下载了
- 你现在应该在LLaMa-Factory环境中的LLaMa-Factory目录里面，它会复制到LLaMa-Factory文件夹里的Qwen2.5-3B文件夹
- 然后打开 WebUI：`llamafactory-cli webui`
- 填写 模型路径 模型名称 数据文件夹的路径 和数据集，（是否使用混合精度训练）这个是坑小心点 有的显卡不支持bf16就选fp16还不行就选fp32，有些显卡fp32性能比fp16好就用fp32
- 然后就可以直接开始了，最左边第一个按钮可以生成PowerShell用的命令，橘色的按钮可以直接开始
5. 模型合并导出
<pre style="white-space: pre-wrap; word-wrap: break-word;">
llamafactory-cli export `
    --model_name_or_path Qwen/Qwen2.5-3B ` #这里填Hugging Face路径
    --adapter_name_or_path ./saves/Qwen2.5-3B/lora/sft  ` 这里填刚才微调模型工作区路径
    --template qwen ` #这里是模板，用通义千问就填 qwen 用llama3 就填 llama3
    --finetuning_type lora `
    --export_dir megred-model-path ` #这是输出文件夹，就是在当前文件夹下创建一个叫megred-model-path的文件夹
    --export_size 2 `
    --export_device cpu `
    --export_legacy_format False
</pre>
6. 转换GGUF
- 复制llama.cpp到电脑上：`git clone https://github.com/ggerganov/llama.cpp.git`
- 进入安装第三方库的文件夹：`cd llama.cpp/gguf-py`
- 安装第三方库：`pip install --editable .`
- 安装完回到是一个文件夹：`cd ..`
- 转换成GGUF：`python convert_hf_to_gguf.py megred-model-path` #megred-model-path是刚才合并导出的路径




