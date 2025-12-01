# Eazy Normal（简单法线）
[Version 1.0](https://github.com/lingxingmiao/Tools/tree/main/Minecraft%20%E6%B3%95%E7%BA%BF%E7%BA%B9%E7%90%86%E7%94%9F%E6%88%90%E5%B7%A5%E5%85%B7/ver1.0)
的更高阶版本，包含了 Version 1.0 的绝大部分功能。<br/>
这一代版本性能远远低于 Version 1.0，平均慢50%
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
  - 传入：fp:PIL.Image.Image(高度图)，normal:numpy.float16(法线强度)，ao:numpy.float16(环境光遮蔽强度)
  - 返回：PIL.Image.Image(法线纹理)
