import os
import requests
import time
import pytest
import json
import pymongo
import docker
from multiprocessing import Process
import shutil
from tx.router import plugin, plugin_config
from contextlib import contextmanager
import tempfile
from bson.objectid import ObjectId
import api
import yaml
from debug.utils import bag_equal, bag_contains
from tx.router.plugin_config import to_docker_compose
from api.jwt import generate_token

import os
tag=os.environ['TX_TAG']

CLIENT_DELAY = 1

auth_token = generate_token( "test", ["admin"])

auth_token2 = generate_token( "test2", ["guest"])

headers = {"Authorization": f"Bearer {auth_token}"}

headers2 = {"Authorization": f"Bearer {auth_token2}"}

base_url = "http://txrouter:8080/v1"

@pytest.fixture(scope="session", autouse=True)
def pause():
    yield
    if os.environ.get("PAUSE") == "1":
        input("Press Enter to continue...")

        
@pytest.fixture(scope='function', autouse=True)
def test_log(request):
    print("Test '{}' STARTED".format(request.node.nodeid)) # Here logging is used, you can use whatever you want to use for logs
    yield
    print("Test '{}' COMPLETED".format(request.node.nodeid))


name = "nginx10"
name2 = "nginx20"


def pc(temp_dir_name):
    return {
        "image": "nginx:1.19.2",
        "environment": {},
        "name": name,
        "port": 80,
        "volumes": [
            {
                "target": "/usr/share/nginx/html",
                "source": temp_dir_name,
                "type": "bind",
                "read_only": True
            }
        ]
    
    }


def pc2(temp_dir_name):
    return {
        "image": "nginx:1.19.2",
        "environment": {},
        "name": name2,
        "port": 80,
        "volumes": [
            {
                "target": "/usr/share/nginx/html",
                "source": temp_dir_name,
                "type": "bind",
                "read_only": True
            }
        ]
    
    }


echo_pc = {
    "image": "tx-router-test-flask-echo-server:" + tag,
    "environment": {},
    "name": "echo",
    "port": 80,
    "environment": {
        "HOST": "0.0.0.0",
        "PORT": "80"
    },
    "volumes": []
}

echo_pc2 = {
    "image": "tx-router-test-flask-echo-server:" + tag,
    "name": "echo2",
    "port": 80,
    "environment": {
        "HOST": "0.0.0.0",
        "PORT": "80",
        "VAR": "data"
    },
    "volumes": []
}

echo_pcs_dep = [
    {
        "image": "tx-router-test-flask-echo-server:" + tag,
        "environment": {},
        "name": "echo",
        "port": 80,
        "environment": {
            "HOST": "0.0.0.0",
            "PORT": "80"
        }
    }, {
        "image": "tx-router-test-flask-echo-server:" + tag,
        "name": "echo2",
        "port": 80,
        "environment": {
            "HOST": "0.0.0.0",
            "PORT": "80",
            "VAR": "data"
        },
        "depends_on": ["echo"]
    }
]


echo_pcs_dep2 = [
    {
        "image": "tx-router-test-flask-echo-server:" + tag,
        "environment": {},
        "name": "echo",
        "port": 80,
        "depends_on": ["echo2"]
    }, {
        "image": "tx-router-test-flask-echo-server:" + tag,
        "name": "echo2",
        "port": 80,
        "depends_on": ["echo"]
    }
]


echo_pcs_dep3 = [
    {
        "image": "tx-router-test-flask-echo-server:" + tag,
        "environment": {},
        "name": "echo",
        "port": 80
    }, {
        "image": "tx-router-test-flask-echo-server:" + tag,
        "environment": {},
        "name": "echo2",
        "port": 80,
        "depends_on": ["echo0"]
    }, {
        "image": "tx-router-test-flask-echo-server:" + tag,
        "name": "echo3",
        "port": 80,
        "depends_on": ["echo0"]
    }
]


fil = {"name": name}

fil2 = {"name": name2}

def test_run_container_get():
    with tempfile.TemporaryDirectory(prefix="/tmp/") as temp_dir_name:
        os.chmod(temp_dir_name, 0o755)
        s = "pds"
        with open(os.path.join(temp_dir_name, "index.json"), "w+") as f:
            f.write(json.dumps(s))

        try:
            apc = pc(temp_dir_name)
            plugin.run_container(apc)

            container_name = apc["name"]

            time.sleep(CLIENT_DELAY)
            resp = requests.get("http://{host}/index.json".format(host=container_name))

            assert resp.status_code == 200
            assert resp.json() == s
        finally:
            plugin.stop_container(apc)
            plugin.remove_container(apc)


def test_run_container_get_relative_path():
    host_cwd_mount = os.environ["HOST_CWD_MOUNT"]
    with tempfile.TemporaryDirectory(prefix=os.path.join(host_cwd_mount, "")) as temp_dir_name:
        _, basename = os.path.split(temp_dir_name)
        os.chmod(temp_dir_name, 0o755)
        s = "pds"
        with open(os.path.join(temp_dir_name, "index.json"), "w+") as f:
            f.write(json.dumps(s))

        try:
            apc = pc(f"./{basename}")
            plugin.run_container(apc)

            container_name = apc["name"]

            time.sleep(CLIENT_DELAY)
            resp = requests.get("http://{host}/index.json".format(host=container_name))

            assert resp.status_code == 200
            assert resp.json() == s
        finally:
            plugin.stop_container(apc)
            plugin.remove_container(apc)


def write_config(apcs, f):
    yaml.dump(to_docker_compose(apcs), f, default_flow_style=False)


def test_run_container_from_init_env():
    try:
        apc = echo_pc
        apcs = [apc]
        init_plugin_path = "/plugin"
        os.mkdir(init_plugin_path)
        with open(f"{init_plugin_path}/echo.yaml", "w+") as f:
            f.write('''
services:
  echo:
    image: tx-router-test-flask-echo-server:${TAG}
    environment: {}
    port: 80
    environment:
      HOST: 0.0.0.0
      PORT: "80"
    volumes: []
''')
        os.environ["INIT_PLUGIN_PATH"] = init_plugin_path
        os.environ["TAG"] = tag
        plugin.init_plugin()
        del os.environ["TAG"]
        del os.environ["INIT_PLUGIN_PATH"]
        assert bag_contains(plugin_config.get_plugin_configs({}), apcs)

        container_name = apc["name"]

        time.sleep(CLIENT_DELAY)
        resp = requests.get("http://{host}/".format(host=container_name))

        assert resp.status_code == 200
        assert resp.json()["method"] == "GET"
        shutil.rmtree(init_plugin_path)
    finally:
        plugin.stop_container(apc)
        plugin.remove_container(apc)
        plugin_config.delete_plugin_configs(apc)


def test_run_container_from_init():
    try:
        apc = echo_pc
        apcs = [apc]
        init_plugin_path = "/plugin"
        os.mkdir(init_plugin_path)
        with open(f"{init_plugin_path}/echo.yaml", "w+") as f:
            write_config(apcs, f)
        os.environ["INIT_PLUGIN_PATH"] = init_plugin_path

        plugin.init_plugin()
        assert bag_contains(plugin_config.get_plugin_configs({}), apcs)

        container_name = apc["name"]

        time.sleep(CLIENT_DELAY)
        resp = requests.get("http://{host}/".format(host=container_name))

        assert resp.status_code == 200
        assert resp.json()["method"] == "GET"
        shutil.rmtree(init_plugin_path)
    finally:
        plugin.stop_container(apc)
        plugin.remove_container(apc)
        plugin_config.delete_plugin_configs(apc)


def test_delete_container_from_init():
    apc = echo_pc
    apcs = [apc]
    init_plugin_path = "/plugin"
    os.mkdir(init_plugin_path)
    with open(f"{init_plugin_path}/echo.yaml", "w+") as f:
        write_config(apcs, f)
        
    os.environ["INIT_PLUGIN_PATH"] = init_plugin_path
        
    plugin.init_plugin()
        
    container_name = apc["name"]

    time.sleep(CLIENT_DELAY)
    plugin.delete_init_plugin()
        
    with pytest.raises(Exception):
        resp = requests.get("http://{host}/".format(host=container_name))

    assert bag_equal(plugin_config.get_plugin_configs({}), [])
    shutil.rmtree(init_plugin_path)



def test_run_container_from_init2():
    try:
        apc = echo_pc
        apc2 = echo_pc2
        apcs = [apc, apc2]
        init_plugin_path = "/plugin"
        os.mkdir(init_plugin_path)
        with open(f"{init_plugin_path}/echo.yaml", "w+") as f:
            write_config(apcs, f)
            
        os.environ["INIT_PLUGIN_PATH"] = init_plugin_path

        plugin.init_plugin()
        assert bag_contains(plugin_config.get_plugin_configs({}), apcs)

        container_name = apc["name"]
        container_name2 = apc2["name"]

        time.sleep(CLIENT_DELAY)
        resp = requests.get("http://{host}/".format(host=container_name))

        assert resp.status_code == 200
        assert resp.json()["method"] == "GET"
        resp2 = requests.get("http://{host}/".format(host=container_name2))

        assert resp2.status_code == 200
        assert resp2.json()["method"] == "GET"
        shutil.rmtree(init_plugin_path)
    finally:
        plugin.stop_container(apc)
        plugin.remove_container(apc)
        plugin_config.delete_plugin_configs(apc)
        plugin.stop_container(apc2)
        plugin.remove_container(apc2)
        plugin_config.delete_plugin_configs(apc2)


def test_delete_container_from_init2():
    apc = echo_pc
    apc2 = echo_pc2
    apcs = [apc, apc2]
    init_plugin_path = "/plugin"
    os.mkdir(init_plugin_path)
    with open(f"{init_plugin_path}/echo.yaml", "w+") as f:
        write_config(apcs, f)
            
    os.environ["INIT_PLUGIN_PATH"] = init_plugin_path
        
    plugin.init_plugin()
        
    container_name = apc["name"]
    container_name2 = apc2["name"]

    time.sleep(CLIENT_DELAY)
    plugin.delete_init_plugin()
        
    with pytest.raises(Exception):
        resp = requests.get("http://{host}/".format(host=container_name))

    with pytest.raises(Exception):
        resp = requests.get("http://{host}/".format(host=container_name2))
        
    assert bag_equal(plugin_config.get_plugin_configs({}), [])
    shutil.rmtree(init_plugin_path)



def test_run_container_from_init_dep():
    apcs = echo_pcs_dep
    try:
        init_plugin_path = "/plugin"
        os.mkdir(init_plugin_path)
        with open(f"{init_plugin_path}/echo.yaml", "w+") as f:
            write_config(apcs, f)
        os.environ["INIT_PLUGIN_PATH"] = init_plugin_path

        plugin.init_plugin()
        assert bag_contains(plugin_config.get_plugin_configs({}), apcs)

        time.sleep(CLIENT_DELAY)
        for apc in apcs:
            container_name = apc["name"]

            resp = requests.get(f"http://{container_name}/")

        assert resp.status_code == 200
        assert resp.json()["method"] == "GET"
        shutil.rmtree(init_plugin_path)
    finally:
        for apc in apcs:
            plugin.stop_container(apc)
            plugin.remove_container(apc)
            plugin_config.delete_plugin_configs(apc)


def test_delete_container_from_init_dep():
    apcs = echo_pcs_dep
    init_plugin_path = "/plugin"
    os.mkdir(init_plugin_path)
    with open(f"{init_plugin_path}/echo.yaml", "w+") as f:
        write_config(apcs, f)
        
    os.environ["INIT_PLUGIN_PATH"] = init_plugin_path
        
    plugin.init_plugin()
        
    time.sleep(CLIENT_DELAY)
    plugin.delete_init_plugin()
        
    for apc in apcs:
        container_name = apc["name"]

        with pytest.raises(Exception):
            resp = requests.get(f"http://{container_name}/")

    assert bag_equal(plugin_config.get_plugin_configs({}), [])
    shutil.rmtree(init_plugin_path)



def test_run_container_from_init_deps2():
    apcs = echo_pcs_dep2
    init_plugin_path = "/plugin"
    os.mkdir(init_plugin_path)
    with open(f"{init_plugin_path}/echo.yaml", "w+") as f:
        write_config(apcs, f)
    os.environ["INIT_PLUGIN_PATH"] = init_plugin_path
        
    with pytest.raises(Exception):
        plugin.init_plugin()

    for apc in apcs:
        container_name = apc["name"]

        with pytest.raises(Exception):
            resp = requests.get(f"http://{container_name}/")

    shutil.rmtree(init_plugin_path)


def test_run_container_from_init_deps3():
    apcs = echo_pcs_dep3
    init_plugin_path = "/plugin"
    os.mkdir(init_plugin_path)
    with open(f"{init_plugin_path}/echo.yaml", "w+") as f:
        write_config(apcs, f)
    os.environ["INIT_PLUGIN_PATH"] = init_plugin_path
        
    with pytest.raises(Exception):
        plugin.init_plugin()

    for apc in apcs:
        container_name = apc["name"]

        with pytest.raises(Exception):
            resp = requests.get(f"http://{container_name}/")

    shutil.rmtree(init_plugin_path)


def test_run_container_get_echo():
    try:
        apc = echo_pc

        plugin.run_container(apc)

        container_name = apc["name"]

        time.sleep(CLIENT_DELAY)
        resp = requests.get(f"http://{container_name}/")

        assert resp.status_code == 200
        assert resp.json()["method"] == "GET"

    finally:
        plugin.stop_container(apc)
        plugin.remove_container(apc)


def test_run_container_post_echo():
    s = "pds"
    try:
        apc = echo_pc

        plugin.run_container(apc)

        container_name = apc["name"]

        time.sleep(CLIENT_DELAY)
        resp = requests.post(f"http://{container_name}", headers={"Content-Type": "application/json"}, json=s)

        assert resp.status_code == 200
        assert resp.json()["data"] == json.dumps(s)
        assert resp.json()["method"] == "POST"

    finally:
        plugin.stop_container(apc)
        plugin.remove_container(apc)


def test_run_container_delete_echo():
    s = "pds"
    try:
        apc = echo_pc

        plugin.run_container(apc)

        container_name = apc["name"]

        time.sleep(CLIENT_DELAY)
        resp = requests.delete(f"http://{container_name}", headers={"Content-Type": "application/json"}, json=s)

        assert resp.status_code == 200
        assert resp.json()["data"] == json.dumps(s)
        assert resp.json()["method"] == "DELETE"

    finally:
        plugin.stop_container(apc)
        plugin.remove_container(apc)


def test_run_container_post_echo_proxy():
    s = "pds"
    try:
        apc = echo_pc

        plugin_config.add_plugin_configs([apc])
        plugin.run_container(apc)

        container_name = apc["name"]

        time.sleep(CLIENT_DELAY)
        resp = requests.post(f"{base_url}/plugin/{container_name}/index.json", headers={"Content-Type": "application/json"}, json=s)

        assert resp.status_code == 200
        assert resp.json()["data"] == json.dumps(s)
        assert resp.json()["method"] == "POST"

    finally:
        plugin.stop_container(apc)
        plugin.remove_container(apc)
        plugin_config.delete_plugin_configs({})


def test_run_container_delete_echo_proxy():
    s = "pds"
    try:
        apc = echo_pc

        plugin_config.add_plugin_configs([apc])
        plugin.run_container(apc)

        container_name = apc["name"]

        time.sleep(CLIENT_DELAY)
        resp = requests.delete(f"{base_url}/plugin/{container_name}/index.json", headers={"Content-Type": "application/json"}, json=s)

        assert resp.status_code == 200
        assert resp.json()["data"] == json.dumps(s)
        assert resp.json()["method"] == "DELETE"

    finally:
        plugin.stop_container(apc)
        plugin.remove_container(apc)
        plugin_config.delete_plugin_configs({})


def test_run_plugin_get_echo_x_forwarded_path():
    try:
        apc = echo_pc
        
        plugin_config.add_plugin_configs([apc])
        plugin.run_container(apc)
        
        container_name = apc["name"]

        time.sleep(CLIENT_DELAY)
        resp = requests.get(f"{base_url}/plugin/{container_name}/index.json")

        assert resp.status_code == 200
        assert resp.json()["method"] == "GET"
        assert "X-Forwarded-Path" in resp.json()["headers"]
        assert resp.json()["headers"]["X-Forwarded-Path"] == f"/v1/plugin/{container_name}"

    finally:
        plugin.stop_container(apc)
        plugin.remove_container(apc)
        plugin_config.delete_plugin_configs({})


def test_run_plugin_post_echo_x_forwarded_path():
    s = "pds"
    try:
        apc = echo_pc

        plugin_config.add_plugin_configs([apc])
        plugin.run_container(apc)

        container_name = apc["name"]

        time.sleep(CLIENT_DELAY)
        resp = requests.post(f"{base_url}/plugin/{container_name}/index.json", headers={"Content-Type": "application/json"}, json=s)

        assert resp.status_code == 200
        assert resp.json()["data"] == json.dumps(s)
        assert resp.json()["method"] == "POST"
        assert "X-Forwarded-Path" in resp.json()["headers"]
        assert resp.json()["headers"]["X-Forwarded-Path"] == f"/v1/plugin/{container_name}"

    finally:
        plugin.stop_container(apc)
        plugin.remove_container(apc)
        plugin_config.delete_plugin_configs({})


def test_run_plugin_get_echo_x_forwarded_path_reverse_proxy_rewrite():
    try:
        apc = echo_pc

        plugin_config.add_plugin_configs([apc])
        plugin.run_container(apc)

        container_name = apc["name"]

        time.sleep(CLIENT_DELAY)

        reverse_proxy_rewrite = "reverse_proxy_path"
        resp = requests.get(f"{base_url}/plugin/{container_name}/index.json", headers={"X-Forwarded-Path": reverse_proxy_rewrite})

        assert resp.status_code == 200
        assert resp.json()["method"] == "GET"
        assert "X-Forwarded-Path" in resp.json()["headers"]
        assert resp.json()["headers"]["X-Forwarded-Path"] == f"{reverse_proxy_rewrite}/v1/plugin/{container_name}"

    finally:
        plugin.stop_container(apc)
        plugin.remove_container(apc)
        plugin_config.delete_plugin_configs({})


def test_run_plugin_post_echo_x_forwarded_path_reverse_proxy_rewrite():
    s = "pds"
    try:
        apc = echo_pc

        plugin_config.add_plugin_configs([apc])
        plugin.run_container(apc)

        container_name = apc["name"]

        time.sleep(CLIENT_DELAY)

        reverse_proxy_rewrite = "reverse_proxy_path"
        resp = requests.post(f"{base_url}/plugin/{container_name}/index.json", headers={"Content-Type": "application/json", "X-Forwarded-Path": reverse_proxy_rewrite}, json=s)

        assert resp.status_code == 200
        assert resp.json()["data"] == json.dumps(s)
        assert resp.json()["method"] == "POST"
        assert "X-Forwarded-Path" in resp.json()["headers"]
        assert resp.json()["headers"]["X-Forwarded-Path"] == f"{reverse_proxy_rewrite}/v1/plugin/{container_name}"

    finally:
        plugin.stop_container(apc)
        plugin.remove_container(apc)
        plugin_config.delete_plugin_configs({})


def test_run_container_get_echo_404():
    try:
        apc = echo_pc

        plugin.run_container(apc)

        container_name = apc["name"]

        time.sleep(CLIENT_DELAY)
        resp = requests.get("http://{host}/?status=404".format(host=container_name))

        assert resp.status_code == 404

    finally:
        plugin.stop_container(apc)
        plugin.remove_container(apc)


def test_run_container_post_echo_404():
    s = "pds"
    try:
        apc = echo_pc

        plugin.run_container(apc)

        container_name = apc["name"]

        time.sleep(CLIENT_DELAY)
        resp = requests.post("http://{host}/?status=404".format(host=container_name), headers={"Content-Type": "application/json"}, json=s)

        assert resp.status_code == 404

    finally:
        plugin.stop_container(apc)
        plugin.remove_container(apc)


def test_run_container_environment_post_echo():
    s = "pds"
    try:
        apc = echo_pc2
        plugin.run_container(apc)

        container_name = apc["name"]

        time.sleep(CLIENT_DELAY)
        resp = requests.post("http://{host}/".format(host=container_name), headers={"Content-Type": "application/json"}, json=s)

        assert resp.status_code == 200
        assert resp.json()["data"] == json.dumps(s)
        assert resp.json()["method"] == "POST"
    finally:
        plugin.stop_container(apc)
        plugin.remove_container(apc)


def test_add_plugin_config():
    try:
        apc = pc("/tmp")
        plugin_config.add_plugin_configs([apc])
        ps = plugin_config.get_plugin_configs(fil)
        assert len(ps) == 1
    finally:
        plugin_config.delete_plugin_configs({})


def test_add_plugin_config2():
    try:
        apc = pc("/tmp")
        plugin_config.add_plugin_configs([apc])
        with pytest.raises(Exception):
            plugin_config.add_plugin_configs([apc])
    finally:
        plugin_config.delete_plugin_configs({})


def test_update_plugin_config():
    try:
        apc = pc("/tmp")
        apc2 = pc2("/tmp")
        plugin_config.add_plugin_configs([apc])
        ps = plugin_config.get_plugin_configs({})
        assert len(ps) == 1
        ps = plugin_config.get_plugin_configs(fil)
        assert len(ps) == 1
        plugin_config.replace_plugin_config(name, apc2)
        ps = plugin_config.get_plugin_configs({})
        assert len(ps) == 1
        ps = plugin_config.get_plugin_configs(fil)
        assert len(ps) == 0
        ps = plugin_config.get_plugin_configs(fil2)
        assert len(ps) == 1
    finally:
        plugin_config.delete_plugin_configs({})


def test_delete_plugin_config():
    try:
        apc = pc("/tmp")
        plugin_config.add_plugin_configs([apc])
        ps = plugin_config.get_plugin_configs({})
        assert len(ps) == 1
        ps = plugin_config.get_plugin_configs(fil)
        assert len(ps) == 1
        plugin_config.delete_plugin_config(name)
        ps = plugin_config.get_plugin_configs({})
        assert len(ps) == 0
        ps = plugin_config.get_plugin_configs(fil)
        assert len(ps) == 0
    finally:
        plugin_config.delete_plugin_configs({})


def test_delete_plugin_configs_name_regex():
    try:
        apc = pc("/tmp")
        apc2 = pc2("/tmp")
        plugin_config.add_plugin_configs([apc, apc2])
        ps = plugin_config.get_plugin_configs({})
        assert len(ps) == 2
        ps = plugin_config.get_plugin_configs(fil)
        assert len(ps) == 1
        plugin_config.delete_plugin_configs({"name": {"$regex": "nginx.*"}})
        ps = plugin_config.get_plugin_configs({})
        assert len(ps) == 0
        ps = plugin_config.get_plugin_configs(fil)
        assert len(ps) == 0
    finally:
        plugin_config.delete_plugin_configs({})


def test_add_plugin_config_api():
    try:
        apc = pc("/tmp")
        resp = requests.put(f"{base_url}/admin/plugin", headers={"Content-Type": "application/json", **headers}, json=[apc])
        assert resp.status_code == 200
        ps = plugin_config.get_plugin_configs({})
        assert len(ps) == 1
        ps = plugin_config.get_plugin_configs(fil)
        assert len(ps) == 1
    finally:
        plugin_config.delete_plugin_configs({})


def test_update_plugin_config_api():
    try:
        apc = pc("/tmp")
        apc2 = pc2("/tmp")
        resp = requests.put(f"{base_url}/admin/plugin", headers={"Content-Type": "application/json", **headers}, json=[apc])
        assert resp.status_code == 200
        ps = plugin_config.get_plugin_configs({})
        assert len(ps) == 1
        ps = plugin_config.get_plugin_configs(fil)
        assert len(ps) == 1
        resp = requests.post(f"{base_url}/admin/plugin/{name}", headers={"Content-Type": "application/json", **headers}, json=apc2)
        assert (resp.status_code == 200 or resp.status_code == 204)
        ps = plugin_config.get_plugin_configs({})
        assert len(ps) == 1
        ps = plugin_config.get_plugin_configs(fil)
        assert len(ps) == 0
        ps = plugin_config.get_plugin_configs(fil2)
        assert len(ps) == 1
    finally:
        plugin_config.delete_plugin_configs({})


def test_delete_plugin_config_api():
    try:
        apc = pc("/tmp")
        resp = requests.put(f"{base_url}/admin/plugin", headers={"Content-Type": "application/json", **headers}, json=[apc])
        assert resp.status_code == 200
        ps = plugin_config.get_plugin_configs({})
        assert len(ps) == 1
        ps = plugin_config.get_plugin_configs(fil)
        assert len(ps) == 1
        resp = requests.delete(f"{base_url}/admin/plugin/{name}", headers=headers)
        assert resp.status_code == 200
        ps = plugin_config.get_plugin_configs({})
        assert len(ps) == 0
        ps = plugin_config.get_plugin_configs(fil)
        assert len(ps) == 0
    finally:
        plugin_config.delete_plugin_configs({})


def test_delete_plugin_configs_api_name():
    try:
        apc = pc("/tmp")
        resp = requests.put(f"{base_url}/admin/plugin", headers={"Content-Type": "application/json", **headers}, json=[apc])
        assert resp.status_code == 200
        ps = plugin_config.get_plugin_configs({})
        assert len(ps) == 1
        ps = plugin_config.get_plugin_configs(fil)
        assert len(ps) == 1
        resp = requests.delete(f"{base_url}/admin/plugin?name={name}", headers=headers)
        assert resp.status_code == 200
        ps = plugin_config.get_plugin_configs({})
        assert len(ps) == 0
        ps = plugin_config.get_plugin_configs(fil)
        assert len(ps) == 0
    finally:
        plugin_config.delete_plugin_configs({})


def test_delete_plugin_configs_api_name_regex():
    try:
        apc = pc("/tmp")
        apc2 = pc2("/tmp")
        resp = requests.put(f"{base_url}/admin/plugin", headers={"Content-Type": "application/json", **headers}, json=[apc])
        assert resp.status_code == 200
        resp = requests.put(f"{base_url}/admin/plugin", headers={"Content-Type": "application/json", **headers}, json=[apc2])
        assert resp.status_code == 200
        ps = plugin_config.get_plugin_configs({})
        assert len(ps) == 2
        ps = plugin_config.get_plugin_configs(fil)
        assert len(ps) == 1
        resp = requests.delete(f"{base_url}/admin/plugin?name_regex=nginx.*", headers=headers)
        assert resp.status_code == 200
        ps = plugin_config.get_plugin_configs({})
        assert len(ps) == 0
        ps = plugin_config.get_plugin_configs(fil)
        assert len(ps) == 0
    finally:
        plugin_config.delete_plugin_configs({})


def test_run_plugin_container():
    with tempfile.TemporaryDirectory(prefix="/tmp/") as temp_dir_name:
        os.chmod(temp_dir_name, 0o755)
        s = "pds"
        with open(os.path.join(temp_dir_name, "index.json"), "w+") as f:
            f.write(json.dumps(s))

        try:
            apc = pc(temp_dir_name)
            plugin_config.add_plugin_configs([apc])
            ps = plugin_config.get_plugin_configs({"name": name})
            assert len(ps) == 1
            apc = ps[0]
            plugin.run_container(apc)
        
            resp = requests.get(f"{base_url}/plugin/{name}/index.json")
        
            assert resp.status_code == 200
            assert resp.json() == s
        finally:
            api.delete_containers()
            plugin_config.delete_plugin_configs({})


def test_run_non_existent_plugin_container_get():
    resp = requests.get(f"{base_url}/plugin/nonplugin/index.json")

    assert resp.status_code == 404


def test_run_non_existent_plugin_container_post():
    resp = requests.post(f"{base_url}/plugin/notaplugin/index.json")

    assert resp.status_code == 404


def test_run_plugin_container_get_echo_405():

    try:
        apc = echo_pc
        plugin_config.add_plugin_configs([apc])
        container_name = apc["name"]
        ps = plugin_config.get_plugin_configs({"name": container_name})
        assert len(ps) == 1
        apc = ps[0]
        plugin.run_container(apc)
        
        time.sleep(CLIENT_DELAY)
        resp = requests.get(f"{base_url}/plugin/{container_name}/index.json?status=405")
        
        assert resp.status_code == 405
    finally:
        api.delete_containers()
        plugin_config.delete_plugin_configs({})


def test_run_plugin_container_post_echo_405():
    s = "pds"
    
    try:
        apc = echo_pc
        plugin_config.add_plugin_configs([apc])
        container_name = apc["name"]
        ps = plugin_config.get_plugin_configs({"name": container_name})
        assert len(ps) == 1
        apc = ps[0]
        plugin.run_container(apc)
        
        time.sleep(CLIENT_DELAY)
        resp = requests.post(f"{base_url}/plugin/{container_name}/index.json?status=405", headers={"Content-Type": "application/json"}, json=s)

        assert resp.status_code == 405

    finally:
        api.delete_containers()
        plugin_config.delete_plugin_configs({})


def test_run_plugin_container_api():
    with tempfile.TemporaryDirectory(prefix="/tmp/") as temp_dir_name:
        os.chmod(temp_dir_name, 0o755)
        s = "pds"
        with open(os.path.join(temp_dir_name, "index.json"), "w+") as f:
            f.write(json.dumps(s))

        try:
            apc = pc(temp_dir_name)
            plugin_config.add_plugin_configs([apc])
            ps = plugin_config.get_plugin_configs({"name": name})
            assert len(ps) == 1
            apc = ps[0]

            resp = requests.put(f"{base_url}/admin/plugin/{name}/container", headers=headers)
            assert (resp.status_code == 200 or resp.status_code == 204)

            resp = requests.get(f"{base_url}/plugin/{name}/index.json")

            assert resp.status_code == 200
            assert resp.json() == s
        finally:
            api.delete_containers()
            plugin_config.delete_plugin_configs({})


def test_get_plugin_config_api():
    with tempfile.TemporaryDirectory(prefix="/tmp/") as temp_dir_name:
        os.chmod(temp_dir_name, 0o755)
        s = "pds"
        with open(os.path.join(temp_dir_name, "index.json"), "w+") as f:
            f.write(json.dumps(s))

        try:
            apc = pc(temp_dir_name)
            plugin_config.add_plugin_configs([apc])
            ps = plugin_config.get_plugin_configs({"name": name})
            assert len(ps) == 1
            apc = ps[0]
            apc["_id"] = str(apc["_id"])

            resp = requests.put(f"{base_url}/admin/plugin/{name}/container", headers=headers)
            assert (resp.status_code == 200 or resp.status_code == 204)

            resp = requests.get(f"{base_url}/admin/plugin/{name}", headers=headers)

            assert resp.status_code == 200
            assert resp.json() == apc
        finally:
            api.delete_containers()
            plugin_config.delete_plugin_configs({})


def test_get_plugin_configs_api_name():
    with tempfile.TemporaryDirectory(prefix="/tmp/") as temp_dir_name:
        os.chmod(temp_dir_name, 0o755)
        s = "pds"
        with open(os.path.join(temp_dir_name, "index.json"), "w+") as f:
            f.write(json.dumps(s))

        try:
            apc = pc(temp_dir_name)
            plugin_config.add_plugin_configs([apc])
            ps = plugin_config.get_plugin_configs({"name": name})
            assert len(ps) == 1
            apc = ps[0]
            apc["_id"] = str(apc["_id"])

            resp = requests.get(f"{base_url}/admin/plugin?name={name}", headers=headers)

            assert resp.status_code == 200
            assert resp.json() == [apc]
        finally:
            plugin_config.delete_plugin_configs({})



def test_get_plugin_configs_name_regex():
    with tempfile.TemporaryDirectory(prefix="/tmp/") as temp_dir_name:
        os.chmod(temp_dir_name, 0o755)
        s = "pds"
        with open(os.path.join(temp_dir_name, "index.json"), "w+") as f:
            f.write(json.dumps(s))

        try:
            apc = pc(temp_dir_name)
            apc2 = pc2(temp_dir_name)
            plugin_config.add_plugin_configs([apc, apc2])
            ps = plugin_config.get_plugin_configs({})
            assert len(ps) == 2
            for apc0 in ps:
                apc0["_id"] = str(apc0["_id"])

            ps2 = plugin_config.get_plugin_configs({"name": {"$regex": "nginx.*"}})
            for a in ps2:
                a["_id"] = str(a["_id"])

            assert bag_equal(ps2, ps)
        finally:
            plugin_config.delete_plugin_configs({})


def test_get_plugin_configs_api_name_regex():
    with tempfile.TemporaryDirectory(prefix="/tmp/") as temp_dir_name:
        os.chmod(temp_dir_name, 0o755)
        s = "pds"
        with open(os.path.join(temp_dir_name, "index.json"), "w+") as f:
            f.write(json.dumps(s))

        try:
            apc = pc(temp_dir_name)
            apc2 = pc2(temp_dir_name)
            plugin_config.add_plugin_configs([apc, apc2])
            ps = plugin_config.get_plugin_configs({})
            assert len(ps) == 2
            for apc0 in ps:
                apc0["_id"] = str(apc0["_id"])

            resp = requests.get(f"{base_url}/admin/plugin?name_regex=nginx.*", headers=headers)

            assert resp.status_code == 200
            assert bag_equal(resp.json(), ps)
        finally:
            plugin_config.delete_plugin_configs({})


def test_get_plugin_container_api():
    with tempfile.TemporaryDirectory(prefix="/tmp/") as temp_dir_name:
        os.chmod(temp_dir_name, 0o755)
        s = "pds"
        with open(os.path.join(temp_dir_name, "index.json"), "w+") as f:
            f.write(json.dumps(s))

        try:
            apc = pc(temp_dir_name)
            plugin_config.add_plugin_configs([apc])
            ps = plugin_config.get_plugin_configs({"name": name})
            assert len(ps) == 1
            apc = ps[0]

            resp = requests.put(f"{base_url}/admin/plugin/{name}/container", headers=headers)
            assert (resp.status_code == 200 or resp.status_code == 204)

            resp = requests.get(f"{base_url}/admin/plugin/{name}/container", headers=headers)

            assert resp.status_code == 200
            assert resp.json() == {"status": "running"}
        finally:
            api.delete_containers()
            plugin_config.delete_plugin_configs({})


def test_run_plugin_containers_api():
    with tempfile.TemporaryDirectory(prefix="/tmp/") as temp_dir_name:
        os.chmod(temp_dir_name, 0o755)
        s = "pds"
        with open(os.path.join(temp_dir_name, "index.json"), "w+") as f:
            f.write(json.dumps(s))

        try:
            apc = pc(temp_dir_name)
            apc2 = pc2(temp_dir_name)
            plugin_config.add_plugin_configs([apc, apc2])
            ps = plugin_config.get_plugin_configs({})
            assert len(ps) == 2
            apc = ps[0]

            resp = requests.put(f"{base_url}/admin/container", headers=headers)
            assert (resp.status_code == 200 or resp.status_code == 204)

            resp = requests.get(f"{base_url}/plugin/{name}/index.json")

            assert resp.status_code == 200
            assert resp.json() == s
            resp2 = requests.get(f"{base_url}/plugin/{name2}/index.json")

            assert resp2.status_code == 200
            assert resp2.json() == s
        finally:
            api.delete_containers()
            plugin_config.delete_plugin_configs({})


def test_get_plugin_containers_api():
    with tempfile.TemporaryDirectory(prefix="/tmp/") as temp_dir_name:
        os.chmod(temp_dir_name, 0o755)
        s = "pds"
        with open(os.path.join(temp_dir_name, "index.json"), "w+") as f:
            f.write(json.dumps(s))

        try:
            apc = pc(temp_dir_name)
            apc2 = pc2(temp_dir_name)
            plugin_config.add_plugin_configs([apc, apc2])
            ps = plugin_config.get_plugin_configs({})
            assert len(ps) == 2
            apc = ps[0]

            resp = requests.put(f"{base_url}/admin/container", headers=headers)
            assert (resp.status_code == 200 or resp.status_code == 204)

            resp = requests.get(f"{base_url}/admin/container", headers=headers)

            assert resp.status_code == 200
            assert bag_equal(resp.json(), [{"name": name, "container": {"status": "running"}}, {"name": name2, "container": {"status": "running"}}])
        finally:
            api.delete_containers()
            plugin_config.delete_plugin_configs({})


def test_auth():
    resp = requests.get(f"{base_url}/admin/plugin", headers=headers)
    print(resp.text)
    assert resp.status_code == 200
    
    
def test_auth_401():
    resp = requests.get(f"{base_url}/admin/plugin")
    print(resp.text)
    assert resp.status_code == 401

    
def test_auth_403():
    resp = requests.get(f"{base_url}/admin/plugin", headers=headers2)
    print(resp.text)
    assert resp.status_code == 403


v0 = {
    "name": "volume0"
}

v1 = {
    "name": "volume0",
    "persistent": True
}


client = docker.from_env()

def test_create_volume():
    vols = client.volumes.list()
    nvols = len(vols)
    
    plugin.create_volume(v0)
    vols = client.volumes.list()
    assert len(vols) == nvols + 1

    plugin.delete_volume(v0)
    

def test_create_volume2():
    vols = client.volumes.list()
    nvols = len(vols)
    
    plugin.create_volume(v0)
    vols = client.volumes.list()
    assert len(vols) == nvols + 1

    with pytest.raises(Exception):
        plugin.create_volume(v0)

    plugin.delete_volume(v0)
    

def test_create_persistent_volume():
    vols = client.volumes.list()
    nvols = len(vols)
    
    plugin.create_volume(v0)
    vols = client.volumes.list()
    assert len(vols) == nvols + 1

    plugin.create_volume(v1)
    vols = client.volumes.list()
    assert len(vols) == nvols + 1

    plugin.delete_volume(v0)
    

def test_delete_volume():
    vols = client.volumes.list()
    nvols = len(vols)
    
    plugin.create_volume(v0)
    vols = client.volumes.list()
    assert len(vols) == nvols + 1

    plugin.delete_volume(v0)
    vols = client.volumes.list()
    assert len(vols) == nvols
    
    
def test_delete_persistent_volume():
    vols = client.volumes.list()
    nvols = len(vols)
    
    plugin.create_volume(v0)
    vols = client.volumes.list()
    assert len(vols) == nvols + 1

    plugin.delete_volume(v1)
    vols = client.volumes.list()
    assert len(vols) == nvols + 1
    
    plugin.delete_volume(v0)

    
def test_delete_volume2():
    with pytest.raises(Exception):
        plugin.delete_volume(v0)
    

def test_run_command():
    try:
        msg = "hello, world!"
        pc = {
            "image": "nginx:1.19.2",
            "environment": {},
            "name": "name",
            "entrypoint": ["echo", msg]
        }
        
        c = plugin.run_container(pc)
        assert c.logs() == (msg + "\n").encode()
        
    finally:
        plugin.stop_container(pc)
        plugin.remove_container(pc)
