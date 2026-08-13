"""
图片处理模块
处理图片保存、画廊管理等功能
重构版本 - 使用公共模块
"""

import datetime
import shutil
from pathlib import Path
from PIL import Image, ImageOps
from utils import ensure_directory, validate_file_extension
from config_manager import config_manager


THUMBNAIL_SIZE = (640, 640)
THUMBNAIL_SUFFIX = "_thumb.webp"


def get_thumbnail_path(image_path):
    image_path = Path(image_path)
    return image_path.with_name(f"{image_path.stem}{THUMBNAIL_SUFFIX}")


def create_gallery_thumbnail(image_source, image_path, force=False):
    """为画廊生成体积较小的 WebP 缩略图，使用原子替换避免半文件。"""
    image_path = Path(image_path)
    thumbnail_path = get_thumbnail_path(image_path)
    if thumbnail_path.exists() and not force:
        return thumbnail_path

    temporary_path = thumbnail_path.with_name(f".{thumbnail_path.name}.tmp")
    opened_image = None
    try:
        if isinstance(image_source, (str, Path)):
            opened_image = Image.open(image_source)
            source = opened_image
        else:
            source = image_source

        thumbnail = ImageOps.exif_transpose(source).copy()
        thumbnail.thumbnail(THUMBNAIL_SIZE, Image.Resampling.LANCZOS, reducing_gap=3.0)
        if thumbnail.mode not in {"RGB", "RGBA"}:
            thumbnail = thumbnail.convert("RGB")
        thumbnail.save(temporary_path, format="WEBP", quality=82, method=4)
        temporary_path.replace(thumbnail_path)
        return thumbnail_path
    finally:
        if opened_image is not None:
            opened_image.close()
        temporary_path.unlink(missing_ok=True)

def save_to_gallery(image, filename, prompt, width, height, steps, gen_time, optimization_mode,
                    cancellation_check=None):
    """将图片保存到gallery文件夹中的子文件夹"""
    import time

    print(f"🔧 [save_to_gallery] 开始保存流程")
    print(f"   - filename: {filename}")
    print(f"   - size: {width}x{height}")

    filename = validate_file_extension(filename)
    gallery_dir = ensure_directory(config_manager.get("gallery_dir", "gallery")).resolve()
    print(f"   - gallery_dir: {gallery_dir}")
    print(f"   - gallery_dir exists: {gallery_dir.exists()}")

    # 获取文件名（不含扩展名）作为子文件夹名
    base_name = Path(filename).stem
    extension = Path(filename).suffix
    print(f"   - base_name: {base_name}")
    print(f"   - extension: {extension}")

    # 原子创建唯一目录，避免同名请求在同一秒内互相覆盖。
    image_folder = gallery_dir / base_name
    counter = 0
    while True:
        try:
            image_folder.mkdir(parents=False, exist_ok=False)
            break
        except FileExistsError:
            counter += 1
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            suffix = f"_{counter}" if counter > 1 else ""
            image_folder = gallery_dir / f"{base_name}_{timestamp}{suffix}"

    print(f"   - 最终文件夹路径: {image_folder}")

    print(f"   - 文件夹创建完成: {image_folder.exists()}")

    def check_cancelled():
        if not cancellation_check:
            return
        try:
            cancellation_check()
        except Exception:
            shutil.rmtree(image_folder, ignore_errors=True)
            raise

    # 保存图片到子文件夹（带超时检测）
    image_path = image_folder / f"{base_name}{extension}"
    print(f"   - 图片保存路径: {image_path}")
    save_start = time.time()

    try:
        check_cancelled()
        print(f"   - 开始调用 image.save()...")
        image.save(image_path)
        check_cancelled()
        save_time = time.time() - save_start
        print(f"💾 图片保存完成，耗时: {save_time:.2f}秒")
        print(f"   - 文件存在: {image_path.exists()}")
        print(f"   - 文件大小: {image_path.stat().st_size / 1024:.2f} KB")
    except Exception as e:
        print(f"❌ 图片保存失败: {e}")
        shutil.rmtree(image_folder, ignore_errors=True)
        raise

    # 新作品在保存阶段立即生成缩略图，画廊无需传输原始大图。
    try:
        check_cancelled()
        create_gallery_thumbnail(image, image_path)
        check_cancelled()
    except Exception as thumbnail_error:
        check_cancelled()
        print(f"⚠️ 缩略图生成失败，将在访问画廊时重试: {thumbnail_error}")

    # 创建参数信息文件
    info_file = image_folder / f"{base_name}_info.txt"
    print(f"   - 创建info文件: {info_file}")
    try:
        check_cancelled()
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
        check_cancelled()
        print(f"❌ info文件创建失败: {e}")
        # info文件失败不影响主流程

    check_cancelled()
    print(f"✅ [save_to_gallery] 全部完成")
    return image_path
