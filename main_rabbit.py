#coding:utf-8
import logging
from tornado.ioloop import IOLoop
from tornado import  ioloop
from tornado import gen
from tornado.iostream import StreamClosedError
from tornado.tcpserver import TCPServer
from tornado.options import options, define
from tornado import stack_context
#from file_sync.p_sftp import File_operation,local_path,Backup_path,Rsync_Linux
import os,ConfigParser
import json
import sys
#from common.agent import init_log
from setting import *
from service_log.service_c import Service_execute,Read_log,Thread_t
import threading
import traceback
from config_rw.rw_c import Config_modification
from monitor.run import Process_io,mongo_cpu_mem,disk_men
from common.agent import Rabbit_receive
from multiprocessing import Process, Queue

define("port", default=9888, help="TCP port to listen on")
logger = logging.getLogger(__name__)
connect=None
ssh=None
t1=None


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

