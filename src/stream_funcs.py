import logging, time, sys, re
from globus_compute_sdk import Executor, ShellFunction

#TODO: check : "${HAPROXY_CONFIG_PATH:=/tmp/.scistream}" and [[ -z "$HAPROXY_CONFIG_PATH" ]] && HAPROXY_CONFIG_PATH="/tmp/.scistream"

def p2cs(args, endpoint_name, uuid):
    """Start the Producer's S2CS on the endpoint with the given arguments."""

    cmd =   f"""
            bash -c '
            [[ -z "$HAPROXY_CONFIG_PATH" ]] && HAPROXY_CONFIG_PATH="/tmp/.scistream" && mkdir -p "$HAPROXY_CONFIG_PATH"
            if [[ -z "$(ps -ef | grep "[ ]$(cat /tmp/.scistream/s2cs.pid)")" ]]; then timeout 60s setsid stdbuf -oL -eL s2cs --server_crt=$HAPROXY_CONFIG_PATH/server.crt --server_key=$HAPROXY_CONFIG_PATH/server.key --verbose --listener_ip={args.p2cs_listener} --type=StunnelSubprocess > "$HAPROXY_CONFIG_PATH/p2cs.log" 2>&1 & echo $! > "$HAPROXY_CONFIG_PATH/s2cs.pid"; else timeout 60s setsid stdbuf -oL -eL s2cs --server_crt=$HAPROXY_CONFIG_PATH/server.crt --server_key=$HAPROXY_CONFIG_PATH/server.key --verbose --listener_ip={args.p2cs_listener} --type=StunnelSubprocess > "$HAPROXY_CONFIG_PATH/p2cs.log" 2>&1 & echo $! > "$HAPROXY_CONFIG_PATH/s2cs.pid"; fi
            sleep 1 && cat "$HAPROXY_CONFIG_PATH/p2cs.log"
            '
            """
                #if [[ -z "$(ps -ef | grep "[ ]$(cat /tmp/.scistream/s2cs.pid)")" ]]; then setsid stdbuf -oL -eL s2cs --server_crt="/home/seena/scistream/server.crt" --server_key="/home/seena/scistream/server.key" --verbose --num_conn "{args.num_conn}" --listener_ip="{args.p2cs_listener}" --type="{args.type}" > "$HAPROXY_CONFIG_PATH/p2cs.log" 2>&1 & echo $! > "$HAPROXY_CONFIG_PATH/s2cs.pid"; else setsid stdbuf -oL -eL s2cs --server_crt="/home/seena/scistream/server.crt" --server_key="/home/seena/scistream/server.key" --verbose --listener_ip="{args.p2cs_listener}" --type="{args.type}" > "$HAPROXY_CONFIG_PATH/p2cs.log" 2>&1 & echo $! > "$HAPROXY_CONFIG_PATH/s2cs.pid"; fi
                #s2cs --server_crt=/home/seena/scistream/server.crt --server_key=/home/seena/scistream/server.key --verbose  --listener_ip=128.135.24.119 --type="StunnelSubprocess"  | tee "$HAPROXY_CONFIG_PATH/p2cs.log"  2>&1 &
                #TODO: Check if s2cs update will be compatible with the current start s2cs command conditions (runs only if the s2cs is not running)

    with Executor(endpoint_id=uuid) as gce:

        print(f"Starting the Producer's S2CS: \n"
              f"    endpoint: {endpoint_name.capitalize()} \n"
              f"    endpoint uid: {uuid} \n"
              f"    sync_port: {args.sync_port} \n"
              f"    p2cs_listener: {args.p2cs_listener} \n"
              f"    inbound_starter: {args.inbound_ep} \n"
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
            [[ -z "$HAPROXY_CONFIG_PATH" ]] && HAPROXY_CONFIG_PATH="/tmp/.scistream" && mkdir -p "$HAPROXY_CONFIG_PATH"
            if [[ -z "$(ps -ef | grep "[ ]$(cat /tmp/.scistream/s2cs.pid)")" ]]; then timeout 60s setsid stdbuf -oL -eL s2cs --server_crt=$HAPROXY_CONFIG_PATH/server.crt --server_key=$HAPROXY_CONFIG_PATH/server.key --verbose --listener_ip={args.c2cs_listener} --type=StunnelSubprocess  > "$HAPROXY_CONFIG_PATH/c2cs.log" 2>&1 & echo $! > "$HAPROXY_CONFIG_PATH/s2cs.pid"; else timeout 60s setsid stdbuf -oL -eL s2cs --server_crt=$HAPROXY_CONFIG_PATH/server.crt --server_key=$HAPROXY_CONFIG_PATH/server.key --verbose --listener_ip={args.c2cs_listener} --type=StunnelSubprocess  > "$HAPROXY_CONFIG_PATH/c2cs.log" 2>&1 & echo $! > "$HAPROXY_CONFIG_PATH/s2cs.pid"; fi
            sleep 1 && cat "$HAPROXY_CONFIG_PATH/c2cs.log"
            '
            """
            #TODO: think of something to kill the open s2cs processes if the inbound or outbound doesn't work! try to kill em!!
            #if [[ -z "$(ps -ef | grep "[ ]$(cat /tmp/.scistream/s2cs.pid)")" ]]; then setsid stdbuf -oL -eL s2cs --server_crt="/home/seena/scistream/server.crt" --server_key="/home/seena/scistream/server.key" --verbose --num_conn "{args.num_conn}" --listener_ip="{args.c2cs_listener}" --type="{args.type}"  > "$HAPROXY_CONFIG_PATH/c2cs.log" 2>&1 & echo $! > "$HAPROXY_CONFIG_PATH/s2cs.pid"; else setsid stdbuf -oL -eL s2cs --server_crt="/home/seena/scistream/server.crt" --server_key="/home/seena/scistream/server.key" --verbose --listener_ip="{args.c2cs_listener}" --type="{args.type}"  > "$HAPROXY_CONFIG_PATH/c2cs.log" 2>&1 & echo $! > "$HAPROXY_CONFIG_PATH/s2cs.pid"; fi
            # s2cs --server_crt="/home/seena/scistream/server.crt" --server_key="/home/seena/scistream/server.key" --verbose --listener_ip=128.135.24.120 --type="StunnelSubprocess"  > "$HAPROXY_CONFIG_PATH/c2cs.log" &
            #TODO: Check if s2cs update will be compatible with the current start s2cs command conditions (runs only if the s2cs is not running)

    with Executor(endpoint_id=uuid) as gce:

        print(f"Starting the Consumer's S2CS: \n"
              f"    endpoint: {endpoint_name.capitalize()} \n"
              f"    endpoint uid: {uuid} \n"
              f"    sync_port: {args.sync_port} \n"
              f"    c2cs_listener: {args.c2cs_listener} \n"
              f"    outbound_starter: {args.outbound_ep} \n"
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
            [[ -z "$HAPROXY_CONFIG_PATH" ]] && HAPROXY_CONFIG_PATH="/tmp/.scistream" && mkdir -p "$HAPROXY_CONFIG_PATH"
            sleep 1
            timeout 10 s2uc inbound-request --server_cert=$HAPROXY_CONFIG_PATH/server.crt --remote_ip {args.prod_ip} --num_conn 5 --receiver_ports=5074,5075,5076,5077,5078  --s2cs {args.p2cs_ip}:{args.sync_port}  > "$HAPROXY_CONFIG_PATH/conin.log" 2>&1 & echo $! >> "$HAPROXY_CONFIG_PATH/inbound.pid"
            while ! grep -q "prod_listeners:" "$HAPROXY_CONFIG_PATH/conin.log"; do sleep 1; done
            sleep 1
            cat "$HAPROXY_CONFIG_PATH/conin.log"
            '
            """
            #s2uc inbound-request --server_cert="/home/seena/scistream/server.crt" --remote_ip "{args.prod_ip}" --num_conn "{args.num_conn}" --receiver_ports="{args.inbound_src_ports}" --s2cs "{args.p2cs_ip}:{args.sync_port}"  > "$HAPROXY_CONFIG_PATH/conin.log" 2>&1 &
            # s2uc inbound-request --server_cert="/home/seena/scistream/server.crt" --remote_ip 128.135.24.117  --num_conn 5 --receiver_ports=5074,5075,5076,37000,47000  --s2cs 128.135.164.119:{args.sync_port}

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
            while not future.done():
                time.sleep(1)
                
            print("The Inbound Connection is completed.")
            result = future.result()
            logging.debug(f"INBOUND Output: {result.stdout}")
            #logging.debug(f"INBOUND Errors: {result.stderr}")
            
            info = result.stdout
            _LISTENERS = re.findall(r'(?im)^listeners:\s*"([^"]+)"', info)
            _PROD_LISTENERS = re.findall(r'(?im)^prod_listeners:\s*"([^"]+)"', info)
            _UID = re.search(r'^([a-f0-9-]{36})\s+.*INVALID_TOKEN PROD', info, re.MULTILINE)

            stream_uid = _UID.group(1) if _UID else None
            listen_ports = [port.split(":")[-1] for port in _LISTENERS]
            prod_ports = [port.split(":")[-1] for port in _PROD_LISTENERS]
            print(f"stream: {stream_uid}, listen ports: {listen_ports}, and the prod ports: {prod_ports}")
            
            return stream_uid, listen_ports

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
    print(f"Ports: {ports}")
    listen_ports = ports[0]

    cmd =   f"""
            bash -c '
            [[ -z "$HAPROXY_CONFIG_PATH" ]] && HAPROXY_CONFIG_PATH="/tmp/.scistream" && mkdir -p "$HAPROXY_CONFIG_PATH"
            timeout 10s setsid stdbuf -oL -eL s2uc outbound-request --server_cert=$HAPROXY_CONFIG_PATH/server.crt --remote_ip {args.c2cs_ip} --s2cs {args.c2cs_ip}:{args.sync_port}  --receiver_ports=5100 "{stream_uid}" {args.p2cs_ip}:5100,{args.p2cs_ip}:5101,{args.p2cs_ip}:5102,{args.p2cs_ip}:5103,{args.p2cs_ip}:5104  > "$HAPROXY_CONFIG_PATH/conout.log" & echo $! >> "$HAPROXY_CONFIG_PATH/outbound.pid"
            while ! grep -q "Hello message sent successfully" "$HAPROXY_CONFIG_PATH/conout.log"; do sleep 1 ; done
            sleep 1
            cat "$HAPROXY_CONFIG_PATH/conout.log"
            '
            """
            #setsid stdbuf -oL -eL s2uc outbound-request --server_cert="/home/seena/scistream/server.crt" --remote_ip "{args.p2cs_ip}" --s2cs "{args.c2cs_listener}":{args.sync_port}  --num_conn "{args.num_conn}" --receiver_ports="{listen_ports}" "{stream_uid}" 128.135.164.119:5100,128.135.164.119:5101,128.135.164.119:5102,128.135.164.119:5103,128.135.164.119:5104  > "$HAPROXY_CONFIG_PATH/conout.log" &
            #s2uc outbound-request --server_cert="/home/seena/scistream/server.crt" --remote_ip "{args.p2cs_ip}" --s2cs "{args.c2cs_listener}":{args.sync_port}  --num_conn "{args.num_conn}" --receiver_ports="{listen_ports}" "{stream_uid}" "{args.p2cs_ip}":"{listen_ports}",  > "$HAPROXY_CONFIG_PATH/conout.log" &
            # s2uc outbound-request --server_cert="/home/seena/scistream/server.crt" --remote_ip 128.135.164.119 --s2cs 128.135.24.120:{args.sync_port}  --receiver_ports=5100 0cddc36c-f3b5-11ef-9275-aee3018ac00c 128.135.164.119:5100,128.135.164.119:5101,128.135.164.119:5102,128.135.164.119:5103,128.135.164.119:5104          "{args.p2cs_ip}":"{listen_ports}"   

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