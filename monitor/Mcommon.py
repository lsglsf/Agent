#!/usr/bin/env python
#coding:utf-8

import atexit
import time
import sys
from common.agent import Mongodb_Operate
from setting import cf,http_server,http_path,logger
from common.agent import Http_Rquest
import json
import psutil
import datetime
import os
from common.agent import Mongdb_data


def bytes2human(n):
    """
    """
    symbols = ('K', 'M', 'G', 'T', 'P', 'E', 'Z', 'Y')
    prefix = {}
    for i, s in enumerate(symbols):
        prefix[s] = 1 << (i + 1) * 10
    for s in reversed(symbols):
        if n >= prefix[s]:
            value = float(n) / prefix[s]
            return '%.2f %s/s' % (value, s)
    return '%.2f B/s' % (n)


def poll(interval):
    procs = [p for p in psutil.process_iter()]
    for p in procs[:]:
        try:
            p._before = p.io_counters()
        except psutil.Error:
            procs.remove(p)
            continue
    disks_before = psutil.disk_io_counters()
    time.sleep(interval)
    for p in procs[:]:
        with p.oneshot():
            try:
                p._after = p.io_counters()
                p._cmdline = ' '.join(p.cmdline())
                if not p._cmdline:
                    p._cmdline = p.name()
                p._username = p.username()
            except (psutil.NoSuchProcess, psutil.ZombieProcess):
                procs.remove(p)
    disks_after = psutil.disk_io_counters()

    for p in procs:
        p._read_per_sec = p._after.read_bytes - p._before.read_bytes
        p._write_per_sec = p._after.write_bytes - p._before.write_bytes
        p._total = p._read_per_sec + p._write_per_sec

    disks_read_per_sec = disks_after.read_bytes - disks_before.read_bytes
    disks_write_per_sec = disks_after.write_bytes - disks_before.write_bytes

    processes = sorted(procs, key=lambda p: p._total, reverse=True)
    return (processes, disks_read_per_sec, disks_write_per_sec)

@Mongdb_data(db="process_io")
def mongo_io_insrt(proc,disks_read_per_sec,disks_write_per_sec):
    time_io_data=str(time.time()).split('.')[0]
    ret={}
    ret[time_io_data]={}
    ret['id']=time_io_data
    http_se={}
    http_se['data']=[]
    for p in proc:
        data_l={}
        pid_p=str(p.pid)
        ret[time_io_data][pid_p]={}
        ret[time_io_data][pid_p]['pid']= str(p.pid)
        ret[time_io_data][pid_p]['username']=p._username
        #ret[time_io_data][pid_p]['read'] = bytes2human(p._read_per_sec)
        #ret[time_io_data][pid_p]['write'] = bytes2human(p._write_per_sec)
        ret[time_io_data][pid_p]['read'] = p._read_per_sec
        ret[time_io_data][pid_p]['write'] = p._write_per_sec
        ret[time_io_data][pid_p]['cmdline'] = p._cmdline
   # if  bytes2human(p._read_per_sec).split()[1] == 'k' and bytes2human(p._read_per_sec)[-1] == 'k':
       # print bytes2human(p._read_per_sec).split()[1],bytes2human(p._read_per_sec).split()[0]
        if bytes2human(p._read_per_sec).split(' ')[1] not in ["B/s","K/s"]  or bytes2human(p._write_per_sec).split(' ')[1] not in ["B/s","K/s"]:
            data_l['pid']=p.pid
            data_l['username']=p._username
            data_l['read']=bytes2human(p._read_per_sec)
            data_l['write']=bytes2human(p._write_per_sec)
            data_l['cmdline']=p._cmdline
            http_se['data'].append(data_l)
    if http_se['data']:
        data_http=Http_Rquest.posthttp(url=http_server,data=json.dumps(http_se),path=http_path)
    logger.warning("进程磁盘IO - {0}".format(http_se))
    return ret



class System_ps(object):

    @classmethod
    def bytes2human(cls,n):
        symbols = ('K', 'M', 'G', 'T', 'P', 'E', 'Z', 'Y')
        prefix = {}
        for i, s in enumerate(symbols):
            prefix[s] = 1 << (i + 1) * 10
        for s in reversed(symbols):
            if n >= prefix[s]:
                value = int(float(n) / prefix[s])
                return '%s%s' % (value, s)
        return "%sB" % n

    @classmethod
    def poll(cls,interval):
        # sleep some time
        #time.sleep(interval)
        procs = []
        procs_status = {}
        for p in psutil.process_iter():
            try:
                p.dict = p.as_dict(['username', 'nice', 'memory_info',
                                    'memory_percent', 'cpu_percent',
                                    'cpu_times', 'name', 'status','cmdline'])
                try:
                    procs_status[p.dict['status']] += 1
                except KeyError:
                    procs_status[p.dict['status']] = 1
            except psutil.NoSuchProcess:
                pass
            else:
                procs.append(p)

        # return processes sorted by CPU percent usage
        processes = sorted(procs, key=lambda p: p.dict['cpu_percent'],
                           reverse=True)
        return (processes, procs_status)



    @classmethod
    @Mongdb_data(db="process_cpu_men")
    def data_process(cls,procs, procs_status):
        time_io_data = str(str(time.time()).split('.')[0])
        ret = {}
        ret[time_io_data] = {}
        ret['id'] = time_io_data
        http_se = {}
        http_se['data'] = []
        for p in procs:
            pid_p=str(p.pid)
            ret[time_io_data][pid_p]={}
            if p.dict['cpu_times'] is not None:
                ctime = datetime.timedelta(seconds=sum(p.dict['cpu_times']))
                ctime = "%s:%s.%s" % (ctime.seconds // 60 % 60,
                                      str((ctime.seconds % 60)).zfill(2),
                                      str(ctime.microseconds)[:2])
            else:
                ctime = ''
            if p.dict['memory_percent'] is not None:
                p.dict['memory_percent'] = round(p.dict['memory_percent'], 1)
            else:
                p.dict['memory_percent'] = ''
            if p.dict['cpu_percent'] is None:
                p.dict['cpu_percent'] = ''
            if p.dict['username']:
                username = p.dict['username'][:8]
            else:
                username = ""
            if p.dict['cmdline']:
                cmdline = p.dict['cmdline']
            else:
                cmdline = ""
            ret[time_io_data][pid_p]['pid']= p.pid
            ret[time_io_data][pid_p]['username'] = username
            ret[time_io_data][pid_p]['nice'] = p.dict['nice']
            ret[time_io_data][pid_p]['vms'] = cls.bytes2human(getattr(p.dict['memory_info'], 'vms', 0))
            ret[time_io_data][pid_p]['rss'] = cls.bytes2human(getattr(p.dict['memory_info'], 'rss', 0))
            ret[time_io_data][pid_p]['cpu_percent'] = str(p.dict['cpu_percent'])
            ret[time_io_data][pid_p]['memory_percent'] = str(p.dict['memory_percent'])
            ret[time_io_data][pid_p]['ctime'] = ctime
            ret[time_io_data][pid_p]['name'] = p.dict['name'] or ''
            ret[time_io_data][pid_p]['cmdline'] = cmdline
            if p.dict['cpu_percent'] > 80 or p.dict['memory_percent'] > 80:
                data_l={
                    'pid':p.pid,
                    'username':username,
                    'nice':p.dict['nice'],
                    'vms':cls.bytes2human(getattr(p.dict['memory_info'], 'vms', 0)),
                    'rss':cls.bytes2human(getattr(p.dict['memory_info'], 'rss', 0)),
                    'cpu_percent':p.dict['cpu_percent'],
                    'memory_percent':p.dict['memory_percent'],
                    'ctime':ctime,
                    'name':p.dict['name'] or '',
                    'cmdline':cmdline,
                }
                http_se['data'].append(data_l)
        if http_se['data']:
            data_http = Http_Rquest.posthttp(url=http_server, data=json.dumps(http_se), path=http_path)
        logger.warning("进程CPU-内存 - {0}".format(http_se))
        return ret

class System_info(object):
    @classmethod
    def bytes2human(cls,n):
        symbols = ('K', 'M', 'G', 'T', 'P', 'E', 'Z', 'Y')
        prefix = {}
        for i, s in enumerate(symbols):
            prefix[s] = 1 << (i + 1) * 10
        for s in reversed(symbols):
            if n >= prefix[s]:
                value = float(n) / prefix[s]
                return '%.1f%s' % (value, s)
        return "%sB" % n


    @classmethod
    @Mongdb_data(db="system_disk")
    def disk(cls):
        time_io_data = str(str(time.time()).split('.')[0])
        ret={}
        ret[time_io_data]={}
        ret['id'] = time_io_data
        ret[time_io_data]['disk']=[]
        http_se = {}
        http_se['data'] = []
        for part in psutil.disk_partitions(all=False):
            sys={}
            if os.name == 'nt':
                if 'cdrom' in part.opts or part.fstype == '':
                    continue
            usage = psutil.disk_usage(part.mountpoint)
            sys['device']=part.device
            sys['total']=cls.bytes2human(usage.total)
            sys['used']=cls.bytes2human(usage.used)
            sys['free']=cls.bytes2human(usage.free)
            sys['percent']= int(usage.percent)
            sys['fstype'] = part.fstype
            sys['mountpoint']= part.mountpoint
            ret[time_io_data]['disk'].append(sys)
            if int(usage.percent) > 80 and part.fstype != 'iso9660':
                http_se['data'].append(sys)
        if http_se['data']:
            logger.warning("磁盘 {0}".format(http_se))
        return ret


    @classmethod
    @Mongdb_data(db="system_men")
    def men(cls):
        time_io_data = str(str(time.time()).split('.')[0])
        ret={}
        ret[time_io_data]={}
        ret['id'] = time_io_data
        ret[time_io_data]['mem']={}
        ret[time_io_data]['swap']={}
        virt = psutil.virtual_memory()
        swap = psutil.swap_memory()
        ret[time_io_data]['mem']['total']=cls.bytes2human(virt.total)
        ret[time_io_data]['mem']['used']=cls.bytes2human(virt.used)
        ret[time_io_data]['mem']['free']=cls.bytes2human(virt.free)
        ret[time_io_data]['mem']['shared']=cls.bytes2human(getattr(virt, 'shared', 0))
        ret[time_io_data]['mem']['buffers']=cls.bytes2human(getattr(virt, 'buffers', 0))
        ret[time_io_data]['mem']['cached']=cls.bytes2human(getattr(virt, 'cached', 0))
        ret[time_io_data]['swap']['total'] = cls.bytes2human(swap.total)
        ret[time_io_data]['swap']['used']=cls.bytes2human(swap.used)
        ret[time_io_data]['swap']['free']=cls.bytes2human(swap.free)
        if 'm' in cls.bytes2human(virt.free) or 'k' in cls.bytes2human(virt.free):
            logger.warning(ret)
        return ret





