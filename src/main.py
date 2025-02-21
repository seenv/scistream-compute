import argparse
import threading, queue
from concurrent.futures import ThreadPoolExecutor, as_completed
from globus_compute_sdk import Client 
from sci_funcs1 import p2cs, c2cs, conin, conout
from mini_funcs import daq, dist, sirt


def get_args():
    argparser = argparse.ArgumentParser(description="arguments")
    argparser.add_argument('--sync-port', help="syncronization port",default="5000")
    argparser.add_argument('--p2cs-listener', help="listerner's IP of p2cs", default="128.135.24.119")
    argparser.add_argument('--p2cs-ip', help="IP address of the s2cs on producer side", default="128.135.164.119")
    argparser.add_argument('--type', help= "proxy type", default="StunnelSubprocess")
    argparser.add_argument('--c2cs-listener', help="listerner's IP of c2cs", default="128.135.24.120")
    argparser.add_argument('--c2cs_ip', help="IP address of the s2cs on consumer side", default='128.135.164.120')
    argparser.add_argument('--prod-ip', help="producer's IP address", default='128.135.24.117')
    #argparser.add_argument('--cons-ip', help="consumer's IP address", default="128.135.24.118")
    argparser.add_argument('--version', help="scistream version", default="1.2")

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



def wrapper(func, args, uuid, results_queue, sci_ep):
    """ Wrapper function to capture function output inside a thread """
    key = func(args, uuid)  # Run the function
    results_queue.put((sci_ep, key))  # Store the result in the queue



if __name__ == "__main__":

    gcc = Client()
    args = get_args()

    mini_funcs = {"daq": daq, "dist": dist, "sirt": sirt}
    #sci_funcs = {"that": p2cs, "neat": c2cs, "this": pub, "swell": con}
    #sci_funcs = {"that": p2cs, "neat": c2cs, "swell": con}
    
    inbound_sync = {"that": p2cs, "swell": conin}
    outbound_sync = {"neat": c2cs, "swell": conout}

    #scistream
    inbound, outbound = {}, {}
    results_queue = queue.Queue()   # queue to store results

    # iterate over sci_funcs (keys = endpoint names, values = functions)
    for sci_ep, func in inbound_sync.items():
        uuid = get_uuid(gcc, sci_ep)
        thread = threading.Thread(target=func, args=(args, uuid, results_queue), daemon=True)
        inbound[thread] = sci_ep
        #threads.append(thread)
        thread.start()
    
    scistream_uuid, sync_ports, port_list = None, None, None
    while any(t.is_alive() for t in inbound):
        while not results_queue.empty():
            key, value = results_queue.get()
            if key =="uuid":
                scistream_uuid = value
            elif key == "sync":
                sync_ports = value
            elif key == "ports":
                port_list = value

    # check if all inbounds are finished
    for thread, sci_ep in inbound.items():
        thread.join()
        print(f"Task Execution on Endpoint '{sci_ep}' has Finished") 

    # Ensure all necessary values are set before proceeding
    if scistream_uuid is None or port_list is None:
        print("Error: Required values missing. Exiting.")
        exit(1)

    # Start Outbound Threads
    for sci_ep, func in outbound_sync.items():
        uuid = get_uuid(gcc, sci_ep)
        thread = threading.Thread(target=func, args=(args, uuid, scistream_uuid, port_list, results_queue), daemon=True)
        outbound[thread] = sci_ep
        thread.start()

    # Ensure all outbound tasks are finished
    for thread, sci_ep in outbound.items():
        thread.join()
        print(f"Task Execution on Endpoint '{sci_ep}' has Finished")





"""
    # iterate over sci_funcs (keys = endpoint names, values = functions)
    for sci_ep, func in outbound_sync.items():
        uuid = get_uuid(gcc, sci_ep)
        thread = threading.Thread(
            target=func, 
            args=(args, uuid, scistream_uuid, port_list, results_queue), 
            daemon=True
        )
        outbound[thread] = sci_ep
        threads2.append(thread)
"""
"""
    # mini-aps
    mini = {}
    for mini_ep, func in mini_funcs.items():
        uuids = get_uuid(gcc, mini_ep)
        thread = threading.Thread(target=func, args= (args, uuids), daemon=True)
        mini[thread] = mini_ep
    
    for thread in mini:
        thread.start()

    for thread in mini:
        thread.join()
        print(f"Task Execution on Endpoint '{mini[thread]}' has Finished")

"""