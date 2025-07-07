import argparse
import logging
import threading, queue, time, sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from globus_compute_sdk import Client 
from stream_funcs import p2cs, c2cs, inbound, outbound
from kill_funcs import stop_s2cs, stop_s2uc
from key_funcs import key_gen, key_dist, crt_dist
from mini_funcs import daq, dist, sirt
from nginx import p2cs_nginx_conf, c2cs_nginx_conf
from config import get_args
import asyncio


"""# Reset all logging handlers
for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)"""

"""# Optionally, clear the logging configuration
logging.shutdown()"""

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("app.log"),
        # logging.StreamHandler()  # Uncomment for console output
    ]
    #force=True
)


#TODO: get the ip addresses using the globus compute from the socket but should find the local and the public out of them!!!!



def get_status(gcc, uuid, name):
    """Get the status of the endpoint with the given endpoint UUID."""

    status = get_endpoint_status(uuid)
    metadata = gcc.get_endpoint_metadata(uuid)
    stop_response = gcc.stop_endpoint(uuid)            #Return type: json
    task_id = gcc.get_worker_hardware_details(uuid)
    result_status = gcc.get_result(task_id)

#TODO: add the code to create the keys on each endpoint and create an env for it, so it gets the key address!
#TODO: the Client system also needs an endpoint to creat the keys?!
#TODO: also seperate the get_uuid and get_status functions so we don't sys.exit before we kill all the previous threads (exit steps)
#TODO: get the name of the endpoint from the command line and not hardcoded


def reload_endpoints():
    del_list = ['prod', 'cons', 'c2cs', 'p2cs']
    print(f"Deleting endpoints: {del_list}\n")
    for ep in gcc.get_endpoints():
        status = gcc.get_endpoint_status(ep['uuid'])['status']
        if status != 'online':
            if ep['name'] in del_list:
                print(f"{ep['name']} ({ep['uuid']}) is {status}, deleting...")
                gcc.delete_endpoint(ep['uuid'])
        else:
            print(f"{ep['name']} ({ep['uuid']}) is {status}, skipping deletion")
            
            
def health_check():
    """Check the health of the endpoints and log the status."""
    
    print("Checking the health of the endpoints...")
    logging.info("Checking the health of the endpoints...")
    
    ep_mapping = {}
    
    try:
        for name, func in merge_list.items():
            ep_name = name.strip().lower()
            if ep_name in ep_names:
                ep = next(ep for ep in endpoints if ep.get('name', '').strip().lower() == ep_name)
                uuid = ep.get('uuid')
                ep_mapping[ep_name] = uuid
                if gcc.get_endpoint_status(uuid).get('status', 'offline') != 'online':
                    print(f"Endpoint {name} with UID {uuid} is offline")
                    logging.error(f"Endpoint {name} is offline")
                    #reload_endpoints()
                    sys.exit(1)
        print(f"All endpoints are online and running \n")
        return ep_mapping
    except Exception as e:
        print(f"Error checking endpoint status: {str(e)}")
        logging.error(f"Error checking endpoint status: {str(e)}")
        sys.exit(1)



def get_uuid(name):
    """Get the UUID of the endpoint with the given name."""
    
    try:
        uuid = ep_mapping.get(name.strip().lower())
        if not uuid or gcc.get_endpoint_status(uuid).get('status', 'offline') != 'online':
                status = gcc.get_endpoint_status(uuid).get('status', 'offline')
                print(f"Status of endpoint {name} has changed to {status} \n")
                logging.info(f"Status of endpoint {name} has changed to {status} \n")
                #raise ValueError("Endpoint status is offline!")
                #TODO: instead of exit, it should start rolling back (also kill the previous threads, etc.)
                sys.exit(1)         
                
        return uuid
    
    except Exception as e:
        logging.debug(f"Error fetching UUID for {name}: {str(e)}")
        sys.exit(1)
            

def stop_service():
    """
    Kill the orphan processes of the S2CS on the producer and consumer endpoints.
    Since the processes are disowned using the 'setsid', they need to be killed
    no matter the connection status. (it won't affect the status)
    """

    kill_threads = {}

    # iterate over sci_funcs (keys = endpoint names, values = functions)
    for endpoint, func in clean.items():
        print(f"Stopping orphan processes on {endpoint}, {func}")
        thread = threading.Thread(target=func,  args=(args, endpoint, get_uuid(endpoint)), daemon=True)
        kill_threads[thread] = endpoint
        thread.start()
        logging.debug(f"MAIN: Starting killing Orphan processes on '{endpoint}' ")

    for thread, endpoint in kill_threads.items():
        thread.join()
        logging.debug(f"MAIN: Finished killing Orphan processes on '{endpoint}' ")



def start_keygen():
    """Generate the keys for the endpoints."""
        
    key, crt = key_gen(args, args.p2cs_ep, get_uuid(args.p2cs_ep))
    if key is not None or crt is not None:
        logging.debug(f"MAIN: The Key Generation '{args.p2cs_ep}' has finished")
        key_dist(args, args.c2cs_ep, get_uuid(args.c2cs_ep), key, crt)
        if args.inbound_ep != args.outbound_ep:
            crt_dist(args, args.inbound_ep, get_uuid(args.inbound_ep), crt)
            crt_dist(args, args.outbound_ep, get_uuid(args.outbound_ep), crt)
        else:
            crt_dist(args, args.inbound_ep, get_uuid(args.inbound_ep), crt)
    else:
        logging.error(f"MAIN: The Key Generation '{args.p2cs_en}' has failed to generate the keys")
        sys.exit(1)
        
        
        
def start_s2cs():
    """Start the S2CS functions "p2cs" and "c2cs" on the producer and consumer endpoints."""

    s2cs_threads = {}

    # iterate over sci_funcs (keys = endpoint names, values = functions)
    for endpoint, func in s2cs.items():
        thread = threading.Thread(target=func,  args=(args, endpoint, get_uuid(endpoint)), daemon=True)
        
        s2cs_threads[thread] = endpoint
        thread.start()
        logging.debug(f"MAIN: The S2CS '{endpoint}' has started")

    for thread, endpoint in s2cs_threads.items():
        thread.join()
        logging.debug(f"MAIN: The S2CS '{endpoint}' has finished")



def start_connection():
    """Manage the full connection process, optionally running inbound and outbound in parallel."""

    #connections = {args.inbound_ep: inbound, args.outbound_ep: outbound}

    stream_uid, ports = inbound(args, args.inbound_ep,  get_uuid(args.inbound_ep))
    
    if stream_uid and len(ports) == int(args.num_conn):
        outbound(args, args.inbound_ep, get_uuid(args.outbound_ep), stream_uid, ports) 
    else:
        logging.error("Failed to retrieve Stream UID and Port. Outbound will not start.")
        #exit(1)



def start_mini():
    """Starts the mini functions "daq", "dist" on the producer and "sirt" consumer endpoints."""

    mini = {}

    for endpoint, func in mini_funcs.items():
        thread = threading.Thread(target=func, args= (args, get_uuid(endpoint)), daemon=True)
        mini[thread] = endpoint
    
    for thread in mini:
        thread.start()

    for thread in mini:
        thread.join()
        print(f"Task Execution on Endpoint '{mini[thread]}' has Finished")


def start_nginx():
    """Start the Nginx configuration for the endpoints."""
    
    p2cs_nginx_conf(args, args.p2cs_ep, get_uuid(args.p2cs_ep))
    c2cs_nginx_conf(args, args.c2cs_ep, get_uuid(args.c2cs_ep))
    logging.info("Nginx configuration completed")


gcc = Client()
args = get_args()

#keys = {args.p2cs_ep: p2cs, args.c2cs_ep: key_dist, args.inbound_ep: key_dist, args.outbound_ep: key_dist}
#keys = {args.p2cs_ep: key_gen}
s2cs = {args.p2cs_ep: p2cs, args.c2cs_ep: c2cs}
connections = {args.inbound_ep: inbound, args.outbound_ep: outbound}
clean = {args.p2cs_ep: stop_s2cs, args.c2cs_ep: stop_s2cs, args.inbound_ep: stop_s2uc}
mini_funcs = {"daq": daq, "dist": dist, "sirt": sirt} 

merge_list = (s2cs | connections | mini_funcs) if args.mini else (s2cs | connections)
endpoints = gcc.get_endpoints()
ep_names = {ep.get('name', '').strip().lower() for ep in endpoints}


if __name__ == "__main__":
    
    ep_mapping = health_check()
    args.cleanup and stop_service()
    
    #if args.type == "Nginx": start_nginx()
    #elif args.type in ("HaproxySubprocess", "StunnelSubprocess"): start_keygen(); start_s2cs(); start_connection()
    #args.type in ("HaproxySubprocess", "StunnelSubprocess") and (start_keygen(), start_s2cs(), start_connection())     #will ignore the return values
    
    if args.type == "Nginx":
        start_nginx()
    elif args.type in ["HaproxySubprocess", "StunnelSubprocess"]:
        start_keygen()
        start_s2cs()
        start_connection()

    #args.mini and start_mini()