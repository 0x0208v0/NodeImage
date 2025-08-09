from __future__ import annotations

import json
import os
import sys

import click
from dotenv import load_dotenv

from ._client import Client
from ._utils import ENV_API_KEY
from ._utils import get_api_key_from_env


def check_api_key(ctx: click.Context) -> None:
    if not ctx.obj['api_key']:
        click.echo(f'错误: 未设置 API Key，请通过 --api-key 参数或环境变量 {ENV_API_KEY} 提供', err=True)
        ctx.exit(1)


@click.group()
@click.option('--api-key', help=f'API Key (也可设置环境变量 {ENV_API_KEY})')
@click.pass_context
def cli(ctx, api_key: str | None):
    """NodeImage 图片托管服务命令行工具

    支持图片上传、列表查看和删除操作。

    获取 API Key: https://www.nodeimage.com

    \b
    Examples:
      nodeimage debug                   # 输出调试信息
      nodeimage upload image.jpg        # 上传本地图片
      nodeimage upload https://...      # 上传网络图片
      nodeimage list                    # 列出所有图片
      nodeimage delete <image_id>       # 删除图片
    """
    ctx.ensure_object(dict)
    ctx.obj['api_key'] = api_key or get_api_key_from_env()
    if not ctx.obj['api_key']:
        load_dotenv()
        ctx.obj['api_key'] = get_api_key_from_env()


@cli.command(name='debug')
@click.pass_context
def debug(ctx):
    """输出调试信息"""
    click.echo('当前工作目录:')
    click.echo(os.getcwd())

    click.echo('Python 可执行文件:')
    click.echo(sys.executable)

    click.echo('API Key：')
    click.echo(ctx.obj['api_key'])


@cli.command(name='list')
@click.pass_context
def list_images(ctx):
    """列出所有已上传的图片"""
    check_api_key(ctx)
    client = Client(ctx.obj['api_key'])
    result = client.get_images()
    click.echo(json.dumps(result))


@cli.command(name='upload')
@click.pass_context
@click.argument('image_path_or_url')
def upload_image(ctx, image_path_or_url):
    """上传图片文件或URL

    Arguments:
      IMAGE_PATH_OR_URL  本地图片文件路径或网络图片URL
    """
    check_api_key(ctx)
    client = Client(ctx.obj['api_key'])
    result = client.upload_image(image_path_or_url)
    click.echo(json.dumps(result))


@cli.command(name='delete')
@click.pass_context
@click.argument('image_id')
@click.confirmation_option(prompt='确认要删除这张图片吗？')
def delete_image(ctx, image_id):
    """删除指定图片 (不可撤销)

    Arguments:
      IMAGE_ID  图片ID (通过 'nodeimage list' 获取)
    """
    check_api_key(ctx)
    client = Client(ctx.obj['api_key'])
    result = client.delete_image(image_id)
    click.echo(json.dumps(result))
