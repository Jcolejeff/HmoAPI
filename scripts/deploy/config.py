# from decouple import config
# PORT=config("PORT", default="7001", cast=str)
# LOG_URL=config("LOG_URL", default="/var/www/timbu/staging/travel.api/logs", cast=str)
LOG_URL="/var/www/timbu/staging/travel.api/logs"
PORT=7001

bind = f"0.0.0.0:{PORT}"
backlog = 2048
workers = 2    
worker_class = "uvicorn.workers.UvicornWorker"
worker_connections = 1000
timeout = 30
keepalive = 2
spew = False
daemon = False
pidfile = None
umask = 0
user = None
group = None
tmp_upload_dir = None
errorlog = f"{LOG_URL}/error.log"
loglevel = "error"
accesslog = f"{LOG_URL}/access.log"
access_log_format = '%(h)s %(l)s %(t)s "%(r)s" %(s)s %(b)s "%(R)s" "%(f)s" %(u)s'
#%h %^[%d:%t %^] "%r" %s %b "%R" "%u"
#access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'
proc_name = None
