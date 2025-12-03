"""
优化模式模块
处理显存优化和性能调优相关功能
"""

def select_optimization_mode():
    """让用户选择优化模式"""
    print("\n" + "="*50)
    print("🔧 请选择显存优化模式")
    print("="*50)
    print("1. 基础优化 - 平衡性能和显存使用")
    print("2. 低显存优化 - 最小化显存占用，适合低显存设备")
    
    while True:
        from user_input import get_integer_input
        choice = get_integer_input("请选择优化模式", 1, 1, 2)
        
        if choice == 1:
            print("✅ 已选择: 基础优化模式")
            return "basic"
        elif choice == 2:
            print("✅ 已选择: 低显存优化模式")
            return "low_vram"

def apply_low_vram_optimizations(pipe):
    """应用最低显存优化方法"""
    print("🔧 启用低显存优化模式...")
    
    try:
        # 先重置设备映射，以便启用CPU卸载
        if hasattr(pipe, 'reset_device_map'):
            print("🔄 重置设备映射...")
            pipe.reset_device_map()
        
        # 启用所有可用的内存优化技术
        pipe.enable_attention_slicing("max")  # 最大切片
        pipe.enable_sequential_cpu_offload()  # 顺序CPU卸载
        
        print("✅ 低显存优化已启用")
    except Exception as e:
        print(f"⚠️ 启用低显存优化时出错: {e}")
        print("💡 尝试使用基本优化...")
        # 如果出错，至少启用注意力切片
        pipe.enable_attention_slicing("max")
        print("✅ 已启用基本优化")

def is_high_resolution(width, height):
    """检查是否为高分辨率（大于2K）"""
    # 2K分辨率通常指2048×1080或更高
    # 这里我们检查任一边长大于2048或总像素数大于2K
    return width > 2048 or height > 2048 or (width * height > 2048 * 1080)