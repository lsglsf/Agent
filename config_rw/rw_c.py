from common.agent import get_path
import subprocess
from setting import *
import json
import threading

class Config(object):

    def __init__(self):
        pass

    def _read(self):
        pass

    def _write(self):
        pass

    def _read_path(self):
        pass


class Config_modification(Config):

    def __init__(self,data,stream,EOF):
        super(Config, self).__init__()
        self.data=data
        self.stream=stream
        self.EOF=EOF

    def _read_path(self):
        print self.data
        ret=[{'name':self.data['path'],'children':[]}]
        ret_list=get_path(ret[0]['name'],ret[0]['children'])
        return ret

    def _read(self):
        with open('/root/c.py', 'rb') as f:
             return f.read()

    def run(self):
        return self._read_path()
