import argparse
import logging
import threading, queue, time, sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from globus_compute_sdk import Client 
from stream_funcs import p2cs, c2cs, inbound, outbound, stop_s2cs
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
    argparser.add_argument('-c', '--cleanup', action="store_true", help="clean up the orphan processes", default=True)
    argparser.add_argument('-v', '--verbose', action="store_true", help="Initiate a new stream connection", default=False)

    argparser.add_argument('--p2cs_ep', help="p2cs endpoint name", default="thats")
    argparser.add_argument('--c2cs_ep', help="c2cs endpoint name", default="neat")
    argparser.add_argument('--inbound_ep', help="inbound initiator endpoint name", default="swell")
    argparser.add_argument('--outbound_ep', help="outbound initiator endpoint name", default="swell")
    argparser.add_argument('--p2cs_key', help="p2cs key", default="p2cs")
    argparser.add_argument('--c2cs_key', help="c2cs key", default="c2cs")
    argparser.add_argument('--inbound_key', help="inbound key", default="swell")
    argparser.add_argument('--outbound_key', help="outbound key", default="swell")
    #argparser.add_argument('--inbound_ep', help="initiate the inbound stream connection", default="swell")             # the server certification should be specified
    #argparser.add_argument('--outbound_ep', help="initiate the outbound stream connection", default="swell")           # the server certification should be specified

    
    argparser.add_argument('--type', help= "proxy type: HaproxySubprocess, StunnelSubprocess, Haproxy", default="StunnelSubprocess")
    argparser.add_argument('--rate', type=int, help="transfer rate",default=10000)         #TODO: Add it to the command lines
    argparser.add_argument('--num_conn', type=int, help="THe number of specified ports", default=5)
    argparser.add_argument('--inbound_src_ports', type=str, help="Comma-separated list of inbound receiver ports", default="5074,5075,5076,5077,5078")
    argparser.add_argument('--outbound_dst_ports', type=str, help="Comma-separated list of outbound receiver ports", default="5100,5101,5102,5103,5104")    #dynamically is increased by the s2uc and then is read from the log file

    argparser.add_argument('-m', '--mini', action='store_true', help="Run the mini-apps", default=False)
    argparser.add_argument('--num_mini', type=int, help="The number of concurrent aps-mini-app run", default=5)
    

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
#TODO: also seperate the get_uuid and get_status functions so we don't sys.exit before we kill all the previous threads (exit steps)
#TODO: get the name of the endpoint from the command line and not hardcoded



    """
    server: (Self-Signed)
    openssl req -x509 -nodes -days 365 \
    -newkey rsa:2048 \
    -keyout server.key -out server.crt \
    -subj "/CN=172.17.0.2" \
    -addext "subjectAltName=IP:172.17.0.2"
    
    or using Certificate Signing Request (CSR):
    on the server
    openssl req -new -newkey rsa:2048 -nodes \
    -keyout server.key -out server.csr \
    -subj "/CN=192.168.1.100" \
    -addext "subjectAltName=IP:192.168.1.100"
    
        Samething as above:
            openssl genrsa -out server.key 2048
            openssl req -new -key server.key -out server.csr \
            -subj "/CN=192.168.1.100" \
            -addext "subjectAltName=IP:192.168.1.100"

    client:
    # 1. Generate client.key (same as before)
    openssl genrsa -out client.key 2048

    # 2. Create a self-signed certificate for the "client CA"
    openssl req -x509 -new -key client.key -out client.crt \
    -days 365 -subj "/CN=MyLocalCA"

    # 3. Sign the CSR from the server
    openssl x509 -req -in server.csr -CA client.crt -CAkey client.key \
    -CAcreateserial -out server.crt -days 365 \
    -extfile <(printf "subjectAltName=IP:192.168.1.100")
    """


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
                    print(f"Endpoint {name} is offline")
                    logging.error(f"Endpoint {name} is offline")
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
    for clean_s2cs_endpoint, _ in clean.items():
        thread = threading.Thread(target=stop_s2cs,  args=(args, clean_s2cs_endpoint, get_uuid(clean_s2cs_endpoint)), daemon=True)
        kill_threads[thread] = clean_s2cs_endpoint
        thread.start()
        logging.debug(f"MAIN: Starting killing Orphan processes on '{clean_s2cs_endpoint}' ")

    for thread, clean_s2cs_endpoint in kill_threads.items():
        thread.join()
        logging.debug(f"MAIN: Finished killing Orphan processes on '{clean_s2cs_endpoint}' ")
        
        
        
def start_s2cs():
    """Start the S2CS functions "p2cs" and "c2cs" on the producer and consumer endpoints."""

    s2cs_threads = {}

    # iterate over sci_funcs (keys = endpoint names, values = functions)
    for s2cs_endpoint, func in s2cs.items():
        thread = threading.Thread(target=func,  args=(args, s2cs_endpoint, get_uuid(s2cs_endpoint)), daemon=True)
        
        s2cs_threads[thread] = s2cs_endpoint
        thread.start()
        logging.debug(f"MAIN: The S2CS '{s2cs_endpoint}' has started")

    for thread, s2cs_endpoint in s2cs_threads.items():
        thread.join()
        logging.debug(f"MAIN: The S2CS '{s2cs_endpoint}' has finished")



def start_connection():
    """Manage the full connection process, optionally running inbound and outbound in parallel."""

    connections = {args.inbound_ep: inbound, args.outbound_ep: outbound}

    stream_uid, ports = inbound(args, args.inbound_ep,  get_uuid(args.inbound_ep))
    if stream_uid and len(ports) == int(args.num_conn):
        outbound(args, args.inbound_ep, get_uuid(args.outbound_ep), stream_uid, ports) 
    else:
        logging.error("Failed to retrieve Stream UID and Port. Outbound will not start.")
        #exit(1)



def start_mini():
    """Starts the mini functions "daq", "dist" on the producer and "sirt" consumer endpoints."""

    mini = {}

    for mini_endpoint, func in mini_funcs.items():
        uuid = get_uuid(mini_endpoint)
        thread = threading.Thread(target=func, args= (args, uuid), daemon=True)
        mini[thread] = mini_endpoint
    
    for thread in mini:
        thread.start()

    for thread in mini:
        thread.join()
        print(f"Task Execution on Endpoint '{mini[thread]}' has Finished")
        


gcc = Client()
args = get_args()

#keys = {args.p2cs_ep: p2cs_key, args.c2cs_ep: c2cs_key, args.inbound_ep: inbound_key, args.outbound_ep: outbound_key}
s2cs = {args.p2cs_ep: p2cs, args.c2cs_ep: c2cs}
connections = {args.inbound_ep: inbound, args.outbound_ep: outbound}
clean = {args.p2cs_ep: stop_s2cs, args.c2cs_ep: stop_s2cs}
mini_funcs = {"daq": daq, "dist": dist, "sirt": sirt} 

merge_list = (s2cs | connections | mini_funcs) if args.mini else (s2cs | connections)
endpoints = gcc.get_endpoints()
ep_names = {ep.get('name', '').strip().lower() for ep in endpoints}


if __name__ == "__main__":
    
    ep_mapping = health_check()
    args.cleanup and stop_service()
    
    start_s2cs()
    start_connection()
    
    args.mini and start_mini()
    
    
"""
#TODO: change it to the following, and write the variables, lists, etc. that are sent to different functions


def main():
    ep_mapping = health_check()
    args.cleanup and stop_service()
    
    start_s2cs()
    start_connection()
    
    args.mini and start_mini()

if __name__ == "__main__":
    main()
    """
