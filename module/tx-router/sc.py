import sys
from tx.router.plugin import init_plugin, delete_init_plugin

def on_starting(server):
    print("starting server")
    sys.stdout.flush()
    init_plugin()

def on_exit(server):
    print("stopping server")
    sys.stdout.flush()
    delete_init_plugin()

    
