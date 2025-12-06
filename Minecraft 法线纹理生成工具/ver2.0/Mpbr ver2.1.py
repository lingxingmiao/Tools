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
    def image2pbr(fp: img.Image, normal: np.float16 = 1.3, ao_int: np.uint8 = 2, ao_rad: np.uint8 = 3, eazy_mode: str = None, eazy: np.uint16 = 16) -> img.Image:
        """灰度图像生成法线纹理图像

        Args:
            fp (PIL.Image.Image): 输入灰度图像.
            normal (numpy.float16, optional): 范围：0.0-2.0 默认值：1.3 控制法线强度.
            ao_int (numpy.uint8, optional): 范围：0-100. 默认值：2 控制环境光遮蔽强度.
            ao_rad (numpy.uint8, optional): 范围：2-5. 默认值：3 控制环境光遮蔽半径.
            eazy_mode (str, optional): 默认值：None 可选值：decimal，integer 简单模式开关以及模式.
            eazy (numpy.uint16, optional): 范围：None 0-2048 默认值：16 简单模式的分辨率大小.

        Returns:
            PIL.Image.Image: 完整法线纹理图像.
        """
        if eazy_mode is None:
            灰度 = np.array(fp.convert('L'), np.uint8)
        else:
            def 单像素转换(_r, _g, _b):
                a_, b_, c_, d_, e_, f_ = f"{_r:02x}{_g:02x}{_b:02x}"
                if eazy_mode is "decimal":
                    深度值 = f"{b_}{d_}{f_}.{a_}{c_}{e_}"
                elif eazy_mode is "integer":
                    深度值 = f"{a_}{c_}{e_}.{b_}{d_}{f_}"
                深度值 = 深度值.replace('f', '').replace('F', '')
                灰度值 = 0.0 if 深度值 == "." else float(深度值)
                灰度值 = 255 * (eazy - 4 * 灰度值) / 16.0
                return 灰度值
            图像矩阵 = np.array(fp, np.uint8)
            灰度 = np.vectorize(单像素转换, otypes=[np.uint8])(图像矩阵[..., 0], 图像矩阵[..., 1], 图像矩阵[..., 2])
        h, w = 灰度.shape
        小法线矩阵 = np.full((h, w, 4), 128, np.uint8)
        灰度a, 灰度b, 灰度c, 灰度d = 灰度[1:], 灰度[:-1], 灰度[:, 1:], 灰度[:, :-1]
        小法线矩阵[1:, :,  0] = 128 - np.where(灰度a > 灰度b, 灰度a - 灰度b, 0) / 2
        小法线矩阵[:-1, :, 1] = 128 + np.where(灰度b > 灰度a, 灰度b - 灰度a, 0) / 2
        小法线矩阵[:, 1:,  2] = 128 - np.where(灰度c > 灰度d, 灰度c - 灰度d, 0) / 2
        小法线矩阵[:, :-1, 3] = 128 + np.where(灰度d > 灰度c, 灰度d - 灰度c, 0) / 2
        小法线矩阵 = np.clip(128 + np.sign(偏移 := 小法线矩阵.astype(np.float32) - 128) * (np.abs(偏移) ** normal), 0, 255).astype(np.uint8)
        法线矩阵 = np.full((h * 8, w * 8, 2), 128, np.uint8)
        法线矩阵[0::8, :, 1] = np.repeat(小法线矩阵[:, :, 0], 8, axis=1)
        法线矩阵[7::8, :, 1] = np.repeat(小法线矩阵[:, :, 1], 8, axis=1)
        法线矩阵[:, 0::8, 0] = np.repeat(小法线矩阵[:, :, 2], 8, axis=0)
        法线矩阵[:, 7::8, 0] = np.repeat(小法线矩阵[:, :, 3], 8, axis=0)
        遮蔽高度 = np.repeat(np.repeat(灰度, 8, axis=0), 8, axis=1).astype(np.int16)
        积核尺寸 = 2 * ao_rad + 1
        积核面积 = 积核尺寸 * 积核尺寸
        高度之和 = uniform_filter(遮蔽高度, size=积核尺寸, mode='nearest', output=np.int32) * 积核面积
        高度差值 = 高度之和 - 遮蔽高度 * 积核面积
        遮蔽缩放 = 100 * 积核面积 - 高度差值 * ao_int
        遮蔽裁剪 = np.clip(遮蔽缩放, 0, 100 * 积核面积)
        遮蔽结果 = (遮蔽裁剪 * 255 // (100 * 积核面积)).astype(np.uint8)
        RGBA矩阵 = np.full((h * 8, w * 8, 4), 255, np.uint8)
        RGBA矩阵[:, :, 0] = 法线矩阵[:, :, 0]
        RGBA矩阵[:, :, 1] = 法线矩阵[:, :, 1]
        RGBA矩阵[:, :, 2] = 遮蔽结果
        RGBA矩阵[:, :, 3] = np.repeat(np.repeat(灰度, 8, axis=0), 8, axis=1)
        RGBA矩阵 = img.fromarray(RGBA矩阵)
        return RGBA矩阵
