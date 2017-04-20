#coding:utf-8
import os
import logging
import commands
from setting import *
import urllib2
import traceback
import json
import urllib
import redis
import pymongo
import httplib
import hashlib
import pika
from pika.exceptions import ConnectionClosed
from Crypto.Cipher import AES
from binascii import b2a_hex, a2b_hex
#from filesync_test11 import fun_file


def d_rsync(source,target,ip,user,password_file):
    #cmd="/usr/bin/rsync -vzrtopg --progress --delete --exclude='.svn/' {0}@{1}::{2} {3} --password-file={4}".format(user,ip,source,target,password_file)
    cmd = "/usr/bin/rsync -vzrtopg --progress --exclude='.svn/' {0}@{1}::{2} {3} --password-file={4}".format(user, ip, source, target, password_file)
    logger.info("rsync {0}".format(cmd))
    data=commands_execute(cmd)
    return data

def commands_execute(cmd):
    ret=''
    logger.info("commands {0}".format(cmd))
    data=commands.getstatusoutput(cmd)
    ret=data
    return ret



def get_path(dir,dir_list):
    for i in os.listdir(dir):
        sys={}
        path_file=os.path.join(dir,i)
        if os.path.isfile(path_file):
            #print path_file
            sys['name']=i
            dir_list.append(sys)
        elif os.path.isdir(path_file):
            sys['name']=i
            sys['children']=[]
            dir_list.append(sys)
            get_path(path_file,sys['children'])
           # print path_file
    return dir_list


class Http_Rquest(object):
    @classmethod
    def sendhttp(self,url,data):
        header = {"Content-Type": "application/json"}
        try:
            data=urllib.urlencode(data)
            request = urllib2.Request(url,data)
            for key in header:
                request.add_header(key, header[key])
            try:
                result = urllib2.urlopen(request)
                #result_t=json.loads(result.read())
                result_t=result.read()
            except:
                result_t = traceback.format_exc()
                logger.error(result_t)
            else:
                result.close()
            return result_t
        except:
            s = traceback.format_exc()
            logger.error('execute func %s failure : %s' % (self.sendhttp, s))

    @classmethod
    def gethttp(self,url):
        header = {"Content-Type": "application/json"}
        try:
            request = urllib2.Request(url)
            for key in header:
                request.add_header(key, header[key])
            try:
                result = urllib2.urlopen(request)
                #result_t=json.loads(result.read())
                result_t=result.read()
            except:
                result_t = traceback.format_exc()
                logger.error(result_t)
            else:
                result.close()
            return result_t
        except:
            s = traceback.format_exc()
            logger.error('execute func %s failure : %s' % (self.sendhttp, s))

    @classmethod
    def posthttp(cls,url,data,path):
        #data = urllib.urlencode(data)
        try:
            headers = {"Content-type": "application/json"}
            conn = httplib.HTTPConnection(url)
            conn.request('POST', path, data, headers)
            httpres = conn.getresponse()
        except:
            logger.error("http {0}".format(traceback.format_exc()))
        # print httpres.status
        #print httpres.reason
        #print httpres.read()

    @classmethod
    def get_status(self,url):
        try:
            res = urllib.urlopen(url)
            page_status = res.getcode()
            return page_status
        except:
            return 0


def Mongdb_error():
    def fun_m(fun):
        def fun_p( self,*args, **kwargs):
            if kwargs.get('db',None) == None or kwargs.get('table',None):
                try:
                    data = fun(self,**kwargs)
                except:
                    logger.error(traceback.format_exc())
                    data = 0
            else:
                return 0
            return data
        return fun_p
    return fun_m

def Mongdb_data(db,type=None):
    def func(fun):
        def func_p(*args,**kwargs):
            if type == None:
                data_d=fun(*args,**kwargs)
                mongo_rw=Mongodb_Operate(host=cf.get('global', 'mongodb_ip'),port=int(cf.get('global', 'mongodb_port')))
                run_data=mongo_rw.insert_one(db=db,table=mongo_table,data=data_d)
                mongo_rw.close()
                logger.info("{0}".format(db))
                return run_data
        return func_p
    return func

def data(read,write):
    pass



class Redis_0perate(object):

    def __init__(self):
        pass

    def write(self):
        pass

    def read(self):
        pass

    def connet(self):
        pass

    def delnete(self):
        pass



class Mongodb_Operate(object):
    """
    monogdb 操作
    """

    def __init__(self,host,port,username=None,password=None):
        self.host=host
        self.port=port
        self.username=username
        self.password=password
        self.connet_m=self.connet()

    @Mongdb_error()
    def insert_one(self,**kwargs):
        db=kwargs.get('db',None)
        table=kwargs.get('table',None)
        dbs=self.connet_m[db]
        try:
            dbs[table].insert_one(kwargs.get('data',None))
            return 1
        except:
            logger.error(traceback.format_exc())
            return 0

    @Mongdb_error()
    def read(self,**kwargs):
        db=kwargs.get('db',None)
        table=kwargs.get('table',None)
        arg=kwargs.get('arg',None)
        ret=[]
        if arg == None:
            dbs=self.connet_m[db]
           # find_data = dbs[table].find({})
            for i in dbs[table].find({}):
                ret.append(i)
        else:
            dbs=self.connet_m[db]
            for i in dbs[table].find({}):
                ret.append(i)
        return ret



    def connet(self):
        connet_m = None
        if self.username == None:
            connet_m=pymongo.MongoClient(self.host,self.port)
        else:
            connet_m=pymongo.MongoClient(self.host,self.port,self.username,self.password)
        return connet_m

    @Mongdb_error()
    def update(self,**kwargs):
        db=kwargs.get('db',None)
        table=kwargs.get('table',None)
        if kwargs.get('source',None) != None:
            dbs=self.connet_m[db]
            dbs[table].update_one(kwargs.get('source',None),{"$set":kwargs.get('target',None)})
            return 1
        else:
            logger.error('source None')
            return 0

    @Mongdb_error()
    def delnete(self,**kwargs):
        db=kwargs.get('db',None)
        table=kwargs.get('table',None)
        dbs = self.connet_m[db]
        dbs[table].delete_one(kwargs.get('data',None))
        return 1
        #db.my_collection.delete_one({'id': 1})
        #pass

    def close(self):
        self.connet_m.close()



class PyCrypt(object):
    def __init__(self, key):
        self.key = key
        self.mode = AES.MODE_CBC

    def encrypt(self, passwd=None, length=32):
        if not passwd:
            passwd = self.gen_rand_pass()

        cryptor = AES.new(self.key, self.mode, b'6122ca7d906ad5e1')
        try:
            count = len(passwd)
        except TypeError:
            #raise ServerError('Encrypt password error, TYpe error.')
            pass

        add = (length - (count % length))
        passwd += ('\0' * add)
        cipher_text = cryptor.encrypt(passwd)
        return b2a_hex(cipher_text)

    def decrypt(self, text):
        cryptor = AES.new(self.key, self.mode, b'6122ca7d906ad5e1')
        try:
            plain_text = cryptor.decrypt(a2b_hex(text))
        except TypeError:
            pass
            #raise ServerError('Decrypt password error, TYpe error.')
        return plain_text.rstrip('\0')
CRYPTOR = PyCrypt('weishikejihuaban')








