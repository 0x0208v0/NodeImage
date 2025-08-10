from __future__ import annotations

import csv
import io
import json
import re
import sys
from pathlib import Path
from typing import Callable

import click
from dotenv import load_dotenv

from .__version__ import __version__
from ._client import Client
from ._utils import ENV_API_KEY
from ._utils import get_api_key_from_env
from ._utils import is_image_file
from ._utils import is_path
from ._utils import is_url
from ._utils import iter_files_in_path
from ._utils import write_csv_file
from ._utils import write_xlsx_file

# 命令示例常量
CLI_EXAMPLES = """常用命令:\n\n\b
查看版本信息：\nnodeimage version\n\n\b
查看调试信息和配置状态：\nnodeimage debug\n\n\b
上传本地图片文件：\nnodeimage upload image.jpg\n\n\b
列出所有已上传的图片：\nnodeimage list\n\n\b
下载指定图片到本地：\nnodeimage download imageid123\n\n\b
删除指定图片（不可撤销）：\nnodeimage delete imageid123\n\n
"""

DEBUG_EXAMPLES = """使用示例:\n\n\b
显示当前配置和环境信息：\nnodeimage debug\n\n\b
使用指定API Key进行调试：\nnodeimage debug --api-key xxx\n\n
"""

LIST_EXAMPLES = """使用示例:\n\n\b
显示图片ID列表：\nnodeimage list\n\n\b
显示完整JSON数据：\nnodeimage list -f json\n\n\b
美化JSON输出：\nnodeimage list -f json -p\n\n\b
导出CSV文件：\nnodeimage list -f csv\n\n\b
导出到指定文件：\nnodeimage list -f csv -o my.csv\n\n\b
导出Excel文件：\nnodeimage list -f xlsx -o data.xlsx\n\n\b
导出到指定目录：\nnodeimage list -f csv -o ./output/my.csv\n\n
"""

UPLOAD_EXAMPLES = """使用示例:\n\n\b
上传本地图片：\nnodeimage upload image.jpg\n\n\b
上传网络图片：\nnodeimage upload https://example.com/pic.jpg\n\n\b
上传多个文件：\nnodeimage upload img1.jpg img2.png\n\n\b
上传整个文件夹：\nnodeimage upload images/\n\n\b
跳过确认提示：\nnodeimage upload images/ -y\n\n
"""

DELETE_EXAMPLES = """使用示例:\n\n\b
删除指定图片：\nnodeimage delete abc123\n\n\b
跳过确认删除：\nnodeimage delete abc123 -y\n\n\b
删除多个图片：\nnodeimage delete id1 id2 id3\n\n\b
从文件批量删除：\nnodeimage delete -f ids.txt\n\n\b
批量删除跳过确认：\nnodeimage delete -f ids.txt -y\n\n\b
通过管道删除：\nnodeimage list | nodeimage delete -y\n\n
"""

DOWNLOAD_EXAMPLES = """使用示例:\n\n\b
下载到默认目录：\nnodeimage download abc123\n\n\b
下载到指定目录：\nnodeimage download abc123 -o photos/\n\n\b
下载多个图片：\nnodeimage download id1 id2 id3\n\n\b
从文件批量下载：\nnodeimage download -f ids.txt\n\n\b
跳过确认提示：\nnodeimage download -f ids.txt -y\n\n\b
通过管道下载：\nnodeimage list | nodeimage download -y\n\n
"""

VERSION_EXAMPLES = """使用示例:\n\n\b
显示版本信息：\nnodeimage version\n\n\b
显示完整版本信息：\nnodeimage version -f\n\n
"""

# CLI命令帮助信息常量
CLI_HELP = f"""NodeImage 图片托管服务命令行工具\n\b
获取 API Key: https://www.nodeimage.com\n\b
{CLI_EXAMPLES}\n\b
使用 nodeimage <command> --help 查看每个命令的详细用法。\n
"""

DEBUG_HELP = f"""显示调试信息和配置状态\n
{DEBUG_EXAMPLES}
"""

LIST_HELP = f"""列出已上传的图片，支持多种输出格式\n
{LIST_EXAMPLES}"""

UPLOAD_HELP = f"""上传本地文件、网络URL或文件夹中的图片\n
{UPLOAD_EXAMPLES}"""

DELETE_HELP = f"""删除指定图片（不可撤销）\n
{DELETE_EXAMPLES}"""

DOWNLOAD_HELP = f"""下载图片到本地\n
{DOWNLOAD_EXAMPLES}"""

VERSION_HELP = f"""显示版本信息\n
{VERSION_EXAMPLES}"""

# 选项帮助信息常量
API_KEY_HELP = f'API Key (也可设置环境变量 {ENV_API_KEY})'
FORMAT_HELP = '输出格式: id(默认) | json | csv | xlsx'
OUTPUT_HELP = '输出文件路径'
PRETTY_HELP = '美化JSON输出'
YES_HELP = '跳过确认提示'
FILE_HELP = '包含图片ID的文件，每行一个ID'
OUTPUT_DIR_HELP = '输出目录路径'
FULL_VERSION_HELP = '显示完整版本信息'


def check_api_key(ctx: click.Context) -> None:
    """检查API Key是否已设置，如果未设置则显示错误并退出程序。

    Args:
        ctx: Click上下文对象，包含API Key信息
    """
    if not ctx.obj['api_key']:
        click.echo(
            click.style('错误: ', fg='red', bold=True)
            + f'未设置 API Key，请通过 --api-key 参数或环境变量 {ENV_API_KEY} 提供',
            err=True,
        )
        ctx.exit(1)


def get_first_column(line: str) -> str:
    """从文本行中提取第一列内容，支持逗号、制表符或空格分隔。

    Args:
        line: 待解析的文本行

    Returns:
        第一列的字符串内容
    """
    return re.split(r'[,\t ]+', line)[0]


def read_image_ids_from_file(file_path: str | Path) -> list[str]:
    """从文件中读取图片ID列表，每行一个ID。

    支持以#开头的注释行和空行，提取每行第一列作为图片ID。

    Args:
        file_path: 文件路径，支持字符串或Path对象

    Returns:
        图片ID列表

    Raises:
        Exception: 当文件不存在或读取失败时抛出异常
    """
    if not is_path(file_path):
        raise Exception(f'文件不存在: {file_path}')
    image_ids = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if line and not line.startswith('#'):  # 跳过空行和注释行
                    image_id = get_first_column(line)
                    if image_id:
                        image_ids.append(image_id)
                    else:
                        click.echo(f'警告: 第 {line_num} 行格式无效: {line}', err=True)
        return image_ids
    except Exception as e:
        raise Exception(f'无法读取文件 {file_path}: {e}')


def collect_image_paths(paths_or_urls: list[str]) -> list[str]:
    """收集图片路径和URL列表，支持文件、目录和网络URL。

    对于本地路径，会递归遍历目录查找图片文件；对于URL直接添加到列表中。

    Args:
        paths_or_urls: 路径或URL列表，可以是文件、目录或网络地址

    Returns:
        所有找到的图片路径和URL列表
    """
    all_paths = []
    for path in paths_or_urls:
        # 如果是网络URL，直接添加
        if is_url(path):
            all_paths.append(path)
            continue

        # 使用 utils 中的函数来遍历文件
        for file_path in iter_files_in_path(path):
            if is_image_file(file_path):
                all_paths.append(str(file_path))
                click.echo(f'  发现图片: {file_path}')
    return all_paths


def execute_batch_operation(
    items: list[str],
    operation_func: Callable,
    operation_name: str,
    success_color: str = 'green',
    error_color: str = 'red',
) -> dict:
    """执行批量操作，对每个项目调用指定的操作函数。

    Args:
        items: 待处理的项目列表
        operation_func: 操作函数，接受单个项目作为参数
        operation_name: 操作名称，用于显示进度信息
        success_color: 成功消息的颜色，默认绿色
        error_color: 错误消息的颜色，默认红色

    Returns:
        包含操作结果统计的字典，包括总数、成功数、失败数等信息
    """
    results = []
    errors = []

    click.echo(f'开始批量{operation_name} {len(items)} 个项目...')

    for i, item in enumerate(items, 1):
        try:
            click.echo(f'[{i}/{len(items)}] {operation_name}: {item}')
            result = operation_func(item)
            results.append({'index': i, 'input': item, 'status': 'success', 'result': result})
            click.echo(click.style(f'  成功: {item}', fg=success_color))
        except Exception as e:
            error_msg = f'{operation_name}失败: {str(e)}'
            click.echo(click.style(f'  失败: {error_msg}', fg=error_color))
            errors.append({'index': i, 'input': item, 'status': 'error', 'error': str(e)})

    # 返回汇总结果
    return {
        'total': len(items),
        'successful': len(results),
        'failed': len(errors),
        'results': results,
        'errors': errors,
    }


def display_batch_summary(summary: dict, operation_name: str) -> None:
    """显示批量操作的汇总结果。

    Args:
        summary: 批量操作结果字典，包含统计信息和详细结果
        operation_name: 操作名称，用于显示标题
    """
    click.echo(click.style(f'\n批量{operation_name}完成!', fg='blue', bold=True))
    click.echo(f'总计: {summary["total"]} 个')
    click.echo(click.style(f'成功: {summary["successful"]} 个', fg='green'))
    click.echo(
        click.style(f'失败: {summary["failed"]} 个', fg='red')
        if summary['failed'] > 0
        else f'失败: {summary["failed"]} 个'
    )

    if summary['errors']:
        click.echo('\n失败的项目:')
        for error in summary['errors']:
            click.echo(f'  - {error["input"]}: {error["error"]}')

    # 输出JSON结果
    click.echo(json.dumps(summary, ensure_ascii=False))


def collect_image_ids(ctx: click.Context, image_ids: list[str], file: str | None, from_stdin: bool = False) -> list[
    str]:
    """收集图片ID列表，支持从命令行参数、文件或标准输入读取。

    Args:
        ctx: Click上下文对象，用于错误处理时退出程序
        image_ids: 命令行传入的图片ID列表
        file: 包含图片ID的文件路径，可选
        from_stdin: 是否从标准输入读取，可选

    Returns:
        去重后的图片ID列表

    Raises:
        SystemExit: 当没有提供有效的图片ID时退出程序
    """
    all_image_ids = []

    if from_stdin:
        # 从标准输入读取ID列表
        try:
            import sys
            if not sys.stdin.isatty():
                for line in sys.stdin:
                    line = line.strip()
                    if line and not line.startswith('#'):  # 跳过空行和注释行
                        image_id = get_first_column(line)
                        if image_id:
                            all_image_ids.append(image_id)
            else:
                click.echo('错误: 没有从管道接收到输入', err=True)
                ctx.exit(1)
        except Exception as e:
            click.echo(f'错误: 从标准输入读取失败: {e}', err=True)
            ctx.exit(1)
    elif file:
        # 从文件读取ID列表
        try:
            all_image_ids = read_image_ids_from_file(file)
        except Exception as e:
            click.echo(f'错误: {e}', err=True)
            ctx.exit(1)
    else:
        # 从命令行参数获取ID
        if not image_ids:
            click.echo('错误: 请指定图片ID、使用 --file 参数或通过管道传入数据', err=True)
            ctx.exit(1)
        all_image_ids = list(image_ids)

    if not all_image_ids:
        click.echo('错误: 没有找到有效的图片ID', err=True)
        ctx.exit(1)

    # 去重并返回
    return list(set(all_image_ids))


def _extract_image_ids(result):
    """从API响应中提取图片ID列表。

    Args:
        result: API响应结果，可能包含images字段的字典

    Returns:
        图片ID列表
    """
    image_ids = []
    if isinstance(result, dict):
        if 'images' in result:
            # 新格式: {"images": [{"image_id": "xxx", ...}, ...]}
            for item in result['images']:
                if isinstance(item, dict) and 'image_id' in item:
                    image_ids.append(item['image_id'])
    return image_ids


def _extract_image_data(result):
    """从API响应中提取图片数据，返回字段列表和数据行。

    Args:
        result: API响应结果，可能是包含images字段的字典或图片列表

    Returns:
        tuple: (字段顺序列表, 数据行列表)，用于表格显示
    """
    # 提取图片数据
    images = []
    if isinstance(result, dict) and 'images' in result:
        images = result['images']
    elif isinstance(result, list):
        images = result

    if not images:
        return [], []

    # 收集所有可能的字段
    all_fields = set()
    data_rows = []

    for img in images:
        if isinstance(img, dict):
            row = {}
            # 第一列始终是ID
            if 'image_id' in img:
                row['image_id'] = img['image_id']
                all_fields.add('image_id')
            elif 'id' in img:
                row['id'] = img['id']
                all_fields.add('id')
            else:
                continue

            # 添加其他字段
            for key, value in img.items():
                if key not in ['image_id', 'id']:
                    # 处理嵌套的links字段
                    if key == 'links' and isinstance(value, dict):
                        for link_key, link_value in value.items():
                            field_name = f'link_{link_key}'
                            row[field_name] = link_value
                            all_fields.add(field_name)
                    else:
                        row[key] = value
                        all_fields.add(key)

            data_rows.append(row)

    # 确保字段顺序：ID字段在前，其他字段按字母顺序
    id_fields = [f for f in all_fields if f in ['image_id', 'id']]
    other_fields = sorted([f for f in all_fields if f not in ['image_id', 'id']])
    field_order = id_fields + other_fields

    return field_order, data_rows


@click.group(help=CLI_HELP)
@click.option('--api-key', help=API_KEY_HELP)
@click.pass_context
def cli(ctx, api_key: str | None):
    ctx.ensure_object(dict)
    ctx.obj['api_key'] = api_key or get_api_key_from_env()
    if not ctx.obj['api_key']:
        load_dotenv()
        ctx.obj['api_key'] = get_api_key_from_env()


@cli.command(name='version', help=VERSION_HELP)
@click.option('--full', '-f', is_flag=True, help=FULL_VERSION_HELP)
def version(full: bool):
    """显示版本信息。"""
    if full:
        # 显示完整版本信息
        click.echo(click.style('NodeImage CLI 版本信息:', fg='cyan', bold=True))
        click.echo(f'   版本: {__version__}')
        click.echo(f'   Python: {sys.version}')
        click.echo(f'   平台: {sys.platform}')
    else:
        # 只显示版本号
        click.echo(__version__)


@cli.command(name='debug', help=DEBUG_HELP)
@click.pass_context
def debug(ctx):
    click.echo(click.style('当前工作目录:', fg='cyan', bold=True))
    click.echo(f'   {Path.cwd()}')

    click.echo(click.style('Python 可执行文件:', fg='cyan', bold=True))
    click.echo(f'   {sys.executable}')

    click.echo(click.style('API Key 状态:', fg='cyan', bold=True))
    if ctx.obj['api_key']:
        api_key_display = ctx.obj['api_key'][:8] + '...' if len(ctx.obj['api_key']) > 8 else ctx.obj['api_key']
        click.echo(f'   {click.style("已配置", fg="green")} ({api_key_display})')
    else:
        click.echo(f'   {click.style("未配置", fg="red")}')


@cli.command(name='list', help=LIST_HELP)
@click.pass_context
@click.option(
    '--format',
    '-f',
    type=click.Choice(['id', 'json', 'csv', 'xlsx'], case_sensitive=False),
    default='id',
    help=FORMAT_HELP,
)
@click.option('--output', '-o', type=click.Path(), required=False, help=OUTPUT_HELP)
@click.option('--pretty', '-p', is_flag=True, help=PRETTY_HELP)
def list_images(ctx, format: str, output: str, pretty: bool):
    check_api_key(ctx)
    client = Client(ctx.obj['api_key'])
    result = client.get_images()

    # 根据格式处理输出
    if format == 'id':
        # 默认格式：只显示图片ID
        image_ids = _extract_image_ids(result)
        if not image_ids:
            click.echo(click.style('未找到图片', fg='yellow'), err=True)
            return

        for image_id in image_ids:
            click.echo(image_id)

    elif format == 'json':
        # JSON格式输出
        if output:
            # 输出到文件
            # 如果output是空字符串或None（只指定了-o但没有文件名），使用默认文件名
            if not output or output == '' or output == '.':
                output = 'image_infos.json'

            # 检查文件是否已存在，如果存在则提示用户确认
            if is_path(output):
                if not click.confirm(f'文件 {output} 已存在，是否覆盖？'):
                    click.echo('操作已取消')
                    return

            try:
                with open(output, 'w', encoding='utf-8') as f:
                    if pretty:
                        json.dump(result, f, indent=2, ensure_ascii=False)
                    else:
                        json.dump(result, f, indent=2, ensure_ascii=False)
                click.echo(click.style('JSON数据已保存到: ', fg='green') + f'{output}')
            except Exception as e:
                click.echo(f'保存JSON文件失败: {e}', err=True)
                ctx.exit(1)
        else:
            # 输出到控制台
            if pretty:
                click.echo(json.dumps(result, indent=2, ensure_ascii=False))
            else:
                click.echo(json.dumps(result, ensure_ascii=False))

    elif format == 'csv':
        # CSV格式输出
        if output:
            # 输出到文件
            # 如果output是空字符串或None（只指定了-o但没有文件名），使用默认文件名
            if not output or output == '' or output == '.':
                output = 'image_infos.csv'

            # 检查文件是否已存在，如果存在则提示用户确认
            if is_path(output):
                if not click.confirm(f'文件 {output} 已存在，是否覆盖？'):
                    click.echo('操作已取消')
                    return

            try:
                # 提取数据
                field_order, data_rows = _extract_image_data(result)
                if not data_rows:
                    click.echo('未找到图片数据', err=True)
                    return

                # 使用工具函数写入CSV文件
                write_csv_file(output, field_order, data_rows)
                click.echo(click.style('CSV文件已保存到: ', fg='green') + f'{output}')
            except Exception as e:
                click.echo(f'导出CSV文件失败: {e}', err=True)
                ctx.exit(1)
        else:
            # 输出到控制台
            try:
                # 提取数据
                field_order, data_rows = _extract_image_data(result)
                if not data_rows:
                    click.echo('未找到图片数据', err=True)
                    return

                # 输出CSV格式到控制台
                output_buffer = io.StringIO()
                writer = csv.DictWriter(output_buffer, fieldnames=field_order)
                writer.writeheader()
                writer.writerows(data_rows)

                click.echo(output_buffer.getvalue())
            except Exception as e:
                click.echo(f'输出CSV格式失败: {e}', err=True)
                ctx.exit(1)

    elif format == 'xlsx':
        # Excel格式输出
        if not output:
            click.echo('错误: XLSX格式需要指定输出文件，请使用 -o 参数', err=True)
            ctx.exit(1)

        # 如果output是空字符串或None（只指定了-o但没有文件名），使用默认文件名
        if not output or output == '' or output == '.':
            output = 'image_infos.xlsx'

        # 检查文件是否已存在，如果存在则提示用户确认
        if is_path(output):
            if not click.confirm(f'文件 {output} 已存在，是否覆盖？'):
                click.echo('操作已取消')
                return

        try:
            # 提取数据
            field_order, data_rows = _extract_image_data(result)
            if not data_rows:
                click.echo('未找到图片数据', err=True)
                return

            # 使用工具函数写入Excel文件
            write_xlsx_file(output, field_order, data_rows)
            click.echo(click.style('Excel文件已保存到: ', fg='green') + f'{output}')

        except ImportError as e:
            if 'openpyxl' in str(e):
                click.echo('错误: 需要安装openpyxl依赖，请运行: pip install openpyxl', err=True)
            else:
                click.echo(f'错误: 缺少必要依赖: {e}', err=True)
            ctx.exit(1)
        except Exception as e:
            click.echo(f'导出Excel文件失败: {e}', err=True)
            ctx.exit(1)


@cli.command(name='upload', help=UPLOAD_HELP)
@click.pass_context
@click.argument('images', nargs=-1)
@click.option('--yes', '-y', is_flag=True, help=YES_HELP)
def upload_image(ctx, images: list, yes: bool):
    check_api_key(ctx)
    client = Client(ctx.obj['api_key'])

    # 收集图片路径或URL
    if not images:
        click.echo('错误: 请指定图片URL或路径或文件夹，如: nodeimage upload image2.png', err=True)
        ctx.exit(1)

    all_images = list(images)

    # 处理文件夹遍历，收集所有图片路径
    all_images = collect_image_paths(all_images)

    if not all_images:
        click.echo('错误: 没有找到有效的图片路径', err=True)
        ctx.exit(1)

    # 去重
    all_images = list(set(all_images))

    # 确认提示
    if not yes:
        click.echo(f'准备上传 {len(all_images)} 张图片:')
        for img_path in all_images:
            click.echo(f'  - {img_path}')

        if not click.confirm('确认继续上传吗？'):
            click.echo('已取消上传')
            return

    # 执行批量上传
    summary = execute_batch_operation(all_images, client.upload_image, '上传')

    # 显示汇总结果
    display_batch_summary(summary, '上传')


@cli.command(name='delete', help=DELETE_HELP)
@click.pass_context
@click.argument('image_ids', nargs=-1)
@click.option('--file', '-f', type=click.Path(exists=True), help=FILE_HELP)
@click.option('--yes', '-y', is_flag=True, help=YES_HELP)
def delete_image(ctx, image_ids: list[str], file: str, yes: bool):
    check_api_key(ctx)
    client = Client(ctx.obj['api_key'])

    # 检测是否有管道输入
    import sys
    from_stdin = not sys.stdin.isatty() and not image_ids and not file

    # 收集图片ID
    all_image_ids = collect_image_ids(ctx, image_ids, file, from_stdin)

    # 确认提示（删除操作需要特别确认）
    if not yes:
        click.echo(f'准备删除 {len(all_image_ids)} 张图片:')
        for img_id in all_image_ids:
            click.echo(f'  - {img_id}')

        click.echo('\n警告：删除操作不可撤销！')

        # 如果是从管道输入，提示用户使用 -y 参数
        if from_stdin:
            click.echo('错误: 通过管道输入时必须使用 -y 参数跳过确认提示', err=True)
            click.echo('示例: nodeimage list | nodeimage delete -y', err=True)
            ctx.exit(1)

        if not click.confirm('确认要删除这些图片吗？'):
            click.echo('已取消删除')
            return

        # 二次确认
        if not click.confirm('再次确认：你真的要删除这些图片吗？'):
            click.echo('已取消删除')
            return

    # 执行批量删除
    summary = execute_batch_operation(all_image_ids, client.delete_image, '删除')

    # 显示汇总结果
    display_batch_summary(summary, '删除')


@cli.command(name='download', help=DOWNLOAD_HELP)
@click.pass_context
@click.argument('image_ids', nargs=-1)
@click.option('--file', '-f', type=click.Path(exists=True), help=FILE_HELP)
@click.option('--output', '-o', type=click.Path(), help=OUTPUT_DIR_HELP)
@click.option('--yes', '-y', is_flag=True, help=YES_HELP)
def download_image(ctx, image_ids: list[str], file: str, output: str, yes: bool):
    check_api_key(ctx)
    client = Client(ctx.obj['api_key'])

    # 检测是否有管道输入
    import sys
    from_stdin = not sys.stdin.isatty() and not image_ids and not file

    # 收集图片ID
    all_image_ids = collect_image_ids(ctx, image_ids, file, from_stdin)

    # 确定输出目录
    if output:
        output_dir = output
    else:
        # 默认下载到当前目录下的 images/ 文件夹
        output_dir = Path.cwd() / 'images'

    # 确认提示
    if not yes:
        click.echo(f'准备下载 {len(all_image_ids)} 张图片:')
        for img_id in all_image_ids:
            click.echo(f'  - {img_id}')

        # 如果是从管道输入，提示用户使用 -y 参数
        if from_stdin:
            click.echo('错误: 通过管道输入时必须使用 -y 参数跳过确认提示', err=True)
            click.echo('示例: nodeimage list | nodeimage download -y', err=True)
            ctx.exit(1)

        if not click.confirm('确认继续下载吗？'):
            click.echo('已取消下载')
            return

    # 检查并创建输出目录
    output_path = Path(output_dir)
    if not output_path.exists():
        if not yes:
            click.echo(f'输出目录不存在: {output_path.absolute()}')
            if not click.confirm('是否创建此目录并继续下载？'):
                click.echo('已取消下载')
                return

        try:
            output_path.mkdir(parents=True, exist_ok=True)
            click.echo(f'已创建输出目录: {output_path.absolute()}')
        except Exception as e:
            click.echo(f'错误: 无法创建输出目录 {output_dir}: {e}', err=True)
            ctx.exit(1)
    else:
        click.echo(f'输出目录: {output_path.absolute()}')

    # 下载所有图片
    results = []
    for i, image_id in enumerate(all_image_ids, 1):
        try:
            click.echo(f'正在下载第 {i}/{len(all_image_ids)} 张图片: {image_id}')
            image_info = client.download_image(image_id)
            (output_path / f'{image_id}{image_info.ext}').write_bytes(image_info.content)
            results.append({'image_id': image_id, 'status': 'success', 'result': image_id})
            click.echo(click.style(f'成功下载: {image_id}', fg='green'))
        except Exception as e:
            error_msg = f'下载失败: {image_id} - {e}'
            click.echo(click.style(f'{error_msg}', fg='red'), err=True)
            results.append({'image_id': image_id, 'status': 'error', 'error': str(e)})

    # 输出汇总结果
    summary = {
        'total': len(all_image_ids),
        'successful': len([r for r in results if r['status'] == 'success']),
        'failed': len([r for r in results if r['status'] == 'error']),
        'results': results,
    }

    click.echo(
        click.style('\n下载完成!', fg='blue', bold=True)
        + f' 总计: {summary["total"]}, '
        + click.style(f'成功: {summary["successful"]}', fg='green')
        + ', '
        + (
            click.style(f'失败: {summary["failed"]}', fg='red')
            if summary['failed'] > 0
            else f'失败: {summary["failed"]}'
        )
    )
    click.echo(json.dumps(summary, indent=2, ensure_ascii=False))
