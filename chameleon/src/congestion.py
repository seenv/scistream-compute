import subprocess, socket, os, logging, time, getpass
from datetime import datetime
from pathlib import Path
from utils import run_subprocess, sys_reload, mkdir, run_stats
import logging


def congestion_check(host, congestion):
    try:
        if host != "local":
            cmd = ["ssh", host, "sysctl", "net.ipv4.tcp_congestion_control"]
        else:
            cmd = ["sysctl", "net.ipv4.tcp_congestion_control"]

        proc = run_subprocess(cmd, text=True)

        if proc is None:
            raise Exception(f"CONGESTION: Failed to run command on {host.upper()}")

        stdout, stderr = proc.communicate()
        if proc.returncode != 0:
            raise Exception(stderr.strip())

        current = stdout.split('=')[1].strip()
        logging.info(f"CONGESTION: Congestion control on {host.upper()}:    current {current.upper()},     expected: {congestion.upper()}")
        return True if congestion == current else False
    
    except Exception as e:
        logging.error(f"CONGESTION: Failed checking congestion control on {host.upper()}: {e} \n")
        raise Exception(f"CONGESTION: Error checking congestion control on {host.upper()}: {e} \n")



def congestion_change(host, congestion):
    try:
        if host != "local":
            cmd = ["ssh", host, "sudo", "sysctl", f"net.ipv4.tcp_congestion_control={congestion}"]
        else:
            cmd = ["sudo", "sysctl", f"net.ipv4.tcp_congestion_control={congestion}"]

        logging.info(f"CONGESTION: Setting congestion control to {congestion.upper()} on {host.upper()}.")
        proc = run_subprocess(cmd, text=True)

        if proc is None:
            return None

        stdout, stderr = proc.communicate()
        if proc.returncode != 0:
            raise Exception(stderr.strip())

        logging.info(f"CONGESTION: Successfully set congestion control to {stdout.strip()} on {host.upper()}")
        #return congestion ?
        return 

    except Exception as e:
        logging.error(f"CONGESTION: Failed switching to {congestion.upper()} on {host.upper()}:\n {e} \n")
        raise Exception(f"CONGESTION: Error changing congestion control: {e} \n")



