"""验证正式部署的请求；Linux 使用真实 Gunicorn，Windows 使用同一个 WSGI 应用。"""

import argparse
import gzip
import json
import os
import re
import secrets
import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import HTTPRedirectHandler, Request, build_opener

ROOT = Path(__file__).resolve().parent.parent
HOSTNAME = "studyhub-smoke.onrender.com"


def command(arguments, env):
    result = subprocess.run(arguments, cwd=ROOT, env=env, capture_output=True, text=True)
    if result.returncode:
        # 不把可能包含数据库诊断信息的完整输出写入 CI 日志。
        raise RuntimeError(f"检查失败：{arguments[1:3]}，退出码 {result.returncode}")
    return result


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--postgres", action="store_true", help="使用 CI 的临时 PostgreSQL，验证迁移")
    parser.add_argument("--serve-wsgi", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.serve_wsgi:
        from wsgiref.simple_server import make_server

        sys.path.insert(0, str(ROOT))
        from config.wsgi import application

        with make_server("127.0.0.1", int(os.environ["PORT"]), application) as server:
            server.serve_forever()
        return

    env = os.environ.copy()
    for key in list(env):
        if key.startswith("DJANGO_") or key.startswith("RENDER") or key == "DATABASE_URL":
            env.pop(key)
    env.update(
        RENDER="true",
        RENDER_EXTERNAL_HOSTNAME=HOSTNAME,
        DJANGO_DEBUG="false",
        DJANGO_SECRET_KEY=secrets.token_urlsafe(64),
        PYTHONUTF8="1",
        PYTHONUNBUFFERED="1",
    )
    if args.postgres:
        if not os.environ.get("DATABASE_URL"):
            raise RuntimeError("--postgres 需要 CI 临时数据库的 DATABASE_URL。")
        env["DATABASE_URL"] = os.environ["DATABASE_URL"]
        env["DJANGO_DB_SSL_REQUIRED"] = os.environ.get("DJANGO_DB_SSL_REQUIRED", "true")
    else:
        # 本地仅验证请求与正式配置，不把它记作真实 PostgreSQL 测试。
        env["DATABASE_URL"] = "postgresql://smoke:unused@127.0.0.1:1/smoke"

    for changes, expected in [
        ({"DJANGO_SECRET_KEY": ""}, "DJANGO_SECRET_KEY"),
        ({"DATABASE_URL": ""}, "DATABASE_URL"),
        ({"DATABASE_URL": "sqlite:///wrong.sqlite3"}, "必须使用 PostgreSQL"),
        ({"DJANGO_DEBUG": "true"}, "必须关闭 DEBUG"),
        ({"DJANGO_ALLOWED_HOSTS": "*"}, "不能使用 *"),
        ({"DATABASE_URL": "unknown://user:secret-marker@host/db"}, "不是有效的 PostgreSQL"),
    ]:
        result = subprocess.run(
            [sys.executable, "manage.py", "check"], cwd=ROOT, env=env | changes,
            capture_output=True, text=True, encoding="utf-8",
        )
        assert result.returncode != 0 and expected in result.stderr, expected
        assert "secret-marker" not in result.stderr
    print("PASS: 生产配置缺失、错误数据库、DEBUG 和通配域名均拒绝启动；错误不回显连接串")

    command([sys.executable, "manage.py", "check", "--deploy", "--fail-level", "ERROR"], env)
    command([sys.executable, "manage.py", "collectstatic", "--noinput"], env)
    if args.postgres:
        command([sys.executable, "manage.py", "migrate", "--noinput"], env)
        command([sys.executable, "manage.py", "shell", "-c",
                 "from django.db import connection; "
                 "assert connection.vendor == 'postgresql'; "
                 "cursor = connection.cursor(); cursor.execute('SELECT 1'); "
                 "assert cursor.fetchone() == (1,)"], env)
        print("PASS: 临时 PostgreSQL 上迁移与真实查询成功")
    else:
        print("INFO: 本地使用占位数据库地址，未测试 PostgreSQL 连接或迁移")

    with socket.socket() as reserved:
        reserved.bind(("127.0.0.1", 0))
        env["PORT"] = str(reserved.getsockname()[1])
    base = f"http://127.0.0.1:{env['PORT']}"
    opener = build_opener(NoRedirect())

    def request(path, *, secure=True, hostname=HOSTNAME, compressed=False):
        headers = {"Host": hostname}
        if secure:
            headers["X-Forwarded-Proto"] = "https"
        if compressed:
            headers["Accept-Encoding"] = "gzip"
        req = Request(base + path, headers=headers)
        try:
            response = opener.open(req, timeout=3)
        except HTTPError as error:
            response = error
        with response:
            body = response.read()
            if response.headers.get("Content-Encoding") == "gzip":
                body = gzip.decompress(body)
            return response.status, response.headers, body

    if os.name == "nt":
        server_command = [sys.executable, str(Path(__file__).resolve()), "--serve-wsgi"]
        server_name = "Windows WSGI 应用（Gunicorn 在 Linux CI 验证）"
    else:
        command(["bash", "-n", "scripts/render-build.sh"], env)
        command(["bash", "-n", "scripts/render-start.sh"], env)
        server_command = ["bash", "scripts/render-start.sh"]
        server_name = "真实 Gunicorn + Render 启动脚本"

    with tempfile.TemporaryFile() as output:
        process = subprocess.Popen(server_command, cwd=ROOT, env=env, stdout=output, stderr=output)
        try:
            deadline = time.monotonic() + 30
            while True:
                if process.poll() is not None:
                    raise RuntimeError("正式服务器在启动时退出。")
                try:
                    status, _, body = request("/health/", secure=False)
                    if status == 200:
                        break
                except (URLError, TimeoutError, ConnectionError):
                    pass
                if time.monotonic() > deadline:
                    raise RuntimeError("正式服务器未能在 30 秒内就绪。")
                time.sleep(0.2)

            assert json.loads(body) == {"status": "ok"}
            assert request("/health/", secure=False)[1]["Cache-Control"] == "no-store"
            status, headers, body = request("/")
            assert status == 200, status
            html = body.decode("utf-8")
            assert "今天，给自己的成长留一点时间。" in html
            assert "在这里，收好你的每一点进步。" in html
            assert headers["X-Frame-Options"] == "DENY"
            assert "max-age=3600" in headers["Strict-Transport-Security"]
            assets = re.findall(r'(?:href|src)="(/static/[^\"]+)"', html)
            assert any(re.search(r"styles\.[0-9a-f]{12}\.css$", path) for path in assets)
            assert any(path.endswith(".svg") for path in assets)
            for path in assets:
                asset_status, asset_headers, asset_body = request(path, compressed=True)
                assert asset_status == 200 and asset_body, path
                if path.endswith(".css"):
                    assert "text/css" in asset_headers["Content-Type"]
                    assert "immutable" in asset_headers["Cache-Control"]
                elif path.endswith(".svg"):
                    assert "image/svg+xml" in asset_headers["Content-Type"]
            assert request("/", hostname="unknown.example")[0] == 400
            status, headers, _ = request("/", secure=False)
            assert status == 301 and headers["Location"] == f"https://{HOSTNAME}/"
            print(f"PASS: {server_name}；首页、哈希静态文件、健康检查、HTTPS 和域名限制")
        finally:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)


if __name__ == "__main__":
    main()
