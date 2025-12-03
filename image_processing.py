"""
图片处理模块
处理图片保存、画廊管理等功能
"""

import datetime
from pathlib import Path

def save_to_gallery(image, filename, prompt, width, height, steps, gen_time, optimization_mode):
    """将图片保存到gallery文件夹中的子文件夹"""
    # 确保gallery文件夹存在
    gallery_dir = Path("gallery")
    gallery_dir.mkdir(exist_ok=True)
    
    # 获取文件名（不含扩展名）作为子文件夹名
    base_name = Path(filename).stem
    extension = Path(filename).suffix
    
    # 创建以文件名命名的子文件夹
    image_folder = gallery_dir / base_name
    
    # 如果文件夹已存在，添加时间戳
    if image_folder.exists():
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        image_folder = gallery_dir / f"{base_name}_{timestamp}"
    
    image_folder.mkdir(exist_ok=True)
    
    # 保存图片到子文件夹
    image_path = image_folder / f"{base_name}{extension}"
    image.save(image_path)
    
    # 创建参数信息文件
    info_file = image_folder / f"{base_name}_info.txt"
    with open(info_file, 'w', encoding='utf-8') as f:
        f.write(f"图片名称: {base_name}{extension}\n")
        f.write(f"提示词: {prompt}\n")
        f.write(f"图片尺寸: {width}x{height}\n")
        f.write(f"推理步数: {steps}\n")
        f.write(f"优化模式: {optimization_mode}\n")
        f.write(f"生成时间: {gen_time:.2f}秒\n")
        f.write(f"创建时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    return image_folder