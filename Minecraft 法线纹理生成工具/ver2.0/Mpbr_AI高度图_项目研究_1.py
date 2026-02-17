import numpy as np
from PIL import Image as img
from scipy.ndimage import uniform_filter
from transformers import pipeline
import torch
import multiprocessing as mp
from functools import partial
from tqdm import tqdm
from pathlib import Path

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
            ao: bool = True,
            ao_int: np.float16 = 1.0,
            ao_rad: np.uint8 = 4,
            height: bool = True,
            eazy_mode: str | None = None,
            eazy: np.uint16 = 16,
        ) -> img.Image:
        """灰度图像生成法线纹理图像

        Args:
            fp (PIL.Image.Image): 输入灰度图像.
            normal (bool, optional): 默认值：True 默认开启法线开关.
            normal_int (numpy.float16, optional): 范围：0.0-2.0 默认值：1.3 控制法线强度.
            ao (bool, optional): 默认值：True 控制环境光遮蔽开关.
            ao_int (numpy.float16, optional): 范围：0-100. 默认值：2 控制环境光遮蔽强度.
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
                if eazy_mode == "decimal":
                    深度值 = f"{b_}{d_}{f_}.{a_}{c_}{e_}"
                elif eazy_mode == "integer":
                    深度值 = f"{a_}{c_}{e_}.{b_}{d_}{f_}"
                深度值 = 深度值.replace('f', '').replace('F', '')
                灰度值 = 0.0 if 深度值 == "." else float(深度值)
                灰度值 = 255 * (eazy - 4 * 灰度值) / 16.0
                return 灰度值
            图像矩阵 = np.array(fp, np.uint8)
            灰度 = np.vectorize(单像素转换, otypes=[np.uint8])(图像矩阵[..., 0], 图像矩阵[..., 1], 图像矩阵[..., 2])
        h, w = 灰度.shape
        RGBA矩阵 = np.full((h * 8, w * 8, 4), 255, np.uint8)
        if normal == True:
            小法线矩阵 = np.full((h, w, 4), 128, np.uint8)
            灰度a, 灰度b, 灰度c, 灰度d = 灰度[1:], 灰度[:-1], 灰度[:, 1:], 灰度[:, :-1]
            小法线矩阵[1:, :,  0] = 128 - np.where(灰度a > 灰度b, 灰度a - 灰度b, 0) / 2
            小法线矩阵[:-1, :, 1] = 128 + np.where(灰度b > 灰度a, 灰度b - 灰度a, 0) / 2
            小法线矩阵[:, 1:,  2] = 128 - np.where(灰度c > 灰度d, 灰度c - 灰度d, 0) / 2
            小法线矩阵[:, :-1, 3] = 128 + np.where(灰度d > 灰度c, 灰度d - 灰度c, 0) / 2
            小法线矩阵 = np.clip(128 + np.sign(偏移 := 小法线矩阵.astype(np.float32) - 128) * (np.abs(偏移) ** normal_int), 0, 255).astype(np.uint8)
            法线矩阵 = np.full((h * 8, w * 8, 2), 128, np.uint8)
            法线矩阵[0::8, :, 1] = np.repeat(小法线矩阵[:, :, 0], 8, axis=1)
            法线矩阵[7::8, :, 1] = np.repeat(小法线矩阵[:, :, 1], 8, axis=1)
            法线矩阵[:, 0::8, 0] = np.repeat(小法线矩阵[:, :, 2], 8, axis=0)
            法线矩阵[:, 7::8, 0] = np.repeat(小法线矩阵[:, :, 3], 8, axis=0)
            RGBA矩阵[:, :, 0] = 法线矩阵[:, :, 0]
            RGBA矩阵[:, :, 1] = 法线矩阵[:, :, 1]
        else:
            RGBA矩阵[:, :, 0] = 128
            RGBA矩阵[:, :, 1] = 128
        if ao == True:
            遮蔽高度 = np.repeat(np.repeat(灰度, 8, axis=0), 8, axis=1).astype(np.int16)
            积核尺寸 = 2 * ao_rad + 1
            积核面积 = 积核尺寸 * 积核尺寸
            高度之和 = uniform_filter(遮蔽高度, size=积核尺寸, mode='nearest', output=np.int32) * 积核面积
            高度差值 = 高度之和 - 遮蔽高度 * 积核面积
            遮蔽缩放 = 100 * 积核面积 - 高度差值 * ao_int
            遮蔽裁剪 = np.clip(遮蔽缩放, 0, 100 * 积核面积)
            遮蔽结果 = (遮蔽裁剪 * 255 // (100 * 积核面积)).astype(np.uint8)
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
        zoom: bool = False,
    ) -> img.Image:
        """漫反射与法线合并，image分辨率与normal相同
        
        Args:
            image (PIL.Image.Image): 漫反射图像.
            normal (PIL.Image.Image): 法线图像.
            zoom (bool, optional): 默认值：False 是否放大image图像.

        Returns:
            PIL.Image.Image: 漫反射图像.

        """
        漫反射图像 = Mpbr.open(image).convert('RGBA')
        漫反射图像 = np.array(漫反射图像, np.int16)
        漫反射图像 = np.repeat(np.repeat(漫反射图像, 8, axis=0), 8, axis=1) if zoom == True else 漫反射图像
        法线图像 = Mpbr.open(normal.convert('RGB'))
        法线R, 法线G, 法线B = 法线图像.split()[:3]
        法线R = 128 - np.array(法线R, np.int16)
        法线G = 128 - np.array(法线G, np.int16)
        法线B = np.array(法线B, np.int16) - 255
        增量 = 法线R + 法线G + 法线B
        漫反射图像[..., :3] += 增量[..., np.newaxis]
        漫反射图像 = np.clip(漫反射图像, 0, 255).astype(np.uint8)
        漫反射图像 = img.fromarray(漫反射图像)
        return 漫反射图像
    def 获取资源文件夹后文件夹路径(path):
        完整路径 = Path(path)
        assets索引 = 完整路径.parts.index('assets')
        相对部分 = 完整路径.parts[assets索引:-1]
        文件名无扩展 = 完整路径.stem
        return str(Path(*相对部分) / 文件名无扩展)
    def 深度估计计算法线(
        单个深度,
        normal: bool = True,
        normal_int: np.float16 = 1.3,
        ao: bool = True,
        ao_int: np.float16 = 1.0,
        ao_rad: np.uint8 = 4,
        height: bool = True,
    ) -> img.Image:
        return Mpbr.image2normal(单个深度['depth'], normal, normal_int, ao, ao_int, ao_rad, height)
    def depth_estimator2normal(
        image: list,
        normal: bool = True,
        normal_int: np.float16 = 1.3,
        ao: bool = True,
        ao_int: np.float16 = 1.0,
        ao_rad: np.uint8 = 4,
        height: bool = True,
    ) -> list:
        深度估计器 = pipeline(
        task="depth-estimation", 
        model="Intel/zoedepth-nyu-kitti",
        dtype=torch.float32,
        device="cuda:0",
        attn_implementation="flash_attention_2",
        )
        图像 = [img.open(path) for path in image]
        深度 = []
        for idx in tqdm(range(len(图像)), desc="深度估计"):
            try:
                原图 = 图像[idx]
                放大图 = 原图.resize((原图.width * 1, 原图.height * 1), resample=img.Resampling.NEAREST)
                深度结果 = 深度估计器(放大图)
                深度图 = 深度结果['depth']
                缩小深度图 = 深度图.resize((原图.width, 原图.height), resample=img.Resampling.LANCZOS)
                深度.append({'depth': 缩小深度图})
            except Exception as e:
                print(f"跳过图像 {image[idx]}: {e}")
                深度.append({'depth': 原图.convert("L")})
        法线图像 = []
        with mp.Pool(processes=int(mp.cpu_count()/2)) as 池:
            处理函数 = partial(Mpbr.深度估计计算法线, normal=normal, normal_int=normal_int, ao=ao, ao_int=ao_int, ao_rad=ao_rad, height=height)
            法线图像 = list(tqdm(池.imap(处理函数, 深度), total=len(深度), desc='计算法线'))
        法线图像 = [[Mpbr.获取资源文件夹后文件夹路径(index), index2] for index, index2 in tqdm(zip(image, 法线图像), total=len(image), desc="复写路径")]
        return 法线图像