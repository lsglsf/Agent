import os
#from common.agent import init_log
import ConfigParser
import logging
import hashlib

def init_log(log_file):
    try:
        logger = logging.getLogger()
        handler = logging.FileHandler(log_file)
        # format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s'
        # datefmt='%a, %d %b %Y %H:%M:%S'
        formatter = logging.Formatter('[%(asctime)s][%(levelname)s]: %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel("ERROR")
        return logger
    except:
        pass

pro_path = os.path.split(os.path.realpath(__file__))[0]
LOG_PATH = os.path.join(pro_path,"agent.log")
logger = init_log(LOG_PATH)
TIME_FORMAT='%Y-%m-%d %H:%M:%S'
pro_path = os.path.split(os.path.realpath(__file__))[0]
DEPLOY_CONFIG_PATH = os.path.join(pro_path,"config/agent.conf")
cf = ConfigParser.ConfigParser()
cf.read(DEPLOY_CONFIG_PATH)
http_server = '{0}:8080'.format(cf.get('global', 'server_ip'))
http_path = "/v1/service/list/mail/"
http_send1 = 'http://{0}:8080/v1/service/list/mail/'.format(cf.get('global', 'server_ip'))
mongo_table=str(hashlib.md5(cf.get('global', 'manage_ip')).hexdigest())