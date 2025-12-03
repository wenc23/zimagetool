"""
用户输入处理模块
提供用户输入验证和获取功能
"""

def get_user_input(prompt_text, default_value=None):
    """获取用户输入，支持默认值"""
    if default_value:
        user_input = input(f"{prompt_text} (默认: {default_value}): ").strip()
        return user_input if user_input else default_value
    else:
        return input(f"{prompt_text}: ").strip()

def get_integer_input(prompt_text, default_value=None, min_value=None, max_value=None):
    """获取整数输入，支持范围验证"""
    while True:
        try:
            if default_value:
                input_str = input(f"{prompt_text} (默认: {default_value}): ").strip()
                value = int(input_str) if input_str else default_value
            else:
                value = int(input(f"{prompt_text}: ").strip())
            
            if min_value is not None and value < min_value:
                print(f"❌ 值不能小于 {min_value}，请重新输入")
                continue
            if max_value is not None and value > max_value:
                print(f"❌ 值不能大于 {max_value}，请重新输入")
                continue
                
            return value
        except ValueError:
            print("❌ 请输入有效的整数")