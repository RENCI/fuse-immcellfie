import os
import syslog
import time
import logging
import requests
from tx.dateutils.utils import tstostr
from tx.router import plugin_config
from tx.logging.utils import tx_log, timestamp

logger = logging.getLogger()
logger.setLevel(logging.INFO)

logging_plugin = os.environ.get("LOGGING")
def log(level, event, source, *args, **kwargs):
    pc = plugin_config.get_plugin_config(logging_plugin)
    if pc is None:
        logger.log(logging.INFO, f"{level},{event},{timestamp},{source},{args},{kwargs}")
    else:
        tx_log("http://{host}:{port}/log".format(host=pc["name"], port=pc["port"]), level, event, source, *args, **kwargs)

post_headers = {
    "Content-Type": "application/json",
    "Accept": "application/json"
}

def l(event, source, log_args=False, log_ret=False):
    def function_wrapper(func):
        def function_wrapped(*args, **kwargs):
            log(syslog.LOG_NOTICE, f"{event}_begin", timestamp(), source, *(args if log_args else []), **(kwargs if log_args else {}))
            try:
                ret = func(*args, **kwargs)
                log(syslog.LOG_NOTICE, f"{event}_end", timestamp(), source, *(args if log_args else []), **({"ret": ret} if log_ret else {}), **(kwargs if log_args else {}))
                return ret
            except Exception as e:
                log(syslog.LOG_ERR, f"{event}_exception", timestamp(), source, *args, exception=e, **kwargs)
                raise
        return function_wrapped
    return function_wrapper


