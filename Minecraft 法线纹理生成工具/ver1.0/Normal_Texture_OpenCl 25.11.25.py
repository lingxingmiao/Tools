import numpy as np
import Normal_Texture as nt
from PIL import Image as img
import os
try:
    import pyopencl as cl
    _编译的内核缓存 = {}
    os.environ['PYOPENCL_NO_CACHE'] = '1'
    def init_opencl():
        try:
            platforms = cl.get_platforms()
            if not platforms:
                return None, None
            platform = platforms[0]
            devices = platform.get_devices()
            if not devices:
                return None, None
            context = cl.Context([devices[0]])
            queue = cl.CommandQueue(context)
            _OpenCL = True
            return context, queue, _OpenCL
        except Exception as e:
            _OpenCL = False
            return None, None, _OpenCL
    context, queue, _OpenCL = init_opencl()
except Exception:
    _OpenCL = False

def ImageTNormal(图片: np.ndarray, 法线纹理: np.ndarray = [True, True, False]) -> np.ndarray:
    """图片转法线纹理
    Args:
        图片 (多维数组): ReadImage方法读取的灰度数组
        法线纹理 (数组): [高度图, 左上纹理空隙修复.启用像素内法线会自动关闭, 像素内法线]
    Returns:
        多维数组: RGBA格式数组图片，可以使用SaveImage方法保存
    """
    global _OpenCL
    图片宽, 图片高 = 图片.shape[:2]
    if (图片宽 * 图片高) > 1024:
        _OpenCL = False
    灰度矩阵 = 图片转灰度矩阵(图片)
    灰度向量矩阵 = 灰度矩阵转向量矩阵(灰度矩阵)
    R通道法线, G通道法线 = 向量矩阵转法线纹理(图片, 灰度向量矩阵, 法线纹理[2])
    法线纹理[1] = False if 法线纹理[2] else 法线纹理[1]
    R通道图片 = 通道图片修复(_64位矩阵转图片(R通道法线, channels_output='single')) if 法线纹理[1] else _64位矩阵转图片(R通道法线, channels_output='single')
    G通道图片 = np.rot90(通道图片修复(_64位矩阵转图片(G通道法线, channels_output='single')) if 法线纹理[1] else _64位矩阵转图片(G通道法线, channels_output='single'), k=1)
    if _OpenCL:
        法线图片 = 合并通道(R通道图片, G通道图片, 扩展8倍(图片), 法线纹理[0])
    else:
        法线图片 = 合并通道(R通道图片, G通道图片, np.repeat(np.repeat(图片, 8, axis=0), 8, axis=1), 法线纹理[0])
    return 法线图片
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
    if _OpenCL:
        return nt.向量矩阵转法线纹理(图片, 灰度向量矩阵, 像素内法线)
    图片高, 图片宽 = 图片.shape[:2]
    灰度向量矩阵_flat = 灰度向量矩阵.astype(np.uint8).flatten()
    法线矩阵 = np.full((图片高, 图片宽, 64), 2, dtype=np.uint8)
    法线矩阵2 = np.full((图片高, 图片宽, 64), 2, dtype=np.uint8)
    kernel_code = """
    __kernel void vector_to_normal(
        __global const uchar* gray_vector_matrix,
        __global uchar* normal_matrix,
        __global uchar* normal_matrix2,
        const int height,
        const int width,
        const int pixel_internal_normal)
    {
        int row = get_global_id(0);
        int col = get_global_id(1);
        if (row >= height || col >= width) return;
        int idx = (row * width + col) * 5;
        uchar center_value = gray_vector_matrix[idx + 4];
        if (center_value == 0) {
            for (int i = 0; i < 8; i++) {
                int normal_idx = (row * width + col) * 64 + (i + 1) * 8 - 1;
                if (normal_idx < height * width * 64) {
                    normal_matrix[normal_idx] = 0;
                }
            }
        } else if (center_value == 2) {
            for (int i = 0; i < 8; i++) {
                if (pixel_internal_normal) {
                    int next_col = col + 1;
                    if (next_col < width) {
                        int normal_idx = (row * width + next_col) * 64 + i * 8;
                        if (normal_idx >= 0 && normal_idx < height * width * 64) {
                            normal_matrix[normal_idx] = 1;
                        }
                    }
                } else {
                    int normal_idx = (row * width + col) * 64 + (i + 1) * 8 - 1;
                    if (normal_idx < height * width * 64) {
                        normal_matrix[normal_idx] = 1;
                    }
                }
            }
        }
        int rot_row = col;
        int rot_col = height - 1 - row;
        if (rot_row >= 0 && rot_row < width && rot_col >= 0 && rot_col < height) {
            int rot_idx = (rot_row * height + rot_col) * 5;
            uchar rot_value = gray_vector_matrix[rot_idx + 2];
            if (rot_value == 0) {
                for (int i = 0; i < 8; i++) {
                    int normal2_idx = (rot_row * height + rot_col) * 64 + i * 8;
                    if (normal2_idx >= 0 && normal2_idx < height * width * 64) {
                        normal_matrix2[normal2_idx] = 0;
                    }
                }
            } else if (rot_value == 2) {
                for (int i = 0; i < 8; i++) {
                    if (pixel_internal_normal) {
                        int prev_col = rot_col - 1;
                        if (prev_col >= 0) {
                            int normal2_idx = (rot_row * height + prev_col) * 64 + (i + 1) * 8 - 1;
                            if (normal2_idx < height * width * 64) {
                                normal_matrix2[normal2_idx] = 1;
                            }
                        }
                    } else {
                        int normal2_idx = (rot_row * height + rot_col) * 64 + i * 8;
                        if (normal2_idx >= 0 && normal2_idx < height * width * 64) {
                            normal_matrix2[normal2_idx] = 1;
                        }
                    }
                }
            }
        }
    }"""
    program = cl.Program(context, kernel_code).build()
    gray_vector_buf = cl.Buffer(context, cl.mem_flags.READ_ONLY | cl.mem_flags.COPY_HOST_PTR, hostbuf=灰度向量矩阵_flat)
    normal_buf = cl.Buffer(context, cl.mem_flags.READ_WRITE, size=法线矩阵.nbytes)
    normal2_buf = cl.Buffer(context, cl.mem_flags.READ_WRITE, size=法线矩阵2.nbytes)
    cl.enqueue_copy(queue, normal_buf, 法线矩阵)
    cl.enqueue_copy(queue, normal2_buf, 法线矩阵2)
    global_size = (图片高, 图片宽)
    program.vector_to_normal(queue, global_size, None,gray_vector_buf, normal_buf, normal2_buf,np.int32(图片高), np.int32(图片宽),np.int32(像素内法线))
    cl.enqueue_copy(queue, 法线矩阵, normal_buf)
    cl.enqueue_copy(queue, 法线矩阵2, normal2_buf)
    法线矩阵2 = np.rot90(法线矩阵2, 3)
    return 法线矩阵, 法线矩阵2
    

def 通道图片修复(image_array):
    if _OpenCL:
        return nt.通道图片修复(image_array)
    height, width = image_array.shape
    image_flat = image_array.astype(np.uint8).flatten()
    output_array = np.zeros_like(image_array)
    kernel_code = """
    __kernel void channel_repair_optimized(
        __global const uchar* input_image,
        __global uchar* output_image,
        const int height,
        const int width)
    {
        int row = get_global_id(0);
        int col = get_global_id(1);
        
        if (row >= height || col >= width) return;
        
        int idx = row * width + col;
        uchar current_value = input_image[idx];
        uchar output_value = current_value;
        
        // 如果不是最后一行
        if (row < height - 1) {
            int next_idx = idx + width;  // 下一行相同列
            uchar next_value = input_image[next_idx];
            
            // 检查下一行的值是否为 1 或 255
            if (next_value == 1 || next_value == 255) {
                output_value = next_value;
            }
        }
        
        output_image[idx] = output_value;
    }
    """
    

    kernel_key = "channel_repair_optimized"
    if kernel_key not in _编译的内核缓存:
        program = cl.Program(context, kernel_code).build()
        _编译的内核缓存[kernel_key] = program.channel_repair_optimized
    kernel = _编译的内核缓存[kernel_key]
    
    input_buf = cl.Buffer(context, cl.mem_flags.READ_ONLY | cl.mem_flags.COPY_HOST_PTR, 
                            hostbuf=image_flat)
    output_buf = cl.Buffer(context, cl.mem_flags.WRITE_ONLY, 
                            size=output_array.nbytes)
    
    global_size = (height, width)
    kernel(queue, global_size, None,
            input_buf, output_buf,
            np.int32(height), np.int32(width))
    
    cl.enqueue_copy(queue, output_array, output_buf)
    return output_array
def 合并通道(img_r_numpy, img_g_numpy, img_alpha_rgb_numpy, 法线纹理):
    if _OpenCL:
        return nt.合并通道(img_r_numpy, img_g_numpy, img_alpha_rgb_numpy, 法线纹理)
    height, width = img_r_numpy.shape
    img_r_flat = img_r_numpy.astype(np.uint8).flatten()
    img_g_flat = img_g_numpy.astype(np.uint8).flatten()
    if not 法线纹理:
        img_alpha_gray = np.full((height, width), 255, dtype=np.uint8)
    else:
        img_alpha_gray = 图片转灰度矩阵(img_alpha_rgb_numpy)
    img_alpha_flat = img_alpha_gray.astype(np.uint8).flatten()
    rgba_img = np.zeros((height, width, 4), dtype=np.uint8)
    kernel_code = """
    __kernel void merge_channels(
        __global const uchar* img_r,
        __global const uchar* img_g,
        __global const uchar* img_alpha,
        __global uchar* output_rgba,
        const int height,
        const int width)
    {
        int row = get_global_id(0);
        int col = get_global_id(1);
        
        if (row >= height || col >= width) return;
        
        int idx = row * width + col;
        int rgba_idx = idx * 4;
        
        // 直接按照目标格式 [R, G, B, A] 写入
        // 注意：原函数最后有通道重排 [2, 1, 0, 3]，所以我们直接写入正确的位置
        output_rgba[rgba_idx] = img_r[idx];      // R 通道
        output_rgba[rgba_idx + 1] = img_g[idx];  // G 通道  
        output_rgba[rgba_idx + 2] = 255;         // B 通道固定为 255
        output_rgba[rgba_idx + 3] = img_alpha[idx]; // Alpha 通道
    }"""
    program = cl.Program(context, kernel_code).build()
    img_r_buf = cl.Buffer(context, cl.mem_flags.READ_ONLY | cl.mem_flags.COPY_HOST_PTR, hostbuf=img_r_flat)
    img_g_buf = cl.Buffer(context, cl.mem_flags.READ_ONLY | cl.mem_flags.COPY_HOST_PTR, hostbuf=img_g_flat)
    img_alpha_buf = cl.Buffer(context, cl.mem_flags.READ_ONLY | cl.mem_flags.COPY_HOST_PTR, hostbuf=img_alpha_flat)
    output_buf = cl.Buffer(context, cl.mem_flags.WRITE_ONLY, size=rgba_img.nbytes)
    global_size = (height, width)
    program.merge_channels(queue, global_size, None,img_r_buf, img_g_buf, img_alpha_buf, output_buf,np.int32(height), np.int32(width))
    cl.enqueue_copy(queue, rgba_img, output_buf)
    return rgba_img
def _64位矩阵转图片(voxel_64d_array, channels_output='single'):
    if _OpenCL:
        return nt._64位矩阵转图片(voxel_64d_array, channels_output)
    height, width, _ = voxel_64d_array.shape
    block_size = 8
    voxel_flat = voxel_64d_array.astype(np.uint8).flatten()
    final_height = height * block_size
    final_width = width * block_size
    image_2d = np.zeros((final_height, final_width), dtype=np.uint8)
    kernel_code = """
    __kernel void voxel_to_image_optimized(
        __global const uchar* voxel_array,
        __global uchar* output_image,
        const int height,
        const int width,
        const int block_size)
    {
        int output_row = get_global_id(0);
        int output_col = get_global_id(1);
        if (output_row >= height * block_size || output_col >= width * block_size) return;
        int block_row = output_row / block_size;
        int block_col = output_col / block_size;
        int inner_row = output_row % block_size;
        int inner_col = output_col % block_size;
        int voxel_index = (block_row * width + block_col) * (block_size * block_size) + 
                         inner_row * block_size + inner_col;
        uchar voxel_value = voxel_array[voxel_index];
        uchar pixel_value;
        if (voxel_value == 0) {
            pixel_value = 1;
        } else if (voxel_value == 1) {
            pixel_value = 255;
        } else if (voxel_value == 2) {
            pixel_value = 128;
        } else {
            pixel_value = 0;
        }
        output_image[output_row * (width * block_size) + output_col] = pixel_value;
    }"""
    program = cl.Program(context, kernel_code).build()
    voxel_buf = cl.Buffer(context, cl.mem_flags.READ_ONLY | cl.mem_flags.COPY_HOST_PTR, hostbuf=voxel_flat)
    output_buf = cl.Buffer(context, cl.mem_flags.WRITE_ONLY, size=image_2d.nbytes)
    global_size = (final_height, final_width)
    program.voxel_to_image_optimized(queue, global_size, None,voxel_buf, output_buf,np.int32(height), np.int32(width),np.int32(block_size))
    cl.enqueue_copy(queue, image_2d, output_buf)
    return image_2d
    
def 灰度矩阵转向量矩阵(灰度矩阵):
    if _OpenCL:
        return nt.灰度矩阵转向量矩阵(灰度矩阵)
    height, width = 灰度矩阵.shape
    灰度矩阵_flat = 灰度矩阵.astype(np.uint8).flatten()
    灰度矩阵比较矩阵 = np.zeros((height, width, 5), dtype=np.uint8)
    kernel_code = """
    __kernel void gray_to_vector(
        __global const uchar* gray_matrix,
        __global uchar* result_matrix,
        const int height,
        const int width)
    {
        int row = get_global_id(0);
        int col = get_global_id(1);
        if (row >= height || col >= width) return;
        int idx = (row * width + col) * 5;
        uchar current_value = gray_matrix[row * width + col];
        result_matrix[idx] = current_value;
        int2 directions[4] = {
            (int2)(-1, 0),
            (int2)(1, 0),
            (int2)(0, -1),
            (int2)(0, 1)
        };
        for (int i = 0; i < 4; i++) {
            int new_row = row + directions[i].x;
            int new_col = col + directions[i].y;
            if (new_row >= 0 && new_row < height && new_col >= 0 && new_col < width) {
                uchar compare_value = gray_matrix[new_row * width + new_col];
                if (current_value > compare_value) {
                    result_matrix[idx + i + 1] = 2;
                } else if (current_value == compare_value) {
                    result_matrix[idx + i + 1] = 1;
                } else {
                    result_matrix[idx + i + 1] = 0;
                }
            } else {
                result_matrix[idx + i + 1] = 3;
            }
        }
    }"""
    program = cl.Program(context, kernel_code).build()
    gray_buf = cl.Buffer(context, cl.mem_flags.READ_ONLY | cl.mem_flags.COPY_HOST_PTR, hostbuf=灰度矩阵_flat)
    result_buf = cl.Buffer(context, cl.mem_flags.WRITE_ONLY, size=灰度矩阵比较矩阵.nbytes)
    global_size = (height, width)
    program.gray_to_vector(queue, global_size, None,gray_buf, result_buf,np.int32(height), np.int32(width))
    cl.enqueue_copy(queue, 灰度矩阵比较矩阵, result_buf)
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
def 扩展8倍(图片):
    height, width = 图片.shape[:2]
    channels = 图片.shape[2] if len(图片.shape) == 3 else 1
    重复次数 = 8
    output_height = height * 重复次数
    output_width = width * 重复次数
    output_size = output_height * output_width * channels
    图片_flat = 图片.astype(np.uint8).flatten()
    if channels == 1:
        output_array = np.zeros((output_height, output_width), dtype=np.uint8)
    else:
        output_array = np.zeros((output_height, output_width, channels), dtype=np.uint8)
    kernel_code = """
    __kernel void expand_8x8_simple(
        __global const uchar* input_image,
        __global uchar* output_image,
        const int input_height,
        const int input_width,
        const int output_height,
        const int output_width,
        const int channels)
    {
        int out_row = get_global_id(0);
        int out_col = get_global_id(1);
        
        if (out_row >= output_height || out_col >= output_width) return;
        
        // 计算在输入图片中的对应位置
        int in_row = out_row / 8;
        int in_col = out_col / 8;
        
        if (in_row >= input_height) in_row = input_height - 1;
        if (in_col >= input_width) in_col = input_width - 1;
        
        int input_idx = (in_row * input_width + in_col) * channels;
        int output_idx = (out_row * output_width + out_col) * channels;
        
        for (int c = 0; c < channels; c++) {
            output_image[output_idx + c] = input_image[input_idx + c];
        }
    }"""
    kernel_key = "expand_8x8_simple"
    if kernel_key not in _编译的内核缓存:
        program = cl.Program(context, kernel_code).build()
        _编译的内核缓存[kernel_key] = program.expand_8x8_simple
    kernel = _编译的内核缓存[kernel_key]
    input_buf = cl.Buffer(context, cl.mem_flags.READ_ONLY | cl.mem_flags.COPY_HOST_PTR, hostbuf=图片_flat)
    output_buf = cl.Buffer(context, cl.mem_flags.WRITE_ONLY, size=output_array.nbytes)
    max_global_size = 4096
    global_height = min(output_height, max_global_size)
    global_width = min(output_width, max_global_size)
    global_size = (global_height, global_width)
    kernel(queue, global_size, None,input_buf, output_buf,np.int32(height), np.int32(width), np.int32(output_height), np.int32(output_width),np.int32(channels))
    cl.enqueue_copy(queue, output_array, output_buf)
    return output_array
