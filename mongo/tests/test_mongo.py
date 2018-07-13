import pymongo
import common

from types import ListType

def test_mongo(spin_up_mongo, set_up_mongo, check):

    instance_one = {
        'server': "mongodb://testUser:testPass@localhost:%s/test?authSource=authDB" % common.PORT1
    }
    instance_two = {
        'server': "mongodb://testUser2:testPass2@localhost:%s/test" % common.PORT2
    }

    # Run the check against our running server
    check.check(instance_one)

    # Sleep for 1 second so the rate interval >=1
    time.sleep(1)

    # Run the check again so we get the rates
    check.check(instance_one)

    # Metric assertions
    metrics = check.get_metrics()
    assert metrics

    assert isinstance(metrics, ListType)
    assert len(metrics) > 0

    metric_val_checks = {
        'mongodb.asserts.msgps': lambda x: x >= 0,
        'mongodb.fsynclocked': lambda x: x >= 0,
        'mongodb.globallock.activeclients.readers': lambda x: x >= 0,
        'mongodb.metrics.cursor.open.notimeout': lambda x: x >= 0,
        'mongodb.metrics.document.deletedps': lambda x: x >= 0,
        'mongodb.metrics.getlasterror.wtime.numps': lambda x: x >= 0,
        'mongodb.metrics.repl.apply.batches.numps': lambda x: x >= 0,
        'mongodb.metrics.ttl.deleteddocumentsps': lambda x: x >= 0,
        'mongodb.network.bytesinps': lambda x: x >= 1,
        'mongodb.network.numrequestsps': lambda x: x >= 1,
        'mongodb.opcounters.commandps': lambda x: x >= 1,
        'mongodb.opcountersrepl.commandps': lambda x: x >= 0,
        'mongodb.oplog.logsizemb': lambda x: x >= 1,
        'mongodb.oplog.timediff': lambda x: x >= 1,
        'mongodb.oplog.usedsizemb': lambda x: x >= 0,
        'mongodb.replset.health': lambda x: x >= 1,
        'mongodb.replset.state': lambda x: x >= 1,
        'mongodb.stats.avgobjsize': lambda x: x >= 0,
        'mongodb.stats.storagesize': lambda x: x >= 0,
        'mongodb.connections.current': lambda x: x >= 1,
        'mongodb.connections.available': lambda x: x >= 1,
        'mongodb.uptime': lambda x: x >= 0,
        'mongodb.mem.resident': lambda x: x > 0,
        'mongodb.mem.virtual': lambda x: x > 0,
    }

    tested_metrics = set()
    for m in metrics:
        metric_name = m[0]
        if metric_name in metric_val_checks:
            assert metric_val_checks[metric_name](m[2])
            tested_metrics.add(metric_name)

    if len(metric_val_checks) - len(tested_metrics) != 0:
        print "missing metrics: %s" % (set(metric_val_checks.keys()) - tested_metrics)
    assert len(metric_val_checks) - len(tested_metrics) == 0

    # Run the check against our running server
    check.check(instance_two)
    # Sleep for 1 second so the rate interval >=1
    time.sleep(1)
    # Run the check again so we get the rates
    check.check(instance_two)

    # Service checks
    service_checks = check.get_service_checks()
    print service_checks
    service_checks_count = len(service_checks)
    assert isinstance(service_checks, ListType)
    assert service_checks_count > 0
    assert len([sc for sc in service_checks if sc['check'] == self.check.SERVICE_CHECK_NAME]) == 4
    # Assert that all service checks have the proper tags: host and port
    assert len([sc for sc in service_checks if "host:localhost" in sc['tags']]) == service_checks_count
    assert len([sc for sc in service_checks if "port:%s" % common.PORT1 in sc['tags'] or "port:%s" % common.PORT2 in sc['tags']]) == service_checks_count
    assert len([sc for sc in service_checks if "db:test" in sc['tags']]) == service_checks_count

    # Metric assertions
    metrics = check.get_metrics()
    assert metrics
    assert isinstance(metrics, ListType)
    assert len(metrics) > 0

    for m in metrics:
        metric_name = m[0]
        if metric_name in metric_val_checks:
            assert metric_val_checks[metric_name](m[2])
