import os, logging, time
from datetime import datetime
from pathlib import Path

from config import Config
from utils import run_subprocess, sys_reload, mkdir, run_stats
from congestion import congestion_check, congestion_change
from proxy import proxy_check, proxy_change


def stop_iperf(host):
    try:
        #logging.info(f"IPERF: Stopping iperf on {host.capitalize()}")
        cmd = ["ssh", host, "pkill iperf3"]
        proc = run_subprocess(cmd, text=True)
        if proc is None:
            logging.error(f"IPERF: Failed to stop iperf on {host.capitalize()}")
            return None
        
        stdout, stderr = proc.communicate()
        #if proc.returncode != 0:
        #    logging.error(f"IPERF: Failed to stop iperf on {host.capitalize()}: {stderr.strip()}")
        #    return None

        #logging.info(f"IPERF: Successfully stopped iperf on {host.capitalize()}")
    except Exception as e:
        logging.error(f"IPERF: Error stopping iperf on {host.capitalize()} {e}", exc_info=True)
        raise RuntimeError(f"IPERF: Error stopping iperf on {host.capitalize()}  {e}") from e


def start_iperf_servers(port, parallel, run, output_dir):
    try:      
        #logging.info(f"IPERF: Starting iperf server in {output_dir} with name {log_file}")
        log_file = os.path.join(output_dir, f"iperf_{port}_R{run}.json")
        processes = []
        prods = {"chi-prod": "5074", "chi-p2cs": "6666"}
        for host, port in prods.items():
            cmd = [
                "ssh", host,
                f"iperf3 -s -1 -p {port} -V --timestamp --logfile {log_file}"
            ]

            #logging.info(f"IPERF: Starting iperf server on {host.capitalize()}")
            proc = run_subprocess(cmd, text=True)
            logging.info(f"IPERF: Started iperf server on {host.capitalize()}")
            processes.append(proc)
        #return processes
        return

    except Exception as e:
        logging.error(f"IPERF: Unable to start the iperf server {e}", exc_info=True)
        raise RuntimeError(f"IPERF: Error starting iperf server  {e}\n") from e

    #{ iperf3 -s -p 5074 &   iperf3 -s -p 5075 &   iperf3 -s -p 5076 &   wait; } | ts '[%Y-%m-%d %H:%M:%S]' | tee iperf_log/$(date +%Y%m%d_%H%M%S)_prod.log
    #{ iperf3 -s -p 6666 &   wait; } | ts '[%Y-%m-%d %H:%M:%S]' | tee iperf_log/$(date +%Y%m%d_%H%M%S)_p2cs.log



def iperf_s2cs(congestion, window, parallel, duration, run, output_dir):
    try:
        port = "6666"
        s2cs_stats = []
        for neme, host in Config._S2CS_HOSTS.items():
            #output_dir = output_dir[name]
            s2cs_stats.append(run_stats(host, duration + 8, run, os.path.join(output_dir, f"stats_{port}_R{run}.json"), Config._RMT_SYS_SCRIPT))
        time.sleep(5)
        
        #s2cs_iperf("chi-c2cs", Config._P2CS_IP, "6666", congestion, win_size, parallel, duration, output_dir)
        #iperf_client("chi-c2cs", Config._P2CS_IP, "6666", congestion, window, parallel, duration, run, output_dir)
        
        log_file = os.path.join(output_dir, f"iperf_{port}_R{run}.json")
        
        cmd = [
                "ssh", "chi-c2cs",
                #f"iperf3 -c {Config._P2CS_IP} -p {port} -O 3 -R "
                f"iperf3 -c {Config._P2CS_IP} -p {port} -R "
                f"-V -Z -w {window} -P {parallel} -t {duration} "
                f"--timestamp --logfile {log_file}"
            ]

        proc = run_subprocess(cmd, text=True)
        if proc is None:
            logging.error(f"IPERF: Failed to run command on {host.capitalize()}")
            return None
        
        logging.info(f"IPERF: Started iperf between P2CS and C2CS")
        stdout, stderr = proc.communicate()
        if proc.returncode != 0:
            logging.error(f"IPERF: Failed to run iperf on {host.capitalize()}: {stderr.strip()}")
            return None
        
        for stats in s2cs_stats:
            stdout, stderr = stats.communicate()        
            """if proc.returncode != 0:
                logging.error(f"IPERF: Failed to run iperf on {host.capitalize()}: {stderr.strip()}")
                raise RuntimeError(f"IPERF: Error running iperf on {host.capitalize()}  {stderr.strip()}")"""
            logging.info("STATS: Completed System Monitor successfully")
        
        logging.info("IPERF: iperf is done.\n")
        return
    
    except Exception as e:
        logging.error(f"IPERF: Error running iperf on {host.capitalize()} {e}", exc_info=True)
        raise RuntimeError(f"IPERF: Error running iperf on {host.capitalize()}  {e}") from e




def iperf_endpoint(congestion, window, parallel, duration, run, output_dir):
    try:
        port = "5100"
        endpoint_stats = []
        for name, host in Config._ENDPOINTS.items():
            #output_dir = output_dir[name]
            endpoint_stats.append(run_stats(host, duration + 8, run, os.path.join(output_dir, f"stats_{port}_R{run}.json"), Config._RMT_SYS_SCRIPT))
            #if host == "chi-cons":
            #    cons_output_dir = output_dir       
        time.sleep(5)
        #run_iperf(Config._C2CS_IP, Config._BASE_PORT, congestion, win_size, parallel, duration, run, output_dir)
        #iperf_client("chi-cons", Config._C2CS_IP, Config._BASE_PORT, congestion, window, parallel, duration, run, output_dir)

        log_file = os.path.join(output_dir, f"iperf_{port}_R{run}.json")
        
        cmd = [
                "ssh", "chi-cons",
                #f"iperf3 -c {Config._C2CS_IP} -p {port} -O 3 -R "
                f"iperf3 -c {Config._C2CS_IP} -p {port} -R "
                f"-V -Z -w {window} -P {parallel} -t {duration} "
                f"--timestamp --logfile {log_file}"
            ]
        
        proc = run_subprocess(cmd, text=True)
        if proc is None:
            logging.error(f"IPERF: Failed to run command on {host.capitalize()}")
            return None
        logging.info(f"IPERF: Started iperf between PROD and CONS")
        time.sleep(15)
        proc.wait()
        stdout, stderr = proc.communicate()
        if proc.returncode != 0:
            logging.error(f"IPERF: Failed to run iperf on {host.capitalize()}: {stderr.strip()}")
            return None

        #checking whether the sys monitoring script is done
        for stats in endpoint_stats:
            stats.wait()
            #stdout, stderr = stats.communicate()
            """if stats.returncode != 0:
                logging.error(f"IPERF: Failed to run iperf on {host.capitalize()}: {stderr.strip()}")
                raise RuntimeError(f"IPERF: Error running iperf on {host.capitalize()}  {stderr.strip()}")"""
            logging.info("STATS: Completed System Monitor successfully")
            
        logging.info("IPERF: iperf is done.\n")
        return
    
    except Exception as e:
        logging.error(f"IPERF: Error running iperf on {host.capitalize()} {e}", exc_info=True)
        raise RuntimeError(f"IPERF: Error running iperf on {host.capitalize()}  {e}") from e



def iperf_main():
    logging.info("IPERF: Starting iperf main process \n") 
    total_runs = len(Config._TIME_FRAMES) * len(Config._CONGESTIONS) * len(Config._PROXY) * len(Config._PARALLELS) * Config._RUN_NUM * len(Config._WIN_SIZE)

    #prev_congestion = Config._CONGESTIONS[0]
    #prev_proxy = Config._PROXY[0]
    prev_congestion = None
    prev_proxy = None

    combinations = (
        (congestion, proxy, duration, parallel, window, run)
        for congestion in Config._CONGESTIONS
        for proxy in Config._PROXY
        for duration in Config._TIME_FRAMES
        for parallel in Config._PARALLELS
        for window in Config._WIN_SIZE
        for run in range(1, Config._RUN_NUM + 1)
    )

    for total_idx, (congestion, proxy, duration, parallel, window, run) in enumerate(combinations, start=1):

        if congestion != prev_congestion:
            for _, host in Config._HOSTS.items():
                if not congestion_check(host, congestion):
                    congestion_change(host, congestion)
                sys_reload(host)
                time.sleep(2)
            prev_congestion = congestion

        if proxy != prev_proxy:
            if not proxy_check(Config._S2CS_HOSTS, proxy):
                proxy_change(Config._MERROW_GLOBUS_SCRIPT, Config._S2CS_HOSTS, proxy)
            time.sleep(1)
            prev_proxy = proxy

        logging.info(f" ----- Congestion: {congestion.capitalize()}, proxy: {proxy}, Duration: {duration}, Parallel: {parallel}, Window: {window}, Run:{Config._RUN_NUM} ----- \n")
        logging.info(f"IPERF: Total: {total_idx} / {total_runs}: Run: {run} / {Config._RUN_NUM} ----------------------------- ")
        logging.info(f"TIME: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} \n")

        for host in Config._HOSTS.values():
            stop_iperf(host)
            time.sleep(2)
            #output_dir = Path(Config._HOME_DIR) / f"{proxy}" / f"{congestion}" / f"P{parallel}" / f"T{duration}" / f"R{run}"
            output_dir = Path(Config._HOME_DIR) / f"{proxy}" / f"{congestion}" / f"P{parallel}" / f"T{duration}"
            mkdir(host, output_dir)
            #output_dir[name] = outdir
        
        time.sleep(2)
        start_iperf_servers(Config._BASE_PORT, parallel, run, output_dir)

        time.sleep(2)
        iperf_endpoint(congestion, window, parallel, duration, run, output_dir)

        time.sleep(10)
        iperf_s2cs(congestion, window, parallel, duration, run, output_dir)

        if run == Config._RUN_NUM:
            logging.info(f"IPERF: Complete run {run} / {Config._RUN_NUM} ------------------------------------ \n")
            time.sleep(5)

    logging.info("All experiments complete")
    time.sleep(10)
