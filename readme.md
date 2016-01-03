# lxc collectd plugin

## features

* privileged and unprivileged container
* cpu metric
* memory metric

## Installation

* sudo pip install nsenter
* copy "collectd_lxc.py" in a directory (exemple: `/etc/collectd/plugins/`)
* Configure collectd, create file `/etc/collectd/collectd.conf.d/lxc.conf` with content

````xml
LoadPlugin python
<Plugin python>
    ModulePath "/etc/collectd/plugins/"
    LogTraces true
    Interactive false
    Import "collectd_lxc"
    <Module collectd_lxc>
    </Module>
</Plugin>
````