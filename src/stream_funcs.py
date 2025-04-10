import logging
import time
from globus_compute_sdk import Executor, ShellFunction



def p2cs(args, endpoint_name, uuid):
    """Start the Producer's S2CS on the endpoint with the given arguments."""

    cmd =   f"""
            bash -c '
            if [[ -z "$HAPROXY_CONFIG_PATH" ]]; then HAPROXY_CONFIG_PATH="/tmp/.scistream"; fi
            mkdir -p "$HAPROXY_CONFIG_PATH"
            if [[ -z "$(ps -ef | grep "[ ]$(cat /tmp/.scistream/s2cs.pid)")" ]]; then setsid stdbuf -oL -eL s2cs --server_crt="/home/seena/scistream/server.crt" --server_key="/home/seena/scistream/server.key" --verbose --num_conn "{args.num_conn}" --listener_ip="{args.p2cs_listener}" --type="{args.type}" > "$HAPROXY_CONFIG_PATH/p2cs.log" 2>&1 & echo $! > "$HAPROXY_CONFIG_PATH/s2cs.pid"; else setsid stdbuf -oL -eL s2cs --server_crt="/home/seena/scistream/server.crt" --server_key="/home/seena/scistream/server.key" --verbose --listener_ip="{args.p2cs_listener}" --type="{args.type}" > "$HAPROXY_CONFIG_PATH/p2cs.log" 2>&1 & echo $! > "$HAPROXY_CONFIG_PATH/s2cs.pid"; fi
            sleep 5 && cat "$HAPROXY_CONFIG_PATH/p2cs.log"
            '
            """            
                #s2cs --server_crt=/home/seena/scistream/server.crt --server_key=/home/seena/scistream/server.key --verbose  --listener_ip=128.135.24.119 --type="StunnelSubprocess"  | tee "$HAPROXY_CONFIG_PATH/p2cs.log"  2>&1 &
                #TODO: Check if s2cs update will be compatible with the current start s2cs command conditions (runs only if the s2cs is not running)

    with Executor(endpoint_id=uuid) as gce:

        print(f"Starting the Producer's S2CS: \n"
              f"    endpoint: {endpoint_name.capitalize()} \n"
              f"    endpoint uid: {uuid} \n"
              f"    sync_port: {args.sync_port} \n"
              f"    p2cs_listener: {args.p2cs_listener} \n"
              f"    inbound_starter: {args.inbound_starter} \n"
              f"    type: {args.type} \n"
              f"    rate: {args.rate} \n"
              f"    num_conn: {args.num_conn} \n"
              f"\n")
        logging.debug(f"P2CS: Starting the Producer's S2CS on the endpoint ({endpoint_name.capitalize()}) with args: \n{args}")
        future = gce.submit(ShellFunction(cmd, walltime=10))

        try:
            result = future.result()
            logging.debug(f"Producer's S2CS Stdout: {result.stdout}")
            #logging.debug(f"Producer's S2CS Stderr: {result.stderr}")
            #print(f"Producer's S2CS on the endpoint {endpoint_name.capitalize()} Stdout: \n{result.stdout} \n")

        except Exception as e:
            logging.error(f"Producer's S2CS Exception: {e}")
            sys.exit(1)
            
        #gce.shutdown(wait=False, cancel_futures=False)
        print(f"Producer's S2CS is completed on the endpoint {endpoint_name.capitalize()} \n")     #TODO: first check if the s2cs is online and then print this message



def c2cs(args, endpoint_name, uuid):
    """Start the Consumer's S2CS on the endpoint with the given arguments."""
    
    cmd =   f"""
            bash -c '
            if [[ -z "$HAPROXY_CONFIG_PATH" ]]; then HAPROXY_CONFIG_PATH="/tmp/.scistream"; fi
            mkdir -p "$HAPROXY_CONFIG_PATH"
            if [[ -z "$(ps -ef | grep "[ ]$(cat /tmp/.scistream/s2cs.pid)")" ]]; then setsid stdbuf -oL -eL s2cs --server_crt="/home/seena/scistream/server.crt" --server_key="/home/seena/scistream/server.key" --verbose --num_conn "{args.num_conn}" --listener_ip="{args.c2cs_listener}" --type="{args.type}"  > "$HAPROXY_CONFIG_PATH/c2cs.log" 2>&1 & echo $! > "$HAPROXY_CONFIG_PATH/s2cs.pid"; else setsid stdbuf -oL -eL s2cs --server_crt="/home/seena/scistream/server.crt" --server_key="/home/seena/scistream/server.key" --verbose --listener_ip="{args.c2cs_listener}" --type="{args.type}"  > "$HAPROXY_CONFIG_PATH/c2cs.log" 2>&1 & echo $! > "$HAPROXY_CONFIG_PATH/s2cs.pid"; fi
            sleep 5 && cat "$HAPROXY_CONFIG_PATH/c2cs.log"
            '
            """
            # s2cs --server_crt="/home/seena/scistream/server.crt" --server_key="/home/seena/scistream/server.key" --verbose --listener_ip=128.135.24.120 --type="StunnelSubprocess"  > "$HAPROXY_CONFIG_PATH/c2cs.log" &
            #TODO: Check if s2cs update will be compatible with the current start s2cs command conditions (runs only if the s2cs is not running)

    with Executor(endpoint_id=uuid) as gce:

        print(f"Starting the Consumer's S2CS: \n"
              f"    endpoint: {endpoint_name.capitalize()} \n"
              f"    endpoint uid: {uuid} \n"
              f"    sync_port: {args.sync_port} \n"
              f"    c2cs_listener: {args.c2cs_listener} \n"
              f"    outbound_starter: {args.outbound_starter} \n"
              f"    type: {args.type} \n"
              f"    rate: {args.rate} \n"
              f"    num_conn: {args.num_conn} \n"
              f"\n")
        logging.debug(f"C2CS: Starting the Consumer's S2CS on the endpoint {endpoint_name.capitalize()} with args: \n{args}")
        future = gce.submit(ShellFunction(cmd, walltime=10))

        try:
            result = future.result()
            logging.debug(f"Consumer's S2CS Stdout: {result.stdout}")
            #logging.debug(f"Consumer's S2CS Stderr: {result.stderr}")
            #print(f"Consumer's S2CS on the endpoint {endpoint_name.capitalize()} Stdout: \n{result.stdout} \n")

        except Exception as e:
            logging.error(f"Consumer's S2CS Exception: {e}")
            sys.exit(1)
            
        #gce.shutdown(wait=False, cancel_futures=False)
        print(f"Consumer's S2CS is completed on the endpoint {endpoint_name.capitalize()} \n")     #TODO: first check if the s2cs is online and then print this message




def inbound(args, endpoint_name,uuid, max_retries=3, delay=2):
    """Start the inbound connection and extract Stream UID and Port with retries."""

    cmd =   f"""
            bash -c '
            if [[ -z "$HAPROXY_CONFIG_PATH" ]]; then HAPROXY_CONFIG_PATH="/tmp/.scistream"; fi
            mkdir -p "$HAPROXY_CONFIG_PATH"
            sleep 5
            s2uc inbound-request --server_cert="/home/seena/scistream/server.crt" --remote_ip "{args.prod_ip}" --num_conn "{args.num_conn}" --receiver_ports="{args.inbound_src_ports}" --s2cs "{args.p2cs_ip}:5000"  > "$HAPROXY_CONFIG_PATH/conin.log" 2>&1 &
            while ! grep -q "prod_listeners:" "$HAPROXY_CONFIG_PATH/conin.log"; do sleep 1; done
            sleep 5
            cat "$HAPROXY_CONFIG_PATH/conin.log"
            '
            """
            # s2uc inbound-request --server_cert="/home/seena/scistream/server.crt" --remote_ip 128.135.24.117  --num_conn 5 --receiver_ports=5074,5075,5076,37000,47000  --s2cs 128.135.164.119:5000

            #TODO: instead of adding sleep 5 secs before running the code, check if there exist the p2cs.log is not empty and run then run the command
            #TODO: better way to do this is to check whether the port is open or not

    with Executor(endpoint_id=uuid) as gce:

        print(f"Starting the Inbound Connection: \n"
              f"    endpoint: {endpoint_name.capitalize()} \n"
              f"    endpoint uid: {uuid} \n"
              f"    sync_port: {args.sync_port} \n"
              f"    p2cs_ip: {args.p2cs_ip} \n"
              f"    prod_ip: {args.prod_ip} \n"
              f"    inbound_src_ports: {args.inbound_src_ports} \n"
              f"\n")
        logging.debug(f"INBOUND: Starting connection on endpoint ({endpoint_name.capitalize()}) with args: \n{args}")
        future = gce.submit(ShellFunction(cmd))

        try:
            result = future.result()
            logging.debug(f"INBOUND Output: {result.stdout}")
            #logging.debug(f"INBOUND Errors: {result.stderr}")

            stream_uid, listen_ports = None, []
            for retry in range(max_retries + int(args.num_conn)):
                
                for line in result.stdout.splitlines():
                    if "INVALID_TOKEN PROD" in line and stream_uid is None:
                        stream_uid = line.split(" ")[0]
                        logging.debug(f"Extracted Stream UID: {stream_uid}")
                    if line.strip().startswith("listeners:"):
                        parts = line.split(":")
                        if len(parts) > 1 and len(listen_ports) < int(args.num_conn):
                            listen_ports.append(parts[-1].strip('"'))
                            logging.debug(f"Extracted Listener Port: {listen_ports[-1]}")
                            #print (f"The producer's listening port is: {listen_ports[-1]} \n")


                if stream_uid and len(listen_ports) == int(args.num_conn):
                    logging.debug(f"INBOUND: The S2CS initiated the Stream Inbound Connection with Stream UID : {stream_uid} and port is: {listen_ports}")
                    print(f"The S2CS initiated the Stream Inbound Connection with Stream UID : {stream_uid} and ports: {listen_ports} \n")
                    #gce.shutdown(wait=False, cancel_futures=False)
                    return stream_uid, listen_ports

                logging.warning(f"retrying extraction... attempt {retry+1}/{max_retries}")
                time.sleep(delay)

        except Exception as e:
            logging.error(f"INBOUND Exception: {e}")
            print(f"The Inbound Connection failed due to the following Exception: {e} \n")
            sys.exit(1)

        logging.error("INBOUND: The Inbound Connection failed to extract Stream UID and Port.")
        print(f"The Inbound Connection failed to extract Stream UID and Port. \n")
        #gce.shutdown(wait=True, cancel_futures=False)
        #return None, None  # Return None if extraction fails



def outbound(args, endpoint_name, uuid, stream_uid, ports):
    """Start the outbound connection using the extracted Stream UID and Port."""

    if not stream_uid or len(ports) < int(args.num_conn):
        print(f"The Outbound Connection failed due to missing Stream UID or Port on the endpoint {endpoint_name.capitalize()} {stream_uid, ports}")
        logging.error(f"OUTBOUND: The Outbound Connection failed due to missing Stream UID or Port on the endpoint {endpoint_name.capitalize()} {stream_uid, ports}")
        return

    #listen_ports = ",".join(ports)
    listen_ports = ports[0]

    cmd =   f"""
            bash -c '
            if [[ -z "$HAPROXY_CONFIG_PATH" ]]; then HAPROXY_CONFIG_PATH="/tmp/.scistream"; fi
            mkdir -p "$HAPROXY_CONFIG_PATH"
            setsid stdbuf -oL -eL s2uc outbound-request --server_cert="/home/seena/scistream/server.crt" --remote_ip "{args.p2cs_ip}" --s2cs "{args.c2cs_listener}":5000  --num_conn "{args.num_conn}" --receiver_ports="{listen_ports}" "{stream_uid}" 128.135.164.119:5100,128.135.164.119:5101,128.135.164.119:5102,128.135.164.119:5103,128.135.164.119:5104  > "$HAPROXY_CONFIG_PATH/conout.log" &
            while ! grep -q "Hello message sent successfully" "$HAPROXY_CONFIG_PATH/conout.log"; do sleep 1 ; done
            sleep 1
            cat "$HAPROXY_CONFIG_PATH/conout.log"
            '
            """
            #s2uc outbound-request --server_cert="/home/seena/scistream/server.crt" --remote_ip "{args.p2cs_ip}" --s2cs "{args.c2cs_listener}":5000  --num_conn "{args.num_conn}" --receiver_ports="{listen_ports}" "{stream_uid}" "{args.p2cs_ip}":"{listen_ports}",  > "$HAPROXY_CONFIG_PATH/conout.log" &
            # s2uc outbound-request --server_cert="/home/seena/scistream/server.crt" --remote_ip 128.135.164.119 --s2cs 128.135.24.120:5000  --receiver_ports=5100 0cddc36c-f3b5-11ef-9275-aee3018ac00c 128.135.164.119:5100,128.135.164.119:5101,128.135.164.119:5102,128.135.164.119:5103,128.135.164.119:5104          "{args.p2cs_ip}":"{listen_ports}"   

    with Executor(endpoint_id=uuid) as gce:

        print(f"Starting the Outbound Connection: \n"
              f"    endpoint: {endpoint_name.capitalize()} \n"
              f"    endpoint uid: {uuid} \n"
              f"    p2cs_listener: {args.p2cs_listener} \n"
              f"    c2cs_listener: {args.c2cs_listener} \n"
              f"    p2cs_ip: {args.p2cs_ip} \n"
              f"    cons_ip: {args.cons_ip} \n"
              f"\n")
        logging.debug(f"OUTBOUND: Starting Outbound connection on endpoint ({endpoint_name.capitalize()}) with args: \n{args} \n")
        future = gce.submit(ShellFunction(cmd))

        try:
            result = future.result()
            logging.debug(f"OUTBOUND Output: {result.stdout}")
            #logging.debug(f"OUTBOUND Errors: {result.stderr}")

        except Exception as e:
            logging.error(f"OUTBOUND Exception: {e}")
            print(f"The Outbound Connection failed due to the following Exception: {e}")
            sys.exit(1)

        print(f"The Outbound Connection is completed on the endpoint {endpoint_name.capitalize()} \n")
        logging.debug(f"OUTBOUND: The Outbound Connection is completed on the endpoint {endpoint_name.capitalize()}")
        #gce.shutdown(wait=True, cancel_futures=False)
    


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
              f"    sync_port: {args.sync_port} \n"
              f"    p2cs_listener: {args.p2cs_listener} \n"
              f"    p2cs_ip: {args.p2cs_ip} \n"
              f"    cons_ip: {args.cons_ip} \n"
              f"    c2cs_listener: {args.c2cs_listener} \n"
              f"    outbound_dst_ports: {args.outbound_dst_ports} \n"
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
        
        
        
        
        
        
        
        
        """            pids=$(pgrep -f "s2cs")
            if [[ -n "$pids" ]]; then
                for pid in $pids; do
                    kill -9 "$pid"
                done
                echo "Killed the orphan s2cs processes."
            else
                echo "No orphaned processes found."
            fi
        
        
        STUPID=$(pgrep -f stunnel)
            if [[ -n "$STUPID" ]]; then STUPPID=$(ps -o ppid= -p $(pgrep -f  stunnel) | tr -d ' '); sudo kill -9 $STUPID; sudo kill -9 $STUPPID; fi

            SUB=$(pgrep -f StunnelSubprocess)
            if [[ -n "$SUB" ]]; then; SUBPPID=$(ps -o ppid= -p $(pgrep -f  StunnelSubprocess) | tr -d ' '); sudo kill -9 $SUB; sudo kill -9 $SUBPPID; fi
            
            echo "$(ps -ef | grep python --color=auto )" && echo "$(ps -ef | grep Stunnel --color=auto )" && echo "$(ps -ef | grep stunnel --color=auto )
            
            
                        pgrep -f stunnel | while read -r pid; do ppid=$(ps -o ppid= -p "$pid" | tr -d " "); sudo kill -9 "$pid" "$ppid"; done >> /tmp/kill.log 2>&1

        """