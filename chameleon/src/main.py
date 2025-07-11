import logging
from datetime import datetime

from config import Config
from utils import scp_sys_script
from iperf import iperf_main
from mini import mini_apps_main

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
    logging.info(f"MAIN: Starting the rocess: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} \n")

    scp_sys_script()        #TODO: make it instead of copy/paste
    #scp_docker_yml()       #TODO: make it instead of copy/paste
    iperf_main() if Config._APP == "iperf" else mini_apps_main()


if __name__ == "__main__":
    main()
