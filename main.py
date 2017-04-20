#coding:utf-8
import logging
from tornado.ioloop import IOLoop
from tornado import  ioloop
from tornado import gen
from tornado.iostream import StreamClosedError
from tornado.tcpserver import TCPServer
from tornado.options import options, define
from tornado import stack_context
from file_sync.p_sftp import File_operation,local_path,Backup_path,Rsync_Linux
import os,ConfigParser
import json
import sys
from common.agent import init_log
from setting import *
from service_log.service_c import Service_execute,Read_log,Thread_t
import threading
import traceback
from config_rw.rw_c import Config_modification
from monitor.run import Process_io,mongo_cpu_mem,disk_men
from common.rabbitmq import Rabbit_receive
from multiprocessing import Process, Queue

define("port", default=9888, help="TCP port to listen on")
logger = logging.getLogger(__name__)
connect=None
ssh=None
t1=None


def fun_file(data,stream,EOF):
    global connect,ssh
    ret={}
    path_dict = File_operation.path_join(source=cf.get(data['app'],'host_path'), target=cf.get(data['app'],'local_path'), file_dict=data['data'])
    file_s = File_operation(host=cf.get(data['app'], 'host_ip'), port=int(cf.get(data['app'], 'host_port')),
                            username=cf.get(data['app'], 'host_username'),
                            password=cf.get(data['app'], 'host_password'))
    if connect == None:
        connect= file_s.connection()
        ssh = file_s.__dict__.get("ssh")
        if not connect:
            ret['data']="Authentication failed"
            ret['status']==False
            return json.dumps(ret)
    ret['s']=file_s.path_list(file_list=path_dict['s'],sftp=connect)
    ret['d']=local_path(file_list=path_dict['d'])
    ret['b']=os.path.isdir(cf.get(data['app'],'local_path'))
    ret['app']=data['app']
    ret['fun']=data['app']
    ret['s_host']=cf.get(data['app'],'host_ip')
    ret['t_host']=data['t_host']
    ret['status']=True
    ret['pf']='read'
    return json.dumps(ret)

def file_write(data,stream,EOF):
    global connect,ssh
    ret={}
    if connect == None:
        file_s=File_operation(host=cf.get(data['app'], 'host_ip'), port=int(cf.get(data['app'], 'host_port')),username=cf.get(data['app'], 'host_username'), password=cf.get(data['app'], 'host_password'))
        connect=file_s.connection()
        ssh=file_s.__dict__.get("ssh")
    #stream.write('test11')
    ret['status']=True
    ret['data']="开始备份"
    ret['pf']="backup"
    stream.write(json.dumps(ret)+EOF)
    backup_d=Backup_path.path_copy(cf.get(data['app'],'local_path'),cf.get(data['app'],'backup_path'))
    if backup_d['status']:
        ret={}
        ret['status'] = True
        ret['s']=backup_d['s']
        ret['d']=backup_d['d']
        ret['data'] = backup_d['data']
        ret['pf'] = "backup"
        cf.set(data['app'],'backup_name',ret['d'])
        cf.write(open(DEPLOY_CONFIG_PATH,'w'))
        stream.write(json.dumps(ret) + EOF)
        logger.info("update {0}".format(data))
    #file = File_operation(host=cf.get(data['app'], 'host_ip'), port=int(cf.get(data['app'], 'host_port')),username=cf.get(data['app'], 'host_username'), password=cf.get(data['app'], 'host_password'))
        file_w=File_operation.get_file(source=data['s'],target=data['d'],sftp=connect)
        file_w['status']=True
        file_w['pf']='write'
        logger.info("{0}".format(file_w))
        return json.dumps(file_w)
    else:
        ret['status'] = False
        ret['s']=backup_d['s']
        ret['data'] = backup_d['data']
        ret['pf'] = "backup"
        stream.write(json.dumps(ret)+EOF)

def rsync_files_w(data,stream,EOF):
    ret={}
    ret['status']=True
    ret['data']="开始备份"
    ret['pf']="backup"
    stream.write(json.dumps(ret)+EOF)
    backup_d=Backup_path.path_copy(cf.get(data['app'],'local_path'),cf.get(data['app'],'backup_path'))
    if backup_d['status']:
        ret={}
        ret['status'] = True
        ret['s']=backup_d['s']
        ret['d']=backup_d['d']
        ret['data'] = backup_d['data']
        ret['pf'] = "backup"
        cf.set(data['app'],'backup_name',ret['d'])
        cf.write(open(DEPLOY_CONFIG_PATH,'w'))
        stream.write(json.dumps(ret) + EOF)
        logger.info("update {0}".format(data))
        logger.info("Start synchronization")
    #file = File_operation(host=cf.get(data['app'], 'host_ip'), port=int(cf.get(data['app'], 'host_port')),username=cf.get(data['app'], 'host_username'), password=cf.get(data['app'], 'host_password'))
        rsync_class=Rsync_Linux(source_local=cf.get(data['app'],'host_path'),rsync_path=cf.get(data['app'],'rsync_path'),user=cf.get(data['app'],'rsync_user'),ip=cf.get(data['app'],'host_ip'),source=data['s'],target=data['d'],password_file=cf.get(data['app'], 'password_file'))
        #file_w=File_operation.get_file(source=data['s'],target=data['d'],sftp=connect)
        file_w=rsync_class.file_rsync()
        file_w['status']=True
        file_w['pf']='write'
        logger.info("{0}".format(file_w))
        return json.dumps(file_w)
    else:
        ret['status'] = False
        ret['s']=backup_d['s']
        ret['data'] = backup_d['data']
        ret['pf'] = "backup"
        stream.write(json.dumps(ret)+EOF)


def service_execute(data,stream,EOF):
    ret={}
    th_t=Thread_t(data,stream,EOF)
    th_t.run()
    ret['status']="None"
    ret['data']="开始执行"
    return json.dumps(ret)

def service_config(data,stream,EOF):
    ret={}
    conf_object=Config_modification(data=data,stream=stream,EOF=EOF)
    conf_object_data=conf_object.run()
    ret['status']="None"
    ret['data']=conf_object_data
    return json.dumps(ret)

class Callback_fun(object):
    def __init__(self,stream,address,io_loop):
        self.stream=stream
        self.address=address
        self.io_loop=io_loop
        self.EOF = b'\n'
        self.message_callback=stack_context.wrap(self.data_fun)
     #   self.stream.set_close_callback(self.no_close)

    @gen.coroutine
    def read_data(self):
        global connect,ssh
        while True:
            #yield self.stream.read_until(self.EOF, callback=self.message_callback)
            try:
                data=yield self.stream.read_until(self.EOF)
                self.data_fun(data)
            except StreamClosedError:
                logger.warning("Lost client at host %s", self.address[0])
                if ssh != None or connect != None:
                    ssh.close()
                    connect.close()
                    connect=None
                    ssh = None
                    break
            except Exception as e:
                s = traceback.format_exc()
                logging.error(s)
                break

    def no_close(self):
        global connect
        self.stream.close()
        connect.close()

    def data_fun(self,data):
        data_json=json.loads(data)
        return_data=globals()[data_json['fun']](data_json,self.stream,self.EOF)
        self.write(return_data+self.EOF)

    def write(self,data):
        self.stream.write(data)

class Agent_main(TCPServer):
    def __init__(self):
        super(Agent_main,self).__init__()
    def handle_stream(self, stream, address):
        callback_f=Callback_fun(stream=stream,address=address,io_loop=self.io_loop)
        callback_f.read_data()


def daemonize(stdin='/dev/null', stdout='/dev/null', stderr='/dev/null'):
    try:
        pid = os.fork()
        if pid > 0:
            sys.exit(0)
    except OSError, e:
        sys.stderr.write("fork #1 failed: (%d) %s\n" % (e.errno, e.strerror))
        sys.exit(1)
    os.chdir("/")
    os.umask(0)
    os.setsid()
    try:
        pid = os.fork()
        if pid > 0:
            sys.exit(0)
    except OSError, e:
        sys.stderr.write("fork #2 failed: (%d) %s\n" % (e.errno, e.strerror))
        sys.exit(1)


def tornado():
    options.parse_command_line()
    server = Agent_main()
    server.listen(options.port)
    logger.info("Listening on TCP port %d", options.port)
    ioloop.PeriodicCallback(Process_io,60000).start()
    ioloop.PeriodicCallback(mongo_cpu_mem, 60000).start()
    ioloop.PeriodicCallback(disk_men, 60000).start()
    ioloop.IOLoop.current().start()

def rabbitmq():
    rabbitmq_r=Rabbit_receive(host='192.168.2.224')
    rabbitmq_r.start()
    pass
''''
if __name__ == "__main__":
    tornado_start =Process(target=tornado,args=())
    rabbitmq_start = Process(target=rabbitmq, args=())
    tornado_start.start()
    rabbitmq_start.start()
    tornado_start.join()
    rabbitmq_start.join()
    pass
'''
if __name__ == "__main__":
    rabbitmq_start = Process(target=rabbitmq, args=())
    rabbitmq_start.start()
   # daemonize('/dev/null', '/tmp/daemon_stdout.log', '/tmp/daemon_error.log')
    options.parse_command_line()
    server = Agent_main()
    server.listen(options.port)
    logger.info("Listening on TCP port %d", options.port)
    ioloop.PeriodicCallback(Process_io,60000).start()
    ioloop.PeriodicCallback(mongo_cpu_mem, 60000).start()
    ioloop.PeriodicCallback(disk_men, 60000).start()
    ioloop.IOLoop.current().start()

