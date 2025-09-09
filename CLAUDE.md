# CLAUDE.md

此文件为Claude Code (claude.ai/code) 在此代码库中工作提供指导。

## 开发命令

### 运行服务器
```bash
uv run pdfreadermcp
```

### 包管理
```bash
# 安装依赖
uv sync

# 安装开发依赖
uv sync --dev

# 运行测试（暂无pytest配置，使用独立测试文件）
uv run python test_easyocr.py
```

### 项目设置
- 使用 `uv` 包管理器进行Python依赖管理
- 要求Python 3.11+（参见.python-version）
- 入口点：`src/pdfreadermcp/__main__.py`
- 使用中国PyPI镜像加速依赖安装

## 架构概览

### MCP服务器结构
这是一个基于FastMCP构建的MCP（模型上下文协议）服务器，提供PDF处理功能。

**核心组件：**
- `src/pdfreadermcp/server.py`: FastMCP服务器，包含工具定义（`read_pdf`, `ocr_pdf`）
- `src/pdfreadermcp/tools/pdf_reader.py`: 使用pdfplumber进行文本提取
- `src/pdfreadermcp/tools/pdf_ocr.py`: 使用**EasyOCR**进行OCR处理（不是PaddleOCR）
- `src/pdfreadermcp/utils/`: 支持缓存、分块和文件处理的工具类

### 工具架构
- **read_pdf**: 智能文本提取，具备质量检测功能
- **ocr_pdf**: 基于EasyOCR的OCR，用于扫描文档
- 两个工具都支持灵活的页面范围语法：`"1,3,5-10,-1"`
- 输出格式：包含分块、元数据和质量评分的结构化JSON

### 核心功能
- **智能缓存系统**: `utils/cache.py`中基于文件的失效缓存
- **文本质量分析**: 自动检测何时需要OCR
- **分块策略**: 可配置的文本分割，保持上下文重叠
- **多语言OCR**: EasyOCR，默认支持中文和英文

### 依赖关系（重要：使用EasyOCR，不是PaddleOCR）
- **核心依赖**: mcp[cli], pdfplumber, pdf2image, easyocr, torch, numpy
- **文本处理**: langchain-text-splitters用于分块
- **图像处理**: pillow用于图像处理
- **配置**: 使用中国PyPI镜像加速安装

### OCR引擎详情
服务器使用**EasyOCR**，不是PaddleOCR：
- 默认语言：`ch_sim,en`（简体中文，英文）
- 通过`use_gpu`参数支持GPU加速
- 首次运行时自动下载OCR模型

### 配置
- 使用FastMCP框架实现MCP服务器
- 工具是用`@app.tool()`装饰的异步函数
- 错误处理返回结构化JSON响应
- 在pyproject.toml中配置中国镜像源（清华大学镜像等）

## 实际项目结构
```
pdfreadermcp/
├── pyproject.toml              # uv项目配置
├── mcp.json                   # MCP服务器配置
├── README.md                  # 项目说明文档
├── CLAUDE.md                  # 开发指导文档
├── src/pdfreadermcp/
│   ├── __init__.py           # 包初始化
│   ├── __main__.py           # 入口点
│   ├── server.py             # FastMCP服务器实现
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── pdf_reader.py     # PDF文本提取工具
│   │   └── pdf_ocr.py        # EasyOCR处理工具
│   └── utils/
│       ├── __init__.py
│       ├── cache.py          # 缓存系统
│       ├── chunker.py        # 文本分块工具
│       └── file_handler.py   # 文件操作工具
└── tmp/                      # 临时文件目录
```

## 测试
- 项目根目录包含独立测试文件（无pytest配置）
- 运行测试：`uv run python test_easyocr.py`
- 测试文件直接验证EasyOCR功能

## 工具详细说明

### read_pdf工具
```python
@app.tool()
async def read_pdf(
    file_path: str,              # PDF文件路径
    pages: str = None,           # 页面范围，如 "1,3,5-10,-1"
    chunk_size: int = 1000,      # 文本块最大大小
    chunk_overlap: int = 100     # 块间重叠字符数
) -> str
```

**功能特性：**
- 使用pdfplumber进行高质量文本提取
- 自动文本质量分析，检测低质量文本
- 推荐需要OCR的页面
- 基于文件修改时间的智能缓存
- 递归文本分块，保持语义完整性

### ocr_pdf工具
```python
@app.tool()
async def ocr_pdf(
    file_path: str,              # PDF文件路径
    pages: str = None,           # 页面范围
    language: str = "ch_sim,en", # OCR语言代码
    chunk_size: int = 1000,      # 文本块大小
    use_gpu: bool = False        # 是否使用GPU加速
) -> str
```

**功能特性：**
- 基于EasyOCR的高精度文字识别
- 支持80+种语言（包括中文简体/繁体）
- GPU加速支持（可选）
- 置信度评分和质量分析
- 自动下载和缓存OCR模型

## 语言支持（EasyOCR）

### 主要支持的语言代码
- **中文**: `ch_sim`(简体), `ch_tra`(繁体)
- **英文**: `en`
- **日文**: `ja`
- **韩文**: `ko`
- **其他**: `fr`(法语), `de`(德语), `es`(西班牙语), `ru`(俄语)等

### 语言组合示例
- `"ch_sim,en"` - 中英混合（默认）
- `"ch_tra,en"` - 繁体中文+英文
- `"ja,en"` - 日英混合
- `"ko,en"` - 韩英混合

## 性能特性

### 缓存系统
`utils/cache.py`实现的智能缓存：
- **文件修改检测**: 基于文件修改时间和大小自动失效
- **参数敏感**: 不同参数组合使用不同缓存条目
- **内存管理**: 可配置最大条目数和过期时间
- **LRU策略**: 自动清理最旧的缓存条目

### 文本质量分析
`pdf_reader.py`中的质量检测算法：
- 字符词比率分析
- 句子结构检测
- 字母字符比例
- 特殊字符密度检查
- 自动推荐OCR阈值判断

### 分块策略
`utils/chunker.py`实现递归文本分割：
- 语义分隔符优先：段落 → 句子 → 单词 → 字符
- 可配置重叠保持上下文连贯性
- 页面边界保持
- 元数据传播

### 文件处理
`utils/file_handler.py`提供：
- 页面范围解析（支持负索引、范围、组合语法）
- PDF文件验证
- 错误处理和路径规范化

## 错误处理

所有工具返回标准化JSON格式：
```json
{
  "success": false,
  "error": "具体错误信息",
  "extraction_method": "text_extraction" | "easyocr"
}
```

常见错误类型：
- 文件不存在或不可读
- 无效页面范围
- OCR引擎初始化失败
- 内存不足或处理超时

## 开发注意事项

### 重要更正
- **注意**: README.md和`__init__.py`中仍错误地提到PaddleOCR，实际使用EasyOCR
- 项目依赖已正确配置为EasyOCR（见pyproject.toml）
- 代码实现完全基于EasyOCR API

### 性能建议
1. 首次运行会下载EasyOCR模型（约100MB+）
2. 大文档建议分页处理避免内存问题
3. GPU加速可显著提升OCR速度（需CUDA支持）
4. 缓存有效期内重复操作几乎瞬间完成

### 调试和监控
- 所有工具支持详细的元数据输出
- 错误信息包含完整的异常堆栈
- 缓存命中率可通过`cache.get_stats()`监控
- 支持异步操作，适合并发处理多个文档

## Claude Desktop配置

在Claude Desktop配置文件中添加：
```json
{
  "mcpServers": {
    "pdfreadermcp": {
      "command": "uv",
      "args": [
        "--directory",
        "/home/lihongwen/project/pdfreadermcp",
        "run",
        "pdfreadermcp"
      ]
    }
  }
}
```