#!/usr/bin/env python2.7

import glob
import os
import re
from nsenter import Namespace

def configer(ObjConfiguration):
   collectd.debug('Configuring lxc collectd')

def initer():
    collectd.debug('initing lxc collectd')

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
                        with Namespace(container_PID, 'mnt'):
                            sys_class_net='/sys/class/net/'
                            for interface in os.listdir(sys_class_net):
                                net_statistics_dir=os.path.join(sys_class_net,interface,'statistics')
                                with open(os.path.join(net_statistics_dir, 'tx_bytes')) as f:
                                    print(f.readline().rstrip())
                                with open(os.path.join(net_statistics_dir, 'rx_bytes')) as f:
                                    print(f.readline().rstrip())
                                with open(os.path.join(net_statistics_dir, 'tx_packets')) as f:
                                    print(f.readline().rstrip())
                                with open(os.path.join(net_statistics_dir, 'rx_packets')) as f:
                                    print(f.readline().rstrip())
                                with open(os.path.join(net_statistics_dir, 'tx_errors')) as f:
                                    print(f.readline().rstrip())
                                with open(os.path.join(net_statistics_dir, 'rx_errors')) as f:
                                    print(f.readline().rstrip())
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
