import os
import logging
from pymongo import MongoClient
from contextlib import contextmanager
from bson.objectid import ObjectId
from get_docker_secret import get_docker_secret

logger = logging.getLogger()
logger.setLevel(logging.INFO)

@contextmanager
def plugin_db():
    mongo_database = os.environ["MONGO_DATABASE"]
    c = MongoClient(os.environ["MONGO_HOST"], int(os.environ["MONGO_PORT"]), username=os.environ["MONGO_NON_ROOT_USERNAME"], password=get_docker_secret("MONGO_NON_ROOT_PASSWORD"), authSource=mongo_database)
    try:
        db = c[mongo_database]
        collection = db[os.environ["MONGO_COLLECTION"]]
        yield collection
    finally:
        c.close()
    

def get_plugin_configs(fil):
    with plugin_db() as collection:
        return list(collection.find(fil))


def get_plugin_config(name):
    with plugin_db() as collection:
        return collection.find_one({"name": name})


def get_plugin_ids(fil):
    with plugin_db() as collection:
        return list(collection.find(fil, []))


def add_plugin_configs(ps):
    if len(ps) > 0:
        with plugin_db() as collection:
            for pc in ps:
                name = pc["name"]
                if len(get_plugin_configs({"name": name})) > 0:
                    raise RuntimeError("plugin name \"{name}\" already exists in database".format(name=name))
            return collection.insert_many(ps).inserted_ids
    
    
def update_plugin_configs(fil, update):
    with plugin_db() as collection:
        return collection.update_many(fil, update).modified_count


def replace_plugin_config(name, update):
    with plugin_db() as collection:
        if name != update["name"] and len(get_plugin_configs({"name": update["name"]})) > 0:
            raise RuntimeError("plugin name \"{name}\" already exists in database".format(name=update["name"]))
        return collection.replace_one({"name": name}, update).modified_count


def delete_plugin_configs(fil):
    with plugin_db() as collection:
        return collection.delete_many(fil).deleted_count


def delete_plugin_config(name):
    with plugin_db() as collection:
        return collection.delete_one({"name": name}).deleted_count

    
def from_docker_compose(a):
    return list(map(lambda x: {"name": x[0], **x[1]}, a.get("services", {}).items())), list(map(lambda x: {"name": x[0], **x[1]}, a.get("volumes", {}).items()))


def delete_from_dict(d, k):
    d2 = d.copy()
    del d2[k]
    return d2


def to_docker_compose(apcs):
    return {
        "version": "3",
        "services": {
            apc["name"] : delete_from_dict(apc, "name") for apc in apcs
        }
    }


def sort_plugin_configs(pcs):
    started = set()
    pcs2 = pcs
    pcs3 = []
    pcs4 = []
    while len(pcs2) > 0:
        for pc in pcs2:
            dep = set(pc.get("depends_on", []))
            if dep.issubset(started):
                pcs4.append(pc)
                started.add(pc["name"])
            else:
                pcs3.append(pc)
        if len(pcs3) == len(pcs2):
            raise RuntimeError("unsatisfied dependencies")
        else:
            pcs2 = pcs3
            pcs3 = []
    return pcs4

