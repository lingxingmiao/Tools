import numpy as np
from PIL import Image as img
import time

def ImageTNormal(图片: np.ndarray, 法线纹理: np.ndarray = [True, True, False]) -> np.ndarray:
    """图片转法线纹理
    Args:
        图片 (多维数组): ReadImage方法读取的灰度数组
        法线纹理 (数组): [高度图, 左上纹理空隙修复，启用像素内法线会自动关闭, 像素内法线]
    Returns:
        多维数组: RGBA格式数组图片，可以使用SaveImage方法保存
    """
    灰度矩阵 = 图片转灰度矩阵(图片)
    灰度向量矩阵 = 灰度矩阵转向量矩阵(灰度矩阵)
    R通道法线, G通道法线 = 向量矩阵转法线纹理(图片, 灰度向量矩阵, 法线纹理[2])
    法线纹理[1] = False if 法线纹理[2] else 法线纹理[1]
    R通道图片 = 通道图片修复(_64位矩阵转图片(R通道法线, channels_output='single')) if 法线纹理[1] else _64位矩阵转图片(R通道法线, channels_output='single')
    G通道图片 = np.rot90(通道图片修复(_64位矩阵转图片(G通道法线, channels_output='single')) if 法线纹理[1] else _64位矩阵转图片(G通道法线, channels_output='single'), k=1)
    return 合并通道(R通道图片, G通道图片, np.repeat(np.repeat(图片, 8, axis=0), 8, axis=1), 法线纹理[0])
def ReadImage(输入: str | np.ndarray) -> np.ndarray:
    """读取图片为数组
    Args:
        输入 (字符串 | 多维数组): 图片路径或PIL读取的图片数组
    Returns:
        多维数组: 灰度图片数组
    """
    图片 = 输入 if isinstance(输入, np.ndarray) else np.array(img.open(输入))
    if len(图片.shape) == 3 and 图片.shape[2] == 3:
        图片 = 图片[:, :, ::-1]
    return 图片
def SaveImage(图片: np.ndarray, 文件路径: str) -> str:
    """保存图片数组为图片
    Args:
        图片 (多维数组): RGBA图片数组
        文件路径 (字符串): 保存的文件路径
    Returns:
        字符串: 传入的文件路径
    """
    img.fromarray(图片, mode='RGBA').save(文件路径)
    return 文件路径






#主逻辑
def 向量矩阵转法线纹理(图片, 灰度向量矩阵, 像素内法线):
    图片高, 图片宽 = 图片.shape[:2]
    法线矩阵 = np.full((图片高, 图片宽, 64), 2, dtype=np.uint8)
    法线矩阵2 = np.full((图片高, 图片宽, 64), 2, dtype=np.uint8)
    for 行索引 ,行向量 in enumerate(灰度向量矩阵):
        for 列索引 ,向量 in enumerate(行向量):
            try:
                if 行向量[列索引][4] == 0:
                    for i in range(8):
                        法线矩阵[行索引][列索引][(i+1)*8-1] = 0
                elif 行向量[列索引][4] == 2:
                    for i in range(8):
                        if 像素内法线:
                            法线矩阵[行索引][列索引+1][i*8-8] = 1
                        else:
                            法线矩阵[行索引][列索引][(i+1)*8-1] = 1
            except IndexError: pass
    for 行索引 ,行向量 in enumerate(np.rot90(灰度向量矩阵, k=-1)):
        for 列索引 ,向量 in enumerate(行向量):
            try:
                if 行向量[列索引][2] == 0:
                    for i in range(8):
                        法线矩阵2[行索引][列索引][i*8-8] = 0
                elif 行向量[列索引][2] == 2:
                    for i in range(8):
                        if 像素内法线:
                            法线矩阵2[行索引][列索引-1][(i+1)*8-1] = 1
                        else:
                            法线矩阵2[行索引][列索引][i*8-8] = 1
            except IndexError: pass
    return 法线矩阵, 法线矩阵2
def 通道图片修复(image_array):
    output_array = image_array.copy()
    current_row = image_array[1:, :]
    mask = (current_row == 1) | (current_row == 255)
    output_array[:-1, :][mask] = current_row[mask]
    return output_array
def 合并通道(img_r_numpy, img_g_numpy, img_alpha_rgb_numpy, 法线纹理):
    img_alpha_gray = 255 if not 法线纹理 else 图片转灰度矩阵(img_alpha_rgb_numpy)
    height, width = img_r_numpy.shape
    combined_img_with_alpha = np.zeros((height, width, 4), dtype=np.uint8)
    combined_img_with_alpha[:, :, 0] = 255
    combined_img_with_alpha[:, :, 1] = img_g_numpy
    combined_img_with_alpha[:, :, 2] = img_r_numpy
    combined_img_with_alpha[:, :, 3] = img_alpha_gray
    rgba_img = combined_img_with_alpha[:, :, [2, 1, 0, 3]]
    return rgba_img
def _64位矩阵转图片(voxel_64d_array, channels_output='single'):
    height, width, _ = voxel_64d_array.shape
    block_size = int(np.sqrt(64))
    reshaped_blocks = voxel_64d_array.reshape(height, width, block_size, block_size)
    transposed_blocks = reshaped_blocks.transpose(0, 2, 1, 3) # (H, 8, W, 8)
    final_height = height * block_size
    final_width = width * block_size
    expanded_2d = transposed_blocks.reshape(final_height, final_width)
    image_2d = np.zeros_like(expanded_2d, dtype=np.uint8)
    image_2d[expanded_2d == 0] = 1
    image_2d[expanded_2d == 1] = 255
    image_2d[expanded_2d == 2] = 128
    return image_2d
def 灰度矩阵转向量矩阵(灰度矩阵):
    height, width = 灰度矩阵.shape
    channels = 5
    灰度矩阵比较矩阵 = np.zeros((height, width, channels), dtype=np.uint8)
    灰度矩阵比较矩阵[:, :, 0] = 灰度矩阵
    directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    for 行索引 in range(height):
        for 列索引 in range(width):
            当前灰度值 = 灰度矩阵[行索引][列索引]
            for i, (row_offset, col_offset) in enumerate(directions):
                new_row = 行索引 + row_offset
                new_col = 列索引 + col_offset
                if 0 <= new_row < height and 0 <= new_col < width:
                    比较值 = 灰度矩阵[new_row][new_col]
                    if 当前灰度值 > 比较值:
                        灰度矩阵比较矩阵[行索引][列索引][i+1] = 2
                    elif 当前灰度值 == 比较值:
                        灰度矩阵比较矩阵[行索引][列索引][i+1] = 1
                    elif 当前灰度值 < 比较值:
                        灰度矩阵比较矩阵[行索引][列索引][i+1] = 0
                else:
                    灰度矩阵比较矩阵[行索引][列索引][i+1] = 3
    return 灰度矩阵比较矩阵       
def 图片转灰度矩阵(图片):
    if len(图片.shape) == 2:
        return 图片
    elif len(图片.shape) == 3:
        灰度矩阵 = (
            0.114 * 图片[:, :, 0] +
            0.587 * 图片[:, :, 1] +
            0.299 * 图片[:, :, 2]
        )
        return np.clip(灰度矩阵, 0, 255).astype(图片.dtype)
