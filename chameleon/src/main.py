#import subprocess, socket, os, logging, time, getpass
#from datetime import datetime
#from pathlib import Path

#from congestion import congestion_check, congestion_change
#from utils import run_subprocess, sys_reload, mkdir, run_stats, get_username, scp_sys_script
#from proxy import proxy_check, proxy_change
#from iperf import iperf_main, stop_iperf, start_iperf_servers, iperf_s2cs, iperf_endpoint
#from nginx import nginx_start_iperf_server, nginx_run_iperf, nginx_s2cs_iperf, nginx_main
#from mini import mini_apps_main
#from globus import status_globus_endpoint, restart_globus_endpoints

import logging
from config import Config
from utils import scp_sys_script
from iperf import iperf_main
from mini import mini_apps_main, scp_docker_yml

#logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')

#log_path = os.path.join(_HOME_DIR, "app.log")
#os.makedirs(_HOME_DIR, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("app.log")
    ]
)




# ─── MAIN ───────────────────────────────────────────────────────────────
def main():
    logging.info(f"MAIN: Starting the main process\n")

    scp_sys_script()
    #scp_docker_yml()
    iperf_main() if Config._APP == "iperf" else mini_apps_main()





if __name__ == "__main__":
    main()
