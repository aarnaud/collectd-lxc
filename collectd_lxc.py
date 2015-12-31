#!/usr/bin/env python2.7

import glob
import os
import re


def reader(input_data=None):
    root_lxc_cgroup = glob.glob("/sys/fs/cgroup/*/lxc/*/")
    unprivilege_lxc_cgroup = glob.glob("/sys/fs/cgroup/*/*/*/*/lxc/*/")

    cgroup_lxc = root_lxc_cgroup + unprivilege_lxc_cgroup

    metrics = dict()

    #Get all stats by container group by user
    for cgroup_lxc_metrics in cgroup_lxc:
        m = re.search("/sys/fs/cgroup/(?P<type>[a-zA-Z_]+)/(?:user/(?P<user_id>[0-9]+)\.user/[a-zA-Z0-9]+\.session/)?lxc/(?P<container_name>.*)/", cgroup_lxc_metrics)
        user_id = int(m.group("user_id") or 0)
        stat_type = m.group("type")
        container_name = m.group("container_name")
        if not metrics.has_key(user_id):
            metrics[user_id] = dict()
        if not metrics[user_id].has_key(container_name):
            metrics[user_id][container_name] = dict()
        metrics[user_id][container_name][stat_type] = cgroup_lxc_metrics
        #PID lxc: cat /sys/fs/cgroup/cpuacct/lxc/eni-server-ad/cgroup.procs | head -n 1

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

                    memory_rss = collectd.Values()
                    memory_rss.plugin = "lxc_memory"
                    memory_rss.plugin_instance = lxc_fullname
                    memory_rss.type_instance = "rss"
                    memory_rss.type = 'gauge'
                    memory_rss.values = [mem_rss]
                    memory_rss.dispatch()

                    memory_cache = collectd.Values()
                    memory_cache.plugin = "lxc_memory"
                    memory_cache.plugin_instance = lxc_fullname
                    memory_cache.type_instance = "cache"
                    memory_cache.type = 'gauge'
                    memory_cache.values = [mem_cache]
                    memory_cache.dispatch()

                    memory_swap = collectd.Values()
                    memory_swap.plugin = "lxc_memory"
                    memory_swap.plugin_instance = lxc_fullname
                    memory_swap.type_instance = "swap"
                    memory_swap.type = 'gauge'
                    memory_swap.values = [mem_swap]
                    memory_swap.dispatch()
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

                    CPU_user = collectd.Values()
                    CPU_user.plugin = "lxc_cpu"
                    CPU_user.plugin_instance = lxc_fullname
                    CPU_user.type_instance = "user"
                    CPU_user.type = 'gauge'
                    CPU_user.values = [cpu_user]
                    CPU_user.dispatch()

                    CPU_system = collectd.Values()
                    CPU_system.plugin = "lxc_cpu"
                    CPU_system.plugin_instance = lxc_fullname
                    CPU_system.type_instance = "system"
                    CPU_system.type = 'gauge'
                    CPU_system.values = [cpu_system]
                    CPU_system.dispatch()

                ### End CPU

                ### DISK
                if metric == "blkio":
                    with open(os.path.join(metrics[user_id][container_name][metric], 'blkio.throttle.io_service_bytes'), 'r') as f:
                        lines = f.read()

                    bytes_read = int(re.search("Read\s+(?P<read>[0-9]+)", lines).group("read"))
                    bytes_write = int(re.search("Write\s+(?P<write>[0-9]+)", lines).group("write"))

                    blkio_bytes_read = collectd.Values()
                    blkio_bytes_read.plugin = "lxc_blkio"
                    blkio_bytes_read.plugin_instance = lxc_fullname
                    blkio_bytes_read.type_instance = "bytes_read"
                    blkio_bytes_read.type = 'gauge'
                    blkio_bytes_read.values = [bytes_read]
                    blkio_bytes_read.dispatch()

                    blkio_bytes_write = collectd.Values()
                    blkio_bytes_write.plugin = "lxc_blkio"
                    blkio_bytes_write.plugin_instance = lxc_fullname
                    blkio_bytes_write.type_instance = "bytes_write"
                    blkio_bytes_write.type = 'gauge'
                    blkio_bytes_write.values = [bytes_write]
                    blkio_bytes_write.dispatch()

                    with open(os.path.join(metrics[user_id][container_name][metric], 'blkio.throttle.io_serviced'), 'r') as f:
                        lines = f.read()

                    ops_read = int(re.search("Read\s+(?P<read>[0-9]+)", lines).group("read"))
                    ops_write = int(re.search("Write\s+(?P<write>[0-9]+)", lines).group("write"))

                    blkio_io_read = collectd.Values()
                    blkio_io_read.plugin = "lxc_blkio"
                    blkio_io_read.plugin_instance = lxc_fullname
                    blkio_io_read.type_instance = "ops_read"
                    blkio_io_read.type = 'gauge'
                    blkio_io_read.values = [ops_read]
                    blkio_io_read.dispatch()

                    blkio_io_write = collectd.Values()
                    blkio_io_write.plugin = "lxc_blkio"
                    blkio_io_write.plugin_instance = lxc_fullname
                    blkio_io_write.type_instance = "ops_write"
                    blkio_io_write.type = 'gauge'
                    blkio_io_write.values = [ops_write]
                    blkio_io_write.dispatch()

                ### End DISK


if __name__ == '__main__':
    # Mimic Collectd Values object
    class Values(object):
        def __init__(self):
            self.__dict__["_values"] = {}
        def __setattr__(self, key, value):
            self.__dict__["_values"][key] = value
        def dispatch(self):
            print(self._values)

    import types
    collectd = types.ModuleType("collectd")
    collectd.Values = Values

    reader()
else:
    import collectd
    collectd.register_read(reader)
