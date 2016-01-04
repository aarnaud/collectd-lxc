#!/usr/bin/env python2.7

import glob
import os
import re
import subprocess
from nsenter import Namespace

def configer(ObjConfiguration):
    collectd.info('Configuring lxc collectd')

def initer():
    collectd.info('initing lxc collectd')

def reader(input_data=None):
    root_lxc_cgroup = glob.glob("/sys/fs/cgroup/*/lxc/*/")
    unprivilege_lxc_cgroup = glob.glob("/sys/fs/cgroup/*/*/*/*/lxc/*/")

    cgroup_lxc = root_lxc_cgroup + unprivilege_lxc_cgroup

    metrics = dict()

    #Get all stats by container group by user
    for cgroup_lxc_metrics in cgroup_lxc:
        m = re.search("/sys/fs/cgroup/(?P<type>[a-zA-Z_,]+)/(?:user/(?P<user_id>[0-9]+)\.user/[a-zA-Z0-9]+\.session/)?lxc/(?P<container_name>.*)/", cgroup_lxc_metrics)
        user_id = int(m.group("user_id") or 0)
        stat_type = m.group("type")
        container_name = m.group("container_name")
        if user_id not in metrics:
            metrics[user_id] = dict()
        if container_name not in metrics[user_id]:
            metrics[user_id][container_name] = dict()
        metrics[user_id][container_name][stat_type] = cgroup_lxc_metrics

    # foreach user
    for user_id in metrics:
        # foreach container
        for container_name in metrics[user_id]:
            lxc_fullname = "{0}__{1}".format(user_id, container_name)
            for metric in metrics[user_id][container_name]:
                ### Memory
                if metric == "memory":
                    with open(os.path.join(metrics[user_id][container_name][metric], 'memory.stat'), 'r') as f:
                        lines = f.read().splitlines()

                    mem_rss = 0
                    mem_cache = 0
                    mem_swap = 0

                    for line in lines:
                        data = line.split()
                        if data[0] == "total_rss":
                            mem_rss = int(data[1])
                        elif data[0] == "total_cache":
                            mem_cache = int(data[1])
                        elif data[0] == "total_swap":
                            mem_swap = int(data[1])

                    values = collectd.Values(plugin_instance=lxc_fullname,
                                             type="gauge", plugin="lxc_memory")
                    values.dispatch(type_instance="rss", values=[mem_rss])
                    values.dispatch(type_instance="cache", values=[mem_cache])
                    values.dispatch(type_instance="swap", values=[mem_swap])

                ### End Memory

                ### CPU
                if metric == "cpuacct":
                    with open(os.path.join(metrics[user_id][container_name][metric], 'cpuacct.stat'), 'r') as f:
                        lines = f.read().splitlines()

                    cpu_user = 0
                    cpu_system = 0

                    for line in lines:
                        data = line.split()
                        if data[0] == "user":
                            cpu_user = int(data[1])
                        elif data[0] == "system":
                            cpu_system = int(data[1])

                    values = collectd.Values(plugin_instance=lxc_fullname,
                                             type="gauge", plugin="lxc_cpu")
                    values.dispatch(type_instance="user", values=[cpu_user])
                    values.dispatch(type_instance="system", values=[cpu_system])

                ### End CPU

                ### DISK
                if metric == "blkio":

                    with open(os.path.join(metrics[user_id][container_name][metric], 'blkio.throttle.io_service_bytes'), 'r') as f:
                        lines = f.read()

                    bytes_read = int(re.search("Read\s+(?P<read>[0-9]+)", lines).group("read"))
                    bytes_write = int(re.search("Write\s+(?P<write>[0-9]+)", lines).group("write"))

                    with open(os.path.join(metrics[user_id][container_name][metric], 'blkio.throttle.io_serviced'), 'r') as f:
                        lines = f.read()

                    ops_read = int(re.search("Read\s+(?P<read>[0-9]+)", lines).group("read"))
                    ops_write = int(re.search("Write\s+(?P<write>[0-9]+)", lines).group("write"))

                    values = collectd.Values(plugin_instance=lxc_fullname,
                                             type="gauge", plugin="lxc_blkio")
                    values.dispatch(type_instance="bytes_read", values=[bytes_read])
                    values.dispatch(type_instance="bytes_write", values=[bytes_write])
                    values.dispatch(type_instance="ops_read", values=[ops_read])
                    values.dispatch(type_instance="ops_write", values=[ops_write])

                ### End DISK

                ### Network
                    #PID lxc: cat /sys/fs/cgroup/devices/lxc/CONTAINER-NAME/tasks | head -n 1
                    with open(os.path.join(metrics[user_id][container_name][metric], 'tasks'), 'r') as f:
                        # The first line is PID of container
                        container_PID = f.readline().rstrip()
                        with Namespace(container_PID, 'net'):
                            # To read network metric in namespace, "open" method don't work with namespace
                            network_data = subprocess.check_output(['cat', '/proc/net/dev']).split("\n")
                            # HEAD OF /proc/net/dev :
                            # Inter-|Receive                                                |Transmit
                            # face  |bytes packets errs drop fifo frame compressed multicast|bytes packets errs drop fifo colls carrier compressed
                            for line in network_data[2:]:
                                if line.strip() == "":
                                    continue
                                interface = line.strip().split(':')[0]
                                rx_data = line.strip().split(':')[1].split()[0:7]
                                tx_data = line.strip().split(':')[1].split()[8:15]

                                rx_bytes = int(rx_data[0])
                                tx_bytes = int(tx_data[0])

                                rx_packets = int(rx_data[1])
                                tx_packets = int(tx_data[1])

                                rx_errors = int(rx_data[2])
                                tx_errors = int(tx_data[2])

                                values = collectd.Values(plugin_instance=lxc_fullname,
                                                         type="gauge", plugin="lxc_net")
                                values.dispatch(type_instance="tx_bytes_{0}".format(interface), values=[tx_bytes])
                                values.dispatch(type_instance="rx_bytes_{0}".format(interface), values=[rx_bytes])
                                values.dispatch(type_instance="tx_packets_{0}".format(interface), values=[tx_packets])
                                values.dispatch(type_instance="rx_packets_{0}".format(interface), values=[rx_packets])
                                values.dispatch(type_instance="tx_errors_{0}".format(interface), values=[tx_errors])
                                values.dispatch(type_instance="rx_errors_{0}".format(interface), values=[rx_errors])
                ### End Network


if __name__ == '__main__':
    # Mimic Collectd Values object
    class Values(object):
        def __init__(self, **kwargs):
            self.__dict__["_values"] = kwargs
        def __setattr__(self, key, value):
            self.__dict__["_values"][key] = value
        def dispatch(self, **kwargs):
            values = self._values.copy()
            values.update(kwargs)
            print(values)

    import types
    collectd = types.ModuleType("collectd")
    collectd.Values = Values

    reader()
else:
    import collectd
    collectd.register_config(configer)
    collectd.register_init(initer)
    collectd.register_read(reader)
