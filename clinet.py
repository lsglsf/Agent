#coding:utf-8


#from __future__ import print_function
from tornado.ioloop import IOLoop
from tornado import gen
from tornado.tcpclient import TCPClient
from tornado.options import options, define
import json

from setting import http_server,http_path,http_send1,mongo_table
from common.agent import Http_Rquest


ret={'data':[{'path':'/opt/aa','type':'none','delete':False},{'path':'/root','type':'none','delete':False}],'fun':'fun_file','app':'crm'}
ret1={'cmd':"/etc/init.d/ntpd restart",'path':"/var/log/messages",'fun':'service_execute','app':'start'}
ret2={'cmd':"/etc/init.d/ntpd restart",'path':"/var/log/messages",'fun':'service_execute','app':'stop'}
define("host", default="localhost", help="TCP server host")
define("port", default=9888, help="TCP port to connect to")
define("message", default=json.dumps(ret), help="Message to send")
define("message1", default=json.dumps(ret1), help="Message to send")
define("message2", default=json.dumps(ret2), help="Message to send")

@gen.coroutine
def send_message():
    stream = yield TCPClient().connect(options.host, options.port)
    while True:
        aa = raw_input('请输入read or write')
        if aa == "read":
            yield stream.write((options.message + "\n").encode())
            #        print("Sent to server:", options.message)
            reply = yield stream.read_until(b"\n")
            #        print(reply.decode().strip())
            c = json.loads(reply)
            print(c['s'])
            data = c
            #        print("Response from server:", reply.decode().strip())
            #        print reply.decode()
        if aa == "write":
            print('sdfsaf')
            print(data)
            data['fun']='file_write'
            yield stream.write((json.dumps(data) + "\n").encode())
            reply = yield stream.read_until(b"\n")
            print (reply)
        if aa == 'exit':
            break

@gen.coroutine
def send_message1():
    stream = yield TCPClient().connect(options.host, options.port)
    yield stream.write((options.message + "\n").encode())
    while True:
        reply = yield stream.read_until(b"\n")
        print (reply)

from common.agent import Mongodb_Operate
def mongo():
    test=Mongodb_Operate(host='192.168.44.130',port=27017)
    t1=test.read(db='system_disk',table=mongo_table)
    print t1

 #   print test.insert_one(db='test',table='my_collection',data={'aa':'test'})
    #t1 = test.read(db='test', table='my_collection')
  #  print t1

  #  t1= test.delnete(db='test', table='my_collection' , data={'aa':'test'})
   # print t1
    test.close()

  #  print t1

#    print (t1)
   # t1.close()

def http_send():
    ret={'a':'b'}
    print http_server,ret
   # http_server1=http_server+"?ip={0}&msg={1}".format('192.168.1.1',json.dumps(ret))
   #print http_server1
    #data1=json.dumps(ret)
   # aa = Http_Rquest.posthttp(url=http_server,path=http_path,data=data1)
    print http_send1
    aa = Http_Rquest.sendhttp(url=http_send1,data=ret)
    print aa

if __name__ == "__main__":
    mongo()
   # http_send()
#    options.parse_command_line()
#    IOLoop.current().run_sync(send_message1)
