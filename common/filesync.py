#coding:utf-8
from file_sync.p_sftp import File_operation
from file_sync.p_sftp import local_path,Backup_path,Rsync_Linux
import json
from setting import *
from agent import CRYPTOR


connect=None
ssh=None
t1=None

def fun_file(data,rabbit):
    global connect,ssh
    ret={}
    password=CRYPTOR.decrypt(data['s_host']['password'])
    path_dict = File_operation.path_join(source=data['s_host']['path'], target=data['t_hosts']['path'], file_dict=data['data'])
    file_s = File_operation(host=data['s_host']['ip'], port=data['s_host']['port'],
                            username=data['s_host']['username'],
                            password=password)
    print password
    print file_s
    print path_dict
    if connect == None:
        connect= file_s.connection()
        ssh = file_s.__dict__.get("ssh")
        print ssh
        if connect == None:
            ret['data']="Authentication failed"
            ret['status']=False
            ret['pf'] = 'read'
            rabbit.Work_queues(message=json.dumps(ret))
            #return json.dumps(ret)
    ret['s']=file_s.path_list(file_list=path_dict['s'],sftp=connect)
    ret['d']=local_path(file_list=path_dict['d'])
    ret['b']=data['t_hosts']['path']
    ret['app']=data['app']
    ret['fun']=data['app']
    ret['s_host']=data['s_host']['ip']
    ret['t_host']=data['t_hosts']['ip']
    ret['status']=True
    ret['pf']='read'
    #return json.dumps(ret)
    rabbit.Work_queues(message=json.dumps(ret))

def file_write(data,rabbit):
    global connect,ssh
    ret={}
    if connect == None:
        file_s=File_operation(host=data['s_host']['path'], port=data['s_host']['port'],username=data['s_host']['username'], password=CRYPTOR.decrypt(data['s_host']['password']))
        print CRYPTOR.decrypt(data['s_host']['password'])
        connect=file_s.connection()
        ssh=file_s.__dict__.get("ssh")
        if connect == None:
            ret['data'] = "Authentication failed"
            ret['status'] = False
            ret['pf'] = 'read'
            rabbit.Work_queues(message=json.dumps(ret))
    #stream.write('test11')
    ret['status']=True
    ret['data']="开始备份"
    ret['pf']="backup"
    rabbit.Work_queues(message=json.dumps(ret))
    #stream.write(json.dumps(ret)+EOF)
    backup_d=Backup_path.path_copy(data['t_host']['path'],cf.get('global','backup_path'))
    if backup_d['status']:
        ret={}
        ret['status'] = True
        ret['s']=backup_d['s']
        ret['d']=backup_d['d']
        ret['data'] = backup_d['data']
        ret['pf'] = "backup"
        cf.set('global','backup_name',ret['d'])
        cf.write(open(DEPLOY_CONFIG_PATH,'w'))
     #   stream.write(json.dumps(ret) + EOF)
        rabbit.Work_queues(message=json.dumps(ret))
        logger.info("update {0}".format(data))
    #file = File_operation(host=cf.get(data['app'], 'host_ip'), port=int(cf.get(data['app'], 'host_port')),username=cf.get(data['app'], 'host_username'), password=cf.get(data['app'], 'host_password'))
        print "test"
        print data
        file_w=File_operation.get_file(source=data['s'],target=data['d'],sftp=connect)
        print "test2"
        file_w['status']=True
        file_w['pf']='write'
        logger.info("{0}".format(file_w))
        rabbit.Work_queues(message=json.dumps(file_w))
       # return json.dumps(file_w)
    else:
        ret['status'] = False
        ret['s']=backup_d['s']
        ret['data'] = backup_d['data']
        ret['pf'] = "backup"
        rabbit.Work_queues(message=json.dumps(ret))
    #    stream.write(json.dumps(ret)+EOF)

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