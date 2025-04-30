import logging, time, sys
from globus_compute_sdk import Executor, ShellFunction



def stop_s2cs(args, endpoint_name , uuid):
    """Killing the orphaned processes initiated via globus worker"""
    #TODO: now that we have the uuid we can just kill the pid as they are the same! or can we?!

    cmd =   f"""
            bash -c '
            pgrep -x stunnel | while read -r pid; do ppid=$(ps -o ppid= -p "$pid" | tr -d " "); sudo kill -9 "$pid" "$ppid"; done >> /tmp/kill.log 2>&1
            sleep 5 && echo "$(ps -ef | grep stunnel --color=auto )" >> /tmp/kill.log
            '
            """
    
    with Executor(endpoint_id=uuid) as gce:
        
        print(f"Killing the orphaned processes: \n"
              f"    endpoint: {endpoint_name.capitalize()} \n"
              f"    endpoint uid: {uuid} \n"
              f"\n")
        logging.debug(f"KILL_ORPHANS: Killing orphaned processes on endpoint ({endpoint_name.capitalize()}) with args: \n{args}")
        future = gce.submit(ShellFunction(cmd))

        try:
            result = future.result()
            logging.debug(f"KILL_ORPHANS Output: {result.stdout}")
            #logging.debug(f"KILL_ORPHANS Errors: {result.stderr}")

        except Exception as e:
            logging.error(f"KILL_ORPHANS Exception: {e}")
            print(f"Killing the orphaned processes failed due to the following Exception: {e}")
            sys.exit(1)

        print(f"Killing the orphaned processes is completed on the endpoint {endpoint_name.capitalize()} \n")
        logging.debug(f"KILL_ORPHANS: Killing orphaned processes is completed on the endpoint {endpoint_name.capitalize()}")
        #gce.shutdown(wait=True, cancel_futures=False)
        
        
        
def stop_s2uc(args, endpoint_name , uuid):
    """Killing the orphaned processes initiated via globus worker"""
    #TODO: now that we have the uuid we can just kill the pid as they are the same! or can we?!

    cmd =   f"""
            bash -c '
            pgrep -f "bash -c.*s2uc" | while read -r pid; do ppid=$(ps -o ppid= -p "$pid" | tr -d " "); sudo kill -9 "$pid" "$ppid"; done >> /tmp/kill.log 2>&1
            sleep 5 && echo "$(ps -ef | grep s2uc --color=auto )" >> /tmp/kill.log
            '
            """
    
    with Executor(endpoint_id=uuid) as gce:
        
        print(f"Killing the orphaned processes: \n"
              f"    endpoint: {endpoint_name.capitalize()} \n"
              f"    endpoint uid: {uuid} \n"
              f"\n")
        logging.debug(f"KILL_ORPHANS: Killing orphaned processes on endpoint ({endpoint_name.capitalize()}) with args: \n{args}")
        future = gce.submit(ShellFunction(cmd))

        try:
            result = future.result()
            logging.debug(f"KILL_ORPHANS Output: {result.stdout}")
            #logging.debug(f"KILL_ORPHANS Errors: {result.stderr}")

        except Exception as e:
            logging.error(f"KILL_ORPHANS Exception: {e}")
            print(f"Killing the orphaned processes failed due to the following Exception: {e}")
            sys.exit(1)

        print(f"Killing the orphaned processes is completed on the endpoint {endpoint_name.capitalize()} \n")
        logging.debug(f"KILL_ORPHANS: Killing orphaned processes is completed on the endpoint {endpoint_name.capitalize()}")
        #gce.shutdown(wait=True, cancel_futures=False)        
        
        