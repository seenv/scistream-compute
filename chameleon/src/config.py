import os
import getpass
from pathlib import Path
from datetime import datetime




class Config:
    #_APP = "iperf"
    _APP = "mini-apps"
    
    #_WIN_SIZE = ["0", "64", "128"]
    #_PORT_MAP = {1: 3, 3: 1}
    #_BAND = ["0", "10G"]
    
    _TIME_FRAMES =  [20]    #[5, 10]
    _WIN_SIZE = ["0"]
    _PARALLELS = [1, 3, 5]        #[1,3] 


    #Generals
    _RUN_NUM = 10
    _PROXY = ['Nginx', 'StunnelSubprocess.v1.2', 'HaproxySubprocess', 'StunnelSubprocess.v1.3']        #can't have stunnel after each other as the proxy check will find stunnel and can't find the version
    _CONGESTIONS = ['cubic', 'bbr']
    _HOME_DIR = f"~/{_APP.upper()}-exps/{datetime.now().strftime('%Y-%m-%d')}"
    #_HOME_DIR = os.path.expanduser(f"~/experiments/{_APP}/{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}")


    _USERNAME = getpass.getuser()
    _MERROW_GLOBUS_SCRIPT = "/home/seena/Projects/globus-stream/scistream-compute/src/main.py"
    _SRC_DIR = os.path.expanduser('~/code')
    _C2CS_IP = '10.52.1.30'
    _P2CS_IP = '192.5.87.71'
    _BASE_PORT = 5100
    _LOCAL_SYS_SCRIPT = '/home/seena/Projects/chameleon/src/sys_monitor.py'
    _LOCAL_DOCKER_YML = '/home/seena/Projects/chameleon/mini-apps'
    _RMT_SYS_SCRIPT = '~/sys_monitor.py'
    _MINI_PATH = '~/mini-apps'


    _HOSTS = {"c2cs": "chi-c2cs", "p2cs": "chi-p2cs", "prod": "chi-prod", "cons": "chi-cons"}
    _S2CS_HOSTS = {"p2cs": "chi-p2cs", "c2cs": "chi-c2cs"}
    #_ENDPOINTS = ["chi-prod", "chi-cons"]
    _ENDPOINTS = {"prod": "chi-prod", "cons": "chi-cons"}
    _MODULES = ["daq", "dist", "sirt"]













    """
    _USERNAME = getpass.getuser()
    _HOME_DIR = os.path.expanduser(f'~/experiments/{_APP}/{datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}')
    _MERROW_GLOBUS_SCRIPT = "/home/seena/Projects/globus-stream/scistream-compute/src/main.py"
    _SRC_DIR = os.path.expanduser('~/code')
    _C2CS_IP = '10.52.1.30'
    _P2CS_IP = '192.5.87.71'
    _BASE_PORT = 5100

    _HOSTS = ["local", "chi-c2cs", "chi-prod", "chi-p2cs"]
    _S2CS_HOSTS = {"c2cs": "chi-c2cs", "p2cs": "chi-p2cs"}

    #_RUN_NUM = 10
    #_TIME_FRAMES = [10, 30, 60, 100]
    #_WIN_SIZE = ["0", "64", "128"]
    #_PROXY = ['StunnelSubprocess', 'HaproxySubprocess']
    #_CONGESTIONS = ['cubic', 'bbr', 'bbr2', bbr3']
    #_PARALLELS = [1, 3]

    #_PORT_MAP = {1: 3, 3: 1}
    #_BAND = ["0", "10G"]

    _RUN_NUM = 2
    _TIME_FRAMES = [5, 10]     
    _WIN_SIZE = ["0"]
    _PROXY = ['StunnelSubprocess', 'HaproxySubprocess']
    _CONGESTIONS = ['cubic', 'bbr']
    _PARALLELS = [1,3] """