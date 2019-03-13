#!/usr/bin/python3
import os
#import csv
import time
from pprint import pprint
from influxdb import InfluxDBClient
import psutil

host = '127.0.0.1'
username = 'admin'
password = 'yourpassword'

client = InfluxDBClient(host=host, port=8086, username=username, password=password)
client.switch_database('stats')

date = os.popen("date +%s").read().split('\n')
time = ((int(date[0])) * 1000000000 - 10000000000)
hn = os.popen("hostname").read().split('\n')


total_pids = len(psutil.pids())
pcore_count = psutil.cpu_count(logical=False)
lcore_count = psutil.cpu_count(logical=True)
cpu_load = psutil.cpu_percent(interval=1)
cpu_load_core = psutil.cpu_percent(interval=1, percpu=True)

counters = { 
            'total_pids': total_pids,
            'pcore_count': pcore_count,
            'lcore_count': lcore_count,
            'cpu_load': cpu_load
           }
b = 0
for i in cpu_load_core:
    core = 'core_usage'
    counters.update({("core"+str(b)+"_usage"): i})   
    b += 1
del (b)
a = ['udp4', 'tcp', 'tcp4', 'all', 'inet', 'unix', 'tcp6', 'udp6', 'inet6', 'udp', 'inet4']
for i in a:
    counters.update({"count_net_"+str(i): len(psutil.net_connections(i))}) 
del(a)

### RAM ####
mem = psutil.virtual_memory()
memory = { 
	  'total': mem.total,
          'available': mem.available,
          'percent': mem.percent,
          'used': mem.used,
          'free': mem.free, 
          'active': mem.active, 
          'inactive': mem.inactive,
          'buffers': mem.buffers,
          'cached': mem.cached,
          'shared': mem.shared,
          'slab': mem.slab
	 }
### SWAP ###
swap_mem = psutil.swap_memory()
swap = {
        'total': swap_mem.total,
        'used': swap_mem.used,
        'free': swap_mem.free,
        'percent_used': swap_mem.percent,
        'swap_in': swap_mem.sin,
        'swap_out': swap_mem.sout
       }

#### NETWORK #####
net_tcp_count = {}
def net_tcp(type):
    count = 0
    for i in psutil.net_connections('tcp'):
        if i.status == type:
            count += 1
    return count
tcp_operations = ['LISTEN','SYN_SENT','SYN_RECEIVED','ESTABLISHED','FIN_WAIT_1','FIN_WAIT_2','CLOSE_WAIT','CLOSING','LAST_ACK','TIME_WAIT','CLOSED','SYN','SYN-ACK','ACK']
for i in tcp_operations:
    net_tcp_count.update ({i: net_tcp(i)})

udp_listen_count = 0
udp_established = 0
for i in psutil.net_connections('udp'):
    if len(i.raddr) == 0:
        udp_listen_count += 1
    else:
        udp_established += 1
udp_count = {'LSTEN' : udp_listen_count , 'ESTABLISHED': udp_established }



### DISKS ###
total_disk_io = psutil.disk_io_counters(perdisk=False, nowrap=True)
per_disk_io = psutil.disk_io_counters(perdisk=True, nowrap=True)
disk_io = {'all_disk': {
                      'read_count': total_disk_io.read_count,
                      'write_count': total_disk_io.write_count,
                      'read_bytes': total_disk_io.read_bytes,
                      'write_bytes': total_disk_io.write_bytes,
                      'read_time':  total_disk_io.read_time,
                      'write_time':  total_disk_io.write_time,
                      'read_merged_count':  total_disk_io.read_merged_count,
                      'write_merged_count':  total_disk_io.write_merged_count,
                      'busy_time':  total_disk_io.busy_time
                     }}
for i in per_disk_io.keys():
    disk_io.update ({i: {
                      'read_count': per_disk_io[i].read_count,
                      'write_count': per_disk_io[i].write_count,
                      'read_bytes': per_disk_io[i].read_bytes,
                      'write_bytes': per_disk_io[i].write_bytes,
                      'read_time':  per_disk_io[i].read_time,
                      'write_time':  per_disk_io[i].write_time,
                      'read_merged_count':  per_disk_io[i].read_merged_count,
                      'write_merged_count':  per_disk_io[i].write_merged_count,
                      'busy_time':  per_disk_io[i].busy_time
                     }})

### pids infos###           
pids = {}
for proc in psutil.process_iter():
    try:
        pinfo = proc.as_dict()
    except psutil.NoSuchProcess:
        pass
    else:
        pids.update ({pinfo['pid'] : {
                                     'name': pinfo['name'],
                                     'memory_percent': pinfo['memory_percent'],
                                     'username': pinfo['username'],
                                     'status': pinfo['status'],
                                     'cpu_affinity': pinfo['cpu_affinity'],
                                     'create_time': pinfo['create_time'],
                                     'num_fds': pinfo['num_fds']
                                    }})

app_users = []
for i in pids.keys():
    app_users.append(pids[i]['username'])
app_users = list(set(app_users))
user_app = {}
for i in app_users:
    user_app.update({i: 0})
for i in pids.keys():
     b = (pids[i]['username'])
     user_app[b] += 1

p_status = []
for i in pids.keys():
    p_status.append(pids[i]['status'])
p_status = list(set(p_status))
s_pids = {}
for i in p_status:
    s_pids.update({i: 0})
for i in pids.keys():
    b = (pids[i]['status'])
    s_pids[b] += 1




##pprint (counters)
##pprint (memory)
##pprint (swap)
##pprint (net_tcp_count)
##pprint (udp_count)
##pprint (disk_io)
##pprint (user_app)
##pprint (s_pids)

##Counters
influx_counters = []
influx_counters.append({
			"measurement": "psutil",
			"tags": {
				"hostname" : hn[0],
				"counters": "counters",
			},
			"time": time,
			"fields": counters
			}
			)
client.write_points(influx_counters)
##memory
influx_memory = []
influx_memory.append({
			"measurement": "psutil",
			"tags": {
				"hostname" : hn[0],
				"counters": "memory",
			},
			"time": time,
			"fields": memory
			}
			)
client.write_points(influx_memory)
##swap
influx_swap = []
influx_swap.append({
			"measurement": "psutil",
			"tags": {
				"hostname" : hn[0],
				"counters": "swap",
			},
			"time": time,
			"fields": swap
			}
			)
client.write_points(influx_swap)
influx_pids = []
influx_pids.append({
			"measurement": "psutil",
			"tags": {
				"hostname" : hn[0],
				"counters": "pids",
			},
			"time": time,
			"fields": s_pids
			}
			)
client.write_points(influx_pids)
## TCP counts
influx_net_tcp_count = []
influx_net_tcp_count.append({
			"measurement": "psutil",
			"tags": {
				"hostname" : hn[0],
				"counters": "tcp_count",
			},
			"time": time,
			"fields": net_tcp_count
			}
			)
client.write_points(influx_net_tcp_count)
### UDP Count
influx_udp_count = []
influx_udp_count.append({
			"measurement": "psutil",
			"tags": {
				"hostname" : hn[0],
				"counters": "udp_count",
			},
			"time": time,
			"fields": udp_count
			}
			)
client.write_points(influx_udp_count)

###apps per user
influx_user_app = []
influx_user_app.append({
			"measurement": "psutil",
			"tags": {
				"hostname" : hn[0],
				"counters": "user_app",
			},
			"time": time,
			"fields": user_app
			}
			)
client.write_points(influx_user_app)
##Disk_io
influx_disk_io = []
for i in disk_io.keys():
	influx_disk_io.append({
				"measurement": "psutil",
				"tags": {
					"hostname" : hn[0],
					"counters": i,
				},
				"time": time,
				"fields": disk_io[i]
				}
				)
client.write_points(influx_disk_io)
