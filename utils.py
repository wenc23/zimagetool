"""
工具函数模块
提供通用的工具函数
"""

import datetime
import os
import sys
from pathlib import Path
from typing import Any, Optional, Tuple, Union


def ensure_directory(directory: Union[str, Path]) -> Path:
    """
    确保目录存在

    Args:
        directory: 目录路径

    Returns:
        目录Path对象
    """
    dir_path = Path(directory)
    dir_path.mkdir(parents=True, exist_ok=True)
    return dir_path


def validate_file_extension(filename: str, allowed_extensions: Tuple[str, ...] = ('.png', '.jpg', '.jpeg')) -> str:
    """
    验证文件扩展名，如果无效则添加默认扩展名

    Args:
        filename: 文件名
        allowed_extensions: 允许的扩展名元组

    Returns:
        验证后的文件名
    """
    if not any(filename.lower().endswith(ext) for ext in allowed_extensions):
        filename += '.png'
    return filename


def format_timestamp(timestamp: Optional[datetime.datetime] = None,
                    format_str: str = "%Y%m%d_%H%M%S") -> str:
    """
    格式化时间戳

    Args:
        timestamp: 时间戳，默认为当前时间
        format_str: 格式化字符串

    Returns:
        格式化后的时间字符串
    """
    if timestamp is None:
        timestamp = datetime.datetime.now()
    return timestamp.strftime(format_str)


def get_unique_filename(base_name: str, directory: Union[str, Path],
                       extension: str = ".png") -> Path:
    """
    获取唯一的文件名

    Args:
        base_name: 基础文件名
        directory: 目录路径
        extension: 文件扩展名

    Returns:
        唯一的文件路径
    """
    directory = Path(directory)
    ensure_directory(directory)

    counter = 1
    while True:
        if counter == 1:
            filename = f"{base_name}{extension}"
        else:
            filename = f"{base_name}_{counter}{extension}"

        file_path = directory / filename
        if not file_path.exists():
            return file_path
        counter += 1


def print_section(title: str, width: int = 60, char: str = "="):
    """
    打印带标题的分隔线

    Args:
        title: 标题
        width: 宽度
        char: 分隔字符
    """
    print("\n" + char * width)
    print(f" {title}")
    print(char * width)


def print_success(message: str):
    """打印成功消息"""
    print(f"✅ {message}")


def print_error(message: str):
    """打印错误消息"""
    print(f"❌ {message}")


def print_warning(message: str):
    """打印警告消息"""
    print(f"⚠️ {message}")


def print_info(message: str):
    """打印信息消息"""
    print(f"💡 {message}")


def print_progress(message: str):
    """打印进度消息"""
    print(f"🔄 {message}")


def get_user_input(prompt_text: str, default_value: Optional[str] = None) -> str:
    """
    获取用户输入，支持默认值

    Args:
        prompt_text: 提示文本
        default_value: 默认值

    Returns:
        用户输入
    """
    if default_value:
        user_input = input(f"{prompt_text} (默认: {default_value}): ").strip()
        return user_input if user_input else default_value
    else:
        return input(f"{prompt_text}: ").strip()


def get_integer_input(prompt_text: str, default_value: Optional[int] = None,
                     min_value: Optional[int] = None, max_value: Optional[int] = None) -> int:
    """
    获取整数输入，支持范围验证

    Args:
        prompt_text: 提示文本
        default_value: 默认值
        min_value: 最小值
        max_value: 最大值

    Returns:
        整数输入
    """
    while True:
        try:
            if default_value is not None:
                input_str = input(f"{prompt_text} (默认: {default_value}): ").strip()
                value = int(input_str) if input_str else default_value
            else:
                value = int(input(f"{prompt_text}: ").strip())

            if min_value is not None and value < min_value:
                print_error(f"值不能小于 {min_value}，请重新输入")
                continue
            if max_value is not None and value > max_value:
                print_error(f"值不能大于 {max_value}，请重新输入")
                continue

            return value
        except ValueError:
            print_error("请输入有效的整数")


def get_float_input(prompt_text: str, default_value: Optional[float] = None,
                   min_value: Optional[float] = None, max_value: Optional[float] = None) -> float:
    """
    获取浮点数输入，支持范围验证

    Args:
        prompt_text: 提示文本
        default_value: 默认值
        min_value: 最小值
        max_value: 最大值

    Returns:
        浮点数输入
    """
    while True:
        try:
            if default_value is not None:
                input_str = input(f"{prompt_text} (默认: {default_value}): ").strip()
                value = float(input_str) if input_str else default_value
            else:
                value = float(input(f"{prompt_text}: ").strip())

            if min_value is not None and value < min_value:
                print_error(f"值不能小于 {min_value}，请重新输入")
                continue
            if max_value is not None and value > max_value:
                print_error(f"值不能大于 {max_value}，请重新输入")
                continue

            return value
        except ValueError:
            print_error("请输入有效的数字")


def get_yes_no_input(prompt_text: str, default_value: Optional[bool] = None) -> bool:
    """
    获取是/否输入

    Args:
        prompt_text: 提示文本
        default_value: 默认值

    Returns:
        True 表示是，False 表示否
    """
    while True:
        if default_value is not None:
            default_str = "y" if default_value else "n"
            prompt = f"{prompt_text} (y/n, 默认{default_str}): "
        else:
            prompt = f"{prompt_text} (y/n): "

        user_input = input(prompt).strip().lower()

        if not user_input and default_value is not None:
            return default_value
        elif user_input in ['y', 'yes', '是']:
            return True
        elif user_input in ['n', 'no', '否']:
            return False
        else:
            print_error("请输入 y/n 或 是/否")


def clear_screen():
    """清空屏幕"""
    os.system('cls' if os.name == 'nt' else 'clear')


def get_terminal_width() -> int:
    """获取终端宽度"""
    try:
        return os.get_terminal_size().columns
    except:
        return 80


def is_running_in_terminal() -> bool:
    """检查是否在终端中运行"""
    return sys.stdin.isatty()