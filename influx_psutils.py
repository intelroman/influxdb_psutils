#!/usr/bin/python3
import os
import time
from pprint import pprint
from influxdb import InfluxDBClient
import psutil
from config import *

client = InfluxDBClient(host=host, port=8086, username=username, password=password)
client.switch_database(DB)

date = os.popen("date +%s").read().split('\n')
time = ((int(date[0])) * 1000000000 - 10000000000)
hn = os.popen("hostname").read().split('\n')


total_pids = len(psutil.pids())
pcore_count = psutil.cpu_count(logical=False)
lcore_count = psutil.cpu_count(logical=True)
cpu_load = psutil.cpu_percent(interval=1)
cpu_load_core = psutil.cpu_percent(interval=1, percpu=True)
cpu_times_percent = psutil.cpu_times_percent(interval=1)
pcpu_times_percent = psutil.cpu_times_percent(interval=1, percpu=True)
counters = { 
            'total_pids': total_pids,
            'pcore_count': pcore_count,
            'lcore_count': lcore_count,
            'all_cpu_times_user': cpu_times_percent.user,
            'all_cpu_times_nice': cpu_times_percent.nice,
            'all_cpu_times_system': cpu_times_percent.system,
            'all_cpu_times_idle': cpu_times_percent.idle,
            'all_cpu_times_iowait': cpu_times_percent.iowait,
            'all_cpu_times_irq': cpu_times_percent.irq,
            'all_cpu_times_softirq': cpu_times_percent.softirq,
            'all_cpu_times_steal': cpu_times_percent.steal,
            'all_cpu_times_guest': cpu_times_percent.guest,
            'all_cpu_times_guest_nice': cpu_times_percent.guest_nice,
            'cpu_load': cpu_load
           }
b = 0
for i in cpu_load_core:
    counters.update({("core"+str(b)+"_usage"): i})   
    b += 1
del (b)
a = ['udp4', 'tcp', 'tcp4', 'all', 'inet', 'unix', 'tcp6', 'udp6', 'inet6', 'udp', 'inet4']
for i in a:
    counters.update({"count_net_"+str(i): len(psutil.net_connections(i))}) 
del(a)
b = 0
for i in pcpu_times_percent:
    counters.update({
                     "cpu"+str(b)+"_times_user": pcpu_times_percent[b].user,
                     "cpu"+str(b)+"_times_nice": pcpu_times_percent[b].nice,
                     "cpu"+str(b)+"_times_system": pcpu_times_percent[b].system,
                     "cpu"+str(b)+"_times_idle": pcpu_times_percent[b].idle,
                     "cpu"+str(b)+"_times_iowait": pcpu_times_percent[b].iowait,
                     "cpu"+str(b)+"_times_irq": pcpu_times_percent[b].irq,
                     "cpu"+str(b)+"_times_softirq": pcpu_times_percent[b].softirq,
                     "cpu"+str(b)+"_times_steal": pcpu_times_percent[b].steal,
                     "cpu"+str(b)+"_times_guest": pcpu_times_percent[b].guest,
                     "cpu"+str(b)+"_times_guest_nice": pcpu_times_percent[b].guest_nice
                    })
    b += 1
del(b)
 
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
udp_count = {'LISTEN' : udp_listen_count , 'ESTABLISHED': udp_established }


### DISK patitions
partitions = []
disk_part = psutil.disk_partitions()
for i in disk_part:
    if i.mountpoint.find('deleted') == -1:
       partitions.append(i.mountpoint)
    else:
       continue
part_info = {}
for i in partitions:
    part_info.update({ i: {
                           "total": psutil.disk_usage(i).total,
                           "used": psutil.disk_usage(i).used,
                           "free": psutil.disk_usage(i).free,
                           "percent": psutil.disk_usage(i).percent
                           }})
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

anet_io_counters = psutil.net_io_counters(pernic=False, nowrap=True)
net_io_counters = psutil.net_io_counters(pernic=True, nowrap=True)
net_io_count = { 'all_int': { 
                             'bytes_sent': anet_io_counters.bytes_sent,
                             'bytes_recv': anet_io_counters.bytes_recv,
                             'packets_sent': anet_io_counters.packets_sent,
                             'pcckets_recv': anet_io_counters.packets_recv,
                             'error_in': anet_io_counters.errin,
                             'error_out': anet_io_counters.errout,
                             'drop_in': anet_io_counters.dropin,
                             'drop_out': anet_io_counters.dropout
                            }}
for i in net_io_counters.keys():
    net_io_count.update({ i: { 
                                'bytes_sent': net_io_counters[i].bytes_sent,
                                'bytes_recv': net_io_counters[i].bytes_recv,
                                'packets_sent': net_io_counters[i].packets_sent,
                                'pcckets_recv': net_io_counters[i].packets_recv,
                                'error_in': net_io_counters[i].errin,
                                'error_out': net_io_counters[i].errout,
                                'drop_in': net_io_counters[i].dropin,
                                'drop_out': net_io_counters[i].dropout
                         }})
### Temp
temp = psutil.sensors_temperatures()
temps = {}
b = 0
if bool(temp) == True:
   if type(temp) == dict:
      for i in temp.keys():
          if type(temp[i]) == list:
             for ii in temp[i]:
                 if bool(ii.label) == True:
                     temps.update({ (ii.label) : { "label": ii.label, "current": ii.current, "high": ii.high, "critical": ii.critical }})
                 else:
                     temps.update({ (i)+" "+str(b): {"label": (i)+" "+str(b), "current": ii.current, "high": ii.high, "critical": ii.critical}})
                     b += 1
del(b)
##pprint (temps)
##pprint (net_io_count)
##pprint (counters)
##pprint (memory)
##pprint (swap)
##pprint (net_tcp_count)
##pprint (udp_count)
##pprint (disk_io)
##pprint (user_app)
##pprint (s_pids)
##pprint (part_info)

##Counters
influx_counters = []
influx_counters.append({
			"measurement": "psutil_counters",
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
			"measurement": "psutil_memory",
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
			"measurement": "psutil_swap",
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
			"measurement": "psutil_process",
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
			"measurement": "psutil_tcp_count",
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
			"measurement": "psutil_udp_count",
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
			"measurement": "psutil_user_apps",
			"tags": {
				"hostname" : hn[0],
				"counters": "user_app",
			},
			"time": time,
			"fields": user_app
			}
			)
client.write_points(influx_user_app)
## Disk part
influx_disk_part = []
for i in part_info.keys():
    influx_disk_part.append({
			     "measurement": "psutil_disk_part",
			     "tags": {
			          "hostname" : hn[0],
				  "counters": i,
			     },
			     "time": time,
			     "fields": part_info[i]
			     })
client.write_points(influx_disk_part)
##Disk_io
influx_disk_io = []
for i in disk_io.keys():
    influx_disk_io.append({
			   "measurement": "psutil_disk_io",
			   "tags": {
				"hostname" : hn[0],
				"counters": i,
			   },
			   "time": time,
			   "fields": disk_io[i]
			   }
			   )
client.write_points(influx_disk_io)

##Network I/O
influx_net_io = []
for i in net_io_count.keys():
    influx_net_io.append({
			   "measurement": "psutil_net_io",
			   "tags": {
				"hostname" : hn[0],
				"counters": i,
			   },
			   "time": time,
			   "fields": net_io_count[i]
			   }
			   )
client.write_points(influx_net_io)
## Temp
influx_temp = []
for i in temps.keys():
    influx_temp.append({
			   "measurement": "psutil_temp",
			   "tags": {
				"hostname" : hn[0],
				"counters": i,
			   },
			   "time": time,
			   "fields": temps[i]
			   }
			   )
client.write_points(influx_temp)
