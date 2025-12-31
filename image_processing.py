"""
图片处理模块
处理图片保存、画廊管理等功能
重构版本 - 使用公共模块
"""

import datetime
from pathlib import Path
from utils import ensure_directory
from config_manager import config_manager


def save_to_gallery(image, filename, prompt, width, height, steps, gen_time, optimization_mode):
    """将图片保存到gallery文件夹中的子文件夹"""
    import time

    print(f"🔧 [save_to_gallery] 开始保存流程")
    print(f"   - filename: {filename}")
    print(f"   - size: {width}x{height}")

    # 确保gallery文件夹存在
    gallery_dir = ensure_directory(config_manager.get("gallery_dir", "gallery"))
    print(f"   - gallery_dir: {gallery_dir}")
    print(f"   - gallery_dir exists: {gallery_dir.exists()}")

    # 获取文件名（不含扩展名）作为子文件夹名
    base_name = Path(filename).stem
    extension = Path(filename).suffix
    print(f"   - base_name: {base_name}")
    print(f"   - extension: {extension}")

    # 创建以文件名命名的子文件夹
    image_folder = gallery_dir / base_name

    # 如果文件夹已存在，添加时间戳
    if image_folder.exists():
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        image_folder = gallery_dir / f"{base_name}_{timestamp}"
        print(f"   - 文件夹已存在，使用新名称: {image_folder.name}")

    print(f"   - 最终文件夹路径: {image_folder}")

    ensure_directory(image_folder)
    print(f"   - 文件夹创建完成: {image_folder.exists()}")

    # 保存图片到子文件夹（带超时检测）
    image_path = image_folder / f"{base_name}{extension}"
    print(f"   - 图片保存路径: {image_path}")
    save_start = time.time()

    try:
        print(f"   - 开始调用 image.save()...")
        image.save(image_path)
        save_time = time.time() - save_start
        print(f"💾 图片保存完成，耗时: {save_time:.2f}秒")
        print(f"   - 文件存在: {image_path.exists()}")
        print(f"   - 文件大小: {image_path.stat().st_size / 1024:.2f} KB")
    except Exception as e:
        print(f"❌ 图片保存失败: {e}")
        import traceback
        traceback.print_exc()
        raise

    # 创建参数信息文件
    info_file = image_folder / f"{base_name}_info.txt"
    print(f"   - 创建info文件: {info_file}")
    try:
        with open(info_file, 'w', encoding='utf-8') as f:
            f.write(f"图片名称: {base_name}{extension}\n")
            f.write(f"提示词: {prompt}\n")
            f.write(f"图片尺寸: {width}x{height}\n")
            f.write(f"推理步数: {steps}\n")
            f.write(f"优化模式: {optimization_mode}\n")
            f.write(f"生成时间: {gen_time:.2f}秒\n")
            f.write(f"创建时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        print(f"   - info文件创建完成")
    except Exception as e:
        print(f"❌ info文件创建失败: {e}")
        # info文件失败不影响主流程

    print(f"✅ [save_to_gallery] 全部完成")
    return image_folder