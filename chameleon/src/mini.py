

import subprocess, socket, os, logging, time, getpass
from datetime import datetime
from pathlib import Path
from utils import run_subprocess, sys_reload, mkdir, run_stats, get_username
import logging
from config import Config

from congestion import congestion_check, congestion_change
from proxy import proxy_check, proxy_change


def scp_docker_yml():
    try:
        local_docker_YML = Config._LOCAL_DOCKER_YML
        if not os.path.exists(local_docker_YML):
            logging.error(f"YML: Local YML was not found at {local_docker_YML}")
            raise FileNotFoundError(f"YML: Local YML was not found at {local_docker_YML}")
        for host in Config._HOSTS.values():
            remote_user = get_username(host).strip()
            #print(remote_user)
            if host in ["chi-prod", "chi-cons"]:
                docker_yml = f"{Config._MINI_PATH}/hosts/"
            else:
                docker_yml = f"{Config._MINI_PATH}/s2cs/"

            cmd = ["scp", "-r", docker_yml, 
                   f"{remote_user}@{host}:/home/{remote_user}/mini-apps/"]
                   #f' bash -c" cc@{host}:/home/cc/mini-apps/"']
            #logging.info(f"STATS: Copying system monitor script to {host}")
            proc = run_subprocess(cmd, shell=True)

            if proc is None: 
                raise Exception(f"YML: Failed to copy docker compose yml to {host.upper()}")

            stdout, stderr = proc.communicate()
            if proc.returncode != 0:
                raise Exception(stderr.strip())

            logging.info(f"YML: Successfully copied docker compose yml  to {host.upper()}")
        return

    except Exception as e:
        logging.error(f"YML: Failed to copy docker compose yml to {host.upper()}: {e}")
        raise Exception(f"YML: Error copying docker compose yml to {host.upper()}: {e}")


def container_stats(host):
    try:
        processes, stats = [], {}
        #logging.info(f"CONTAINER: Checking the active container on {host} ")
        if host == "local":
            #cmd_1 = ["docker", "ps", "-aq", "|", "wc", "-l"]
            #cmd_2 = ["docker", "ps", "-q", "|", "wc", "-l"]
            cmd_1 = [f"bash", "-c", f"docker ps -aq | wc -l"]
            cmd_2 = [f"bash", "-c", f"docker ps -q | wc -l"]
            
        else:
            cmd_1 = ["ssh", host, "docker ps -aq | wc -l"]
            cmd_2 = ["ssh", host, "docker ps -q | wc -l"]
            
        cmds = [cmd_1, cmd_2]
        for cmd in cmds:
            proc = run_subprocess(cmd, text=True)
            if proc is None:
                logging.warning(f"CONTAINER STATS: Failed to run the containers check command: {cmd} on {host.upper()}")
                raise RuntimeError(f"Failed to run the containers check command: {cmd} on {host.upper()}")
            processes.append((proc, host, "all" if cmd == cmd_1 else "active"))

        for proc, host, status in processes:
            stdout, stderr = proc.communicate()
            if proc.returncode != 0:
                logging.warning(f"CONTAINER STATS: The container on {host.upper()} didn't run: \n{stdout.strip()}")
                raise RuntimeError(f"CONTAINER STATS: The container on {host}. {stdout.strip()}")
            else:
                #logging.info(f"CONTAINER: {int(stdout.strip())} active container(s) on {host}")
                #logging.info(f"CONTAINER: {status} container(s) on {host}: {stdout.strip()}")
                stats[(host, status)] = int(stdout.strip())
        return stats

    except Exception as e:
        logging.warning(f"CONTAINER STATS: Failed to check remote container: {e}")
        raise Exception(f"Error checking remote container: {e}")



def start_containers(host, module, parallel, run, mini_path, exp_dir):
    try:
        #logging.info(f"CONTAINER: Starting the {module} containers on {host} with {parallel} parallels ")
        
        if host != "local":
            remote_cmd = (
                f"cd {mini_path}/{module}; "
                f"for i in {{1..{parallel}}}; do "
                #f"docker compose -f docker-compose.{module}${{i}} up -d 2>&1 "
                f"docker compose -f docker-compose.{module}${{i}} up  "
                f"| awk '{{ print strftime(\"[%Y-%m-%d %H:%M:%S]\"), $0; fflush() }}' "
                f"> {exp_dir}/{module}${{i}}_R{run}.log & "
                f"done"
            )
            cmd = ["ssh", host, remote_cmd]
            #proc = run_subprocess(cmd, text=True, shell=False)
        else:
            local_cmd = (
                f"cd {mini_path}/{module} && "
                f"for i in {{1..{parallel}}}; do "
                #f"docker compose -f docker-compose.{module}${{i}} up -d 2>&1 "
                f"docker compose -f docker-compose.{module}${{i}} up  "
                f"| awk '{{ print strftime(\"[%Y-%m-%d %H:%M:%S]\"), $0; fflush() }}' > {exp_dir}/{module}${{i}}_R{run}.log & "
                f"done"
            )
            cmd = [f"bash", "-c", local_cmd]
            #proc = run_subprocess(cmd, text=True, shell=True)
        
        proc = run_subprocess(cmd, text=True)
        if proc is None:
            logging.warning(f"START CONTAINER: Failed to run the containers check command: {cmd} on {host.upper()}")
            raise RuntimeError(f"Failed to run the containers check command: {cmd} on {host.upper()}")
        
        #proc.communicate()
        logging.info(f"START CONTAINER: Started {module.upper()} containers on {host.upper()} with {parallel} parallels")
        return True

    except Exception as e:
        logging.warning(f"START CONTAINER: Failed to check remote container {module.upper()}: {e}")
        raise Exception(f"Error checking remote container {module.upper()}: {e}")


def stop_containers(hosts):
    try:
        processes = []
        #for host in Config._ENDPOINTS.values():
        for host in hosts.values():
            if host != "local":
                cmd = [
                    'ssh', host,
                    'bash -c "docker ps -q | xargs --no-run-if-empty docker kill"'
                ]
            else:
                cmd = [
                    'bash', '-c',
                    'docker ps -q | xargs --no-run-if-empty docker kill'
                ]
            proc = run_subprocess(cmd, text=True)
            if proc is None:
                logging.warning(f"STOP CONTAINER: Failed to run the containers stop command on {host.upper()}")
                raise RuntimeError(f"STOP CONTAINER: Failed to run the containers stop command on {host.upper()}")
            processes.append((proc, host))
        for proc, host in processes:
            stdout, stderr = proc.communicate()
            if proc.returncode != 0:
                logging.warning(f"STOP CONTAINER: Failed to stop containers on {host.upper()}: {stdout.strip()}")
                raise RuntimeError(f"STOP CONTAINER: Failed to stop containers on {host.upper()}: {stdout.strip()}")
            logging.info(f"STOP CONTAINER: Successfully stopped containers on {host.upper()}")
        return True
    except Exception as e:
        logging.warning(f"STOP CONTAINER: Failed to stop containers on {host.upper()}: {e}")
        raise Exception(f"Error stopping containers on {host.upper()}: {e}")
    


def wait_and_prune(host, iter):
    #prev_prod_status = False
    for attempt in range(iter):
        stats = container_stats(host)
        active = stats.get((host, "active"), 0)
        #logging.info(f"ACTIVE CONTAINERS: {active} on {host.upper()}")
        #if (host == "chi-prod" and active == 0) or (host != "chi-prod" and active <= 5):
        if (host != "chi-prod" and host != "chi-p2cs" and active <= 5):
            logging.debug(f"WAIT & PRUNE: Containers on {host.upper()} are done")
            return True
            #prune_containers(host)
            #time.sleep(2)
            # Re-check after prune!
            #stats = container_stats(host)
            #if stats.get((host, "all"), 0) != 0:
            #    logging.error(f"CONTAINER: {host} has active containers after cleanup, count: {stats.get((host, 'all'), 0)}")
            #    raise RuntimeError(f"Failed to clean up containers on {host}. Active containers remain.")
            #break
        elif (host == "chi-prod" and active == 0) or (host == "chi-p2cs" and active == 0):
            logging.debug(f"WAIT & PRUNE: Container on {host.upper()} is done")
            #prev_prod_status = True
            return True
        else:
            #logging.info(f"CONTAINER: {host.upper()} is still running, waiting for completion ")
            time.sleep(1)

    return False



def prune_containers(host):
    try:
        #logging.info(f"CONTAINER: Cleaning up the containers on {host} ")
        if host != "local":
            cmd = [
                'ssh', host,
                'bash -c "docker ps -q | xargs --no-run-if-empty docker stop && docker container prune -f"'
            ]
        else:
            cmd = [
                'bash', '-c',
                'docker ps -q | xargs --no-run-if-empty docker stop && docker container prune -f'
            ]
        proc = run_subprocess(cmd, text=True)
        if proc is None:
            logging.warning(f"PRUNE CONTAINER: Failed to run the cleanup on {host.upper()}")
            raise RuntimeError(f"PRUNE CONTAINER: Failed to run the cleanup on {host.upper()}")
        stdout, stderr = proc.communicate()
        if proc.returncode != 0:
            logging.warning(f"PRUNE CONTAINER: Failed to clean up containers on {host} \n{stdout.strip()}")
            raise RuntimeError(f"PRUNE CONTAINER: Failed to clean up containers on {host} \n{stdout.strip()}")

        logging.debug(f"PRUNE CONTAINER: Successfully cleaned up containers on {host.upper()} {stdout.strip()}")
        logging.info(f"PRUNE CONTAINER: Successfully cleaned up containers on {host.upper()}")
        return True
    except Exception as e:
        logging.warning(f"PRUNE CONTAINER: Failed to clean up containers on {host.upper()}: {e}")
        raise Exception(f"Error cleaning up containers on {host.upper()}: {e}")



def run_mini_apps(hosts, duration, parallel, run, output_dir):
    try:
        for host in hosts.values():

            #output_dir = Path(Config._HOME_DIR) / f"{host}" / f"{proxy}" / f"{congestion}" / f"P{parallel}" / f"I{iteration}" / f"R{run}"
            #output_dir.mkdir(parents=True, exist_ok=True)
            mkdir(host, output_dir)

            #logging.info(f"Starting system and network stats logger on {host}")
            if host == "chi-prod" or host == "chi-p2cs":
                module = Config._MODULES[0]
                #stats_prod = run_stats(iteration, run, output_dir, Config._SRC_DIR)
                stats_prod = run_stats(host, duration + 8, run, os.path.join(output_dir, f"stats_R{run}.json"), Config._RMT_SYS_SCRIPT)
                start_containers(host, module, parallel, run, Config._MINI_PATH, output_dir)
                #logging.debug(f"STATS FROM MINI: starting stats {module.upper()} on {host.upper()}")
                #logging.debug(f"CONTAINER: Starting the containers {module.upper()} on {host.upper()} with {parallel} parallels")
            elif host != "chi-prod" and host != "chi-p2cs":
                #stats_cons = run_stats(iteration, run, output_dir, Config._SRC_DIR)
                stats_cons = run_stats(host, duration + 8, run, os.path.join(output_dir, f"stats_R{run}.json"), Config._RMT_SYS_SCRIPT)
                #logging.info(f"STATS FROM MINI: starting stats on {module.upper()} on {host.upper()}")
                for module in Config._MODULES[1:]:
                    time.sleep(1)
                    start_containers(host, module, parallel, run, Config._MINI_PATH, output_dir)
                    #logging.debug(f"CONTAINER: starting the containers {module.upper()} on {host.upper()} with {parallel} parallels")
        
        
        time.sleep(duration + 3 + 1)    #the omit time in iperf + 1 for the docker container startup time
        #for host in Config._ENDPOINTS.values():
            #logging.debug(f"MINI: Stopping the containers on {host.upper()}")
        stop_containers(hosts)

        dist_is_done = False
        for host in hosts.values():
            resp = wait_and_prune(host, duration + 8)
            if host != "chi-prod" and host != "chi-p2cs" and resp:
                dist_is_done = True

        if dist_is_done:
            for host in hosts.values():
                logging.info(f"MINI: Data transfer is done")
                prune_containers(host)
        else:
            logging.warning(f"MINI: Containers are still running after timeout on {host.upper()}\n")
            #raise RuntimeError(f"MINI: {host.upper()} containers are still running after timeout, not pruning!")
        
        time.sleep(5)
        for host in hosts.values():
            resp = wait_and_prune(host, 5)
            if not resp:
                logging.warning(f"CONTAINER: CONTAINERS ON {host.upper()} ARE STILL RUNNING and not PRUNED \n")
        
        stdout, stderr = stats_cons.communicate()
        logging.info("MINI: Completed System Monitor successfully \n")
        return True
    
    except Exception as e:
        logging.warning(f"MINI: Failed to run the mini apps: {e}")
        raise Exception(f"Error running mini apps: {e}")




def mini_apps_main():
    
    logging.info("MINI-APPS: Starting mini apps main process \n")
    
    logging.info("MINI-APPS: Cleaning up the containers on all endpoints")
    for host in Config._ENDPOINTS.values():
        prune_containers(host)
        time.sleep(2)
    
    # iterations, run, congestion, proxy, parallels (total containers), 
    total_runs = len(Config._TIME_FRAMES) * len(Config._CONGESTIONS) * len(Config._PROXY) * len(Config._PARALLELS) * Config._RUN_NUM

    prev_congestion = None
    prev_proxy = None

    combinations = (
        (congestion, proxy, duration, parallel, run)
        for congestion in Config._CONGESTIONS
        for proxy in Config._PROXY
        for duration in Config._TIME_FRAMES
        for parallel in Config._PARALLELS
        for run in range(1, Config._RUN_NUM + 1)
    )

    for total_idx, (congestion, proxy, duration, parallel, run) in enumerate(combinations, start=1):
        
        if congestion != prev_congestion:
            #logging.info("MINI-APPS: Checking the Congestion Control")
            for host in Config._HOSTS.values():
                if not congestion_check(host, congestion):
                    congestion_change(host, congestion)
                sys_reload(host)
                time.sleep(2)
            prev_congestion = congestion

        if proxy != prev_proxy:
            if not proxy_check(Config._S2CS_HOSTS, proxy):
                proxy_change(Config._MERROW_GLOBUS_SCRIPT, Config._S2CS_HOSTS, proxy)
            #time.sleep(5)
            print(f"\n proxy is {proxy} \n")
            prev_proxy = proxy
        #logging.debug(f"MAIN: Current proxy is {proxy}, and the congestion is {congestion.upper()}")

        logging.info(f"----- Congestion: {congestion.capitalize()}, Proxy: {proxy}, Duration: {duration}, Parallel: {parallel}, Run:{Config._RUN_NUM} ----- \n")
        logging.info(f"MINI: Total: {total_idx} / {total_runs}: Run: {run} / {Config._RUN_NUM} ----------------------------- ")
        logging.info(f"TIME: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        #output_dir = Path(Config._HOME_DIR) / f"{proxy}" / f"{congestion}" / f"P{parallel}" / f"I{iteration}" / f"R{run}"
        output_dir = Path(Config._HOME_DIR) / f"{proxy}" / f"{congestion}" / f"P{parallel}" / f"T{duration}"
        #output_dir.mkdir(parents=True, exist_ok=True)

        
        #####
        #run_mini(Config._C2CS_IP, Config._BASE_PORT, congestion, parallel, iteration, run, output_dir)
        run_mini_apps(Config._ENDPOINTS, duration, parallel, run, output_dir)
        time.sleep(5)

        run_mini_apps(Config._S2CS_HOSTS, duration, parallel, run, output_dir)

        #s2cs_iperf("chi-c2cs", Config._P2CS_IP, "6666", congestion, win_size, parallel, iteration, output_dir)
        
        if run == Config._RUN_NUM:
            logging.info(f"MINI: Complete run {run} / {Config._RUN_NUM} ------------------------------------ \n")
            time.sleep(5)

    logging.info("All experiments complete.")
    time.sleep(10)






    """processes = []
    remote_cmd = (
        f"bash -c '"
        f"cd {Config._MINI_PATH}/{module}; "
        f"for i in {{1..{parallel}}}; do "
        f"docker compose -f docker-compose.{module}${{i}} up -d "
        f"| awk \"{{ print strftime(\\\"[%Y-%m-%d %H:%M:%S]\\\"), $0; fflush() }}\" "
        f"> {module}${{i}}.log 2>&1 & "
        #f"disown; "
        f"done'"
    )
    logging.info(f"REMOTE CMD: {remote_cmd}")
    if host != "local":
        cmd = ["ssh", host, remote_cmd]
    else:
        cmd = [
            f"bash -c '"
            f"cd {Config._MINI_PATH}/{module}; "
            f"for i in {{1..{parallel}}}; do "
            f"docker compose -f docker-compose.{module}${{i}} up -d "
            f"| awk \"{{ print strftime(\\\"[%Y-%m-%d %H:%M:%S]\\\"), $0; fflush() }}\" "
            f"> {module}${{i}}.log 2>&1 & "
            #f"disown; "
            f"done'"
        ]
        
    proc = run_subprocess(cmd, text=True)
    if proc:
        processes.append((proc, module))
    else:
        logging.info(f"CONTAINER: Failed to run the containers check command: {cmd} on {host}")
        raise RuntimeError(f"Failed to run the containers check command: {cmd} on {host}")

    if not container_stats(host):
        logging.info(f"CONTAINER: Failed to start the {module} containers on {host}.")
        return False
    time.sleep(1)
        
    logging.info(f"CONTAINER: Started {module} containers on all endpoints with {parallel} parallels.")
    
    for proc, module in processes:
        if module != "sirt":
            stdout, stderr = proc.communicate()
            if proc.returncode != 0:
                logging.info(f"CONTAINER: The container {module} on {host}. {stdout.strip()}")
                return False
            logging.info(f"CONTAINER: The container {module} on {host} started successfully.")
    return True

except Exception as e:
    logging.info(f"Failed to check remote container {module}: {e}")
    raise Exception(f"Error checking remote container {module}: {e}")"""
    
    """shell_cmd = (
        f"cd {mini_path}/{module}; "
        f"for i in {{1..{parallel}}}; do "
        f"docker compose -f docker-compose.{module}${{i}} up -d 2>&1 "
        f"| awk '{{ print strftime(\"[%Y-%m-%d %H:%M:%S]\"), $0; fflush() }}' "
        f"> {module}${{i}}.log; "
        f"done"
    )"""
    
    
    
    
"""def run_mini(c2cs_ip, base_port, congestion, win_size, parallel, iteration, run, output_dir):
    
    for name, host in Config.items():
        stats = container_stats(host)
        if stats.get((host, "all"), 0) > 0:
            logging.info(f"CONTAINER: {host} has active containers, cleaning up ")
            prune_containers(host)
            time.sleep(2) 
            stats = container_stats(host)
            if stats.get((host, "all"), 0) != 0:
                logging.error(f"CONTAINER: {host} has active containers after cleanup, count: {stats.get((host, "all"), 0)}")
                raise RuntimeError(f"Failed to clean up containers on {host}. Active containers remain.")
        else:
            logging.info(f"CONTAINER: {host} has no active containers, no cleanup needed.")
        
    start_containers(module="daq", parallel=5)

    
    for host in hosts:
        logging.info(f"CONTAINER: waiting for completion of the containers on {hosts} ")
        for attempt in range(iteration * 3):
            stats = container_stats(host)
            if ((host == "chi-prod" and stats.get((host, "active"), 0) == 0) or
                (host != "chi-prod" and stats.get((host, "active"), 0) <= 5)):
                logging.info(f"CONTAINER: {host} is done and the containers are stopped")
                prune_containers(host)
                break 
            else:
                #logging.info(f"CONTAINER: {host} is still running, waiting for completion ")
                time.sleep(5)
        else:
            logging.warning(f"CONTAINER: {host} containers are still running after timeout, not pruning!")"""