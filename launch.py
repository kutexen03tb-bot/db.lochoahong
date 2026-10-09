"""Double-click launcher. Installs project dependencies in a private venv.
Local desktop mode binds only to 127.0.0.1; app.py still supports Arena preview.
"""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import secrets
import subprocess
import sys
import threading
import time
import urllib.request
import venv
import webbrowser

ROOT = Path(__file__).resolve().parent
ENV = ROOT / '.venv'
RUNTIME = ROOT / '.linkscope-runtime.json'
LOCK = ROOT / '.linkscope-launch.lock'


def probe(data):
    port = data.get('port')
    token = data.get('token')
    if not isinstance(port, int) or not 1024 <= port <= 65535 or not isinstance(token, str):
        return False
    try:
        # Do not use system HTTP proxy settings for local desktop health checks.
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        with opener.open(f'http://127.0.0.1:{port}/_linkscope_health', timeout=1) as response:
            body = json.load(response)
        return body.get('app') == 'LinkScope' and body.get('token') == token
    except Exception:
        return False


def open_existing():
    try:
        data = json.loads(RUNTIME.read_text(encoding='utf-8'))
        if probe(data):
            webbrowser.open(f"http://127.0.0.1:{data['port']}/")
            print('LinkScope dang chay. Da mo lai trinh duyet.')
            return True
    except (OSError, ValueError):
        pass
    return False


def acquire_lock():
    handle = LOCK.open('a+b')
    handle.seek(0, os.SEEK_END)
    if handle.tell() == 0:
        handle.write(b'0')
        handle.flush()
    handle.seek(0)
    try:
        if os.name == 'nt':
            import msvcrt
            msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        return handle
    except (OSError, BlockingIOError):
        handle.close()
        return None


def prepare_python():
    python = ENV / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python')
    if not python.exists():
        print('Lan dau: dang tao moi truong Python rieng...', flush=True)
        venv.EnvBuilder(with_pip=True).create(ENV)
    digest = hashlib.sha256((ROOT / 'requirements.txt').read_bytes()).hexdigest()
    stamp = ENV / '.linkscope-dependencies'
    health = subprocess.run([str(python), '-c', 'import flask, requests, openpyxl'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    ready = stamp.exists() and stamp.read_text(encoding='utf-8') == digest and health.returncode == 0
    if not ready:
        print('Dang cai/kiem tra thu vien. Can Internet o lan dau; vui long cho...', flush=True)
        subprocess.check_call([str(python), '-m', 'pip', 'install', '--disable-pip-version-check', '-r', str(ROOT / 'requirements.txt')], cwd=ROOT)
        stamp.write_text(digest, encoding='utf-8')
    return python


def serve():
    from werkzeug.serving import make_server
    from app import app
    token = secrets.token_hex(16)

    @app.get('/_linkscope_health')
    def health():
        return {'app': 'LinkScope', 'token': token}

    # Let the OS pick a free port; no conflict with another tool on port 8000.
    server = make_server('127.0.0.1', 0, app, threaded=True)
    data = {'port': server.server_port, 'token': token}
    RUNTIME.write_text(json.dumps(data), encoding='utf-8')
    url = f'http://127.0.0.1:{server.server_port}/'
    stop_browser = threading.Event()

    def open_when_ready():
        for _ in range(40):
            if stop_browser.is_set():
                return
            if probe(data):
                try:
                    if not webbrowser.open(url):
                        print('Khong tu mo duoc trinh duyet. Hay mo: ' + url, flush=True)
                except Exception:
                    print('Hay mo trinh duyet tai: ' + url, flush=True)
                return
            stop_browser.wait(0.25)
        print('Neu trinh duyet chua mo, hay truy cap: ' + url, flush=True)

    print('\n====================================================', flush=True)
    print('LINKSCOPE DA SAN SANG: ' + url, flush=True)
    print('Chi mo tren may nay. Khong cong khai ra Internet.', flush=True)
    print('Giu cua so nay mo khi dung tool.', flush=True)
    print('De dung: bam Ctrl+C trong cua so nay.', flush=True)
    print('====================================================\n', flush=True)
    thread = threading.Thread(target=open_when_ready, daemon=True)
    thread.start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        stop_browser.set()
        server.server_close()
        try:
            if json.loads(RUNTIME.read_text(encoding='utf-8')).get('token') == token:
                RUNTIME.unlink(missing_ok=True)
        except (OSError, ValueError):
            pass
    return 0


def main():
    if sys.version_info < (3, 10):
        print('Can Python 3.10 tro len. Tai tai https://www.python.org/downloads/windows/')
        return 1
    if '--serve' in sys.argv:
        return serve()
    os.chdir(ROOT)
    lock = acquire_lock()
    if lock is None:
        if not open_existing():
            print('Mot cua so LinkScope khac dang khoi dong. Vui long doi cua so do.')
        return 0
    try:
        if open_existing():
            return 0
        python = prepare_python()
        child = subprocess.Popen([str(python), str(ROOT / 'launch.py'), '--serve'], cwd=ROOT)
        try:
            return child.wait()
        except KeyboardInterrupt:
            # Ctrl+C is normally delivered to the entire console process group.
            try:
                child.wait(timeout=5)
            except subprocess.TimeoutExpired:
                child.terminate()
                child.wait(timeout=5)
            return 0
    except (OSError, subprocess.SubprocessError) as exc:
        print('\nKhong khoi dong duoc LinkScope: ' + str(exc))
        print('Kiem tra Internet va quyen ghi thu muc. Giai nen vao thu muc rieng, roi thu lai.')
        return 1
    except KeyboardInterrupt:
        print('\nDa dung khoi dong.')
        return 0
    finally:
        lock.close()


if __name__ == '__main__':
    sys.exit(main())
