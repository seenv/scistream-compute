import subprocess, socket, os, logging, time, getpass
from datetime import datetime
from pathlib import Path
from utils import run_subprocess, sys_reload, mkdir, run_stats
import logging



def status_globus_endpoint(host, name):
    cmd = [
        "ssh", host,
        f'bash -c "source /home/cc/.activate && globus-compute-endpoint list 2>&1; echo OUTPUT_CODE:$?"'
    ]
    proc = run_subprocess(cmd, text=True)
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
                proc = run_subprocess(cmd, text=True)
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
    
    

        
        
        




    

