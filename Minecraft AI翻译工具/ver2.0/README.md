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
### 以后做的功能
- 滚木
## 如何使用
安装 `pip install faiss-cpu` 以及 `pip install numpy`
<pre><code class="language-python">if __name__ == "__main__":
    翻译资源文件(r"C:\Users\FengMang\Desktop\Translator Minecraft\zbgt-0.16.2.jar",
        "http://127.0.0.1:25564/v1/chat/completions", "", "千问3-30b-a3b-动态量化-iq3_m",
        "http://127.0.0.1:25564/v1/embeddings", "", "text-embedding-nomic-embed-text-v1.5-embedding")
    
    导出数据集("Alpaca")
    
    导入参考词("http://127.0.0.1:25564/v1/embeddings", "", "text-embedding-nomic-embed-text-v1.5-embedding")</code></pre>
## API来源
通用/英伟达/AMD：[LM Studio](https://lmstudio.ai/)
英特尔：[Ollama](https://zhuanlan.zhihu.com/p/29653307917)
#### 推荐模型
##### 嵌入模型
- [NomicEmbed文本嵌入v2专家混合8*227M 768维](https://hf-mirror.com/nomic-ai/nomic-embed-text-v2-moe-GGUF/tree/main)（推荐 Q8_0 Q4_K_S，缺点只支持 512 Tokens）（Q8_0 参考速度：133）
- [NomicEmbed文本嵌入v1.5 33M 768维](https://hf-mirror.com/nomic-ai/nomic-embed-text-v1.5-GGUF/tree/main)（推荐 F16，非常平衡，最推荐的一个）（F16 参考速度：108）
- [通义千问嵌入0.6B 1024维](https://hf-mirror.com/Casual-Autopsy/Qwen3-Embedding-0.6B-GGUFs/tree/main)（推荐 Q4_K_S，这个上下文长度巨吃显存）（Q4_0 参考速度：137）
##### 翻译模型
- [通义千问3 80B-A3B](https://hf-mirror.com/unsloth/Qwen3-Next-80B-A3B-Instruct-GGUF/tree/main)（我V100 16G显存不够我用的 UD-IQ2_XXS）（UD-IQ2_XXS 参考速度：7.3+ Tokens）
- [通义千问3 30B-A3B](https://hf-mirror.com/mradermacher/Qwen3-30B-A3B-Instruct-2507-i1-GGUF/tree/main)（推荐 IQ3_M，还算不错）（IQ3_M 参考速度：50+ Tokens）
- [通义千问2.5 14B](https://hf-mirror.com/Mungert/Qwen2.5-14B-Instruct-1M-GGUF/tree/main)（推荐 Q5_K_S IQ3_M，这个一直很稳定的，但是费电，显存不够用这个）（F16-Q4 参考速度：47+ Tokens）
## 编译
<pre><code class="language-PowerShell">conda create -n Translator_Minecraft python=3.12 -y
conda activate Translator_Minecraft
pip install pyinstaller numpy faiss-cpu tqdm requests
pyinstaller -F --hidden-import=requests "TranslatorLib Release.1.py"
conda deactivate
conda env remove -n Translator_Minecraft
</code></pre>
