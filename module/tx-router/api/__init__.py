import requests
from tx.router import plugin_config, plugin
from tx.router.logging import l
import logging
import connexion
import sys
from werkzeug.datastructures import Headers
from flask import Response, request
from tempfile import TemporaryFile

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def set_forwarded_path_header(f):
    def func(name, path, headers, *args, **kwargs):
        forwarded_path0_slash = connexion.request.headers.get("X-Forwarded-Path", "")
        forwarded_path0 = forwarded_path0_slash.rstrip("/")
        forwarded_path = f"{forwarded_path0}/v1/plugin/{name}"
        headers0 = {**headers, "X-Forwarded-Path": forwarded_path}
        logger.debug("headers0 = " + str(headers0))
        return f(name, path, headers0, *args, **kwargs)
    return func


@l("get", "backend")
@set_forwarded_path_header
def get_plugin(name, path, headers, kwargs={}):
    pc = plugin_config.get_plugin_config(name)
    if pc is None:
        return "not found", 404
    
    port = pc.get("port", None)
    if port is None:
        raise RuntimeError("plugin doesn't have port")

    resp = requests.get("http://{host}:{port}/{path}".format(host=pc["name"], port=port, path=path), headers=headers, params=kwargs, stream=True)
    return Response(resp.iter_content(chunk_size=1024*1024), status=resp.status_code, headers=Headers(resp.headers.items()))


@l("post", "backend")
@set_forwarded_path_header
def post_plugin(name, path, headers, stream, kwargs={}):
    return base_plugin(requests.post, name, path, headers, stream, kwargs)


def base_plugin(method, name, path, headers, stream, kwargs):
    pc = plugin_config.get_plugin_config(name)
    if pc is None:
        return "not found", 404

    port = pc.get("port", None)
    if port is None:
        raise RuntimeError("plugin doesn't have port")

    with TemporaryFile() as f:
        chunk_size = 4096
        while True:
            chunk = stream.read(chunk_size)
            if len(chunk) == 0:
                break
            f.write(chunk)
        f.seek(0, 0)
            
        resp = method("http://{host}:{port}/{path}".format(host=pc["name"], port=port, path=path), headers=headers, params=kwargs, data=f, stream=True)

    return Response(resp.iter_content(chunk_size=1024*1024), status=resp.status_code, headers=Headers(resp.headers.items()))


@l("delete", "backend")
@set_forwarded_path_header
def delete_plugin(name, path, headers, stream, kwargs={}):
    return base_plugin(requests.delete, name, path, headers, stream, kwargs)


def get_plugin_config(name):
    pc = plugin_config.get_plugin_config(name)
    pc["_id"] = str(pc["_id"])
    return pc


def fil(name, name_regex):
    fils = []
    if name_regex is not None:
        fils.append({"name": {"$regex": name_regex}})
    if name is not None:
        fils.append({"name": name})
    if len(fils) == 0:
        return {}
    else:
        return {"$and": fils}


def get_plugin_configs(name=None, name_regex=None):
    ps = plugin_config.get_plugin_configs(fil(name, name_regex))
    for pc in ps:
        pc["_id"] = str(pc["_id"])

    return ps


def add_plugin_configs(body):
    pc = plugin_config.add_plugin_configs(body)
    return len(pc)


def delete_plugin_config(name=None, name_regex=None):
    return delete_plugin_configs(name=name, name_regex=name_regex)


def delete_plugin_configs(name=None, name_regex=None):
    return plugin_config.delete_plugin_configs(fil(name, name_regex))


def update_plugin_config(name, body):
    plugin_config.replace_plugin_config(name, body)


def get_plugin_container(name):
    pc = plugin_config.get_plugin_config(name)
    container = plugin.get_container(pc)
    if container is not None:
        return {
            "status": container.status
        }
    else:
        return None


def add_plugin_container(name):
    pc = plugin_config.get_plugin_config(name)
    plugin.run_container(pc)


def delete_plugin_container(name):
    pc = plugin_config.get_plugin_config(name)
    plugin.stop_container(pc)
    plugin.remove_container(pc)


def get_containers():
    containers = []
    for pc in plugin_config.get_plugin_configs({}):
        container = plugin.get_container(pc)
        if container is not None:
            cs = {
                "status": container.status
            }
        else:
            cs = None

        containers.append({
            "name": pc["name"],
            "container": cs
        })
    return containers


def add_containers():
    for pc in plugin_config.get_plugin_configs({}):
        plugin.run_container(pc)


def delete_containers():
    for pc in plugin_config.get_plugin_configs({}):
        plugin.stop_container(pc)
        plugin.remove_container(pc)
