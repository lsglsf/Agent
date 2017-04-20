#coding:utf-8
from setting import  *
import pika
from pika.exceptions import ConnectionClosed
import traceback
import json
from filesync import *
import filesync


def rabbit_auth(aa=None):
    def rabbit_fun(fun):
        def rabbit_parameter(self,*args,**kwargs):
            try:
                fun(self,*args,**kwargs)
            except ConnectionClosed:
                self.connection = None
                self.channel = None
                logger.error("rabbitmq auth-{0}".format(traceback.format_exc()))
            except :
                self.connection = 0
                self.channel = 0
                logger.error("rabbitmq auth-{0}".format(traceback.format_exc()))

        return rabbit_parameter
    return rabbit_fun


class Rabbit_Pika(object):

    @rabbit_auth()
    def __init__(self,host,username=None,password=None):
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(host=host))
        self.channel = self.connection.channel()


    def Work_queues(self):
        pass

    def Publish_Subscribe(self):
        pass

    def Routing(self):
        pass

    def Topics(self):
        pass

    def Rpc(self):
        pass

    def receive(self):
        pass



class Rabbit_queues(Rabbit_Pika):

    def __init__(self,queue,routing_key,correlation_id,channel=None):
        if channel == None:
            super(Rabbit_queues,self).__init__()
        else:
            self.channel=channel
        self.queue=queue
        self.routing_key=routing_key
       # self.message=message
        self.correlation_id=correlation_id

    def Work_queues(self,message):
     #   self.channel.queue_declare(queue=self.queue, durable=True)
        self.channel.basic_publish(exchange='',
                                    routing_key=self.routing_key,
                                    body=message,
                                    properties=pika.BasicProperties(
                                        delivery_mode=2,  # make message persistent
                                        correlation_id=self.correlation_id
                                    ))
        #self.connection.close()

    def Rpc(self):
        pass



def rabbit_connt(aa=None):
    def rabbit_fun(fun):
        def rabbit_parameter(self,*args,**kwargs):
            if self.channel !=None:
                try:
                    fun(self,*args,**kwargs)
                except KeyError:
                    logger.error("rabbitmq - {0}".format(traceback.format_exc()))
                except:
                    logger.error("rabbitmq - {0}".format(traceback.format_exc()))
            else:
                raise ConnectionClosedException()
        return rabbit_parameter
    return rabbit_fun


class Rabbit_receive(Rabbit_Pika):

    def __init__(self,host,username=None,password=None):
        self.host=host
        super(Rabbit_receive,self).__init__(host=self.host)

    @rabbit_connt()
    def receive(self):
        self.channel.queue_declare(queue=cf.get('global','id'), durable=True)
        self.channel.basic_qos(prefetch_count=1)
        self.channel.basic_consume(self.callback_queues,queue=cf.get('global','id'))

    @rabbit_connt()
    def Subscribe_receive(self):
        self.channel.exchange_declare(exchange='logs',type='fanout')
        result = self.channel.queue_declare(exclusive=True)
        queue_name = result.method.queue
        self.channel.queue_bind(exchange='logs',queue=queue_name)
        self.channel.basic_consume(self.callback_Subscribe,
                              queue=queue_name)
    @rabbit_connt()
    def Routing_receive(self):
        self.channel.exchange_declare(exchange='direct_logs',type='direct')
        result = self.channel.queue_declare(exclusive=True)
        queue_name = result.method.queue
        severities=['info1']
        for severity in severities:
            self.channel.queue_bind(exchange='direct_logs',queue=queue_name,routing_key=severity)
        self.channel.basic_consume(self.callback_Routing,queue=queue_name)

    @rabbit_connt()
    def topic_receive(self):
        self.channel.exchange_declare(exchange='topic_logs',type='topic')
        result = self.channel.queue_declare(exclusive=True)
        queue_name = result.method.queue
        binding_keys=['info','*.info','#']
        for binding_key in binding_keys:
            self.channel.queue_bind(exchange='topic_logs',
                               queue=queue_name,
                               routing_key=binding_key)

        self.channel.basic_consume(self.callback_topic,
                              queue=queue_name,)

    def callback_Subscribe(self,ch, method, properties, body):
        print method.routing_key,body
        ch.basic_ack(delivery_tag=method.delivery_tag)



    def callback_queues(self,ch, method, properties, body):
        print method.routing_key,body,properties
        ch.basic_ack(delivery_tag=method.delivery_tag)
        data= json.loads(body)
        #fun =
        #function = getattr(filsync, func)
        func = getattr(filesync,data['fun'])
        #return_data=fun_file(data=data)
        rabbit_object=self.Rpc(queue=properties.reply_to,routing_key=properties.reply_to,channel=self.channel,correlation_id=properties.correlation_id)
        func(data=data,rabbit=rabbit_object)


    def callback_Routing(self,ch, method, properties, body):
        print method.routing_key,body,properties
        ch.basic_ack(delivery_tag=method.delivery_tag)
        self.Rpc()

    def callback_topic(self,ch, method, properties, body):
        print method.routing_key,body
        ch.basic_ack(delivery_tag=method.delivery_tag)
        self.Rpc()

    def Rpc(self,queue,routing_key,correlation_id,channel):
        test=Rabbit_queues(queue=queue,routing_key=routing_key,correlation_id=correlation_id,channel=self.channel)
        return test
       # test.Work_queues()

    @rabbit_connt()
    def start(self):
        self.receive()
       # self.Subscribe_receive()
       # self.Routing_receive()
        #self.topic_receive()
        self.channel.start_consuming()




class RabbitmqException(Exception):
    def __init__(self, err='Rabbitmq 连接失败'):
        Exception.__init__(self, err)

class  ConnectionClosedException(RabbitmqException):
    def __init__(self,err='ConnectionClosed'):
        print 'tewww11'
        RabbitmqException.__init__(self,err)