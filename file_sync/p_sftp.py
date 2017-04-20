# coding:utf-8

import paramiko,datetime,os
import types
import copy,os
import threading
import shutil
from stat import *
from setting import LOG_PATH,logger,TIME_FORMAT
from common.agent import d_rsync
import traceback
import time


class File_operation(object):

    def __init__(self,host,port,username,password):
        self.host=host
        self.port=port
        self.username=username
        self.password=password
        self.sftp=None
        self.ssh=None

    @classmethod
    def get_file(cls,source,target,sftp):
        ret={}
        ret['update']=[]
        ret['delete']=[]
        ret['create']=[]
        for (k,v) in zip(source,target):
            if k['type'] == 'e' and v['type']=='d' or v['type'] == 'f' and k['delete'] == True:
                os.system("rm -rf {0}".format(v['path']))
                ret['delete'].append(v['path'])
            elif k['type'] == 'd':
                if k['delete']==True:
                    os.system("rm -rf {0}".format(v['path']))
                    ret['delete'].append(v['path'])
                else:
                    try:
                        file_list=cls.__get_all_file(cls,sftp,k['path'],v['path'])
                       # print file_list
                        for files_l in file_list:
                            try:
                                sftp.get(files_l['s'],files_l['d'])
                                ret['update'].append(files_l['d'])
                                logger.info(files_l['d'])
                            except IOError:
                                logger.error(traceback.format_exc())
                                os.makedirs(os.path.split(files_l['d'])[0])
                                sftp.get(files_l['s'], files_l['d'])
                                ret['update'].append(files_l['d'])
                                logger.info(files_l['d'])
                    except UnicodeDecodeError:
                        surre = '{0}........同步失败'.format(v['path'])
                        ret['update'].append(surre)
            elif k['type'] == 'f':
                if k['delete'] == True:
                    os.system("rm -rf {0}".format(v['path']))
                    ret['delete'].append(v['path'])
                    logger.info(v['path'])
                else:
                    try:
                        sftp.get(k['path'], v['path'])
                        ret['update'].append(v['path'])
                        logger.info(v['path'])
                    except:
                        logger.error(traceback.format_exc())
                        os.makedirs(os.path.split(v['path'])[0])
                        sftp.get(k['path'], v['path'])
                        ret['update'].append(v['path'])
                        logger.info(v['path'])
        #sftp.close()
        return ret

    def put_file(self):
        pass

    @staticmethod
    def __get_all_file(cls,sftp, remote_dir,local_dir):
        all_files = []
        files = sftp.listdir_attr(remote_dir)
        if remote_dir[-1] == '/':
            remote_dir = remote_dir[0:-1]
        if local_dir[-1] == '/':
            local_dir = local_dir[0:-1]
        for i in files:
            sys={}
          #  print i.filename
            #file_path = os.path.join(remote_dir, i.filename)
            file_path = remote_dir + '/' + i.filename
            local_path=local_dir + '/' + i.filename
         #   print file_path
            if S_ISDIR(i.st_mode):
                all_files.extend(cls.__get_all_file(cls,sftp, file_path,local_path))
            else:
                sys['s']=file_path
                sys['d']=local_path
                all_files.append(sys)
        return all_files

    def connection(self):
        try:
            self.ssh=paramiko.Transport((self.host,self.port))
            self.ssh.connect(username=self.username,password=self.password)
            self.sftp=paramiko.SFTPClient.from_transport(self.ssh)
        except:
            self.sftp=None
            self.ssh = None
            logger.error("身份认证失败-{0}".format(traceback.format_exc()))
        return self.sftp

    def __getattribute__(self, name):
        return object.__getattribute__(self, name)

    @staticmethod
    def path_join(source,target,file_dict):
        ret={}
        source_dic=[]
        for dict_path in file_dict:
            if source in dict_path['path']:
                source_dic.append(copy.deepcopy(dict_path))
                dict_path['path'] = dict_path['path'].replace(source, target)
            else:
                dict_path['type'] = 'e'
                source_dic.append(copy.deepcopy(dict_path))
        ret['s']=source_dic
        ret['d']=file_dict
        return ret



    def path_status(self,sftp,df):
        ret = ''
        logger.error("检测文件-{0}-{1}".format(sftp,df))
        try:
#            sftp=self.connection()
            logger.error("检测文件-{0}".format(df))
            if sftp != None:
                status=sftp.stat(df)
                if S_ISDIR(status.st_mode):
                    ret = 'd'
                elif S_ISREG(status.st_mode):
                    ret = 'f'
                else:
                    ret = 'w'
                logger.error("sftp 检测返回-{0}".format(status))
            else:
                ret='e'
                logger.error("sftp 连接异常")
        except:
            ret = 'e'
            logger.error("sftp 目录检测-{0}".format(traceback.format_exc()))
        finally:
            return ret


    def path_list(self,file_list,sftp):
        for i in file_list:
            if i['type'] != 'e':
                i_type=self.path_status(df=i['path'],sftp=sftp)
                i['type']=i_type
        return file_list

    def close(self):
        if self.sftp !=None:
            self.sftp.close()
        return True

    def __delete__(self):
        self.ssh.close()
        self.sftp.close()



def local_path(file_list):
    for i in file_list:
        if i['type'] != 'e':
            if os.path.isfile(i['path']):
                i['type']='f'
            elif os.path.isdir(i['path']):
                i['type']='d'
            else:
                i['type']='e'
    return file_list


class Backup_path(object):
    def __init__(self):
        pass

    @classmethod
    def time_t(self):
        time_data=time.strftime(TIME_FORMAT, time.localtime(time.time()))
        return ''.join(time_data.split(' ')[0].split('-'))+''.join(time_data.split(' ')[1].split(':'))


    def dir_path(self,path):
        ret=False
        if os.path.isdir(path):
            ret=True
        return ret


    @classmethod
    def path_j(cls,s_path,t_path):
        ret={}
        s_p=os.path.split(s_path)
        if not s_p[1]:
            so_p=os.path.split(s_p[0])[1]
        else:
            so_p=s_p[1]
        bakcp_path=os.path.join(t_path,str(cls.time_t()),so_p)
        if os.path.isdir(t_path):
            ret['path']=bakcp_path
            ret['status']=True
        else:
            os.makedirs(t_path)
            ret['status']=True
            ret['path']=bakcp_path
        return ret

    @classmethod
    def path_copy(cls,s_path,t_path):
        ret={}
        try:
            path_status=cls.path_j(s_path,t_path)
            if path_status['status'] and os.path.isdir(s_path):
                shutil.copytree(s_path,path_status['path'])
                ret['s']=s_path
                ret['d']=path_status['path']
                ret['data']='备份成功'
                ret['status']=True
            else:
                logger.error("{0}不存在未备份".format(s_path))
                ret['data']='未备份'
                ret['s']=s_path
                ret['d'] = path_status['path']
                ret['status']=True
        except:
            ret['status']=False
            ret['s']=s_path
            ret['data']='Abnormal copy '
            logger.error(traceback.format_exc())
        return ret

class Rsync_Linux(object):
    def __init__(self,user,ip,source,target,password_file,rsync_path,source_local):
        self.user=user
        self.ip=ip
        self.source=source
        self.target=target
        self.password_file=password_file
        self.rsync_path=rsync_path
        self.source_local=source_local

    def file_rsync(self):
        ret={}
        ret['update']=[]
        ret['delete']=[]
        ret['create']=[]
        for (k, v) in zip(self.source, self.target):
            if k['type'] == 'e' and k['type']=='d' or k['type'] == 'f' and k['delete'] == True:
                os.system("rm -rf {0}".format(v['path']))
                ret['delete'].append(v['path'])
            else:
                k=self.path_amend(k['path'])
                data=d_rsync(user=self.user,ip=self.ip,source=k,target=v['path'],password_file=self.password_file)
                if data[0] == 0:
                  #  surre='{0}........同步成功'.format(v['path'])
                    ret['update'].append(v['path'])
                else:
                    err='{0}........同步失败'.format(v['path'])
                    ret['update'].append(err)
                logger.info(data)
        logger.info('Synchronization is complete')
        return ret


    def path_amend(self,path):
        sroue_l=os.path.abspath(self.source_local)
        path=path.replace(sroue_l,self.rsync_path)
        return path


























