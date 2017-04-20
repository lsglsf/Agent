#coding:utf-8
import commands
from common.agent import commands_execute
import subprocess
from setting import *
import json
import threading


thread_dict={}

class Borg(object):
    _state = {}
    def __new__(cls, *args, **kw):
        ob = super(Borg, cls).__new__(cls, *args, **kw)
        ob.__dict__ = cls._state
        return ob


class Read_log(object):

    def __init__(self,data,stream,EOF):
        self.stream = stream
        self.EOF = EOF
        self.path = data['path']
        self.status=True

#    @classmethod
#    def __getattribute__(cls, name):
#        return object.__getattribute__(cls, name)

    def sub_log(self):
        popen = subprocess.Popen('tail -f ' + self.path, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        pid = popen.pid
    #    print('Popen.pid:' + str(pid))
        while self.status:
            ret={}
            ret['status']='None'
            line = popen.stdout.readline().strip()
            if self.stream['event'].isSet():
                logger.info("关闭日志文件.{0}".format(self.path))
                break
            if line:
                ret['data']=line
                logger.info("日志数据 {0}".format(ret))
               # self.stream.write(json.dumps(ret)+self.EOF)
                for i in self.stream['stream']:
                  #  i.write(json.dumps(ret)+self.EOF)
                    try:
                        i.write(json.dumps(ret) + self.EOF)
                    except:
                        if len(self.stream['stream']) == 1:
                            self.stream['stream'].remove(i)
                            logger.info('close all')
                            break
                        else:
                            self.stream['stream'].remove(i)
                            logger.error('close')

        popen.kill()
    #    for i in self.stream['stream']:
    #        i.close()

class Read_log_y(object):
    def __init__(self,data,stream,EOF):
        self.stream = stream
        self.EOF = EOF
        self.path = data['path']
        self.status=True

    def consumer(self):
        r = ''
        while True:
            line = yield
            ret={}
            ret['data'] = line
            logger.info("日志数据 {0}".format(ret))
            for i in self.stream['stream']:
                try:
                    i.write(json.dumps(ret) + self.EOF)
                except:
                    if len(self.stream['stream']) == 1:
                        self.stream['stream'].remove(i)
                        logger.info('close all')
                        break
                    else:
                        self.stream['stream'].remove(i)
                        logger.error('close')

    def produce(self,c):
        c.next()
        popen = subprocess.Popen('tail -f ' + self.path, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        pid = popen.pid
        while True:
            ret={}
            ret['status']='None'
            line = popen.stdout.readline().strip()
            if line:
                c.send(line)
        popen.kill()
        c.close()


class Service_execute(object):

    def __init__(self,data,stream,EOF):
        self.stream=stream
        self.EOF=EOF
        self.data=data
        self.cmd=data['cmd']

    def execute(self):
        ret={}
        return_data=commands_execute(self.cmd)
        if return_data[0] == 0:
            ret['status']=return_data[0]
            ret['data']=return_data[1]
            logger.info("执行结果{0}".format(ret))
            #self.stream.write(json.dumps(ret)+self.EOF)
            if type(self.stream) == dict:
                for i in self.stream['stream']:
                    i.write(json.dumps(ret) + self.EOF)
                read_log = Read_log(self.data, self.stream, self.EOF)
                read_log.sub_log()
                logger.info("打开日志文件 {0}".format(self.data['path']))
            else:
                self.stream.write(json.dumps(ret) + self.EOF)
        else:
            ret['status']=return_data[0]
            ret['data']=return_data[1]
         #   self.stream.write(json.dumps(ret)+self.EOF)
            if type(self.stream) == dict:
                for i in self.stream['stream']:
                    i.write(json.dumps(ret) + self.EOF)
            else:
                self.stream.write(json.dumps(ret) + self.EOF)
            logger.info("执行结果{0}".format(ret))
            self.stream.close()

    def execute_y(self):
        ret={}
        return_data=commands_execute(self.cmd)
        if return_data[0] == 0:
            ret['status']=return_data[0]
            ret['data']=return_data[1]
            logger.info("执行结果{0}".format(ret))
            #self.stream.write(json.dumps(ret)+self.EOF)
            if type(self.stream) == dict:
                for i in self.stream['stream']:
                    i.write(json.dumps(ret) + self.EOF)
                read_log = Read_log_y(self.data, self.stream, self.EOF)
                c=read_log.consumer()
                read_log.produce(c)
                logger.info("打开日志文件 {0}".format(self.data['path']))
                return c
            else:
                self.stream.write(json.dumps(ret) + self.EOF)
                return 1
        else:
            ret['status']=return_data[0]
            ret['data']=return_data[1]
         #   self.stream.write(json.dumps(ret)+self.EOF)
            if type(self.stream) == dict:
                for i in self.stream['stream']:
                    i.write(json.dumps(ret) + self.EOF)
            else:
                self.stream.write(json.dumps(ret) + self.EOF)
            logger.info("执行结果{0}".format(ret))
            self.stream.close()
            return 0

    def log_data(self,path):
        pass

class Thread_t(object):
    global thread_dict
    def __init__(self,data,stream,EOF):
        self.stream=stream
        self.EOF=EOF
        self.data=data
        self.stream_i=self.stream_id()
        self.path=self.data['path']

    def stream_id(self):
        return id(self.stream)

    def run(self):
        if self.data['app'] == 'start':
            if self.variable():
                service_execute_i = Service_execute(self.data, thread_dict[self.path], self.EOF)
        #    service_execute_i.execute()
                self.path = threading.Thread(target=service_execute_i.execute, args=())
                self.path.setDaemon(True)
                self.path.start()
            else:
                service_execute_i = Service_execute(self.data, self.stream, self.EOF)
                service_execute_i.execute()
        elif self.data['app'] == 'stop':
            g_stream=thread_dict[self.path]['stream']
            if thread_dict.get(self.path):
                if len(g_stream) == 1:
                    ret={}
                    thread_dict[self.path]['event'].set()
                    #g_stream.remove(self.stream)
                    ret['status']='stop'
                    self.stream.write(json.dumps(ret)+self.EOF)
                    thread_dict.pop(self.path)
                else:
                    g_stream.remove(self.stream)
            else:
                ret = {}
                # g_stream.remove(self.stream)
                ret['status'] = 'stop'
                self.stream.write(json.dumps(ret) + self.EOF)
                self.stream.write('日志文件未打开' + self.EOF)


    def run_y(self):
        if self.data['app'] == 'start':
            if self.variable():
                service_execute_i = Service_execute(self.data, thread_dict[self.path], self.EOF)
                return_data=service_execute_i.execute_y()
                if return_data != 0:
                    thread_dict[self.path]['y']=return_data
                else:
                    thread_dict.pop(self.path)
            else:
                service_execute_i = Service_execute(self.data, self.stream, self.EOF)
                return_data=service_execute_i.execute_y()
                if return_data == 0:
                    thread_dict[self.path]['stream'].remove(self.stream)

        elif self.data['app'] == 'stop':
            g_stream=thread_dict[self.path]['stream']
            if thread_dict.get(self.path):
                if len(g_stream) == 1:
                    ret={}
                    thread_dict[self.path]['y'].close()
                    ret['status']='stop'
                    self.stream.write(json.dumps(ret)+self.EOF)
                    thread_dict.pop(self.path)
                else:
                    g_stream.remove(self.stream)
            else:
                ret = {}
                # g_stream.remove(self.stream)
                ret['status'] = 'stop'
                self.stream.write(json.dumps(ret) + self.EOF)
                self.stream.write('日志文件未打开' + self.EOF)


    def variable(self):
        ret=''
        if thread_dict.get(self.path):
            thread_dict[self.path]['stream'].append(self.stream)
            ret=False
        else:
            thread_dict[self.path]={}
            thread_dict[self.path]['stream']=[self.stream]
            thread_dict[self.path]['event']=threading.Event()
            ret=True
        return ret

