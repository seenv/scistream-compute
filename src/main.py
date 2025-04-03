import argparse
import logging
import threading, queue, time, sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from globus_compute_sdk import Client 
from stream_funcs import p2cs, c2cs, inbound, outbound, stop_s2cs
from iperf_funcs import server, client
from mini_funcs import daq, dist, sirt
import asyncio


"""# Reset all logging handlers
for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)"""

"""# Optionally, clear the logging configuration
logging.shutdown()"""

# Now reconfigure
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("app.log"),
        # logging.StreamHandler()  # Uncomment for console output
    ]
    #force=True
)



def get_args():
    argparser = argparse.ArgumentParser(description="arguments")
    argparser.add_argument('--sync_port', help="syncronization port",default="5000")
    argparser.add_argument('--p2cs_listener', help="listerner's IP of p2cs", default="128.135.24.119")
    argparser.add_argument('--p2cs_ip', help="IP address of the s2cs on producer side", default="128.135.164.119")
    argparser.add_argument('--c2cs_listener', help="listerner's IP of c2cs", default="128.135.24.120")
    argparser.add_argument('--c2cs_ip', help="IP address of the s2cs on consumer side", default='128.135.164.120')
    argparser.add_argument('--prod_ip', help="producer's IP address", default='128.135.24.117')
    argparser.add_argument('--cons_ip', help="consumer's IP address", default="128.135.24.118")
    argparser.add_argument('--inbound_starter', help="initiate the inbound stream connection", default="swell")             # the server certification should be specified
    argparser.add_argument('--outbound_starter', help="initiate the outbound stream connection", default="swell")           # the server certification should be specified
    argparser.add_argument('-c', '--cleanup', action="store_true", help="clean up the orphan processes", default=False)
    argparser.add_argument('-v', '--verbose', action="store_true", help="Initiate a new stream connection", default=False)

    argparser.add_argument('--type', help= "proxy type: HaproxySubprocess, StunnelSubprocess, Haproxy", default="StunnelSubprocess")
    argparser.add_argument('--rate', type=int, help="transfer rate",default=10000)         #TODO: Add it to the command lines
    argparser.add_argument('--num_conn', type=int, help="THe number of specified ports", default=5)
    argparser.add_argument('--inbound_src_ports', type=str, help="Comma-separated list of inbound receiver ports", default="5074,5075,5076,5077,5078")
    argparser.add_argument('--outbound_dst_ports', type=str, help="Comma-separated list of outbound receiver ports", default="5100,5101,5102,5103,5104")    #dynamically is increased by the s2uc and then is read from the log file

    argparser.add_argument('-m', '--mini', action='store_true', help="Run the mini-apps", default=False)
    argparser.add_argument('--num_mini', type=int, help="The number of concurrent aps-mini-app run", default=5)
    
    argparser.add_argument('-i', '--iperf', action='store_true', help="Run the iperf3", default=False)
    argparser.add_argument('--num_iperf', type=int, help="The number of concurrent iperf3 run", default=3)

    return argparser.parse_args()



def get_status(gcc, uuid, name):
    """Get the status of the endpoint with the given endpoint UUID."""

    status = get_endpoint_status(uuid)
    metadata = gcc.get_endpoint_metadata(uuid)
    stop_response = gcc.stop_endpoint(uuid)            #Return type: json
    task_id = gcc.get_worker_hardware_details(uuid)
    result_status = gcc.get_result(task_id)

#TODO: add the code to create the keys on each endpoint
#TODO: the Client system also needs an endpoint to creat the keys?!
#TODO: change it so it first checks if all are available and then starts the functions
#TODO: modify the code so that if in each func it found that the endpoint is offline, it kills all the previous threads
#TODO: also seperate the get_uuid and get_status functions so we don't sys.exit before we kill all the previous threads
#TODO: get the name of the endpoint from the command line and not hardcoded

def get_uuid(client, name):
    """Get the UUID of the endpoint with the given name."""
    try:
        for ep in endpoints:
            endpoint_name = ep.get('name', '').strip().lower()
            if endpoint_name == name.strip().lower():
                uuid = ep.get('uuid')
                print(f"UUID for {name}: {uuid}")
                logging.info(f"UUID for {name}: {uuid}")
                
                endpoint_status = client.get_endpoint_status(uuid)
                status = endpoint_status.get("status", "offline")
                if status == "offline":
                    print(f"Status for {name}: {status} \n")
                    logging.info(f"Status for {name}: {status} \n")
                    #raise ValueError("Endpoint status is offline!")
                    sys.exit(1)
                
                print(f"Status for {name}: {status} \n")
                logging.info(f"Status for {name}: {status} \n")
                return uuid
            
        print(f"UUID for {name} not found")
        logging.debug(f"UUID for {name} not found")
        sys.exit(1)
    except Exception as e:
        logging.debug(f"Error fetching UUID for {name}: {str(e)}")
        sys.exit(1)

def stop_service(args, gcc, clean):
    """
    Kill the orphan processes of the S2CS on the producer and consumer endpoints.
    Since the processes are disowned using the 'setsid', they need to be killed
    no matter the connection status. (it won't affect the status)
    """

    kill_threads = {}

    # iterate over sci_funcs (keys = endpoint names, values = functions)
    for clean_s2cs_endpoint, _ in clean.items():
        thread = threading.Thread(target=stop_s2cs,  args=(args, clean_s2cs_endpoint, get_uuid(gcc, clean_s2cs_endpoint)), daemon=True)
        kill_threads[thread] = clean_s2cs_endpoint
        thread.start()
        logging.debug(f"MAIN: Starting killing Orphan processes on '{clean_s2cs_endpoint}' ")

    for thread, clean_s2cs_endpoint in kill_threads.items():
        thread.join()
        logging.debug(f"MAIN: Finished killing Orphan processes on '{clean_s2cs_endpoint}' ")
        
        
        
def start_s2cs(args, gcc, s2cs):
    """Start the S2CS functions "p2cs" and "c2cs" on the producer and consumer endpoints."""

    s2cs_threads = {}

    # iterate over sci_funcs (keys = endpoint names, values = functions)
    for s2cs_endpoint, func in s2cs.items():
        thread = threading.Thread(target=func,  args=(args, s2cs_endpoint, get_uuid(gcc, s2cs_endpoint)), daemon=True)
        
        s2cs_threads[thread] = s2cs_endpoint
        thread.start()
        logging.debug(f"MAIN: The S2CS '{s2cs_endpoint}' has started")

    for thread, s2cs_endpoint in s2cs_threads.items():
        thread.join()
        logging.debug(f"MAIN: The S2CS '{s2cs_endpoint}' has finished")



def start_connection(args, gcc, connections):
    """Manage the full connection process, optionally running inbound and outbound in parallel."""

    connections = {args.inbound_starter: inbound, args.outbound_starter: outbound}

    stream_uid, ports = inbound(args, args.inbound_starter,  get_uuid(gcc, args.inbound_starter))
    if stream_uid and len(ports) == int(args.num_conn):
        outbound(args, args.inbound_starter, get_uuid(gcc, args.outbound_starter), stream_uid, ports) 
    else:
        logging.error("Failed to retrieve Stream UID and Port. Outbound will not start.")
        #exit(1)



def start_mini():
    """Starts the mini functions "daq", "dist" on the producer and "sirt" consumer endpoints."""

    mini = {}

    for mini_endpoint, func in mini_funcs.items():
        uuid = get_uuid(gcc, mini_endpoint)
        thread = threading.Thread(target=func, args= (args, uuid), daemon=True)
        mini[thread] = mini_endpoint
    
    for thread in mini:
        thread.start()

    for thread in mini:
        thread.join()
        print(f"Task Execution on Endpoint '{mini[thread]}' has Finished")
        
        
        
def start_perf(args, gcc, iperf_funcs):
    """Starts the iperf functions on the producer and consumer endpoints."""

    iperf = {}

    for iperf_endpoint, func in iperf_funcs.items():
        uuid = get_uuid(gcc, iperf_endpoint)
        thread = threading.Thread(target=func, args= (args, uuid), daemon=True)
        iperf[thread] = iperf_endpoint
    
    for thread in iperf:
        thread.start()

    for thread in iperf:
        thread.join()
        print(f"Task Execution on Endpoint '{iperf[thread]}' has Finished")



gcc = Client()
args = get_args()
endpoints = gcc.get_endpoints()

s2cs = {"that": p2cs, "neat": c2cs}
connections = {args.inbound_starter: inbound, args.outbound_starter: outbound}
clean = {"that": stop_s2cs, "neat": stop_s2cs}
iperf_funcs = {"this": server, "swell": client}
mini_funcs = {"daq": daq, "dist": dist, "sirt": sirt} 


if __name__ == "__main__":
    
    #for endpoint in endpoints:
        
        
    args.cleanup and stop_service(args, gcc, clean)
    
    start_s2cs(args, gcc, s2cs)
    start_connection(args, gcc, connections)
    
    args.iperf and start_perf(args, gcc, iperf_funcs)
    args.mini and start_mini()
