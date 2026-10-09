import os

bind = '0.0.0.0:' + os.environ.get('PORT', '10000')
# In-memory request limits are shared by threads, not by processes.
# Keep exactly one worker/instance. Use shared storage before scaling.
workers = 1
worker_class = 'gthread'
threads = 4
timeout = 150
graceful_timeout = 120
keepalive = 5
max_requests = 500
max_requests_jitter = 50
accesslog = None  # Avoid logging query strings/accidental credentials.
errorlog = '-'
capture_output = False
