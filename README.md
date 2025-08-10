# NodeImage

<p align="center">
  <img src="https://www.nodeimage.com/assets/favicon-BqSJi9tv.ico" alt="NodeImage Logo" width="100" height="100">
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

# 安装指定标签（示例：v0.0.2）
$ pip install "git+https://github.com/0x0208v0/nodeimage.git@v0.0.2"
```

## 命令行界面

NodeImage 提供了丰富的命令行界面：

### 基本命令

```shell
# 查看当前版本
$ nodeimage version

# 上传图片
$ nodeimage upload /path/to/image.jpg

# 从URL上传
$ nodeimage upload https://example.com/image.jpg

# 上传多个文件或整个文件夹
$ nodeimage upload img1.jpg img2.png images/

# 列出所有图片（默认只显示ID）
$ nodeimage list

# 列出图片的完整JSON信息
$ nodeimage list -f json

# 导出为CSV或Excel文件
$ nodeimage list -f csv -o images.csv
$ nodeimage list -f xlsx -o images.xlsx

# 下载图片到本地
$ nodeimage download imageid123

# 下载到指定目录
$ nodeimage download imageid123 -o photos/

# 删除图片
$ nodeimage delete imageid123

# 跳过确认直接删除
$ nodeimage delete imageid123 --yes

# 批量操作（支持从文件读取ID列表）
$ nodeimage delete -f image_ids.txt
$ nodeimage download -f image_ids.txt -o downloads/

# 查看调试信息和配置状态
$ nodeimage debug
```

### 管道操作

NodeImage 支持通过 Unix 管道进行批量操作，让您能够将 `list` 命令的输出直接传递给其他命令：

```shell
# 下载所有图片到默认目录
$ nodeimage list | nodeimage download --yes

# 下载所有图片到指定目录
$ nodeimage list | nodeimage download --yes -o photos/

# 删除所有图片（危险操作，请谨慎使用）
$ nodeimage list | nodeimage delete --yes

# 结合其他 Unix 工具进行过滤
$ nodeimage list | head -5 | nodeimage download --yes -o recent/
$ nodeimage list | grep "pattern" | nodeimage download --yes
$ nodeimage list | tail -10 | nodeimage delete --yes

# 将图片ID保存到文件，然后批量操作
$ nodeimage list > image_ids.txt
$ cat image_ids.txt | nodeimage download --yes -o backup/
```

**管道操作说明：**
- 管道会自动检测，无需额外参数
- **必须使用 `--yes` 参数跳过确认提示**（因为管道占用标准输入，无法进行交互确认）
- 支持与 `head`、`tail`、`grep` 等 Unix 工具组合使用
- 管道输入优先级：命令行参数 > 文件输入 > 管道输入

**注意事项：**
- 使用管道时如果不加 `--yes` 参数，程序会显示错误提示并退出
- 删除操作不可撤销，使用管道批量删除时请格外小心

## Python API 快速开始

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

下载图片：

```python
>>> image_info = client.download_image("abc123def456")
>>> with open(f"downloaded{image_info.ext}", "wb") as f:
...     f.write(image_info.content)
>>> print(f"图片已保存，格式: {image_info.content_type}")
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
    base_api_url="https://your-custom-api-endpoint.com",
    base_cdn_url="https://your-custom-cdn-endpoint.com",
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
- **SVG** (`.svg`)

## API 参考

### Client 类

```python
class Client:
    def __init__(
        self, 
        api_key: str, 
        base_api_url: str = "https://api.nodeimage.com",
        base_cdn_url: str = "https://cdn.nodeimage.com", 
        timeout: float | Timeout | None = 10,
        logger: logging.Logger | None = None
    )
    def upload_image(self, image_path_or_url: str | Path) -> dict
    def get_images(self) -> dict
    def delete_image(self, image_id: str) -> dict
    def download_image(self, image_id: str, ext: str = '.webp') -> ImageInfo
    
    @classmethod
    def from_env(cls, logger: logging.Logger | None = None) -> "Client"
```

### CLI 命令

```shell
nodeimage [OPTIONS] COMMAND [ARGS]...

命令:
  debug    显示调试信息和配置状态
  upload   上传图片文件、URL或文件夹
  list     列出已上传的图片，支持多种输出格式
  download 下载图片到本地（支持管道输入）
  delete   根据ID删除图片（不可撤销，支持管道输入）

选项:
  --api-key TEXT  NodeImage API 密钥
  --help          显示帮助信息并退出

输出格式 (list命令):
  id      仅显示图片ID（默认，适合管道操作）
  json    显示完整JSON信息
  csv     导出为CSV格式
  xlsx    导出为Excel格式

管道支持:
  download 和 delete 命令支持从标准输入读取图片ID列表
  使用方式: nodeimage list | nodeimage download --yes
  重要提醒: 管道操作时必须使用 --yes 参数，否则会因无法交互确认而失败
```

## 依赖项

NodeImage 依赖以下库：

- **[httpx](https://github.com/encode/httpx)** - 用于 HTTP 请求（包含 SOCKS 代理支持）
- **[click](https://github.com/pallets/click)** - 用于 CLI 界面
- **[python-dotenv](https://github.com/theskumar/python-dotenv)** - 用于 .env 文件支持
- **[typing_extensions](https://github.com/python/typing_extensions)** - 用于增强类型提示
- **[openpyxl](https://github.com/theorchard/openpyxl)** - 用于 Excel 文件导出功能

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

### 导出Excel文件时提示缺少依赖怎么办？

如果使用 `nodeimage list -f xlsx` 时提示缺少 openpyxl 依赖，请运行：

```shell
pip install openpyxl
```

### 有文件大小限制吗？

具体限制请参考 [NodeImage 官网](https://www.nodeimage.com) 的服务条款。

## 许可证

本项目采用 [MIT 许可证](https://github.com/0x0208v0/nodeimage/blob/main/LICENSE) 进行许可。