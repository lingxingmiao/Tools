import argparse

import TranslatorLib

if __name__ == "__main__":
    解释器0 = argparse.ArgumentParser()
    解释器1 = 解释器0.add_subparsers(dest="mode")
    
    TranslatorLang = 解释器1.add_parser("TranslatorLang", help="翻译语言文件")
    TranslatorPack = 解释器1.add_parser("TranslatorPack", help="翻译资源包文件")
    TranslatorFTBQ = 解释器1.add_parser("TranslatorFTBQ", help="翻译FTBQ任务文件夹")
    TranslatorBQ = 解释器1.add_parser("TranslatorBQ", help="翻译BQ任务文件夹")
    ExportJsonl = 解释器1.add_parser("ExportJsonl", help="导出JSONL数据集文件")
    ImportPrompt = 解释器1.add_parser("ImportPrompt", help="从文件夹里的所有模组光影资源包导入参考词文件")
    ImportPromptDictMini = 解释器1.add_parser("ImportPromptDictMini", help="从I18n Dict_Mini.json导入参考词文件")
    
    TranslatorLang.add_argument("--file0", type=str, required=True, help="输入文件0路径")
    TranslatorLang.add_argument("--output-path", type=str, required=True, help="输出目录路径")
    TranslatorLang.add_argument("--llm-api-url", type=str, required=True, help="LLM API 地址")
    TranslatorLang.add_argument("--llm-api-key", type=str, default="", help="LLM API 密钥")
    TranslatorLang.add_argument("--llm-model", type=str, required=True, help="LLM 模型名称")
    TranslatorLang.add_argument("--emb-api-url", type=str, required=True, help="Embedding API 地址")
    TranslatorLang.add_argument("--emb-api-key", type=str, default="", help="Embedding API 密钥")
    TranslatorLang.add_argument("--emb-model", type=str, required=True, help="Embedding 模型名称")
    TranslatorLang.add_argument("--file1", type=str, default="", help="输入文件1路径")
    TranslatorLang.add_argument("--language", type=str, default="zh_cn", help="语言代码")
    TranslatorLang.add_argument("--emb-max-token", type=int, default=2048, help="Embedding 最大 token 数")
    TranslatorLang.add_argument("--emb-max-batch", type=int, default=2147483647, help="Embedding 最大批大小")
    TranslatorLang.add_argument("--emb-max-workers", type=int, default=16, help="Embedding 最大并发数")
    TranslatorLang.add_argument("--emb-file-name", type=str, default="vectors", help="向量文件名（不含扩展名）")
    TranslatorLang.add_argument("--emb-file-path", type=str, default=".", help="向量文件保存路径")
    TranslatorLang.add_argument("--llm-system-prompt", nargs="*", default=[], help="额外系统提示词列表")
    TranslatorLang.add_argument("--llm-prompt-location", type=str, default="system", help="提示位置(system | user)")
    TranslatorLang.add_argument("--llm-contexts", type=bool, default=True, help="是否启用上下文")
    TranslatorLang.add_argument("--llm-contexts-length", type=int, default=6, help="上下文长度")
    TranslatorLang.add_argument("--llm-max-workers", type=int, default=8, help="LLM 最大并发数")
    TranslatorLang.add_argument("--llm-max-batch", type=int, default=1, help="LLM 最大批大小")
    TranslatorLang.add_argument("--llm-t", type=float, default=0.65, help="采样温度 (temperature)")
    TranslatorLang.add_argument("--llm-p", type=float, default=0.7, help="Top-p 值")
    TranslatorLang.add_argument("--llm-k", type=int, default=50, help="Top-k 值")
    TranslatorLang.add_argument("--index-k", type=int, default=3, help="检索结果数")
    TranslatorPack.add_argument("--file0", type=str, required=True, help="输入文件0路径")
    TranslatorPack.add_argument("--llm-api-url", type=str, required=True, help="LLM API 地址")
    TranslatorPack.add_argument("--llm-api-key", type=str, default="", help="LLM API 密钥")
    TranslatorPack.add_argument("--llm-model", type=str, required=True, help="LLM 模型名称")
    TranslatorPack.add_argument("--emb-api-url", type=str, required=True, help="Embedding API 地址")
    TranslatorPack.add_argument("--emb-api-key", type=str, default="", help="Embedding API 密钥")
    TranslatorPack.add_argument("--emb-model", type=str, required=True, help="Embedding 模型名称")
    TranslatorPack.add_argument("--file1", type=str, default="", help="输入文件1路径")
    TranslatorPack.add_argument("--cache-path", type=str, default="./cache/", help="缓存目录")
    TranslatorPack.add_argument("--output-path", type=str, default="./", help="输出目录路径")
    TranslatorPack.add_argument("--original-language", type=str, default="en_us", help="原始语言代码")
    TranslatorPack.add_argument("--target-language", type=str, default="zh_cn", help="目标语言代码")
    TranslatorPack.add_argument("--emb-max-token", type=int, default=2048, help="Embedding 最大 token 数")
    TranslatorPack.add_argument("--emb-max-batch", type=int, default=2147483647, help="Embedding 最大批大小")
    TranslatorPack.add_argument("--emb-max-workers", type=int, default=16, help="Embedding 最大并发数")
    TranslatorPack.add_argument("--emb-file-name", type=str, default="vectors", help="向量文件名（不含扩展名）")
    TranslatorPack.add_argument("--emb-file-path", type=str, default=".", help="向量文件保存路径")
    TranslatorPack.add_argument("--llm-system-prompt", nargs="*", default=[], help="额外系统提示词列表")
    TranslatorPack.add_argument("--llm-prompt-location", type=str, default="system", help="提示位置(system | user)")
    TranslatorPack.add_argument("--llm-contexts", type=bool, default=True, help="是否启用上下文")
    TranslatorPack.add_argument("--llm-contexts-length", type=int, default=6, help="上下文长度")
    TranslatorPack.add_argument("--llm-max-workers", type=int, default=8, help="LLM 最大并发数")
    TranslatorPack.add_argument("--llm-max-batch", type=int, default=1, help="LLM 最大批大小")
    TranslatorPack.add_argument("--llm-t", type=float, default=0.65, help="采样温度 (temperature)")
    TranslatorPack.add_argument("--llm-p", type=float, default=0.7, help="Top-p 值")
    TranslatorPack.add_argument("--llm-k", type=int, default=50, help="Top-k 值")
    TranslatorPack.add_argument("--index-k", type=int, default=3, help="检索结果数")
    ExportJsonl.add_argument("--mode", type=str, required=True, help="导出格式(ChatML | Alpaca)")
    ExportJsonl.add_argument("--file", type=str, default="dataset.jsonl", help="输出文件路径")
    ExportJsonl.add_argument("--emb-file-name", type=str, default="vectors", help="向量文件名（不含扩展名）")
    ExportJsonl.add_argument("--emb-file-path", type=str, default=".", help="向量文件保存路径")
    ImportPrompt.add_argument("--path", type=str, required=True, help="输入文件夹路径")
    ImportPrompt.add_argument("--emb-api-url", type=str, required=True, help="Embedding API 地址")
    ImportPrompt.add_argument("--emb-api-key", type=str, default="", help="Embedding API 密钥")
    ImportPrompt.add_argument("--emb-model", type=str, required=True, help="Embedding 模型名称")
    ImportPrompt.add_argument("--original-language", type=str, default="en_us", help="原始语言代码")
    ImportPrompt.add_argument("--target-language", type=str, default="zh_cn", help="目标语言代码")
    ImportPrompt.add_argument("--cache-path", type=str, default="./cache/", help="缓存目录")
    ImportPrompt.add_argument("--emb-max-token", type=int, default=2048, help="Embedding 最大 token 数")
    ImportPrompt.add_argument("--emb-max-batch", type=int, default=2147483647, help="Embedding 最大批大小")
    ImportPrompt.add_argument("--emb-max-workers", type=int, default=16, help="Embedding 最大并发数")
    ImportPrompt.add_argument("--emb-file-name", type=str, default="vectors", help="向量文件名（不含扩展名）")
    ImportPrompt.add_argument("--emb-file-path", type=str, default=".", help="向量文件保存路径")
    TranslatorFTBQ.add_argument("--path", type=str, required=True, help="FTB任务文件夹路径")
    TranslatorFTBQ.add_argument("--llm-api-url", type=str, required=True, help="LLM API 地址")
    TranslatorFTBQ.add_argument("--llm-api-key", type=str, default="", help="LLM API 密钥")
    TranslatorFTBQ.add_argument("--llm-model", type=str, required=True, help="LLM 模型名称")
    TranslatorFTBQ.add_argument("--emb-api-url", type=str, required=True, help="Embedding API 地址")
    TranslatorFTBQ.add_argument("--emb-api-key", type=str, default="", help="Embedding API 密钥")
    TranslatorFTBQ.add_argument("--emb-model", type=str, required=True, help="Embedding 模型名称")
    TranslatorFTBQ.add_argument("--language", type=str, default="zh_cn", help="语言代码")
    TranslatorFTBQ.add_argument("--emb-max-token", type=int, default=2048, help="Embedding 最大 token 数")
    TranslatorFTBQ.add_argument("--emb-max-batch", type=int, default=2147483647, help="Embedding 最大批大小")
    TranslatorFTBQ.add_argument("--emb-max-workers", type=int, default=16, help="Embedding 最大并发数")
    TranslatorFTBQ.add_argument("--emb-file-name", type=str, default="vectors", help="向量文件名（不含扩展名）")
    TranslatorFTBQ.add_argument("--emb-file-path", type=str, default=".", help="向量文件保存路径")
    TranslatorFTBQ.add_argument("--llm-system-prompt", nargs="*", default=[], help="额外系统提示词列表")
    TranslatorFTBQ.add_argument("--llm-prompt-location", type=str, default="system", help="提示位置(system | user)")
    TranslatorFTBQ.add_argument("--llm-contexts", type=bool, default=True, help="是否启用上下文")
    TranslatorFTBQ.add_argument("--llm-contexts-length", type=int, default=6, help="上下文长度")
    TranslatorFTBQ.add_argument("--llm-max-workers", type=int, default=8, help="LLM 最大并发数")
    TranslatorFTBQ.add_argument("--llm-max-batch", type=int, default=1, help="LLM 最大批大小")
    TranslatorFTBQ.add_argument("--llm-t", type=float, default=0.65, help="采样温度 (temperature)")
    TranslatorFTBQ.add_argument("--llm-p", type=float, default=0.7, help="Top-p 值")
    TranslatorFTBQ.add_argument("--llm-k", type=int, default=50, help="Top-k 值")
    TranslatorFTBQ.add_argument("--index-k", type=int, default=3, help="检索结果数")
    TranslatorBQ.add_argument("--path", type=str, required=True, help="BQ任务文件夹路径")
    TranslatorBQ.add_argument("--llm-api-url", type=str, required=True, help="LLM API 地址")
    TranslatorBQ.add_argument("--llm-api-key", type=str, default="", help="LLM API 密钥")
    TranslatorBQ.add_argument("--llm-model", type=str, required=True, help="LLM 模型名称")
    TranslatorBQ.add_argument("--emb-api-url", type=str, required=True, help="Embedding API 地址")
    TranslatorBQ.add_argument("--emb-api-key", type=str, default="", help="Embedding API 密钥")
    TranslatorBQ.add_argument("--emb-model", type=str, required=True, help="Embedding 模型名称")
    TranslatorBQ.add_argument("--language", type=str, default="zh_cn", help="语言代码")
    TranslatorBQ.add_argument("--emb-max-token", type=int, default=2048, help="Embedding 最大 token 数")
    TranslatorBQ.add_argument("--emb-max-batch", type=int, default=2147483647, help="Embedding 最大批大小")
    TranslatorBQ.add_argument("--emb-max-workers", type=int, default=16, help="Embedding 最大并发数")
    TranslatorBQ.add_argument("--emb-file-name", type=str, default="vectors", help="向量文件名（不含扩展名）")
    TranslatorBQ.add_argument("--emb-file-path", type=str, default=".", help="向量文件保存路径")
    TranslatorBQ.add_argument("--llm-system-prompt", nargs="*", default=[], help="额外系统提示词列表")
    TranslatorBQ.add_argument("--llm-prompt-location", type=str, default="system", help="提示位置(system | user)")
    TranslatorBQ.add_argument("--llm-contexts", type=bool, default=True, help="是否启用上下文")
    TranslatorBQ.add_argument("--llm-contexts-length", type=int, default=6, help="上下文长度")
    TranslatorBQ.add_argument("--llm-max-workers", type=int, default=8, help="LLM 最大并发数")
    TranslatorBQ.add_argument("--llm-max-batch", type=int, default=1, help="LLM 最大批大小")
    TranslatorBQ.add_argument("--llm-t", type=float, default=0.65, help="采样温度 (temperature)")
    TranslatorBQ.add_argument("--llm-p", type=float, default=0.7, help="Top-p 值")
    TranslatorBQ.add_argument("--llm-k", type=int, default=50, help="Top-k 值")
    TranslatorBQ.add_argument("--index-k", type=int, default=3, help="检索结果数")
    ImportPromptDictMini.add_argument("--file", type=str, required=True, help="输入文件路径")
    ImportPromptDictMini.add_argument("--emb-api-url", type=str, required=True, help="Embedding API 地址")
    ImportPromptDictMini.add_argument("--emb-api-key", type=str, default="", help="Embedding API 密钥")
    ImportPromptDictMini.add_argument("--emb-model", type=str, required=True, help="Embedding 模型名称")
    ImportPromptDictMini.add_argument("--emb-max-token", type=int, default=2048, help="Embedding 最大 token 数")
    ImportPromptDictMini.add_argument("--emb-max-batch", type=int, default=2147483647, help="Embedding 最大批大小")
    ImportPromptDictMini.add_argument("--emb-max-workers", type=int, default=16, help="Embedding 最大并发数")
    ImportPromptDictMini.add_argument("--emb-file-name", type=str, default="vectors", help="向量文件名（不含扩展名）")
    ImportPromptDictMini.add_argument("--emb-file-path", type=str, default=".", help="向量文件保存路径")
    参数 = 解释器0.parse_args()
    if 参数.mode == "TranslatorLang":
        TranslatorLib.翻译语言文件(
            file0=参数.file0,
            output_path=参数.output_path,
            llm_api_url=参数.llm_api_url,
            llm_api_key=参数.llm_api_key,
            llm_model=参数.llm_model,
            emb_api_url=参数.emb_api_url,
            emb_api_key=参数.emb_api_key,
            emb_model=参数.emb_model,
            file1=参数.file1,
            language=参数.language,
            emb_max_token=参数.emb_max_token,
            emb_max_batch=参数.emb_max_batch,
            emb_max_workers=参数.emb_max_workers,
            emb_file_name=参数.emb_file_name,
            emb_file_path=参数.emb_file_path,
            llm_system_prompt=参数.llm_system_prompt,
            llm_prompt_location=参数.llm_prompt_location,
            llm_contexts=参数.llm_contexts,
            llm_contexts_length=参数.llm_contexts_length,
            llm_max_workers=参数.llm_max_workers,
            llm_max_batch=参数.llm_max_batch,
            llm_t=参数.llm_t,
            llm_p=参数.llm_p,
            llm_k=参数.llm_k,
            index_k=参数.index_k
        )
    elif 参数.mode == "TranslatorPack":
        TranslatorLib.翻译资源文件(
            file0=参数.file0,
            llm_api_url=参数.llm_api_url,
            llm_api_key=参数.llm_api_key,
            llm_model=参数.llm_model,
            emb_api_url=参数.emb_api_url,
            emb_api_key=参数.emb_api_key,
            emb_model=参数.emb_model,
            file1=参数.file1,
            cache_path=参数.cache_path,
            output_path=参数.output_path,
            original_language=参数.original_language,
            target_language=参数.target_language,
            emb_max_token=参数.emb_max_token,
            emb_max_batch=参数.emb_max_batch,
            emb_max_workers=参数.emb_max_workers,
            emb_file_name=参数.emb_file_name,
            emb_file_path=参数.emb_file_path,
            llm_system_prompt=参数.llm_system_prompt,
            llm_prompt_location=参数.llm_prompt_location,
            llm_contexts=参数.llm_contexts,
            llm_contexts_length=参数.llm_contexts_length,
            llm_max_workers=参数.llm_max_workers,
            llm_max_batch=参数.llm_max_batch,
            llm_t=参数.llm_t,
            llm_p=参数.llm_p,
            llm_k=参数.llm_k,
            index_k=参数.index_k
        )
    elif 参数.mode == "ExportJsonl":
        TranslatorLib.导出数据集(
            mode=参数.mode,
            file=参数.file,
            emb_file_name=参数.emb_file_name,
            emb_file_path=参数.emb_file_path
        )
    elif 参数.mode == "ImportPrompt":
        TranslatorLib.导入参考词(
            path=参数.path,
            emb_api_url=参数.emb_api_url,
            emb_api_key=参数.emb_api_key,
            emb_model=参数.emb_model,
            original_language=参数.original_language,
            target_language=参数.target_language,
            cache_path=参数.cache_path,
            emb_max_token=参数.emb_max_token,
            emb_max_batch=参数.emb_max_batch,
            emb_max_workers=参数.emb_max_workers,
            emb_file_name=参数.emb_file_name,
            emb_file_path=参数.emb_file_path
        )
    elif 参数.mode == "TranslatorFTBQ":
        TranslatorLib.翻译FTB任务(
            path=参数.path,
            llm_api_url=参数.llm_api_url,
            llm_api_key=参数.llm_api_key,
            llm_model=参数.llm_model,
            emb_api_url=参数.emb_api_url,
            emb_api_key=参数.emb_api_key,
            emb_model=参数.emb_model,
            language=参数.language,
            emb_max_token=参数.emb_max_token,
            emb_max_batch=参数.emb_max_batch,
            emb_max_workers=参数.emb_max_workers,
            emb_file_name=参数.emb_file_name,
            emb_file_path=参数.emb_file_path,
            llm_system_prompt=参数.llm_system_prompt,
            llm_prompt_location=参数.llm_prompt_location,
            llm_contexts=参数.llm_contexts,
            llm_contexts_length=参数.llm_contexts_length,
            llm_max_workers=参数.llm_max_workers,
            llm_max_batch=参数.llm_max_batch,
            llm_t=参数.llm_t,
            llm_p=参数.llm_p,
            llm_k=参数.llm_k,
            index_k=参数.index_k
        )
    elif 参数.mode == "TranslatorBQ":
        TranslatorLib.翻译BQ任务(
            path=参数.path,
            llm_api_url=参数.llm_api_url,
            llm_api_key=参数.llm_api_key,
            llm_model=参数.llm_model,
            emb_api_url=参数.emb_api_url,
            emb_api_key=参数.emb_api_key,
            emb_model=参数.emb_model,
            language=参数.language,
            emb_max_token=参数.emb_max_token,
            emb_max_batch=参数.emb_max_batch,
            emb_max_workers=参数.emb_max_workers,
            emb_file_name=参数.emb_file_name,
            emb_file_path=参数.emb_file_path,
            llm_system_prompt=参数.llm_system_prompt,
            llm_prompt_location=参数.llm_prompt_location,
            llm_contexts=参数.llm_contexts,
            llm_contexts_length=参数.llm_contexts_length,
            llm_max_workers=参数.llm_max_workers,
            llm_max_batch=参数.llm_max_batch,
            llm_t=参数.llm_t,
            llm_p=参数.llm_p,
            llm_k=参数.llm_k,
            index_k=参数.index_k
        )
    elif 参数.mode == "ImportPromptDictMini":
        TranslatorLib.导入DictMini参考词(
            file=参数.file,
            emb_api_url=参数.emb_api_url,
            emb_api_key=参数.emb_api_key,
            emb_model=参数.emb_model,
            emb_max_token=参数.emb_max_token,
            emb_max_batch=参数.emb_max_batch,
            emb_max_workers=参数.emb_max_workers,
            emb_file_name=参数.emb_file_name,
            emb_file_path=参数.emb_file_path
        )
    else:
        解释器0.print_help()