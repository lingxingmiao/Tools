import tkinter as tk
from tkinter import filedialog
import os
from PIL import Image, ImageTk
from Normal_Texture_Lib import Normal_Texture

class UI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Eazy Normal 测试UI")
        self.root.geometry("854x480")
        
        # Variables to store file paths
        self.input_file_var = tk.StringVar()
        self.output_folder_var = tk.StringVar()
        
        # Boolean variable for height map
        self.height_map_var = tk.BooleanVar(value=True)
        
        self.setup_ui()
    
    def setup_ui(self):
        # Create main frame
        main_frame = tk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Left panel
        left_frame = tk.Frame(main_frame, width=400, bg='lightgray')
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 5))
        left_frame.pack_propagate(False)  # Keep the fixed width

        # Input file section
        tk.Label(left_frame, text="PNG输入文件:", bg='lightgray').pack(anchor=tk.W, padx=10, pady=(10, 0))
        input_file_frame = tk.Frame(left_frame, bg='lightgray')
        input_file_frame.pack(fill=tk.X, padx=10, pady=5)
        input_file_entry = tk.Entry(input_file_frame, textvariable=self.input_file_var, state='readonly')
        input_file_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        browse_input_btn = tk.Button(input_file_frame, text="浏览", command=self.browse_input_file)
        browse_input_btn.pack(side=tk.RIGHT, padx=(5, 0))

        # Output folder section
        tk.Label(left_frame, text="输出文件夹:", bg='lightgray').pack(anchor=tk.W, padx=10, pady=(10, 0))
        output_folder_frame = tk.Frame(left_frame, bg='lightgray')
        output_folder_frame.pack(fill=tk.X, padx=10, pady=5)
        output_folder_entry = tk.Entry(output_folder_frame, textvariable=self.output_folder_var, state='readonly')
        output_folder_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        browse_output_btn = tk.Button(output_folder_frame, text="浏览", command=self.browse_output_folder)
        browse_output_btn.pack(side=tk.RIGHT, padx=(5, 0))

        # Height map checkbox
        height_map_checkbox = tk.Checkbutton(left_frame, text="高度图", variable=self.height_map_var, bg='lightgray')
        self.height_map_checkbox = height_map_checkbox
        height_map_checkbox.pack(anchor=tk.W, padx=10, pady=10)

        # Start button at the bottom
        start_button = tk.Button(left_frame, text="开始", command=self.start_processing, height=2)
        start_button.pack(side=tk.BOTTOM, pady=10, padx=10, fill=tk.X)

        # Right panel for image display
        right_frame = tk.Frame(main_frame, bg='white')
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))

        # Image display label
        self.image_label = tk.Label(right_frame, bg='white', text='图片将显示在这里')
        self.image_label.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)
    
    def browse_input_file(self):
        filename = filedialog.askopenfilename(
            title="选择PNG输入文件",
            filetypes=[("PNG files", "*.png"), ("All files", "*.*")]
        )
        if filename:
            self.input_file_var.set(filename)
            self.display_image(filename)

    def browse_output_folder(self):
        foldername = filedialog.askdirectory(title="选择输出文件夹")
        if foldername:
            self.output_folder_var.set(foldername)

    def display_image(self, filepath):
        try:
            # Open and resize the image to fit the display area
            img = Image.open(filepath)
            img.thumbnail((400, 400))  # Adjust size to fit the right panel
            photo = ImageTk.PhotoImage(img)
            
            self.image_label.config(image=photo)
            self.image_label.image = photo  # Keep a reference to avoid garbage collection
        except Exception as e:
            # Don't show error message, just silently fail
            pass

    def start_processing(self):
        input_file = self.input_file_var.get()
        output_folder = self.output_folder_var.get()
        is_height_map = self.height_map_var.get()
        
        if not input_file:
            # Don't show warning message
            return
        
        if not os.path.exists(input_file):
            # Don't show error message
            return
        
        
        路径 = self.output_folder_var.get() if self.output_folder_var.get() else os.path.dirname('self.output_folder_entry')
        图片 = Normal_Texture().Read_Image(self.input_file_var.get())
        _n图片 = Normal_Texture().Image_to_Normal(图片, self.height_map_var.get())
        pil_img = Image.fromarray(_n图片, mode='RGBA')
        pil_img.save(f"{路径}/{os.path.basename(self.input_file_var.get())}_n.png")
        self.display_image(f"{路径}/{os.path.basename(self.input_file_var.get())}_n.png")
    def run(self):
        self.root.mainloop()

# Example usage
if __name__ == "__main__":
    app = UI()
    app.run()