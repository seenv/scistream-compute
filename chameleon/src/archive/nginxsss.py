import subprocess, socket, os, logging, time, getpass
from datetime import datetime
from pathlib import Path
from utils import run_subprocess, sys_reload, mkdir, run_stats
import logging
from config import Config
from congestion import congestion_check, congestion_change
from proxy import proxy_check, proxy_change

def nginx_start_iperf_server(exp_dir):
    try:
        exp_name = os.path.basename(exp_dir)
        logging.info(f"IPERF: Starting iperf server in {exp_dir} with name {exp_name}")
        srv_cmds = {
            "chi-prod": [
                "ssh", "chi-prod",
                f"bash -c \"(iperf3 -s -1 -p 5074 & "
                f"iperf3 -s -1 -p 5075 & "
                f"iperf3 -s -1 -p 5076) 2>&1 | "
                f"ts '[%Y-%m-%d %H:%M:%S]' | tee {exp_dir}/{exp_name}_prod.log\""
            ],
            "chi-p2cs": [
                "ssh", "chi-p2cs",
                f"bash -c \"iperf3 -s -1 -p 6666 2>&1 | "
                f"ts '[%Y-%m-%d %H:%M:%S]' | tee {exp_dir}/{exp_name}_p2cs.log\""
            ]
        }
        srv_procs = []
        for host, cmd in srv_cmds.items():
            mkdir(host, exp_dir)
            logging.info(f"IPERF: Starting iperf server on {host}")
            proc = run_subprocess(cmd, check=True,text=True)
            srv_procs.append(proc)
        return srv_procs
    except Exception as e:
        logging.error(f"IPERF: Unable to start the iperf server", exc_info=True)
        raise RuntimeError(f"IPERF: Error starting iperf server\n") from e

    #{ iperf3 -s -p 5074 &   iperf3 -s -p 5075 &   iperf3 -s -p 5076 &   wait; } | ts '[%Y-%m-%d %H:%M:%S]' | tee iperf_log/$(date +%Y%m%d_%H%M%S)_prod.log
    #{ iperf3 -s -p 6666 &   wait; } | ts '[%Y-%m-%d %H:%M:%S]' | tee iperf_log/$(date +%Y%m%d_%H%M%S)_p2cs.log


def nginx_run_iperf(c2cs_ip, port, congestion, window, parallel, duration, run, output_dir):
    try:
        log_file = os.path.join(output_dir, f"iperf_{port}_R{run}.json")
        logging.info(f"IPERF: Starting iperf on port {port} with congestion {congestion}, window {window}, parallel {parallel}, duration {duration} seconds")
        """iperf_cmd = [
            'iperf3', '-c', c2cs_ip,
            '-p', str(port),
            '-C', str(congestion),
            '-O', '3',
            '-b', '0',  # unlimited bandwidth by default for TCP
            '-R',
            '-Z',
            '-w', window,
            '--fq-rate', '0',
            '-P', str(parallel),
            '-t', str(duration),
            '--timestamp',
            '-J',
            '--logfile', log_file
        ]"""
        iperf_cmd = [
            'iperf3', '-c', c2cs_ip,
            '-p', str(port),
            '-O', '3',
            '-R',
            '-Z',
            '-w', window,
            '-P', str(parallel),
            '-t', str(duration),
            '--timestamp',
            #'-J',
            '--logfile', log_file
        ]
        #return run_subprocess(iperf_cmd)
        proc = run_subprocess(iperf_cmd, text=True)
        if proc is None:
            logging.error("IPERF: Failed to start iperf")
            return None

        stdout, stderr = proc.communicate()
        if proc.returncode != 0:
            logging.error(f"IPERF: Failed running iperf: {stderr.strip()} \n")
            raise Exception(f"IPERF: Error running iperf command: {stderr.strip()} \n")
        
        logging.info(f"IPERF: Successfully ran iperf")
        return
    except Exception as e:
        logging.error(f"IPERF: Failed to run iperf command", exc_info=True)
        raise RuntimeError(f"IPERF: Error running iperf command") from e


def nginx_s2cs_iperf(s2cs_host, p2cs_ip, port, congestion, window, parallel, duration, output_dir):
    try:
        log_file = os.path.join(output_dir, f"nginx_s2cs_iperf.json")
        
        dir_cmd = [
            "ssh",
            s2cs_host,
            f"mkdir -p {output_dir}"
        ]

        """iperf_cmd = [
            "ssh",
            s2cs_host,
            f"iperf3 -c {p2cs_ip} -p {port} -C {congestion} -O 3 -R -Z "
            f"-w {window} --fq-rate 0 -P {parallel} -t 10 -J "
            f"--logfile {log_file}"
        ]"""
        iperf_cmd = [
            "ssh",
            s2cs_host,
            f"iperf3 -c {p2cs_ip} -p {port} -O 3 -R -Z "
            f"-w {window} -P {parallel} -t 10 -J "
            f"--logfile {log_file}"
        ]
        
        logging.info("IPERF: Starting iperf between P2CS and C2CS")
        cmds = [dir_cmd, iperf_cmd]
        
        proc_dir = run_subprocess(dir_cmd, text=True)
        if proc_dir is None:
            logging.error(f"IPERF: Failed to run command on {s2cs_host}")
            return None
        stdout, stderr = proc_dir.communicate()

        if proc_dir.returncode != 0:
            logging.error(f"IPERF: Failed to create directory on {s2cs_host}: {stderr.strip()}")
            return None

        proc_iperf = run_subprocess(iperf_cmd, text=True)
        if proc_iperf is None:
            logging.error(f"IPERF: Failed to run command on {s2cs_host}")
            return None
        stdout, stderr = proc_iperf.communicate()

        if proc_iperf.returncode != 0:
            logging.error(f"IPERF: Failed to run iperf on {s2cs_host}: {stderr.strip()}")
            return None

        logging.info("IPERF: Done between P2CS and C2CS\n")
    
    except Exception as e:
        logging.error(f"IPERF: Error running iperf on {s2cs_host}", exc_info=True)
        raise RuntimeError(f"IPERF: Error running iperf on {s2cs_host}") from e






def nginx_main():
    
    logging.info("IPERF: Starting iperf main process ")
    """for host in Config._ENDPOINTS:
        logging.info("IPERF: CLEANING THE CONTAINERS")
        prune_containers(host)
        time.sleep(2)"""

    total_runs = len(Config._TIME_FRAMES) * len(Config._CONGESTIONS) * len(Config._SCISTREAMS) * len(Config._PARALLELS) * Config._RUN_NUM * len(Config._WIN_SIZE)

    prev_congestion = None
    prev_protocol = None

    combinations = (
        (congestion, protocol, duration, parallel, win_size, run)
        for congestion in Config._CONGESTIONS
        for protocol in Config._SCISTREAMS
        for duration in Config._TIME_FRAMES
        for parallel in Config._PARALLELS
        for win_size in Config._WIN_SIZE
        for run in range(1, Config._RUN_NUM + 1)
    )

    for total_idx, (congestion, protocol, duration, parallel, win_size, run) in enumerate(combinations, start=1):

        if congestion != prev_congestion:
            for host in Config._HOSTS:
                if not congestion_check(host, congestion):
                    congestion_change(host, congestion)
                sys_reload(host)
                time.sleep(2)
            prev_congestion = congestion

        """if protocol != prev_protocol:
            if not proxy_check(Config._S2CS_HOSTS, protocol):
                proxy_change(Config._MERROW_GLOBUS_SCRIPT, Config._S2CS_HOSTS, protocol)
                time.sleep(1)
            prev_protocol = protocol"""

        logging.info(f"----- Congestion: {congestion.capitalize()}, Protocol: {protocol}, Duration: {duration}, Parallel: {parallel}, Window: {win_size}, Run:{Config._RUN_NUM} -----")
        logging.info(f"IPERF: Total: {total_idx} / {total_runs}: Run: {run} / {Config._RUN_NUM} ----------------------------- ")
        logging.info(f"TIME: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        #app_dir = Path(Config._HOME_DIR) / f"{Config._APP}" / f"{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}"
        #output_dir = Path(app_dir) / f"{congestion}" / f"{protocol}" / f"P{parallel}" / f"T{duration}"
        output_dir = Path(Config._HOME_DIR) / f"{protocol}" / f"{congestion}" / f"P{parallel}" / f"T{duration}" / f"R{run}"
        output_dir.mkdir(parents=True, exist_ok=True)

        stats_proc = run_stats(duration + 4, run, output_dir, Config._SRC_DIR)
        time.sleep(1)
        nginx_run_iperf(Config._C2CS_IP, Config._BASE_PORT, congestion, win_size, parallel, duration, run, output_dir)

        stdout, stderr = stats_proc.communicate()
        logging.info("STATS: Completed System Monitor successfully.")

        time.sleep(5)

        nginx_s2cs_iperf("chi-c2cs", Config._P2CS_IP, "6666", congestion, win_size, parallel, duration, output_dir)
        time.sleep(5)

        if run == Config._RUN_NUM:
            logging.info(f"IPERF: Complete run {run} / {Config._RUN_NUM} ------------------------------------ ")
            time.sleep(5)

    logging.info("All experiments complete.")
    time.sleep(10)









    

