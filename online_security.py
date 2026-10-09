"""Password/session/CSRF/rate guards for a SINGLE-worker private deployment.
No API keys or product results are persisted. Use Redis/shared auth for multi-worker use.
"""
from collections import defaultdict, deque
from datetime import timedelta
import hmac
import hashlib
import secrets
import threading
import time

from flask import g, jsonify, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash


class WindowLimiter:
    def __init__(self):
        self.entries = defaultdict(deque)
        self.lock = threading.Lock()

    def allow(self, key, count, seconds=60):
        now = time.monotonic()
        with self.lock:
            q = self.entries[key]
            while q and q[0] <= now - seconds:
                q.popleft()
            if len(q) >= count:
                return False
            q.append(now)
            if len(self.entries) > 2000:
                self.entries = defaultdict(deque, {k: v for k, v in self.entries.items() if v and v[-1] > now - 600})
            return True


def install_security(app, password, secret_key, secure_cookie=True):
    if len(password) < 16:
        raise RuntimeError('LINKSCOPE_PASSWORD must have at least 16 characters. Set it in hosting Environment, never in Git.')
    if len(secret_key) < 32:
        raise RuntimeError('SECRET_KEY must have at least 32 characters. Set it in hosting Environment.')
    password_hash = generate_password_hash(password)
    auth_version = hmac.new(secret_key.encode(), password.encode(), hashlib.sha256).hexdigest()
    app.config.update(SECRET_KEY=secret_key, SESSION_COOKIE_NAME='linkscope_session',
        SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SECURE=secure_cookie,
        SESSION_COOKIE_SAMESITE='Lax', PERMANENT_SESSION_LIFETIME=timedelta(hours=8),
        SESSION_REFRESH_EACH_REQUEST=True, MAX_CONTENT_LENGTH=12 * 1024 * 1024)
    limiter = WindowLimiter()
    slots = threading.BoundedSemaphore(1)
    limits = {'/api/check': 5, '/api/history': 10, '/api/import': 15,
              '/api/export': 15, '/api/history/export': 10, '/api/analyze': 30}

    def csrf_token():
        if 'csrf' not in session:
            session['csrf'] = secrets.token_urlsafe(32)
        return session['csrf']

    @app.context_processor
    def deployment_context():
        return {'deployment_mode': True, 'csrf_token': csrf_token}

    @app.before_request
    def guard():
        if request.path == '/healthz':
            return None
        if request.path == '/login':
            if request.method == 'POST':
                # Global + per-peer limits. Global limit cannot be bypassed by forged forwarding headers.
                if not limiter.allow(('login-global',), 20) or not limiter.allow(('login-peer', request.remote_addr), 5):
                    return render_template('login.html', error='Quá nhiều lần đăng nhập. Vui lòng đợi một phút.'), 429
                token = request.form.get('csrf_token', '')
                if not token or not hmac.compare_digest(token.encode(), session.get('csrf', '').encode()):
                    return render_template('login.html', error='Phiên đăng nhập không hợp lệ. Tải lại trang rồi thử lại.'), 400
            return None
        if not session.get('authenticated') or session.get('auth_version') != auth_version:
            if request.path.startswith('/api/'):
                r = jsonify(error='Phiên đăng nhập đã hết hoặc chưa đăng nhập. Cần tải lại trang để đăng nhập; kết quả chưa xuất có thể mất.')
                r.status_code = 401
                r.headers['X-LinkScope-Session'] = 'expired'
                return r
            return redirect(url_for('login'))
        if request.method not in ('GET', 'HEAD', 'OPTIONS'):
            token = request.headers.get('X-CSRF-Token') or request.form.get('csrf_token', '')
            if not token or not hmac.compare_digest(token.encode(), session.get('csrf', '').encode()):
                return jsonify(error='Yêu cầu không hợp lệ (CSRF). Vui lòng tải lại trang và đăng nhập.'), 403
        if request.path in limits and request.method == 'POST':
            if not limiter.allow(('global-route', request.path), limits[request.path]):
                r = jsonify(error='Đạt giới hạn an toàn của tool. Đợi một phút rồi thử lại.', retryAfter=60)
                r.status_code = 429
                r.headers['Retry-After'] = '60'
                return r
            if not slots.acquire(blocking=False):
                return jsonify(error='Tool đang xử lý yêu cầu khác. Vui lòng thử lại sau.', retryAfter=15), 429
            g.online_slot = True
        return None

    @app.teardown_request
    def release_slot(exc):
        if getattr(g, 'online_slot', False):
            slots.release()
            g.online_slot = False

    def secure_headers(response):
        response.headers['Cache-Control'] = 'no-store'
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['Referrer-Policy'] = 'no-referrer'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['Permissions-Policy'] = 'camera=(), microphone=(), geolocation=()'
        response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; object-src 'none'; base-uri 'self'; form-action 'self'; frame-ancestors 'none'"
        if secure_cookie:
            response.headers['Strict-Transport-Security'] = 'max-age=31536000'
        return response

    # Flask executes these in reverse registration order; run this last.
    app.after_request_funcs.setdefault(None, []).insert(0, secure_headers)

    @app.get('/healthz')
    def online_health():
        return {'status': 'ok'}

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'GET' and session.get('authenticated') and session.get('auth_version') == auth_version:
            return redirect('/')
        if request.method == 'POST':
            candidate = request.form.get('password', '')
            if len(candidate) <= 1024 and check_password_hash(password_hash, candidate):
                session.clear()
                session['authenticated'] = True
                session['auth_version'] = auth_version
                session.permanent = True
                csrf_token()
                return redirect('/')
            return render_template('login.html', error='Mật khẩu chưa đúng. Đây là mật khẩu tool, không phải API Key.'), 401
        return render_template('login.html', error=None)

    @app.post('/logout')
    def logout():
        session.clear()
        return redirect('/login')

    return limiter
