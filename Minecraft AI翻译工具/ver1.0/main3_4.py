import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter.scrolledtext import ScrolledText
import pyperclip

class LangSorterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("语言文件键值排序工具")
        self.root.geometry("800x600")
        
        # 模板文件选择
        self.template_label = tk.Label(root, text="模板文件(en_us.lang):")
        self.template_label.pack(pady=5)
        
        self.template_entry = tk.Entry(root, width=80)
        self.template_entry.pack(pady=5)
        
        self.template_button = tk.Button(root, text="浏览...", command=self.select_template)
        self.template_button.pack(pady=5)
        
        # 目标文件选择
        self.target_label = tk.Label(root, text="目标文件(zh_cn.lang):")
        self.target_label.pack(pady=5)
        
        self.target_entry = tk.Entry(root, width=80)
        self.target_entry.pack(pady=5)
        
        self.target_button = tk.Button(root, text="浏览...", command=self.select_target)
        self.target_button.pack(pady=5)
        
        # 排序按钮
        self.sort_button = tk.Button(root, text="开始排序", command=self.sort_files)
        self.sort_button.pack(pady=10)
        
        # 结果显示区域
        self.result_label = tk.Label(root, text="排序结果:")
        self.result_label.pack(pady=5)
        
        self.result_text = ScrolledText(root, width=100, height=20)
        self.result_text.pack(pady=5)
        
        # 复制按钮
        self.copy_button = tk.Button(root, text="复制结果", command=self.copy_result)
        self.copy_button.pack(pady=5)
        
    def select_template(self):
        file_path = filedialog.askopenfilename(title="选择模板文件", filetypes=[("Lang files", "*.lang")])
        if file_path:
            self.template_entry.delete(0, tk.END)
            self.template_entry.insert(0, file_path)
    
    def select_target(self):
        file_path = filedialog.askopenfilename(title="选择目标文件", filetypes=[("Lang files", "*.lang")])
        if file_path:
            self.target_entry.delete(0, tk.END)
            self.target_entry.insert(0, file_path)
    
    def parse_lang_file(self, file_path):
        """解析.lang文件，返回键值字典和行列表"""
        entries = {}
        lines = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    lines.append(line)
                    stripped = line.strip()
                    if stripped and not stripped.startswith('#') and '=' in stripped:
                        key = stripped.split('=', 1)[0].strip()
                        entries[key] = line
            return entries, lines
        except Exception as e:
            messagebox.showerror("错误", f"读取文件失败: {str(e)}")
            return None, None
    
    def sort_files(self):
        template_file = self.template_entry.get()
        target_file = self.target_entry.get()
        
        if not template_file or not target_file:
            messagebox.showwarning("警告", "请先选择模板文件和目标文件")
            return
        
        # 解析模板文件
        template_entries, template_lines = self.parse_lang_file(template_file)
        if template_entries is None:
            return
        
        # 解析目标文件
        target_entries, target_lines = self.parse_lang_file(target_file)
        if target_entries is None:
            return
        
        # 收集目标文件特有的键
        extra_keys = set(target_entries.keys()) - set(template_entries.keys())
        
        # 构建结果
        result = []
        used_keys = set()
        
        # 按照模板文件的行顺序处理
        for line in template_lines:
            stripped = line.strip()
            if not stripped or stripped.startswith('#'):
                # 保留注释和空行
                result.append(line)
            elif '=' in stripped:
                # 处理键值行
                key = stripped.split('=', 1)[0].strip()
                if key in target_entries:
                    result.append(target_entries[key])
                    used_keys.add(key)
        
        # 添加目标文件特有的键值对
        result.append("\n## 额外键值对 ##\n")
        for key in extra_keys:
            result.append(target_entries[key])
        
        # 显示结果
        self.result_text.delete(1.0, tk.END)
        self.result_text.insert(tk.END, ''.join(result))
        messagebox.showinfo("完成", "文件排序完成！")
    
    def copy_result(self):
        result = self.result_text.get(1.0, tk.END)
        if result.strip():
            pyperclip.copy(result)
            messagebox.showinfo("成功", "结果已复制到剪贴板")
        else:
            messagebox.showwarning("警告", "没有可复制的内容")

if __name__ == "__main__":
    root = tk.Tk()
    app = LangSorterApp(root)
    root.mainloop()
