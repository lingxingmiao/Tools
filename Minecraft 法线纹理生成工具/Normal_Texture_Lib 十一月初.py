import cv2
import numpy as np
from PIL import Image
import os

class Normal_Texture:
    def 参考(self, 原始高度图片):
        图片 = self.Read_Image(原始高度图片)
        _n图片 = self.Image_to_Normal(图片, True)
        pil_img = Image.fromarray(_n图片, mode='RGBA')
        pil_img.save(f"{os.path.basename(原始高度图片)}_n.png")
    def Image_to_Normal(self, 图片, 启用高度):
        灰度矩阵 = self.图片转灰度矩阵(图片)
        灰度向量矩阵 = self.灰度矩阵转向量矩阵(灰度矩阵)
        R通道法线, G通道法线 = self.向量矩阵转法线纹理(图片, 灰度向量矩阵)
        i, R通道图片 = self._64位矩阵转图片(R通道法线, channels_output='single')
        i, G通道图片 = self._64位矩阵转图片(G通道法线, channels_output='single')
        G通道图片 = cv2.rotate(G通道图片, cv2.ROTATE_90_COUNTERCLOCKWISE)
        return self.合并通道(R通道图片, G通道图片, np.repeat(np.repeat(图片, 8, axis=0), 8, axis=1), 启用高度)
    def 向量矩阵转法线纹理(self, 图片, 灰度向量矩阵):
        图片高, 图片宽 = 图片.shape[:2]
        法线矩阵 = np.full((图片高, 图片宽, 64), 2, dtype=np.uint8)
        法线矩阵2 = np.full((图片高, 图片宽, 64), 2, dtype=np.uint8)
        for 行索引 ,行向量 in enumerate(灰度向量矩阵):
            for 列索引 ,向量 in enumerate(行向量):
                if 行向量[列索引][4] == 0:
                    for i in range(8):
                        法线矩阵[行索引][列索引][(i+1)*8-1] = 0
                elif 行向量[列索引][4] == 2:
                    for i in range(8):
                        法线矩阵[行索引][列索引][(i+1)*8-1] = 1
                elif 行向量[列索引][4] == 3:
                    continue
        右转灰度向量矩阵 = np.rot90(灰度向量矩阵, k=-1)
        self.保存矩阵(右转灰度向量矩阵, "右转灰度矩阵比较矩阵.txt")
        for 行索引 ,行向量 in enumerate(右转灰度向量矩阵):
            for 列索引 ,向量 in enumerate(行向量):
                if 行向量[列索引][2] == 0:
                    for i in range(8):
                        法线矩阵2[行索引][列索引][i*8-8] = 0
                elif 行向量[列索引][2] == 2:
                    for i in range(8):
                        法线矩阵2[行索引][列索引][i*8-8] = 1
                elif 行向量[列索引][2] == 3:
                    continue
        return 法线矩阵, 法线矩阵2
    def 合并通道(self, img_r_numpy, img_g_numpy, img_alpha_rgb_numpy, 启用高度):
        img_alpha_gray = 255 if 启用高度 else cv2.cvtColor(img_alpha_rgb_numpy, cv2.COLOR_RGB2GRAY)
        height, width = img_r_numpy.shape
        combined_img_with_alpha = np.zeros((height, width, 4), dtype=np.uint8)
        combined_img_with_alpha[:, :, 0] = 255
        combined_img_with_alpha[:, :, 1] = img_g_numpy
        combined_img_with_alpha[:, :, 2] = img_r_numpy
        combined_img_with_alpha[:, :, 3] = img_alpha_gray
        rgba_img = combined_img_with_alpha[:, :, [2, 1, 0, 3]]
        return rgba_img
    def _64位矩阵转图片(self, voxel_64d_array, channels_output='single'):
        height, width, _ = voxel_64d_array.shape
        block_size = int(np.sqrt(64))
        reshaped_blocks = voxel_64d_array.reshape(height, width, block_size, block_size)
        transposed_blocks = reshaped_blocks.transpose(0, 2, 1, 3) # (H, 8, W, 8)
        final_height = height * block_size
        final_width = width * block_size
        expanded_2d = transposed_blocks.reshape(final_height, final_width)
        image_2d = np.zeros_like(expanded_2d, dtype=np.uint8)
        image_2d[expanded_2d == 0] = 0
        image_2d[expanded_2d == 1] = 255
        image_2d[expanded_2d == 2] = 128
        img = Image.fromarray(image_2d, mode='L')
        return img, image_2d
    def 灰度矩阵转向量矩阵(self, 灰度矩阵):
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
    def Read_Image(self, 文件路径):
        pil_image = Image.open(文件路径)
        图片 = np.array(pil_image)
        if len(图片.shape) == 3 and 图片.shape[2] == 3:
            图片 = cv2.cvtColor(图片, cv2.COLOR_RGB2BGR)
        return 图片
    def 保存矩阵(self, 矩阵, 文件路径):
        height, width, channels = 矩阵.shape
        with open(文件路径, 'w', encoding='utf-8') as f:
            for row in range(height):
                row_data = []
                for col in range(width):
                    pixel_values = 矩阵[row, col, :].tolist()
                    row_data.append(pixel_values)
                f.write(str(row_data) + '\n')
            return True
        return False
    def 图片转灰度矩阵(self, 图片):
        if len(图片.shape) == 2:
            return 图片
        elif len(图片.shape) == 3:
            return cv2.cvtColor(图片, cv2.COLOR_BGR2GRAY)

if __name__ == "__main__":
    # 如何使用
    Normal_Texture().参考(r"machine_coil_nichrome.png")