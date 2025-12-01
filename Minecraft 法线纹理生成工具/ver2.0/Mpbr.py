import numpy as np
from PIL import Image as img

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
    def image2pbr(fp: img.Image, normal: np.float16 = 0.004, ao: np.float16 = 0.25) -> img.Image:
        """灰度图像生成法线纹理图像

        Args:
            fp (PIL.Image.Image): 输入灰度图像.
            normal (numpy.float16, optional): 范围：0.0-1.0 默认值：0.004 控制法线强度.
            ao (numpy.float16, optional): 范围：0.0-1.0. 默认值：0.25 控制环境光遮蔽强度.

        Returns:
            PIL.Image.Image: 完整法线纹理图像.
        """
        灰度 = np.array(fp.convert('L'), np.float16) / 255.0
        h, w = 灰度.shape
        dx = np.clip((灰度[:, :-1] - 灰度[:, 1:] + 1) * 127.5, 0, 255).astype(np.uint8)
        dy = np.clip((灰度[:-1] - 灰度[1:] + 1) * 127.5, 0, 255).astype(np.uint8)
        dx = np.pad(dx, ((0, 0), (0, 1)), constant_values=127)
        dy = np.pad(dy, ((0, 1), (0, 0)), constant_values=127)
        dx = np.clip(128 + (dx.astype(int) - 128) * (normal * 254 + 1), 0, 255).astype(np.uint8)
        dy = np.clip(128 + (dy.astype(int) - 128) * (normal * 254 + 1), 0, 255).astype(np.uint8)
        法线矩阵 = np.full((h * 8, w * 8, 2), 127, np.uint8)
        for k in range(8):
            法线矩阵[k::8, 7::8, 0] = dx
        法线矩阵[7::8, :, 1] = np.repeat(dy, 8, axis=1)
        r = 法线矩阵[..., 0]
        r[:-1] = np.where(r[1:] != 127, r[1:], r[:-1])
        g = 法线矩阵[..., 1]
        g[:, :-1] = np.where(g[:, 1:] != 127, g[:, 1:], g[:, :-1])
        rgba = np.full((h * 8, w * 8, 4), 255, np.uint8)
        rgba[..., :2] = np.clip(法线矩阵, 0, 255).astype(np.uint8)
        rgba[..., 2] = np.repeat(np.repeat(255 - (灰度 + np.float16(ao * 255) * (np.float16(1.0) - 灰度)), 8, axis=0), 8, axis=1)
        rgba[..., 3] = np.array(fp.convert('L').resize((w * 8, h * 8), resample=img.NEAREST))
        image = img.fromarray(rgba, 'RGBA')
        return image