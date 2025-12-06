# Eazy Normal（简单法线）
[Version 1.0](https://github.com/lingxingmiao/Tools/tree/main/Minecraft%20%E6%B3%95%E7%BA%BF%E7%BA%B9%E7%90%86%E7%94%9F%E6%88%90%E5%B7%A5%E5%85%B7/ver1.0)
的更高阶版本，包含了 Version 1.0 的绝大部分功能<br/>
这一代版本性能远远低于 Version 1.0，平均慢50%，需要加速请使用multiprocessing<br/>
<img width="1920" height="1080" alt="4d9b545f34397157e7cd5646e700caad" src="https://github.com/user-attachments/assets/ba613b65-1a9e-4b2e-91a2-a855a279d9c5" />



### Python调用
<pre><code class="language-python">from Mpbr import Mpbr
图像 = Mpbr.open(r"bottom.png")
法线图像 = Mpbr.image2pbr(图像)
法线图像.save(r"bottom_n.png")</code></pre>
### 更新日志
#### 12月1-2日 ver2.0
- 创建 open 方法，与PIL.Image.open方法几乎一样
  - 传入：string或PIL.Image.Image或numpy.ndarray
  - 返回：PIL.Image.Image(RGBA图像)
- 创建 image2pbr 方法
  - 传入：fp:PIL.Image.Image(高度图)，normal:numpy.float16(法线强度0-1)，ao:numpy.float16(环境光遮蔽强度0-1)
  - 返回：PIL.Image.Image(法线纹理)
#### 12月5-6日 ver2.1
- 更改 image2pbr 方法
  - 法线纹理样式参考 [Another Vanilla PBR](https://www.curseforge.com/minecraft/texture-packs/avpbr) 
<pre><code class="language-python">灰度图像生成法线纹理图像
Args:
    fp (PIL.Image.Image): 输入灰度图像.
    normal (numpy.float16, optional): 范围：0.0-2.0 默认值：1.3 控制法线强度.
    ao_int (numpy.uint8, optional): 范围：0-100. 默认值：2 控制环境光遮蔽强度.
    ao_rad (numpy.uint8, optional): 范围：2-5. 默认值：3 控制环境光遮蔽半径.
    eazy_mode (str, optional): 默认值：None 可选值：decimal，integer 简单模式开关以及模式.
    eazy (numpy.uint16, optional): 范围：None 0-2048 默认值：16 简单模式的分辨率大小.
Returns:
    PIL.Image.Image: 完整法线纹理图像.</code></pre>
- 新增简单模式（性能消耗≈15%）
  - 现在你可以在 Photoshop 直接使用十六进制来控制深度了！
  - #abcdef 在 "decimal" 模式下为 bdf.ace，"integer"模式下为 ace.bdf
  - #abcdef 可以写 0-9 以及 F
  - 示例：#235fff eazy_mode=decimal eazy=16 为深 3.25 像素
  - 示例：#72f5ff eazy_mode=integer eazy=32 为深 7.25 像素
