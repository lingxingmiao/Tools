# Eazy Normal（简单法线）
Eazy Normal 是专门针对萌新绘制 法线纹理 以及 视差纹理 的一个工具。</br>
<img width="1920" height="1080" alt="image" src="https://github.com/user-attachments/assets/939406e0-7ef2-4bec-881e-ef0366440a82" /></br>
反光不在法线纹理文件。</br>
## 输入图片格式
图片必须为黑白RGB或灰度图。</br>
程序会根据颜色深度来处理图片。</br>
颜色越浅深度越浅，颜色越深深度越深（深度指高度）。</br>
## 如何使用（UI使用）
<img width="856" height="512" alt="image" src="https://github.com/user-attachments/assets/3f3502cf-92c2-44a4-90b7-81c2460f0de5" /></br>
输入一个图片，然后点开始。</br>
处理完图片会输出在图片输入路径下或者图片输出路径下。</br>
## 如何使用（PyThon调用）
<pre><code class="language-python">import os
from PIL import Image
from Normal_Texture_Lib import Normal_Texture
图片文件 = r"C:\aaa.png"
图片 = Normal_Texture().Read_Image(图片文件)
_n图片 = Normal_Texture().Image_to_Normal(图片, True)
pil_img = Image.fromarray(_n图片, mode='RGBA')
pil_img.save(f"os.path.dirname(图片文件)/{os.path.basename(图片文件)}_n.png")</code></pre>
