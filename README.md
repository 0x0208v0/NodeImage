# NodeImage

<p align="center">
  <img src="https://www.nodeseek.com/static/image/favicon/android-chrome-192x192.png" alt="NodeImage Logo" width="100" height="100">
</p>

<p align="center">
  <a href="https://pypi.org/project/nodeimage/">
    <img src="https://badge.fury.io/py/nodeimage.svg" alt="Package version">
  </a>
  <a href="https://pypi.org/project/nodeimage/">
    <img src="https://img.shields.io/pypi/pyversions/nodeimage.svg" alt="Supported Python versions">
  </a>
</p>

---

> **重要说明**: 本项目是 [NodeImage](https://www.nodeimage.com/) 图片托管服务的**第三方实现** Python 客户端，**非官方实现**。如需官方支持或了解服务详情，请访问 [NodeImage 官网](https://www.nodeimage.com/)。

NodeImage 是一个便捷的 Python 命令行客户端，用于与 [NodeImage](https://www.nodeimage.com/) 图片托管服务进行交互。它提供了简洁的命令行接口和 Python API，让您能够在终端中轻松管理您的图片。

## 系统要求

NodeImage 需要 Python 3.9 或更高版本。

## 安装

使用 PyPI 安装：

```shell
$ pip install nodeimage
```

从 GitHub 安装（最新提交）：

```shell
$ pip install "git+https://github.com/0x0208v0/nodeimage.git"
```

指定分支/标签安装：

```shell
# 安装 main 分支
$ pip install "git+https://github.com/0x0208v0/nodeimage.git@main"

# 安装指定标签（示例：v0.0.1）
$ pip install "git+https://github.com/0x0208v0/nodeimage.git@v0.0.1"
```

## 快速开始

首先导入 NodeImage：

```python
>>> import nodeimage
>>> client = nodeimage.Client("your_api_key_here")
```

上传本地图片：

```python
>>> result = client.upload_image("/path/to/image.jpg")
>>> print(result)
{'id': 'abc123def456', 'url': 'https://...', 'filename': 'image.jpg'}
```

从网络URL上传图片：

```python
>>> result = client.upload_image("https://example.com/image.jpg")
>>> print(result)
{'id': 'xyz789uvw012', 'url': 'https://...', 'filename': 'image.jpg'}
```

列出所有图片：

```python
>>> images = client.get_images()
>>> print(images)
[{'id': 'abc123', 'url': 'https://...', 'filename': 'image1.jpg'}, ...]
```

删除图片：

```python
>>> result = client.delete_image("abc123def456")
>>> print(result)
{'success': True, 'message': 'Image deleted successfully'}
```

## 命令行界面

NodeImage 还提供了命令行界面：

```shell
# 上传图片
$ nodeimage upload /path/to/image.jpg

# 从URL上传
$ nodeimage upload https://example.com/image.jpg

# 列出所有图片
$ nodeimage list

# 删除图片
$ nodeimage delete abc123def456

# 跳过确认直接删除
$ nodeimage delete abc123def456 --yes
```

## 身份认证

### 环境变量（推荐）

```shell
export NODE_IMAGE_API_KEY=your_api_key_here
```

### .env 文件

在项目根目录创建 `.env` 文件：

```shell
NODE_IMAGE_API_KEY=your_api_key_here
```

### 命令行参数

```shell
nodeimage --api-key your_api_key_here upload image.jpg
```

### Python 代码

```python
from nodeimage import Client

# 直接初始化
client = Client("your_api_key_here")

# 从环境变量创建
client = Client.from_env()
```

## 高级用法

### 自定义配置

```python
from nodeimage import Client

client = Client(
    api_key="your_api_key",
    base_url="https://your-custom-endpoint.com",
    timeout=30  # 自定义超时时间（秒）
)
```

### 错误处理

```python
from nodeimage import Client

client = Client("your_api_key")

try:
    result = client.upload_image("/path/to/image.jpg")
    print(f"上传成功: {result}")
except Exception as e:
    print(f"上传失败: {e}")
```

## 支持的图片格式

NodeImage 支持常见的图片格式：

- **JPEG** (`.jpg`, `.jpeg`)
- **PNG** (`.png`)
- **GIF** (`.gif`)
- **WebP** (`.webp`)
- **BMP** (`.bmp`)

## API 参考

### Client 类

```python
class Client:
    def __init__(self, api_key: str, base_url: str = None, timeout: int = 30)
    def upload_image(self, image_path_or_url: str) -> dict
    def get_images(self) -> list
    def delete_image(self, image_id: str) -> dict
    
    @classmethod
    def from_env(cls) -> "Client"
```

### CLI 命令

```shell
nodeimage [OPTIONS] COMMAND [ARGS]...

命令:
  upload  上传图片文件或URL
  list    列出所有已上传的图片
  delete  根据ID删除图片

选项:
  --api-key TEXT  NodeImage API 密钥
  --help          显示帮助信息并退出
```

## 依赖项

NodeImage 依赖以下库：

- **[httpx](https://github.com/encode/httpx)** - 用于 HTTP 请求
- **[click](https://github.com/pallets/click)** - 用于 CLI 界面
- **[python-dotenv](https://github.com/theskumar/python-dotenv)** - 用于 .env 文件支持
- **[typing_extensions](https://github.com/python/typing_extensions)** - 用于增强类型提示

## 获取 API 密钥

1. 访问 [NodeImage 官网](https://www.nodeimage.com)
2. 注册账户或登录现有账户
3. 在用户面板中获取您的 API 密钥

## 常见问题

### 上传失败怎么办？

请检查：

- API 密钥是否正确设置
- 图片文件是否存在且可读
- 网络连接是否正常
- 图片格式是否支持

### 如何查看详细错误信息？

可以通过 Python 代码捕获异常获取详细信息：

```python
try:
    client.upload_image("image.jpg")
except Exception as e:
    print(f"详细错误: {e}")
```

### 有文件大小限制吗？

具体限制请参考 [NodeImage 官网](https://www.nodeimage.com) 的服务条款。

## 许可证

本项目采用 [MIT 许可证](https://github.com/0x0208v0/nodeimage/blob/main/LICENSE) 进行许可。