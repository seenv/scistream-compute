import argparse
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from globus_compute_sdk import Client 
from endpoints import p2cs, c2cs, pub, con


def get_args():
    argparser = argparse.ArgumentParser(description="arguments")
    argparser.add_argument('--sync-port', help="syncronization port",default="5007")
    argparser.add_argument('--p2cs-listener', help="listerner's IP of p2cs", default="128.135.24.119")
    argparser.add_argument('--p2cs-ip', help="IP address of the s2cs on producer side", default="128.135.164.119")
    argparser.add_argument('--type', help= "proxy type", default="Haproxy")
    argparser.add_argument('--c2cs-listener', help="listerner's IP of c2cs", default="128.135.24.120")
    argparser.add_argument('--c2cs_ip', help="IP address of the s2cs on consumer side", default='128.135.164.120')
    argparser.add_argument('--prod-ip', help="producer's IP address", default='128.135.24.117')
    #argparser.add_argument('--cons-ip', help="consumer's IP address", default="128.135.24.118")

    return argparser.parse_args()


def get_ep_stat(gcc, uuid, name):
    from globus_compute_sdk import Executor, ShellFunction, Client

    command = "globus-compute-endpoint list "
    shell_function = ShellFunction(command, walltime=30)
    with Executor(endpoint_id=uuid)as gce:
        future = gce.submit(shell_function)
    try:
        result = future.result(timeout=10)
        print(f"Endpoint {name.capitalize()} Status: \n{result.stdout}", flush=True)
        cln_stderr = "\n".join(line for line in result.stderr.split("\n") if "WARNING" not in line)
        if cln_stderr.strip():
            print(f"Stderr: {cln_stderr}", flush=True)
    except Exception as e:
        print(f"Getting EP Status failed: {e}")



def get_uuid(client, name):
    try:
        endpoints = client.get_endpoints()
        for ep in endpoints:
            endpoint_name = ep.get('name', '').strip()
            if endpoint_name == name.strip().lower():
                #print(f"DEBUG:EndPoint: {name} with UUID: {ep.get('uuid')}")
                get_ep_stat(client, ep.get('uuid'), str(name))
                return ep.get('uuid')
    except Exception as e:
        print(f"error fetching {name}: {str(e)}")
    return None


if __name__ == "__main__":

    gcc = Client()
    args = get_args()

    ep_funcs = {"that": p2cs, "neat": c2cs, "this": pub, "swell": con}

    threads = {}
    # iterate over ep_funcs (keys = endpoint names, values = functions)
    for ep_name, func in ep_funcs.items():
        uuid = get_uuid(gcc, ep_name)
        thread = threading.Thread(target=func, args=(args, uuid), daemon=True)
        threads[thread] = ep_name

    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join()
        print(f"Task Execution on Endpoint '{threads[thread]}' has Finished")  

