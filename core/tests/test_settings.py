"""T001 配置回归：只用临时文件和独立进程，不连接数据库或创建账号。"""

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import patch

from django.conf import global_settings
from django.core.exceptions import ImproperlyConfigured
from django.core.management.utils import get_random_secret_key

from config.local_secret import get_or_create_local_secret

ROOT = Path(__file__).resolve().parents[2]
SESSION_DEFAULTS = {
    "SESSION_ENGINE": "django.contrib.sessions.backends.db",
    "SESSION_COOKIE_AGE": 604800,
    "SESSION_EXPIRE_AT_BROWSER_CLOSE": False,
    "SESSION_SAVE_EVERY_REQUEST": False,
    "SESSION_COOKIE_HTTPONLY": True,
    "LOGIN_URL": "core:login",
    "LOGIN_REDIRECT_URL": "core:workspace",
    "LOGOUT_REDIRECT_URL": "core:home",
}
LOAD_SETTINGS = """
import hashlib, json, os, runpy
from django.conf import global_settings
values = runpy.run_path(os.environ['STUDYHUB_TEST_SETTINGS'])
names = json.loads(os.environ['STUDYHUB_TEST_NAMES'])
print(json.dumps({
    'secret_digest': hashlib.sha256(values['SECRET_KEY'].encode()).hexdigest(),
    'defaults': {name: values.get(name, getattr(global_settings, name)) for name in names},
    'session_cookie_secure': values['SESSION_COOKIE_SECURE'],
    'database_engine': values['DATABASES']['default']['ENGINE'],
}))
"""


def temporary_config_directory():
    # Windows 沙箱的系统临时目录可能不可写；使用已被 Git 忽略的本地 QA 目录。
    qa_directory = ROOT / ".tools" / "qa"
    qa_directory.mkdir(parents=True, exist_ok=True)
    return tempfile.TemporaryDirectory(prefix="t001-", dir=qa_directory)


class LocalSecretTests(unittest.TestCase):
    def setUp(self):
        temporary_directory = temporary_config_directory()
        self.addCleanup(temporary_directory.cleanup)
        self.directory = Path(temporary_directory.name)
        self.path = self.directory / ".local-secret-key"

    def test_first_creation_and_reuse_do_not_rewrite_file(self):
        secret = get_or_create_local_secret(self.path)
        original = self.path.read_bytes()
        modified_at = self.path.stat().st_mtime_ns
        self.assertTrue(len(secret) == 50)
        self.assertTrue(get_or_create_local_secret(self.path) == secret)
        self.assertTrue(self.path.read_bytes() == original)
        self.assertEqual(self.path.stat().st_mtime_ns, modified_at)
        self.assertEqual(list(self.directory.glob("*.tmp")), [])

    def test_invalid_files_fail_without_overwriting_or_disclosing_contents(self):
        for invalid in (b"", b"too-short-private-marker", b"x" * 50,
                        b"a" * 49, b"a" * 51, b"\xffprivate-marker",
                        b"abcde" * 9 + b"ABCDE"):
            with self.subTest(length=len(invalid)):
                self.path.write_bytes(invalid)
                with self.assertRaises(ImproperlyConfigured) as error:
                    get_or_create_local_secret(self.path)
                self.assertTrue(self.path.read_bytes() == invalid)
                self.assertNotIn("private-marker", str(error.exception))

    def test_existing_valid_key_with_line_ending_is_preserved(self):
        secret = get_random_secret_key()
        self.path.write_text(secret + "\n", encoding="ascii")
        original = self.path.read_bytes()
        self.assertTrue(get_or_create_local_secret(self.path) == secret)
        self.assertTrue(self.path.read_bytes() == original)

    def test_unreadable_file_fails_without_replacing_it(self):
        self.path.write_text(get_random_secret_key(), encoding="ascii")
        original = self.path.read_bytes()
        with patch.object(Path, "read_text", side_effect=PermissionError("private-marker")):
            with self.assertRaises(ImproperlyConfigured) as error:
                get_or_create_local_secret(self.path)
        self.assertTrue(self.path.read_bytes() == original)
        self.assertNotIn("private-marker", str(error.exception))

    def test_creation_error_is_configuration_error(self):
        with patch("config.local_secret.tempfile.NamedTemporaryFile",
                   side_effect=PermissionError("private-marker")):
            with self.assertRaises(ImproperlyConfigured) as error:
                get_or_create_local_secret(self.path)
        self.assertFalse(self.path.exists())
        self.assertNotIn("private-marker", str(error.exception))

    def test_failed_publication_removes_temporary_file(self):
        publication = "rename" if os.name == "nt" else "link"
        with patch(f"config.local_secret.os.{publication}", side_effect=OSError("private-marker")):
            with self.assertRaises(ImproperlyConfigured) as error:
                get_or_create_local_secret(self.path)
        self.assertFalse(self.path.exists())
        self.assertEqual(list(self.directory.glob("*.tmp")), [])
        self.assertNotIn("private-marker", str(error.exception))

    def test_concurrent_creators_reuse_winning_key(self):
        # 等所有候选文件写完才发布，实际触发目标文件创建竞争。
        import threading

        ready = threading.Barrier(4)
        publication = "rename" if os.name == "nt" else "link"
        publish = getattr(os, publication)

        def simultaneous_publication(source, destination):
            ready.wait(timeout=10)
            return publish(source, destination)

        with patch(f"config.local_secret.os.{publication}", side_effect=simultaneous_publication):
            with ThreadPoolExecutor(max_workers=4) as executor:
                secrets = list(executor.map(get_or_create_local_secret, [self.path] * 4))
        self.assertTrue(all(secret == secrets[0] for secret in secrets))
        self.assertTrue(self.path.read_text(encoding="ascii") == secrets[0])
        self.assertEqual(list(self.directory.glob("*.tmp")), [])


class SettingsTests(unittest.TestCase):
    def setUp(self):
        temporary_directory = temporary_config_directory()
        self.addCleanup(temporary_directory.cleanup)
        self.directory = Path(temporary_directory.name)
        config_directory = self.directory / "config"
        config_directory.mkdir()
        self.settings_path = config_directory / "settings.py"
        shutil.copyfile(ROOT / "config" / "settings.py", self.settings_path)
        self.path = self.directory / ".local-secret-key"
        self.env = {
            name: value for name, value in os.environ.items()
            if not name.startswith(("DJANGO_", "RENDER", "STUDYHUB_TEST_"))
            and name not in ("DATABASE_URL", "DJANGO_SETTINGS_MODULE")
        }
        self.env.update(
            PYTHONUTF8="1", DJANGO_DEBUG="true", RENDER="false",
            STUDYHUB_TEST_SETTINGS=str(self.settings_path),
            STUDYHUB_TEST_NAMES=json.dumps(list(SESSION_DEFAULTS)),
        )

    def run_settings(self, **changes):
        return subprocess.run(
            [sys.executable, "-c", LOAD_SETTINGS], cwd=ROOT,
            env=self.env | changes, capture_output=True,
            text=True, encoding="utf-8", timeout=15,
        )

    def load_settings(self, **changes):
        result = self.run_settings(**changes)
        self.assertEqual(result.returncode, 0, "临时配置加载应成功")
        return json.loads(result.stdout)

    def test_separate_startups_reuse_local_key_and_planned_defaults(self):
        first = self.load_settings()
        second = self.load_settings()
        self.assertEqual(first["secret_digest"], second["secret_digest"])
        self.assertTrue(self.path.is_file())
        self.assertEqual(first["defaults"], SESSION_DEFAULTS)
        self.assertEqual(first["database_engine"], "django.db.backends.sqlite3")

    def test_environment_key_does_not_create_local_file(self):
        env_key = get_random_secret_key()
        result = self.load_settings(DJANGO_SECRET_KEY=env_key)
        self.assertTrue(result["secret_digest"] == hashlib.sha256(env_key.encode()).hexdigest())
        self.assertFalse(self.path.exists())

    def test_environment_key_bypasses_invalid_local_file(self):
        original = b"invalid-private-marker"
        self.path.write_bytes(original)
        env_key = get_random_secret_key()
        result = self.load_settings(DJANGO_SECRET_KEY=env_key)
        self.assertTrue(result["secret_digest"] == hashlib.sha256(env_key.encode()).hexdigest())
        self.assertTrue(self.path.read_bytes() == original)

    def test_invalid_local_file_refuses_startup_without_disclosure(self):
        original = b"invalid-private-marker"
        self.path.write_bytes(original)
        result = self.run_settings()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn(".local-secret-key 无效", result.stderr)
        self.assertNotIn("invalid-private-marker", result.stderr + result.stdout)
        self.assertTrue(self.path.read_bytes() == original)

    def test_production_without_environment_key_refuses_local_fallback(self):
        self.path.write_text(get_random_secret_key(), encoding="ascii")
        original = self.path.read_bytes()
        result = self.run_settings(DJANGO_DEBUG="false")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("关闭 DEBUG 时必须设置 DJANGO_SECRET_KEY", result.stderr)
        self.assertTrue(self.path.read_bytes() == original)

    def test_production_without_environment_key_does_not_create_file(self):
        result = self.run_settings(DJANGO_DEBUG="false")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("DJANGO_SECRET_KEY", result.stderr)
        self.assertFalse(self.path.exists())

    def test_production_session_and_security_settings_are_unchanged(self):
        # 仅解析配置，占位地址不会建立 PostgreSQL 连接。
        result = self.load_settings(
            DJANGO_DEBUG="false", DJANGO_SECRET_KEY=get_random_secret_key(),
            DATABASE_URL="postgresql://unused:unused@127.0.0.1:1/unused",
        )
        self.assertEqual(result["defaults"], {
            name: getattr(global_settings, name) for name in SESSION_DEFAULTS
        })
        self.assertTrue(result["session_cookie_secure"])
        self.assertFalse(self.path.exists())


if __name__ == "__main__":
    unittest.main()
