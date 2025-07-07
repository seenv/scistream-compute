import subprocess, socket, os, logging, time, getpass
from datetime import datetime
from pathlib import Path
from utils import run_subprocess, sys_reload, mkdir, run_stats
#import logging, warnings
from config import Config


def proxy_check(s2cs_hosts, proxy):
    try:
        """proxy_key_map = {
            "StunnelSubprocess": "stunnel /home/cc/",
            "HaproxySubprocess": "haproxy -f /home/cc/"
        }"""
        proxy_key_map = {
            "StunnelSubprocess.v1.2": "stunnel",
            "StunnelSubprocess.v1.3": "stunnel",
            "HaproxySubprocess": "haproxy",
            "Nginx": "nginx"
        }
        
        value = proxy_key_map.get(proxy)
        if not value:
            logging.error(f"PROXY: The proxy is unknown: {proxy}")
            return None

        all_active = True

        for host in s2cs_hosts.values():
            cmd = ["ssh", host,
                   #f'bash -c "ps aux | grep -i "{value}" | grep -v grep"'
                   #f'bash -c "ps aux | grep -i \'{value}\' | grep -v grep"'     # this should be correct!!!
                   f'bash -c "ps -C {value} -o comm="'
                   ]
            
            proc = run_subprocess(cmd, text=True)
            if proc is None:
                logging.error(f"PROXY: Failed to run proxy check command: {cmd} on {host.upper()}")
                raise RuntimeError(f"PROXY: Failed to run proxy check command: {cmd} on {host.upper()}")

            stdout, stderr = proc.communicate()
            match_found = False
            #for line in stdout.splitlines():
            #    if value in line and "bash -c ps aux" not in line and "grep -i" not in line:
            #        match_found = True
            #        break
            if value in stdout:
                match_found = True
                logging.info(f"PROXY: {proxy} is running on {host.upper()}")
                break
            else:
                logging.warning(f"PROXY: {proxy} is NOT running on {host.upper()}")
                all_active = False

        return all_active

    except Exception as e:
        logging.error(f"Failed to check remote proxy {proxy}: {e}")
        raise Exception(f"Error checking remote proxy {proxy}: {e}")



def change_stunnel_config(config_file):
    try:
        logging.info(f"PROXY: Changing stunnel config to {config_file}")
        stunnel_config_dir = "~/.venv/lib/python3.12/site-packages/src/s2ds"

        for host in Config._S2CS_HOSTS.values():
            cmd = ["ssh", host, f'cp {stunnel_config_dir}/{config_file} {stunnel_config_dir}/stunnel.conf.j2']
            proc = run_subprocess(cmd, text=True)
            if proc is None:
                logging.error(f"PROXY: Failed to change the stunnel config file on {host}")
                raise RuntimeError(f"PROXY: Failed to change the stunnel config file on {host}")

            stdout, stderr = proc.communicate()
            if proc.returncode != 0:
                logging.error(f"PROXY: Error changing stunnel config on {host.upper()}: {stderr.strip()}")
                raise RuntimeError(f"PROXY: Error changing stunnel config on {host.upper()}: {stderr.strip()}")
            else:
                logging.info(f"PROXY: Successfully changed stunnel config on {host.upper()}")
        return True
    except Exception as e:
        logging.error(f"PROXY: Failed to change stunnel config on {host.upper()} {e}")
        raise Exception(f"PROXY: Error changing stunnel config on {host.upper()}: {e}")




def proxy_change(globus_script, s2cs_hosts, proxy):
    #warnings.filterwarnings("ignore", category=UserWarning)
    try:
        logging.info(f"PROXY: Changing the proxy to: {proxy} from Merrow")
        hostname = socket.gethostname()
        
        if proxy =="StunnelSubprocess.v1.2":
            change_stunnel_config("stunnel.conf.j2.v1.2")
            proxy = "StunnelSubprocess"
        elif proxy == "StunnelSubprocess.v1.3":
            change_stunnel_config("stunnel.conf.j2.v1.3")
            proxy = "StunnelSubprocess"
        
        if hostname != "merrow":
            cmd = [
                "ssh",
                "merrow",
                f'bash -c "source /home/seena/Projects/globus-stream/.act-gcc && python3 {globus_script} --type {proxy}"'
            ]
        else:
            cmd = [
                "bash",
                "-c",
                f'source /home/seena/Projects/globus-stream/.act-gcc && python3 {globus_script} --type {proxy}'
            ]
        
        proc = run_subprocess(cmd, text=True)
        if proc is None:
            logging.error("PROXY: Failed to trigger globus proxy change on merrow.")
            return None

        stdout, stderr = proc.communicate()
        """cleaned_stderr = '\n'.join(
            line for line in stderr.splitlines()
            if "sandboxing" not in line.lower() or "Environment differences" not in line
        )
        if cleaned_stderr.strip():
            logging.error(f"PROXY: Errors during proxy change:\n{cleaned_stderr}")
            raise Exception(f"PROXY: Errors during proxy change:\n{cleaned_stderr}")"""
        """for line in stderr.splitlines():
            #if "The Outbound Connection is completed on the endpoint Swell" in stdout and proxy_check(s2cs_hosts, proxy):
            if "Outbound Connection is completed" in line:
                logging.info(f"PROXY: The proxy {proxy} is now started")
                return
        else:
            logging.error(f"Failed to start proxy {proxy}.\nSTDOUT: {stdout}\nSTDERR: {stderr}")
            return None"""

    except subprocess.CalledProcessError as e:
        logging.error(f"PROXY: Error changing proxy to {proxy}:\n{e}\n")
        raise Exception(f"PROXY: Error changing proxy to {proxy}: {e}\n")



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
        for host in s2cs_hosts.values():
            #logging.info(f"PROXY: Checking the active proxy on {host} for {proxy}")
            cmd = ["ssh", host,
                   f'bash -c "ps aux | grep -i "{value}" | grep -v grep"'       
                   ] # this should be correct: grep -i \'{value}\'
            proc = run_subprocess(cmd, text=True,  capture_output=False)
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