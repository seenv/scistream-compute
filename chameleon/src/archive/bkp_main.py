import subprocess
import socket
import os
import logging
import time
from datetime import datetime




# ─── CONFIG ─────────────────────────────────────────────────────────────
_C2CS_IP = '10.52.3.109'
_P2CS_IP = '192.5.87.71'
_BASE_PORT = 5100
_MERROW_GLOBUS_SCRIPT = "/home/seena/Projects/globus-stream/scistream-compute/src/main.py"

hosts = ["local", "chi-c2cs", "chi-prod", "chi-p2cs"]
s2cs_hosts = {"c2cs": "chi-c2cs", "p2cs": "chi-p2cs"}

#_CONGESTIONS = ['cubic', 'bbr']                                     # ['cubic', 'reno', 'bbr']
#_SCISTREAMS = ['StunnelSubprocess', 'HaproxySubprocess']
#_TIME_FRAMES = [30]                 #, 30, 60]                  # [10, 30, 60, 100]
#_PORT_MAP = {1: 3, 3: 1}            #{1: 3, 3: 1} 
#_BAND = ["0", "10G"]                # ['0', '10G']             '-b', str(bandwidth),



_RUN_NUM = 1
_PARALLELS = [1,3] 
_TIME_FRAMES = [10]     
_WIN_SIZE = ["0"]
_SCISTREAMS = ['StunnelSubprocess']
_CONGESTIONS = ['cubic']
_HOME_DIR = os.path.expanduser(f'~/experiments/{datetime.now().strftime("%Y-%m-%d_%H-%M")}')




# Running iperf:
#1:
#TLS.v1.2
"""_RUN_NUM = 5
_PARALLELS = [1, 3] 
_TIME_FRAMES = [30]     
_WIN_SIZE = ["0"]
_SCISTREAMS = ['StunnelSubprocess']
_CONGESTIONS = ['cubic']
_HOME_DIR = os.path.expanduser(f'~/experiments/{datetime.now().strftime("%Y-%m-%d_%H:%M:%S")}')"""
#2:
"""_RUN_NUM = 5
_PARALLELS = [1, 3] 
_TIME_FRAMES = [30]     
_WIN_SIZE = ["0"]
_SCISTREAMS = ['StunnelSubprocess']
_CONGESTIONS = ['bbr']
_HOME_DIR = os.path.expanduser(f'~/experiments/{datetime.now().strftime("%Y-%m-%d_%H:%M:%S")}')"""

#3:
#TLS.v1.3
"""_RUN_NUM = 5
_PARALLELS = [1, 3] 
_TIME_FRAMES = [30]     
_WIN_SIZE = ["0"]
_SCISTREAMS = ['StunnelSubprocess']
_CONGESTIONS = ['cubic']
_HOME_DIR = os.path.expanduser(f'~/experiments/{datetime.now().strftime("%Y-%m-%d_%H:%M:%S")}')"""

#4:
"""_RUN_NUM = 5
_PARALLELS = [1, 3] 
_TIME_FRAMES = [30]     
_WIN_SIZE = ["0"]
_SCISTREAMS = ['StunnelSubprocess']
_CONGESTIONS = ['bbr']
_HOME_DIR = os.path.expanduser(f'~/experiments/{datetime.now().strftime("%Y-%m-%d_%H:%M:%S")}')"""

#3:
#TLS.v1.2
"""_RUN_NUM = 5
_PARALLELS = [1, 3] 
_TIME_FRAMES = [30]     
_WIN_SIZE = ["64"]"""

#4:
#TLS.v1.3
"""_RUN_NUM = 5
_PARALLELS = [1, 3] 
_TIME_FRAMES = [30]     
_WIN_SIZE = ["64"]"""

# Running mini-app:
#1:
#TLS.v1.2
"""_RUN_NUM = 5
_PARALLELS = [1, 3] 
_TIME_FRAMES = [30]     
_WIN_SIZE = ["0"]"""

#2:
#TLS.v1.3
"""_RUN_NUM = 5
_PARALLELS = [1, 3] 
_TIME_FRAMES = [30]     
_WIN_SIZE = ["0"]"""

#6:





logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')
username = os.getlogin()
_HOME_DIR = os.path.expanduser(f'~/experiments/{datetime.now().strftime("%Y-%m-%d_%H:%M:%S")}')
_SRC_DIR = os.path.expanduser('~/code')



total = len(_TIME_FRAMES) * len(_CONGESTIONS) * len(_SCISTREAMS) * len(_PARALLELS) * _RUN_NUM * len(_WIN_SIZE)



# ─── funcs─────────────────────────────────────────────────────
def run_subprocess(cmd, text=False, shell=False, capture_output=True):
    try:
        if shell:
            cmd = " ".join(cmd) if isinstance(cmd, list) else cmd
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=text,
            shell=shell
        )
        return proc
    except Exception as e:
        logging.error(f"Failed: {' '.join(cmd) if isinstance(cmd, list) else cmd}\n{e}")
        return None


def sys_reload(host):
    try:
        if host != "local":
            cmd = ["ssh", host, "sudo", "sysctl", "-p"]
        else:
            cmd = ["sudo", "sysctl", "-p"]

        logging.info(f"SYSRELOAD: Reloading sysctl on {host}")
        proc = run_subprocess(cmd, text=True)

        if proc is None:
            return None

        stdout, stderr = proc.communicate()
        if proc.returncode != 0:
            raise Exception(stderr.strip())

        logging.info(f"SYSRELOAD: Successfully reloaded the sysctl on {host} \n")
        #return congestion ?
        return 
    
    except Exception as e:
        logging.error(f"SYSRELOAD: Failed reloading the sysctl on {host}: {e}")
        raise Exception(f"SYSRELOAD: Failed reloading the sysctl on {host}: {e}")
    
            
            
            
"""def proxy_check(proxy):
    try:
        proxy_key_map = {
            "StunnelSubprocess": "stunnel /home/cc/",
            "HaproxySubprocess": "haproxy -f /home/cc/"
        }

        value = proxy_key_map.get(proxy)
        #print(f"value: {value}, proxy: {proxy}")
        if not value:
            logging.error(f"PROXY: Unknown proxy type: {proxy}")
            return None
        for name, host in s2cs_hosts.items():
            #logging.info(f"PROXY: Checking the active proxy on {host} for {proxy}")
            cmd = ["ssh", host,
                   f'bash -c "ps aux | grep -i "{value}" | grep -v grep"'       
                   ] # this should be correct: grep -i \'{value}\'
            proc = run_subprocess(cmd, text=True, capture_output=True)
            if proc is None:
                logging.error(f"PROXY: Failed to run proxy check command: {cmd} on {host}")
                raise

            stdout, stderr = proc.communicate() 
            #print(f"stdout: {stdout}, stderr: {stderr}")
            for line in stdout.splitlines():
                if value in line and "bash -c ps aux" not in line and "grep -i" not in line:
                    logging.info(f"PROXY: The active proxy is {proxy} on both s2cs's: \n{line.strip()}")
                    return True

            logging.warning(f"PROXY: The active proxy is not {proxy} on {host}. Expected: {value}, Found: {stdout.strip()}")
            return False

    except Exception as e:
        logging.error(f"Failed to check remote proxy {proxy}: {e}")
        raise Exception(f"Error checking remote proxy {proxy}: {e}")"""


def proxy_check(proxy):
    try:
        proxy_key_map = {
            "StunnelSubprocess": "stunnel /home/cc/",
            "HaproxySubprocess": "haproxy -f /home/cc/"
        }

        value = proxy_key_map.get(proxy)
        if not value:
            logging.error(f"PROXY: Unknown proxy type: {proxy}")
            return None

        all_active = True

        for name, host in s2cs_hosts.items():
            cmd = ["ssh", host,
                   #f'bash -c "ps aux | grep -i "{value}" | grep -v grep"'
                   f'bash -c "ps aux | grep -i \'{value}\' | grep -v grep"'     # this should be correct!!!
                   ]
            proc = run_subprocess(cmd, text=True, capture_output=True)
            if proc is None:
                logging.error(f"PROXY: Failed to run proxy check command: {cmd} on {host}")
                raise

            stdout, stderr = proc.communicate()
            match_found = False
            for line in stdout.splitlines():
                if value in line and "bash -c ps aux" not in line and "grep -i" not in line:
                    match_found = True
                    break

            if match_found:
                logging.info(f"PROXY: {proxy} is running on {host}")
            else:
                logging.warning(f"PROXY: {proxy} is NOT running on {host}. Expected: {value}, Got: {stdout.strip()}")
                all_active = False

        return all_active

    except Exception as e:
        logging.error(f"Failed to check remote proxy {proxy}: {e}")
        raise Exception(f"Error checking remote proxy {proxy}: {e}")


def proxy_change(globus_script, proxy):
    try:
        logging.info(f"PROXY: Changing the s2cs proxy to: {proxy} from merrow")
        cmd = [
            "ssh",
            "merrow",
            f'bash -c "source /home/seena/Projects/globus-stream/.act-gcc && python3 {globus_script} --type {proxy}"'
        ]

        proc = run_subprocess(cmd, text=True)
        if proc is None:
            logging.error("PROXY: Failed to trigger globus proxy change on merrow.")
            return None

        stdout, stderr = proc.communicate()
        stdout, stderr = stdout.strip(), stderr.strip()

        if "The Outbound Connection is completed on the endpoint Swell" in stdout and proxy_check(proxy):
            logging.info(f"PROXY: The proxy {proxy} is now started")
            return
        else:
            logging.error(f"Failed to start proxy {proxy}.\nSTDOUT: {stdout}\nSTDERR: {stderr}")
            raise
    except subprocess.CalledProcessError as e:
        logging.error(f"PROXY: Error changing proxy to {proxy}:\n{e}\n")
        raise Exception(f"PROXY: Error changing proxy to {proxy}: {e}\n")
    


def status_globus_endpoint(host, name):
    cmd = [
        "ssh", host,
        f'bash -c "source /home/cc/.activate && globus-compute-endpoint list 2>&1; echo OUTPUT_CODE:$?"'
    ]
    proc = run_subprocess(cmd, text=True, capture_output=True)
    if not proc:
        raise RuntimeError(f"GLOBUS: Failed to get the status of endpoint {name.upper()} on {host.upper()}")
    stdout, stderr = proc.communicate()
    if proc.returncode != 0:
        raise RuntimeError(f"GLOBUS: Failed to get the status of endpoint {name.upper()} on {host.upper()}")

    if f"Running | {name}" in stdout:
        logging.info(f"GLOBUS: Endpoint {name.upper()} is running on host {host.upper()}")
        return ["stop", "start"]
    elif any(status in stdout for status in [f"Stopped | {name}", f"Disconnected | {name}"]):
        logging.info(f"GLOBUS: Endpoint {name.upper()} is not running on host {host.upper()}")
        return ["start"]
    else:
        logging.warning(f"GLOBUS: Failed getting endpoints status:\n{e}\n")
        return []
    
    
    
def restart_globus_endpoints():
    try:
        processes = []
        for name, host in s2cs_hosts.items():
            phases = status_globus_endpoint(host, name)
            for phase in phases:
                cmd = [
                    "ssh", host,
                    f'bash -c "source /home/cc/.activate && globus-compute-endpoint {phase} {name} 2>&1 &"'
                ]
                logging.info(f"GLOBUS: {phase.capitalize()} the endpoint {name.upper()} on {host.upper()}")
                proc = run_subprocess(cmd, text=True, capture_output=True)
                if not proc:
                    raise RuntimeError(f"GLOBUS: Failed to {phase.capitalize()} the endpoint {name.upper()} on {host.upper()}")
                stdout, stderr = proc.communicate()
                if proc.returncode != 0:
                    raise RuntimeError(f"GLOBUS: Failed to {phase.capitalize()} the endpoint {name.upper()} on {host.upper()}")

                logging.info(f"GLOBUS: Successfully {phase.capitalize()} the endpoint {name.upper()} on {host.upper()}\n")
        return True

    except Exception as e:
        logging.error(f"GLOBUS: Failed restarting the endpoints:\n{e}\n")
        raise



def congestion_check(host, congestion):
    try:
        if host != "local":
            cmd = ["ssh", host, "sysctl", "net.ipv4.tcp_congestion_control"]
        else:
            cmd = ["sysctl", "net.ipv4.tcp_congestion_control"]

        proc = run_subprocess(cmd, text=True)

        if proc is None:
            raise Exception(f"CONGESTION: Failed to run command on {host}. Command: {' '.join(cmd)}")

        stdout, stderr = proc.communicate()
        if proc.returncode != 0:
            raise Exception(stderr.strip())

        current = stdout.split('=')[1].strip()
        logging.info(f"CONGESTION: Congestion control on {host}:    current {current},     expected: {congestion}")
        return True if congestion == current else False
    
    except Exception as e:
        logging.error(f"CONGESTION: Failed checking congestion control on {host}: {e} \n")
        raise Exception(f"CONGESTION: Error checking congestion control on {host}: {e} \n")



def congestion_change(host, congestion):
    try:
        if host != "local":
            cmd = ["ssh", host, "sudo", "sysctl", f"net.ipv4.tcp_congestion_control={congestion}"]
        else:
            cmd = ["sudo", "sysctl", f"net.ipv4.tcp_congestion_control={congestion}"]
        
        logging.info(f"CONGESTION: Setting congestion control to {congestion} on {host}.")
        proc = run_subprocess(cmd, text=True)

        if proc is None:
            return None

        stdout, stderr = proc.communicate()
        if proc.returncode != 0:
            raise Exception(stderr.strip())

        logging.info(f"CONGESTION: Successfully set congestion control to {stdout.strip()} on {host} \n")
        #return congestion ?
        return 

    except Exception as e:
        logging.error(f"CONGESTION: Failed switching to {congestion}:\n {e} \n")
        raise Exception(f"CONGESTION: Error changing congestion control: {e} \n")



def mkdir(host, exp_dir):
    try:
        if host != "local":
            cmd = ["ssh", host, f"mkdir -p {exp_dir}"]
        else:
            cmd = ["mkdir", "-p", exp_dir]
        
        logging.info(f"Creating directory {exp_dir} on {host}.")
        proc = run_subprocess(cmd, text=True)

        if proc is None:
            raise Exception(f"Failed to create directory {exp_dir} on {host}")

        stdout, stderr = proc.communicate()
        if proc.returncode != 0:
            raise Exception(stderr.strip())

        logging.info(f"Successfully created directory {exp_dir} on {host}.")
        return

    except Exception as e:
        logging.error(f"Failed to create directory {exp_dir} on {host}: {e}")
        raise Exception(f"Error creating directory {exp_dir} on {host}: {e}")
    
    

def start_iperf_server(exp_dir):
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
        logging.error(f"IPERF: Unable to start the iperf server:\n {e} \n")
        raise Exception(f"IPERF: Error starting iperf server: {e} \n")
    
    #{ iperf3 -s -p 5074 &   iperf3 -s -p 5075 &   iperf3 -s -p 5076 &   wait; } | ts '[%Y-%m-%d %H:%M:%S]' | tee experiments/$(date +%Y%m%d_%H%M%S)_prod.log
    #{ iperf3 -s -p 6666 &   wait; } | ts '[%Y-%m-%d %H:%M:%S]' | tee experiments/$(date +%Y%m%d_%H%M%S)_p2cs.log
    
    
def run_stats(duration, run, output_dir, src_dir):
    try:
        sys_script = os.path.join(src_dir, "sys_monitor.py")
        if not os.path.exists(sys_script):
            logging.error(f"STATS: Script was not found at {sys_script}")
            raise FileNotFoundError(f"STATS: Script was not found at {sys_script}")
            return None
        
        stats_cmd = [
            'timeout', str(duration + 3),
            'python3',
            sys_script,
            '--output_dir',
            output_dir
        ]
        proc = run_subprocess(stats_cmd)
        if proc is None:
            logging.error("STATS: Failed to start System Monitor.")
            raise
        else:
            logging.info("STATS: Started System Monitor in background.")
            return proc
    except Exception as e:
        logging.error(f"STATS: Failed to run System Monitor:\n {e} \n")
        raise Exception(f"STATS: Error running System Monitor: {e} \n")
        return None
    

def run_iperf(c2cs_ip, port, congestion, window, parallel, duration, output_dir):
    try:
        log_file = os.path.join(output_dir, f"iperf_{port}.json")
        logging.info(f"IPERF: Starting iperf on port {port} with congestion {congestion}, window {window}, parallel {parallel}, duration {duration} seconds")
        """iperf_cmd = [
            'iperf3', '-c', c2cs_ip,
            '-p', str(port),
            '-C', str(congestion),
            '-O', '3',
            '-R',
            '-Z',
            '-w', window,
            '--fq-rate', '0',
            '-P', str(parallel),
            '-t', str(duration),
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
            '-J',
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
        logging.error(f"IPERF: Failed to run iperf command {e}")
        raise Exception(f"IPERF: Error running iperf command {e}")




def s2cs_iperf(s2cs_host, p2cs_ip, port, congestion, window, parallel, duration, output_dir):
    try:
        log_file = os.path.join(output_dir, f"s2cs_iperf.json")
        
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
        logging.error(f"IPERF: Error running iperf on {s2cs_host} remote host: {e}")
        raise

    
    
# ─── MAIN ───────────────────────────────────────────────────────────────
def main():
    logging.info(f"MAIN: Starting the main process...\n")
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    #restart_globus_endpoints()
    #print(f"starting proxy check...")
    #curr_proxy = proxy_check(_SCISTREAMS[0])
    #print(f"current proxy is {curr_proxy}")
    #if not curr_proxy:
    #    print(f"current proxy is not {_SCISTREAMS[0]}, changing it now...")
    #else: 
    #    print(f"current proxy is {_SCISTREAMS[0]}, no need to change it.")
    #   proxy_change(_MERROW_GLOBUS_SCRIPT, _SCISTREAMS[0]) if not curr_proxy else None
    #   logging.info(f"MAIN: Current proxy is already {_SCISTREAMS[0]}.")
    #proxy_change(_MERROW_GLOBUS_SCRIPT, _SCISTREAMS[0]) if not proxy_check(_SCISTREAMS[0]) else None
    proxy_change(_MERROW_GLOBUS_SCRIPT, _SCISTREAMS[0])
    time.sleep(2)
    
        
    cnt = 1
    for cng, congestion in enumerate(_CONGESTIONS):
        for host in hosts:
            congestion_change(host, congestion) if not congestion_check(host, congestion) else None
            sys_reload(host)
            time.sleep(2)
            
        for ptl, protocol in enumerate(_SCISTREAMS):
            for duration in _TIME_FRAMES:
                for parallel in _PARALLELS:
                    #for bandwidth in _BAND:
                    for win_size in _WIN_SIZE:

                        logging.info(f"----- Congestion: {congestion}, Protocol: {protocol}, Duration: {duration}, Parallel: {parallel}, Window: {win_size}, Run:{_RUN_NUM} -----\n")
                        #logging.info(f"Address: \"{congestion}_{protocol}/P{parallel}/W{win_size}/T{duration}_R{_RUN_NUM}\" \n")

                        for run in range(1, _RUN_NUM + 1):
                            logging.info(f"IPERF: Total: {cnt} / {total}: Run: {run} / {_RUN_NUM}: {congestion}_{protocol}/P{parallel}/W{win_size}/T{duration}_R{run}\" ")
                            logging.info(f"TIME: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                            cnt += 1
                            #ports = [_BASE_PORT + offset for offset in range(_PORT_MAP[parallel])]

                            output_dir = os.path.join(_HOME_DIR, f"{congestion}_{protocol}", f"P{parallel}", f"T{duration}_R{run}")
                            os.makedirs(output_dir, exist_ok=True)

                            stats_proc = run_stats(duration + 3, run, output_dir, _SRC_DIR)
                            run_iperf(_C2CS_IP, _BASE_PORT, congestion, win_size, parallel, duration, output_dir)
                            """processes = [run_iperf(_C2CS_IP, port, congestion, win_size, parallel, duration, output_dir) for port in ports]
                            if any(proc is None for proc in processes):
                                logging.error("IPERF: Failed to start one or more iperf processes.")
                                for proc in processes:
                                    if proc is not None:
                                        proc.terminate() 
                                continue
                            logging.info("IPERF: Finished running iperf processes.")

                            stdout_stderr = [proc.communicate() for proc in processes]

                            for proc, (stdout, stderr) in zip(processes, stdout_stderr):
                                if proc.returncode != 0:
                                    logging.error(f"IPERF: Failed running iperf: {stderr.decode().strip()} \n")
                                    proc.terminate()
                                    continue"""
                            
                            """processes = []
                            for port in ports:
                                iperf_proc = run_iperf(_C2CS_IP, port, congestion, parallel, duration, output_dir)
                                if iperf_proc:
                                    processes.append(iperf_proc)

                            for proc in processes:
                                stdout, stderr = proc.communicate()
                                # need to stop stats_proc when iperf_proc is done or run it with timeout!
                                if proc.returncode != 0:
                                    logging.info(f"IPERF: Failed: {stderr.decode().strip()} \n")"""

                            stdout, stderr = stats_proc.communicate()
                            #if stats_proc.returncode != 0:
                            #    logging.error(f"STATS: Failed running System Monitor:\n{stderr.decode()} \n")
                            #else:
                            logging.info("STATS: Completed System Monitor successfully. \n")
                            time.sleep(5)

                            # run an iperf between the two s2cs's
                            s2cs_iperf("chi-c2cs", _P2CS_IP, "6666", congestion, win_size, parallel, duration, output_dir)
                            time.sleep(5)

                        logging.info(f"IPERF: Complete run {run} / {_RUN_NUM + 1}: {congestion}_{protocol}/P{parallel}/W{win_size}/T{duration}_R{_RUN_NUM}\" \n")
                        time.sleep(5)
                    
            if protocol != _SCISTREAMS[-1]:
                proxy_change(_MERROW_GLOBUS_SCRIPT, _SCISTREAMS[ptl + 1]) if not proxy_check(_SCISTREAMS[ptl + 1]) else None
                #restart_globus_endpoints()
                time.sleep(2)
                
        #if cng + 1 < len(_CONGESTIONS):
        if congestion != _CONGESTIONS[-1]:
            proxy_change(_MERROW_GLOBUS_SCRIPT, _SCISTREAMS[0]) if not proxy_check(_SCISTREAMS[0]) else None
            time.sleep(2)

            #congestion = _CONGESTIONS[cng + 1]
            #for host in hosts:
            #    congestion_change(host, _CONGESTIONS[cng + 1])
            #    time.sleep(2)
            #    sys_reload(host)

    time.sleep(10)

    s.close()
    logging.info("All experiments complete.")

if __name__ == "__main__":
    main()
    