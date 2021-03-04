import logging
import json
import docker
from docker.types import Mount
from docker.errors import NotFound
import os
import yaml
import sys
import time
import re
import os.path
from .plugin_config import add_plugin_configs, delete_plugin_configs, from_docker_compose, sort_plugin_configs

logger = logging.getLogger()
logger.setLevel(logging.INFO)
hostcwd = os.environ.get("HOST_CWD", "")

# from https://stackoverflow.com/questions/52412297/how-to-replace-environment-variable-value-in-yaml-file-to-be-parsed-using-python
path_matcher2 = re.compile(r'.*\$\{([^}]+)\}.*')
path_matcher = re.compile(r'\$\{([^}]+)\}')

def path_constructor(loader, node):
    ''' Extract the matched value, expand env variable, and replace the match '''
    value = node.value
    i = 0
    value2 = ""
    while True:
        match = path_matcher.search(value, i)
        if not match:
            return value2 + value[i:]
        else:
            env_var = match.group()[2:-1]
            value2 += value[i:match.start()] + os.environ[env_var]
            i = match.end()


class EnvVarLoader(yaml.SafeLoader):
    pass


EnvVarLoader.add_implicit_resolver('!path', path_matcher2, None)
EnvVarLoader.add_constructor('!path', path_constructor)


def start_plugins(pcs):
    for pc in sort_plugin_configs(pcs):
        run_container(pc)


def stop_plugins(pcs):
    for pc in reversed(sort_plugin_configs(pcs)):
        stop_container(pc)


def remove_plugins(pcs):
    for pc in pcs:
        remove_container(pc)


def get_container(pc):
    client = docker.from_env()
    ret = client.containers.get(pc["name"])
    return ret


def network():
    return os.environ["COMPOSE_PROJECT_NAME"] + "_default"


def run_container(pc):
    client = docker.from_env()

    name = pc["name"]
    image = pc["image"]

    try:
        ret = client.containers.get(name)
        logging.info(f"{name} has already been started")
        if ret.image.id == client.images.get(image).id:
            return ret
        else:
            stop_container(pc)
            remove_container(pc)

    except NotFound:
        pass
    
    def source(l):
        source = l["source"]
        if os.sep in source:
            if not os.path.isabs(source):
                source = os.path.join(hostcwd, source)

        return source

    volumes = list(map(lambda l: Mount(l["target"], source(l), type=l["type"], read_only=l["read_only"]), pc.get("volumes", [])))
    logging.info("pc = {0}".format(pc))
    logging.info(f"starting {name}")
    ret = client.containers.run(image, network=network(), mounts=volumes, detach=True, stdout=True, stderr=True, name=name, hostname=name, **{k:v for k,v in pc.items() if k in ["command", "environment", "entrypoint", "restart_policy"]})
    logging.info(f"{name} started")
    return ret


def stop_container(pc):
    name = pc["name"]
    client = docker.from_env()
    ret = client.containers.get(name)
    logging.info(f"stopping {name}")
    ret.stop()
    logging.info(f"waiting for {name} to exit")
    exit_code = ret.wait()
    logging.info(f"{name} stopped {exit_code}")


def remove_container(pc):
    name = pc["name"]
    client = docker.from_env()
    ret = client.containers.get(name)
    logging.info(f"removing {name}")
    ret.remove()
    logging.info(f"{name} removed")


def load_plugins_from_file(f):
    return from_docker_compose(yaml.load(f, Loader=EnvVarLoader))


def load_plugins(init_plugin_path):
    pcs = []
    vs = []
    for fn in os.listdir(init_plugin_path):
        if fn.endswith(".yml") or fn.endswith(".yaml"):
            with open(os.path.join(init_plugin_path, fn), "r") as f:
                content = f.read()
                print(content)
                sys.stdout.flush()
                services, volumes = load_plugins_from_file(content)
                print(services)
                sys.stdout.flush()
                pcs.extend(services)
                vs.extend(volumes)
    return pcs, vs


def create_volume(v):
    client = docker.from_env()
    name = v["name"]
    vol = None

    if v.get("persistent", False):
        try:
            vol = client.volumes.get(name)
        except docker.errors.NotFound:
            pass

    if vol is None:
        try:
            client.volumes.get(name)
            raise RuntimeError(f"cannot create an existing volume {name}")
        except docker.errors.NotFound:
            vol = client.volumes.create(name)
            
    return vol


def create_volumes(vs):
    for v in vs:
        create_volume(v)


def delete_volume(v):
    client = docker.from_env()
    if not v.get("persistent", False):
        client.volumes.get(v["name"]).remove()


def delete_volumes(vs):
    for v in vs:
        delete_volume(v)
        
    
def init_plugin():
    init_plugin_path = os.environ.get("INIT_PLUGIN_PATH")

    if init_plugin_path is not None:
        pcs, vs = load_plugins(init_plugin_path)
        create_volumes(vs)
        start_plugins(pcs)
        add_plugin_configs(pcs)    


def delete_init_plugin():
    init_plugin_path = os.environ.get("INIT_PLUGIN_PATH")

    if init_plugin_path is not None:
        pcs, vs = load_plugins(init_plugin_path)
        stop_plugins(pcs)
        remove_plugins(pcs)
        delete_volumes(vs)
        for pc in pcs:
            delete_plugin_configs(pc)





