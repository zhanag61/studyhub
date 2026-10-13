"""只供本地 DEBUG 回退使用的持久密钥；不打印或覆盖已有密钥。"""

import os
import string
import tempfile
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured
from django.core.management.utils import get_random_secret_key

SECRET_CHARACTERS = frozenset(string.ascii_lowercase + string.digits + "!@#$%^&*(-_=+)")


def get_or_create_local_secret(path: Path) -> str:
    """首次创建，随后复用；竞争创建时读取获胜者的完整文件。"""
    temporary_path = None
    try:
        try:
            secret = path.read_text(encoding="ascii").strip()
        except FileNotFoundError:
            # 完整写入同目录临时文件，再发布；目标存在时不会覆盖。
            with tempfile.NamedTemporaryFile(
                mode="w", encoding="ascii", dir=path.parent,
                prefix=f"{path.name}.", suffix=".tmp", delete=False,
            ) as temporary_file:
                temporary_path = Path(temporary_file.name)
                temporary_file.write(get_random_secret_key())
                temporary_file.flush()
                os.fsync(temporary_file.fileno())
            try:
                if os.name == "nt":
                    # Windows 的 rename 在目标存在时失败；也适用于受限沙箱。
                    os.rename(temporary_path, path)
                    temporary_path = None
                else:
                    # POSIX rename 会覆盖目标，改用不覆盖目标的硬链接。
                    os.link(temporary_path, path)
            except FileExistsError:
                # 另一进程已经发布；复用它的密钥，不使用自己的随机值。
                pass
            secret = path.read_text(encoding="ascii").strip()
    except (OSError, UnicodeError):
        raise ImproperlyConfigured(
            "无法读取或创建 .local-secret-key；请检查本地文件和目录权限。"
        ) from None
    finally:
        if temporary_path is not None:
            try:
                temporary_path.unlink()
            except OSError:
                raise ImproperlyConfigured(
                    "无法清理本地密钥临时文件；请检查目录权限。"
                ) from None

    if (
        len(secret) != 50
        or len(set(secret)) < 5
        or not set(secret) <= SECRET_CHARACTERS
    ):
        raise ImproperlyConfigured(
            ".local-secret-key 无效；需要完整的 Django 随机密钥，已有文件未被覆盖。"
        )
    return secret
