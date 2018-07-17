# (C) Datadog, Inc. 2010-2017
# All rights reserved
# Licensed under Simplified BSD License (see LICENSE)
import subprocess
import time
import os
import sys
import logging

import pymongo
import pytest

from datadog_checks.mongo import MongoDb

from . import common

log = logging.getLogger('conftest')


@pytest.fixture
def aggregator():
    from datadog_checks.stubs import aggregator
    aggregator.reset()
    return aggregator


@pytest.fixture
def check():
    check = MongoDb('mongo', {}, {})
    return check


@pytest.fixture(scope="session")
def set_up_mongo():
    cli = pymongo.mongo_client.MongoClient(
        common.MONGODB_SERVER,
        socketTimeoutMS=30000,
        read_preference=pymongo.ReadPreference.PRIMARY_PREFERRED,)

    cli2 = pymongo.mongo_client.MongoClient(
        common.MONGODB_SERVER2,
        socketTimeoutMS=30000,
        read_preference=pymongo.ReadPreference.PRIMARY_PREFERRED,)

    foos = []
    for _ in range(70):
        foos.append({'1': []})
        foos.append({'1': []})
        foos.append({})

    bars = []
    for _ in range(50):
        bars.append({'1': []})
        bars.append({})

    db = cli['test']
    db.foo.insert_many(foos)
    db.bar.insert_many(bars)


    authDB = cli['authDB']
    authDB.command("createUser", 'testUser', pwd='testPass', roles=[ { 'role': 'read', 'db': 'test' } ])

    db.command("createUser", 'testUser2', pwd='testPass2', roles=[ { 'role': 'read', 'db': 'test' } ])

    yield
    tear_down_mongo()


def tear_down_mongo():
    cli = pymongo.mongo_client.MongoClient(
        common.MONGODB_SERVER,
        socketTimeoutMS=30000,
        read_preference=pymongo.ReadPreference.PRIMARY_PREFERRED,)

    db = cli['test']
    db.drop_collection("foo")
    db.drop_collection("bar")



@pytest.fixture(scope="session")
def spin_up_mongo():
    """
    Start a cluster with one master, one replica and one unhealthy replica and
    stop it after the tests are done.
    If there's any problem executing docker-compose, let the exception bubble
    up.
    """

    env = os.environ

    compose_file = os.path.join(common.HERE, 'compose', 'docker-compose.yml')

    env['DOCKER_COMPOSE_FILE'] = compose_file

    args = [
        "docker-compose",
        "-f", compose_file
    ]

    try:
        cleanup_mongo(args, env)
    except Exception:
        pass

    try:
        subprocess.check_call(args + ["up", "-d"], env=env)
        compose_dir = os.path.join(common.HERE, 'compose')
        script_path = os.path.join(common.HERE, 'compose', 'init.sh')
        setup_sharding(env=env)
    except Exception:
        # cleanup_mongo(args, env)
        raise

    yield
    # cleanup_mongo(args, env)


def setup_sharding(env=None):
    curdir = os.getcwd()
    compose_dir = os.path.join(common.HERE, 'compose')
    os.chdir(compose_dir)
    subprocess.check_call(['bash', 'init.sh'], env=env)
    os.chdir(curdir)
    return


def cleanup_mongo(args, env):
    subprocess.check_call(args + ["down"], env=env)
    try:
        subprocess.check_call(['docker', 'system', 'prune', '-af'])
    except:
        pass
    try:
        subprocess.check_call(['docker', 'volume', 'prune', '-f'])
    except:
        pass
