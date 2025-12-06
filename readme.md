# Z-Image-Turbo 图片生成器

一个基于 Z-Image-Turbo 模型的本地图片生成工具，支持中英文双语提示词、多种优化模式，以及智能提示词优化功能。

## 🚀 特性

- **高效生成**: 基于 Z-Image-Turbo 模型，仅需 8 步推理即可生成高质量图片
- **双语支持**: 完美支持中英文提示词，准确渲染双语文字
- **显存优化**: 提供多种优化模式，支持低显存设备运行
- **智能提示词优化**: 集成 DeepSeek API，支持画风、人物、背景等详细配置
- **交互式界面**: 友好的命令行交互界面，易于使用
- **图片管理**: 自动保存生成图片到画廊，包含元数据记录

## 📋 系统要求

### 硬件要求
- **GPU**: NVIDIA GPU (推荐 RTX 3060 或更高)
- **显存**: 最低 8GB，推荐 16GB 或更高
- **内存**: 最低 16GB，推荐 32GB

### 软件要求
- **操作系统**: Windows 10/11, Linux, macOS
- **Python**: 3.8 或更高版本
- **CUDA**: 11.8 或更高版本 (如使用 NVIDIA GPU)

## 🔧 安装步骤

### 1. 克隆项目
```bash
git clone <你的项目地址>
cd image
```

### 2. 下载模型
```bash
cd models
git clone https://huggingface.co/Tongyi-MAI/Z-Image-Turbo
cd ..
```

### 3. 安装依赖
```bash
# 安装 PyTorch (CUDA 版本)
pip install torch==2.9.0 torchvision==0.24.0 torchaudio==2.9.0 --index-url https://download.pytorch.org/whl/cu130

# 安装最新版 diffusers (必须从源码安装以支持 Z-Image)
pip install --upgrade git+https://github.com/huggingface/diffusers transformers accelerate

# 安装网络请求库
pip install requests
```

### 4. 设置 DeepSeek API 密钥 (可选，用于提示词优化)
```bash
# Windows
setx DEEPSEEK_API_KEY "your_api_key_here"

# Linux/Mac
export DEEPSEEK_API_KEY="your_api_key_here"
```

### 5. 验证安装
```bash
python -c "import diffusers; print(f'diffusers版本: {diffusers.__version__}')"
```

## 🎮 使用方法

### 基本使用
```bash
python main.py
```

### 程序流程
1. **选择优化模式**: 程序启动后会让你选择优化模式
   - 基础模式: 平衡性能和显存使用
   - 低显存模式: 适合显存较小的设备

2. **输入提示词**: 输入图片描述，支持中英文
3. **提示词优化** (可选): 选择是否使用智能提示词优化
   - 快速优化: 简单选择画风风格
   - 详细配置: 自定义画风、人物、姿势、背景、服饰等
4. **输入其他参数**:
   - 图片尺寸 (默认 1024x1024)
   - 推理步数 (默认 9 步)
   - 文件名
5. **生成图片**: 程序会自动生成并保存图片

### 提示词优化功能

#### 快速优化模式
- 简洁优化: 简约风格
- 详细优化: 写实风格
- 专业优化: 数字艺术风格
- 创意优化: 抽象艺术风格

#### 详细配置模式
支持用户自由输入以下配置：
- **画风描述**: 如"日系动漫"、"写实油画"、"赛博朋克"
- **人物描述**: 如"年轻女性"、"可爱小孩"、"中年男性"
- **姿势描述**: 如"坐着"、"行走"、"跳舞"、"思考"
- **背景描述**: 如"樱花树下"、"城市街道"、"室内书房"
- **服饰描述**: 如"和服"、"西装"、"运动装"
- **其他选项**: 光照、构图、额外细节等

### 示例提示词

#### 基础提示词
- **中文**: "一位穿着红色汉服的年轻中国女子，精致的刺绣，完美的妆容"
- **英文**: "A beautiful landscape with mountains, lakes, and sunset, photorealistic"

#### 优化后提示词示例
**原始提示词**: "一个人在公园里"
**优化后** (日系动漫风格): "可爱的年轻女孩坐在樱花盛开的公园长椅上，穿着校服和蝴蝶结，日系动漫风格，柔和的光线，全景构图"

## ⚡ 优化模式说明

### 基础模式
- 使用平衡设备映射
- 启用注意力切片
- 适合显存充足的设备

### 低显存模式
- 启用 CPU 卸载
- 更激进的显存优化
- 适合显存有限的设备

## 🎨 提示词优化器 API 使用

### 代码示例
```python
from prompt_optimizer import AdvancedPromptOptimizer, PromptConfig

# 创建优化器
optimizer = AdvancedPromptOptimizer()

# 自定义配置
config = PromptConfig(
    art_style="赛博朋克风格",
    character_description="未来战士",
    background_description="霓虹灯城市",
    lighting_description="夜晚的蓝色灯光"
)

# 优化提示词
optimized_prompt = optimizer.optimize_with_config("一个人在城市里", config)
```

### 便捷函数
```python
from prompt_optimizer import optimize_with_custom_input

# 快速优化
optimized = optimize_with_custom_input(
    "猫在花园里",
    art_style="油画风格",
    background="古典花园"
)
```

## 🛠️ 故障排除

### 常见问题

**1. 导入错误: `cannot import name 'ZImagePipeline'`**
```bash
# 解决方案: 重新安装最新版 diffusers
pip uninstall diffusers
pip install git+https://github.com/huggingface/diffusers
```

**2. 显存不足错误**
- 选择"低显存模式"
- 减小图片尺寸 (如 768x768)
- 关闭其他占用显存的程序

**3. 模型加载失败**
- 检查模型路径: `models/Z-Image-Turbo` 是否存在
- 重新下载模型文件

**4. 提示词优化 API 错误**
- 检查 DeepSeek API 密钥是否正确设置
- 确认网络连接正常
- 如无 API 密钥，优化器将返回原始提示词

## 📊 性能指标

| 配置 | 生成时间 | 显存占用 |
|------|----------|----------|
| 1024x1024, 9步 | ~10秒 | 12-16GB |
| 低显存模式 | ~20-40秒 | ~0GB |

## 🔗 相关文件

- `prompt_optimizer.py` - 提示词优化器核心模块
- `prompt_optimizer_usage.md` - 详细使用说明
- `test_prompt_optimizer.py` - 功能测试脚本

## 🤝 贡献

欢迎提交 Issue 和 Pull Request 来改进这个项目！

## 📄 许可证

本项目基于 MIT 许可证开源。

## 🙏 致谢

- [Z-Image-Turbo](https://huggingface.co/Tongyi-MAI/Z-Image-Turbo) - 强大的图片生成模型
- [DeepSeek](https://platform.deepseek.com/) - 提供智能提示词优化 API
- [Hugging Face](https://huggingface.co) - 提供的模型和工具
- [Diffusers](https://github.com/huggingface/diffusers) - 优秀的扩散模型库

## 📞 支持

如果遇到问题，请：
1. 查看本 README 的故障排除部分
2. 检查模型文件是否完整下载
3. 确认依赖包版本正确
4. 查看 `prompt_optimizer.py` 获取详细优化器使用说明

---

**享受智能创作的乐趣！** 🎨✨