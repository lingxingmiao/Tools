# Eazy Normal（简单法线）
Eazy Normal 是专门针对萌新绘制 法线纹理 以及 视差纹理 的一个工具。</br>
<img width="1920" height="1080" alt="image" src="https://github.com/user-attachments/assets/939406e0-7ef2-4bec-881e-ef0366440a82" /></br>
反光不在法线纹理文件。</br>
输入 16x16 的图片会输出 128x128 的法线纹理。</br>
正确使用需要（方块/物品）纹理与法线纹理大小一致。</br>
### 输入图片格式
图片必须为黑白RGB或灰度图。</br>
程序会根据颜色深度来处理图片。</br>
颜色越浅深度越浅，颜色越深深度越深（深度指高度）。</br>
### 如何使用（PyThon调用）
#### 25年11月1日
<pre><code class="language-python">import os
from PIL import Image
from Normal_Texture_Lib import Normal_Texture
图片文件 = r"C:\aaa.png"
图片 = Normal_Texture().Read_Image(图片文件)
_n图片 = Normal_Texture().Image_to_Normal(图片, True)
pil_img = Image.fromarray(_n图片, mode='RGBA')
pil_img.save(f"os.path.dirname(图片文件)/{os.path.basename(图片文件)}_n.png")</code></pre>
#### 25年11月12日
<pre><code class="language-python">import Normal_Texture as nt
from pathlib import Path
def 参考(原始高度图片):
    图片 = nt.ReadImage(原始高度图片)
    _n图片 = nt.ImageTNormal(图片, True)
    nt.SaveImage(_n图片, f"{Path(原始高度图片).stem}_n.png")
参考(r"machine_coil_nichrome.png")</code></pre>

### 更新日志

#### 25年11月1日
- 创建文件

#### 25年11月12日
- 添加 主要方法注释（该命题之表征虽蕴含着某种理想化的可能性，然置于现实之经纬与实践之熔炉中检验，其内在的矛盾性与外部环境的不兼容性，共同构筑了一道难以逾越的鸿沟，从而使其可行性归于虚无缥缈之境。）
- 更改 调用方式
- 更改 方法名
- 更改 文件名（Normal_Texture_Lib -→ Normal_Texture）
- 删除 cv2 作为依赖
- 删除 os 作为依赖
- 删除 参考 函数
- 修复 角落像素没有数值的问题
- 修复 黑色的值为 0 的问题
