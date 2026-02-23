import numpy as np
from PIL import Image as img
from scipy.ndimage import uniform_filter

class Mpbr:
    def open(fp: str | img.Image | np.ndarray) -> img.Image:
        """将图像或路径或数组转换为RGBA图像

        Args:
            fp (string | PIL.Image.Image | numpy.ndarray): 图像或路径或数组

        Returns:
            PIL.Image.Image: RGBA图像
        """
        if isinstance(fp, img.Image):
            image = fp
        if isinstance(fp, str):
            image = img.open(fp)
        if isinstance(fp, np.ndarray):
            image = img.fromarray(fp)
        image = image.convert('RGBA')
        return image
    def image2normal(
            fp: img.Image,
            normal: bool = True,
            normal_int: np.float16 = 1.3,
            normal_amplitude: np.uint8 = 0,
            ao: bool = True,
            ao_int: np.float16 = 0.5,
            ao_rad: np.uint8 = 6,
            height: bool = True,
            eazy_mode: str | None = None,
            eazy: np.uint16 = 16,
        ) -> img.Image:
        """灰度图像生成法线纹理图像

        Args:
            fp (PIL.Image.Image): 输入灰度图像.
            normal (bool, optional): 默认值：True 默认开启法线开关.
            normal_int (numpy.float16, optional): 范围：0.0-4.0, 默认值：1.3, 控制法线强度.
            normal_amplitude (numpy.uint8, optional): 范围：0-255, 默认值：0, 两个高度最小相差多少才计算法线.
            ao (bool, optional): 默认值：True, 控制环境光遮蔽开关.
            ao_int (numpy.float16, optional): 范围：0-100, 默认值：0.5, 控制环境光遮蔽强度.
            ao_rad (numpy.uint8, optional): 范围：2-16, 默认值：6, 控制环境光遮蔽半径.
            height (bool, optional): 默认值：True, 高度视差开关.
            eazy_mode (str, optional): 默认值：None, 可选值：decimal，integer 简单模式开关以及模式.
            eazy (numpy.uint16, optional): 范围：None, 0-2048 默认值：16 简单模式的分辨率大小.
        Returns:
            PIL.Image.Image: 完整法线纹理图像.
        """
        if eazy_mode is None:
            灰度 = np.array(fp.convert('L'), np.int16)
        else:
            def 单像素转换(_r, _g, _b):
                a_, b_, c_, d_, e_, f_ = f"{_r:02x}{_g:02x}{_b:02x}"
                if eazy_mode == "decimal":
                    深度值 = f"{b_}{d_}{f_}.{a_}{c_}{e_}"
                elif eazy_mode == "integer":
                    深度值 = f"{a_}{c_}{e_}.{b_}{d_}{f_}"
                深度值 = 深度值.replace('f', '').replace('F', '')
                灰度值 = 0.0 if 深度值 == "." else float(深度值)
                灰度值 = 255 * (eazy - 4 * 灰度值) / 16.0
                return 灰度值
            图像矩阵 = np.array(fp, np.uint8)
            灰度 = np.vectorize(单像素转换, otypes=[np.int16])(图像矩阵[..., 0], 图像矩阵[..., 1], 图像矩阵[..., 2])
        h, w = 灰度.shape
        RGBA矩阵 = np.full((h * 8, w * 8, 4), 255, np.uint8)
        if normal == True:
            小法线矩阵 = np.full((h, w, 4), 128, np.uint8)
            灰度a, 灰度b, 灰度c, 灰度d = 灰度[1:], 灰度[:-1], 灰度[:, 1:], 灰度[:, :-1]
            小法线矩阵[1:, :,  0] = 128 - np.where(灰度a > 灰度b + normal_amplitude, 灰度a - 灰度b, 0) // 2
            小法线矩阵[:-1, :, 1] = 128 + np.where(灰度b > 灰度a + normal_amplitude, 灰度b - 灰度a, 0) // 2
            小法线矩阵[:, 1:,  2] = 128 - np.where(灰度c > 灰度d + normal_amplitude, 灰度c - 灰度d, 0) // 2
            小法线矩阵[:, :-1, 3] = 128 + np.where(灰度d > 灰度c + normal_amplitude, 灰度d - 灰度c, 0) // 2
            小法线矩阵 = np.clip(128 + np.sign(偏移 := 小法线矩阵.astype(np.float32) - 128) * (np.abs(偏移) ** normal_int), 0, 255).astype(np.uint8)
            法线矩阵 = np.full((h * 8, w * 8, 2), 128, np.uint8)
            法线矩阵[0::8, :, 1] = np.repeat(小法线矩阵[:, :, 0], 8, axis=1)
            法线矩阵[7::8, :, 1] = np.repeat(小法线矩阵[:, :, 1], 8, axis=1)
            法线矩阵[:, 0::8, 0] = np.repeat(小法线矩阵[:, :, 2], 8, axis=0)
            法线矩阵[:, 7::8, 0] = np.repeat(小法线矩阵[:, :, 3], 8, axis=0)
            法线矩阵.astype(np.uint8)
            RGBA矩阵[:, :, 0] = 法线矩阵[:, :, 0]
            RGBA矩阵[:, :, 1] = 法线矩阵[:, :, 1]
        else:
            RGBA矩阵[:, :, 0] = 128
            RGBA矩阵[:, :, 1] = 128
        if ao == True:
            遮蔽高度 = np.repeat(np.repeat(灰度, 8, axis=0), 8, axis=1).astype(np.float32)
            积核尺寸 = 2 * ao_rad + 1
            平均高度 = uniform_filter(遮蔽高度, size=积核尺寸, mode='nearest')
            高度差 = 平均高度 - 遮蔽高度
            相对差 = 高度差 / 255.0
            遮蔽强度 = 1.0 - np.clip(相对差 * ao_int, 0, 1.0)
            遮蔽结果 = (遮蔽强度 * 255).astype(np.uint8)
            RGBA矩阵[:, :, 2] = 遮蔽结果
        else:
            RGBA矩阵[:, :, 2] = 255
        if height == True:
            RGBA矩阵[:, :, 3] = np.repeat(np.repeat(灰度, 8, axis=0), 8, axis=1)
        else:
            RGBA矩阵[:, :, 3] = 255
        RGBA矩阵 = img.fromarray(RGBA矩阵)
        return RGBA矩阵
    def image1normal2map(
        image: img.Image,
        normal: img.Image,
        ao_color: tuple = (50.0, 50.0, 50.0, 51.0),
        only_ao = False,
        zoom: bool = False,
    ) -> img.Image:
        """漫反射与法线合并，image分辨率与normal相同
        
        Args:
            image (PIL.Image.Image): 漫反射图像.
            normal (PIL.Image.Image): 法线图像.
            ao_color (tuple, optional): 默认值：(50.5, 49.5, 51.0, 51.5) 控制环境光遮蔽颜色与强度.
            zoom (bool, optional): 默认值：False 是否放大image图像.

        Returns:
            PIL.Image.Image: 漫反射图像.

        """
        漫反射图像 = Mpbr.open(image).convert('RGBA')
        漫反射图像 = np.array(漫反射图像, np.float32)
        漫反射图像 = np.repeat(np.repeat(漫反射图像, 8, axis=0), 8, axis=1) if zoom == True else 漫反射图像
        法线图像 = Mpbr.open(normal.convert('RGB'))
        法线R, 法线G, 法线B = 法线图像.split()[:3]
        法线R = (128 - np.array(法线R, np.float32)) if only_ao == False else 0
        法线G = (128 - np.array(法线G, np.float32)) if only_ao == False else 0
        法线B = np.array(法线B, np.float32) - 255
        增量R = 法线R + 法线G + (法线B * (ao_color[3] - ao_color[0]))
        增量G = 法线R + 法线G + (法线B * (ao_color[3] - ao_color[1]))
        增量B = 法线R + 法线G + (法线B * (ao_color[3] - ao_color[2]))
        增量 = np.stack([增量R, 增量G, 增量B], axis=-1).astype(np.float32)
        漫反射图像[..., :3] += 增量
        漫反射图像 = np.clip(漫反射图像, 0, 255).astype(np.uint8)
        漫反射图像 = img.fromarray(漫反射图像)
        return 漫反射图像
    
    def diffuse2normal(
        fp: img.Image,
        normal: bool = True,
        normal_int: np.float16 = 2.5,
        normal_amplitude: np.uint8 = 0,
        ao: bool = True,
        ao_int: np.float16 = 2,
        ao_rad: np.uint8 = 6,
        height: bool = False,
        mix_height: int = 207,
    ) -> img.Image:
        """漫反射纹理图像添加法线纹理图像
        
        Args:
            fp (PIL.Image.Image): 输入灰度图像.
            normal (bool, optional): 默认值：True, 默认开启法线开关.
            normal_int (numpy.float16, optional): 范围：0.0-4.0, 默认值：1.3, 控制法线强度.
            normal_amplitude (numpy.uint8, optional): 范围：0-255, 默认值：4, 两个高度最小相差多少才计算法线.
            ao (bool, optional): 默认值：True 控制环境光遮蔽开关.
            ao_int (numpy.float16, optional): 范围：0-100, 默认值：2, 控制环境光遮蔽强度.
            ao_rad (numpy.uint8, optional): 范围：2-16, 默认值：6, 控制环境光遮蔽半径.
            height (bool, optional): 默认值：False, 高度视差开关.
            mix_height (int, optional): 范围：0-255, 默认值：207, 最大高度差.
        Returns:
            PIL.Image.Image: 完整法线纹理图像.
        """
        图像 = np.array(fp.convert('RGB'))
        l图像 = (np.dot(图像[...,:3], [0.299, 0.587, 0.114])/2558).astype(np.float32)
        l图像min = l图像.min()
        l图像min = l图像min if l图像min > 0 else 1
        l图像归一化 = np.clip((((l图像 - l图像min) / (l图像.max() - l图像min)) * (255-mix_height) + mix_height), 0, 255).astype(np.uint8)
        return Mpbr.image2normal(img.fromarray(l图像归一化), height=height, normal=normal, normal_int=normal_int, normal_amplitude=normal_amplitude, ao=ao, ao_int=ao_int, ao_rad=ao_rad)