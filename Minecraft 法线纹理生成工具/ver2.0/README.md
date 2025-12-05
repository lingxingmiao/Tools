# Eazy Normal（简单法线）
[Version 1.0](https://github.com/lingxingmiao/Tools/tree/main/Minecraft%20%E6%B3%95%E7%BA%BF%E7%BA%B9%E7%90%86%E7%94%9F%E6%88%90%E5%B7%A5%E5%85%B7/ver1.0)
的更高阶版本，包含了 Version 1.0 的绝大部分功能<br/>
这一代版本性能远远低于 Version 1.0，平均慢50%，需要加速请使用multiprocessing<br/>
<img width="1920" height="1080" alt="image" src="https://github.com/user-attachments/assets/ce06540a-c67e-4221-ab5d-b6aec7dbee29" />


### Python调用
<pre><code class="language-python">from Mpbr import Mpbr
图像 = Mpbr.open(r"bottom.png")
法线图像 = Mpbr.image2pbr(图像)
法线图像.save(r"bottom_n.png")</code></pre>
### 更新日志
#### 12月1-2日
- 创建 open 方法，与PIL.Image.open方法几乎一样
  - 传入：string或PIL.Image.Image或numpy.ndarray
  - 返回：PIL.Image.Image(RGBA图像)
- 创建 image2pbr 方法
  - 传入：fp:PIL.Image.Image(高度图)，normal:numpy.float16(法线强度0-1)，ao:numpy.float16(环境光遮蔽强度0-1)
  - 返回：PIL.Image.Image(法线纹理)
#### 下次
- 更改 image2pbr 方法
  - 传入：fp:PIL.Image.Image(高度图)，normal:numpy.float16(法线强度:0-1)，ao:numpy.float16(环境光遮蔽强度:0-1)，eazy:numpy.uint16(简单模式:None-uint16)
  - 返回：PIL.Image.Image(法线纹理)
- 新增简单模式（性能消耗≈15%）
  - 现在你可以在 Photoshop 直接使用十六进制来控制深度了！（几乎无法使用映射表来反向绘制）
  - #acbdef 表示深 cdf.abe 像素，末尾值位0 f F会被删除，您需要在 eazy:numpy.uint16 传入法线纹理的分辨率
  - 示例：#2185f0 = 深15.28(150.28f)像素，如果图像分辨率为128那么深度最大为32，需要在 eazy:numpy.uint16 传入图像分辨率64
  - 示例：#02f5f0 = 深0.25(0ff.250)像素，如果图像分辨率为16那么深度最大为4，需要在 eazy:numpy.uint16 传入图像分辨率16
