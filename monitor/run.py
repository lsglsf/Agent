#coding:utf-8
from Mcommon import poll,mongo_io_insrt,System_ps,System_info


def Process_io():
    arg=poll(1)
    mongo_io_insrt(*arg)

def mongo_cpu_mem():
    arg = System_ps.poll(interval=1)
    System_ps.data_process(*arg)

def disk_men():
    System_info.disk()
    System_info.men()