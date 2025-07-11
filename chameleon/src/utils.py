import subprocess, os, logging

from config import Config



def run_subprocess(cmd, text=False, shell=False):
    try:
        if shell:
            cmd = " ".join(cmd) if isinstance(cmd, list) else cmd
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=text, shell=shell)
        return proc
    except Exception as e:
        logging.error(f"Failed: {' '.join(cmd) if isinstance(cmd, list) else cmd}\n{e}")
        return None
    #NOTES: No shell=True in Popen with ssh in cmd
    #NOTES: No capture_output=True in Popen
    #NOTES: use f'bash -c"..."' instead of shell=True just to be safe


def sys_reload(host):
    try:
        if host != "local":
            cmd = ["ssh", host, "sudo", "sysctl", "-p"]
        else:
            cmd = ["sudo", "sysctl", "-p"]

        #logging.info(f"SYSRELOAD: Reloading sysctl on {host}")
        proc = run_subprocess(cmd, text=True)

        if proc is None:
            return None

        stdout, stderr = proc.communicate()
        if proc.returncode != 0:
            raise Exception(stderr.strip())

        logging.info(f"SYSRELOAD: Successfully reloaded the sysctl on {host.capitalize()}")
        #return congestion ?
        return 
    
    except Exception as e:
        logging.error(f"SYSRELOAD: Failed reloading the sysctl on {host.capitalize()}: {e}")
        raise Exception(f"SYSRELOAD: Failed reloading the sysctl on {host.capitalize()}: {e}")



def mkdir(host, directory):
    try:
        if host != "local":
            cmd = ["ssh", host, f"mkdir -p {directory}"]
        else:
            cmd = ["mkdir", "-p", directory]
        
        #logging.info(f"Creating directory {directory} on {host.capitalize()}")
        proc = run_subprocess(cmd, text=True)

        if proc is None:
            logging.error(f"UTILS: Failed to create directory {directory} on {host.capitalize()}")
            raise Exception(f"Failed to create directory {directory} on {host.capitalize()}")

        stdout, stderr = proc.communicate()
        if proc.returncode != 0:
            raise Exception(stderr.strip())

        logging.debug(f"UTILS: Successfully created directory {directory} on {host.capitalize()}")
        return

    except Exception as e:
        logging.error(f"UTILS: Failed to create directory {directory} on {host.capitalize()}: {e}")
        raise Exception(f"UTILS: Error creating directory {directory} on {host.capitalize()}: {e}")
    
    

def get_username(host):
    try:
        cmd = ["ssh", host, f"echo $USER"]
        proc = run_subprocess(cmd, text=True)
        if proc is None:
            raise Exception(f"Failed to get username for {host.capitalize()}")
        
        stdout, stderr = proc.communicate()
        if proc.returncode != 0:
            raise Exception(stderr.strip())
        return stdout.strip()
    except Exception as e:
        logging.error(f"Failed to get username: {e}")
        raise Exception(f"Error getting username: {e}")



def scp_sys_script():
    try:
        #local_sys_script = os.path.join(src_dir, "sys_monitor.py")
        local_sys_script = Config._LOCAL_SYS_SCRIPT
        if not os.path.exists(local_sys_script):
            logging.error(f"STATS: Local Script was not found at {local_sys_script}")
            raise FileNotFoundError(f"STATS: Local Script was not found at {local_sys_script}")
        for host in Config._HOSTS.values():
            remote_user = get_username(host)
            #cmd = [["scp", "sys_monitor.py", f"{remote_user}@{host}:~/"] for host in Config._HOSTS.values()]
            cmd = ["scp", local_sys_script, f"{remote_user}@{host}:/home/{remote_user}/"]
            #logging.info(f"STATS: Copying system monitor script to {host}")
            proc = run_subprocess(cmd)
            if proc is None:
                raise Exception(f"STATS: Failed to copy system monitor script to {host.capitalize()}")

            stdout, stderr = proc.communicate()
            if proc.returncode != 0:
                raise Exception(stderr.strip())

            logging.info(f"STATS: Successfully copied system monitor script to {host.capitalize()}")
        return

    except Exception as e:
        logging.error(f"STATS: Failed to copy system monitor script to {host.capitalize()}: {e}")
        raise Exception(f"STATS: Error copying system monitor script to {host.capitalize()}: {e}")



def run_stats(host, duration, run, log_file, src_dir):
    try:
        #sys_script = os.path.join(src_dir, "sys_monitor.py")
        sys_script = "~/sys_monitor.py"
        """if not os.path.exists(sys_script):
            logging.error(f"STATS: Script was not found at {sys_script}")
            raise FileNotFoundError(f"STATS: Script was not found at {sys_script}")
            return None"""
        
        stats_cmd = [
            'ssh', host,
            'timeout', str(duration + 5),
            '~/.venv/bin/python', sys_script,
            '--log_file', log_file
        ]
        proc = run_subprocess(stats_cmd)
        if proc is None:
            logging.error("STATS: Failed to start System Monitor")
            raise Exception("STATS: Failed to start System Monitor")
        else:
            logging.info(f"STATS: Started System Monitor on {host.capitalize()}")
            return proc
        
    except Exception as e:
        logging.error(f"STATS: Failed to run System Monitor:\n {e}")
        raise Exception(f"STATS: Error running System Monitor: {e}")
        return None