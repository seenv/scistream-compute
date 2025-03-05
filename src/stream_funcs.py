import logging
import time
from globus_compute_sdk import Executor, ShellFunction



def p2cs(args, endpoint_name, uuid):
    """Start the Producer's S2CS on the endpoint with the given arguments."""


    cmd =   f"""
            bash -c '
            if [[ -z "$HAPROXY_CONFIG_PATH" ]]; then HAPROXY_CONFIG_PATH="/tmp/.scistream"; fi
            mkdir -p "$HAPROXY_CONFIG_PATH"
            if [[ -z "$(ps -ef | grep "[ ]$(cat /tmp/.scistream/s2cs.pid)")" ]]; then setsid stdbuf -oL -eL s2cs --server_crt="/home/seena/scistream/server.crt" --server_key="/home/seena/scistream/server.key" --verbose --listener_ip="{args.p2cs_listener}" --type="{args.type}" > "$HAPROXY_CONFIG_PATH/p2cs.log" 2>&1 & echo $! > "$HAPROXY_CONFIG_PATH/s2cs.pid"; else setsid stdbuf -oL -eL s2cs --server_crt="/home/seena/scistream/server.crt" --server_key="/home/seena/scistream/server.key" --verbose --listener_ip="{args.p2cs_listener}" --type="{args.type}" > "$HAPROXY_CONFIG_PATH/p2cs.log" 2>&1 & echo $! > "$HAPROXY_CONFIG_PATH/s2cs.pid"; fi
            sleep 5 && cat "$HAPROXY_CONFIG_PATH/p2cs.log"
            '
            """            
                #s2cs --server_crt=/home/seena/scistream/server.crt --server_key=/home/seena/scistream/server.key --verbose  --listener_ip=128.135.24.119 --type="StunnelSubprocess"  | tee "$HAPROXY_CONFIG_PATH/p2cs.log"  2>&1 &
                #TODO: Check if s2cs update will be compatible with the current start s2cs command conditions (runs only if the s2cs is not running)

    with Executor(endpoint_id=uuid) as gce:

        print(f"Starting the Producer's S2CS on the endpoint {endpoint_name.capitalize()} with args: \n{args} \n")
        logging.debug(f"P2CS: Starting the Producer's S2CS on the endpoint ({endpoint_name.capitalize()}) with args: \n{args}")
        future = gce.submit(ShellFunction(cmd, walltime=10))

        try:
            result = future.result()
            logging.debug(f"Producer's S2CS Stdout: {result.stdout}")
            #logging.debug(f"Producer's S2CS Stderr: {result.stderr}")
            print(f"Producer's S2CS on the endpoint {endpoint_name.capitalize()} Stdout: \n{result.stdout} \n")

        except Exception as e:
            logging.error(f"Producer's S2CS Exception: {e}")
        #gce.shutdown(wait=False, cancel_futures=False)
        print(f"Producer's S2CS has completed on the endpoint {endpoint_name.capitalize()} \n")     #TODO: first check if the s2cs is online and then print this message



def c2cs(args, endpoint_name, uuid):

    cmd =   f"""
            bash -c '
            if [[ -z "$HAPROXY_CONFIG_PATH" ]]; then HAPROXY_CONFIG_PATH="/tmp/.scistream"; fi
            mkdir -p "$HAPROXY_CONFIG_PATH"
            if [[ -z "$(ps -ef | grep "[ ]$(cat /tmp/.scistream/s2cs.pid)")" ]]; then setsid stdbuf -oL -eL s2cs --server_crt="/home/seena/scistream/server.crt" --server_key="/home/seena/scistream/server.key" --verbose --listener_ip="{args.c2cs_listener}" --type="{args.type}"  > "$HAPROXY_CONFIG_PATH/c2cs.log" 2>&1 & echo $! > "$HAPROXY_CONFIG_PATH/s2cs.pid"; else setsid stdbuf -oL -eL s2cs --server_crt="/home/seena/scistream/server.crt" --server_key="/home/seena/scistream/server.key" --verbose --listener_ip="{args.c2cs_listener}" --type="{args.type}"  > "$HAPROXY_CONFIG_PATH/c2cs.log" 2>&1 & echo $! > "$HAPROXY_CONFIG_PATH/s2cs.pid"; fi
            sleep 5 && cat "$HAPROXY_CONFIG_PATH/c2cs.log"
            '
            """
            # s2cs --server_crt="/home/seena/scistream/server.crt" --server_key="/home/seena/scistream/server.key" --verbose --listener_ip=128.135.24.120 --type="StunnelSubprocess"  > "$HAPROXY_CONFIG_PATH/c2cs.log" &
            #TODO: Check if s2cs update will be compatible with the current start s2cs command conditions (runs only if the s2cs is not running)

    with Executor(endpoint_id=uuid) as gce:

        print(f"Starting the Consumer's S2CS on the endpoint {endpoint_name.capitalize()} with args: \n{args} \n")
        logging.debug(f"C2CS: Starting the Consumer's S2CS on the endpoint {endpoint_name.capitalize()} with args: \n{args}")
        future = gce.submit(ShellFunction(cmd, walltime=10))

        try:
            result = future.result()
            logging.debug(f"Consumer's S2CS Stdout: {result.stdout}")
            #logging.debug(f"Consumer's S2CS Stderr: {result.stderr}")
            print(f"Consumer's S2CS on the endpoint {endpoint_name.capitalize()} Stdout: \n{result.stdout} \n")

        except Exception as e:
            logging.error(f"Consumer's S2CS Exception: {e}")
        #gce.shutdown(wait=False, cancel_futures=False)
        print(f"Consumer's S2CS has completed on the endpoint {endpoint_name.capitalize()} \n")     #TODO: first check if the s2cs is online and then print this message




def inbound(args, endpoint_name,uuid, max_retries=3, delay=2):
    """Start the inbound connection and extract Stream UID and Port with retries."""

    cmd =   f"""
            bash -c '
            if [[ -z "$HAPROXY_CONFIG_PATH" ]]; then HAPROXY_CONFIG_PATH="/tmp/.scistream"; fi
            mkdir -p "$HAPROXY_CONFIG_PATH"
            sleep 1
            s2uc inbound-request --server_cert="/home/seena/scistream/server.crt" --remote_ip "{args.prod_ip}" --s2cs "{args.p2cs_ip}:5000"  > "$HAPROXY_CONFIG_PATH/conin.log" 2>&1 &
            while ! grep -q "prod_listeners:" "$HAPROXY_CONFIG_PATH/conin.log"; do sleep 1; done
            sleep 5
            cat "$HAPROXY_CONFIG_PATH/conin.log"
            '
            """
            # s2uc inbound-request --server_cert="/home/seena/scistream/server.crt" --remote_ip 128.135.24.117 --s2cs 128.135.164.119:5000

    with Executor(endpoint_id=uuid) as gce:

        print(f"Starting the the Inbound Connection on the endpoint {endpoint_name.capitalize()} with args: \n{args} \n")
        logging.debug(f"INBOUND: Starting connection on endpoint ({endpoint_name.capitalize()}) with args: \n{args}")
        future = gce.submit(ShellFunction(cmd))

        try:
            result = future.result()
            logging.debug(f"INBOUND Output: {result.stdout}")
            #logging.debug(f"INBOUND Errors: {result.stderr}")

            for retry in range(max_retries):
                stream_uid, port = None, None
                
                for line in result.stdout.splitlines():
                    if "INVALID_TOKEN PROD" in line and stream_uid is None:
                        stream_uid = line.split(" ")[0]
                        logging.debug(f"the stream uid is: {stream_uid}")
                    if "listener" in line and port is None:
                        parts = line.split(":")
                        if len(parts) > 1:
                            port = parts[-1].strip('"')
                            logging.debug(f"The producer's listening port is: {port}")

                if stream_uid and port:
                    logging.debug(f"INBOUND: The S2CS initiated the Stream Inbound Connection with Stream UID : {stream_uid} and port is: {port}")
                    print(f"The S2CS initiated the Stream Inbound Connection with Stream UID : {stream_uid} and port is: {port} \n")
                    #gce.shutdown(wait=False, cancel_futures=False)
                    return stream_uid, port

                logging.warning(f"retrying extraction... attempt {retry+1}/{max_retries}")
                time.sleep(delay)

        except Exception as e:
            logging.error(f"INBOUND Exception: {e}")
            print(f"The Inbound Connection failed due to the following Exception: {e} \n")

        logging.error("INBOUND: The Inbound Connection failed to extract Stream UID and Port.")
        print(f"The Inbound Connection failed to extract Stream UID and Port. \n")
        #gce.shutdown(wait=True, cancel_futures=False)
        #return None, None  # Return None if extraction fails



def outbound(args, endpoint_name, uuid, stream_uid, port):
    """Start the outbound connection using the extracted Stream UID and Port."""

    if not stream_uid or not port:
        print(f"The Outbound Connection failed due to missing Stream UID or Port on the endpoint {endpoint_name.capitalize()} \n")
        logging.error(f"OUTBOUND: The Outbound Connection failed due to missing Stream UID or Port on the endpoint {endpoint_name.capitalize()}")
        return

    cmd =   f"""
            bash -c '
            if [[ -z "$HAPROXY_CONFIG_PATH" ]]; then HAPROXY_CONFIG_PATH="/tmp/.scistream"; fi
            mkdir -p "$HAPROXY_CONFIG_PATH"
            setsid stdbuf -oL -eL s2uc outbound-request --server_cert="/home/seena/scistream/server.crt" --remote_ip "{args.p2cs_ip}" --s2cs "{args.c2cs_listener}":5000  --receiver_ports="{port}" "{stream_uid}" "{args.p2cs_ip}":"{port}"  > "$HAPROXY_CONFIG_PATH/conout.log" &
            while ! grep -q "Hello message sent successfully" "$HAPROXY_CONFIG_PATH/conout.log"; do sleep 1 ; done
            sleep 1
            cat "$HAPROXY_CONFIG_PATH/conout.log"
            '
            """
            # s2uc outbound-request --server_cert="/home/seena/scistream/server.crt" --remote_ip 128.135.164.119 --s2cs 128.135.24.120:5000  --receiver_ports=5100 0cddc36c-f3b5-11ef-9275-aee3018ac00c 128.135.164.119:5100

    with Executor(endpoint_id=uuid) as gce:

        print(f"Starting the the Outbound Connection on the endpoint {endpoint_name.capitalize()} with args: \n{args} \n")
        logging.debug(f"OUTBOUND: Starting Outbound connection on endpoint ({endpoint_name.capitalize()}) with args: \n{args}")
        future = gce.submit(ShellFunction(cmd))

        try:
            result = future.result()
            logging.debug(f"OUTBOUND Output: {result.stdout}")
            #logging.debug(f"OUTBOUND Errors: {result.stderr}")

        except Exception as e:
            logging.error(f"OUTBOUND Exception: {e}")
            print(f"The Outbound Connection failed due to the following Exception: {e}")

        print(f"The Outbound Connection has completed on the endpoint {endpoint_name.capitalize()} \n")
        logging.debug(f"OUTBOUND: The Outbound Connection has completed on the endpoint {endpoint_name.capitalize()}")
        #gce.shutdown(wait=True, cancel_futures=False)
    


def kill_orphans(args, endpoint_name , uuid):
    """Killing the orphaned processes initiated via globus worker"""

    cmd =   f"""
            bash -c '
            sleep 10
            pids=$(pgrep -f "s2cs")
            if [[ -n "$pids" ]]; then
                for pid in $pids; do
                    kill -9 "$pid"
                done
                echo "Killed the orphan s2cs processes."
            else
                echo "No orphaned processes found."
            fi
            '
            """
    
    with Executor(endpoint_id=uuid) as gce:
        
        print(f"Killing the orphaned processes on the endpoint {endpoint_name.capitalize()} with args: \n{args} \n")
        logging.debug(f"KILL_ORPHANS: Killing orphaned processes on endpoint ({endpoint_name.capitalize()}) with args: \n{args}")
        future = gce.submit(ShellFunction(cmd, walltime=60))

        try:
            result = future.result()
            logging.debug(f"KILL_ORPHANS Output: {result.stdout}")
            #logging.debug(f"KILL_ORPHANS Errors: {result.stderr}")

        except Exception as e:
            logging.error(f"KILL_ORPHANS Exception: {e}")
            print(f"Killing the orphaned processes failed due to the following Exception: {e}")

        print(f"Killing the orphaned processes has completed on the endpoint {endpoint_name.capitalize()} \n")
        logging.debug(f"KILL_ORPHANS: Killing orphaned processes has completed on the endpoint {endpoint_name.capitalize()}")
        #gce.shutdown(wait=True, cancel_futures=False)