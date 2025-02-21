



def p2cs(args, uuid, result_q):

    from globus_compute_sdk import Executor, ShellFunction, Client
    from globus_compute_sdk.sdk.executor import ComputeFuture
    from concurrent.futures import ThreadPoolExecutor, as_completed
    import threading
    import signal
    from datetime import datetime
    import sys, socket, time, os
    import queue, ast, re

    command =   f"""
                timeout 60 bash -c '
                s2cs --verbose --port={args.sync_port} --listener-ip={args.p2cs_listener} --type={args.type} > /tmp/p2cs.log &

                if [ -n "$HAPROXY_CONFIG_PATH" ] && [ -s "$HAPROXY_CONFIG_PATH/resource.map" ]; then
                    CONFIG_FILE="$HAPROXY_CONFIG_PATH/resource.map"
                else
                    CONFIG_FILE="/tmp/.scistream/resource.map"
                fi
                while ! grep -q "Prod Listeners:" "$CONFIG_FILE"; do
                    sleep 1
                done
                cat "$CONFIG_FILE"
                '
                """

    shell_function = ShellFunction(command, walltime=60)

    with Executor(endpoint_id=uuid) as gce:
        future = gce.submit(shell_function)

        try:
            uid_val, sync_val, lstn_val = None, None, None

            while not future.done(): 
                result = future.result() 
                lines = result.stdout.strip().split("\n")

                for line in lines:
                    if "Sync Port:" in line and sync_val is None:
                        try:
                            sync_val = line.split()[2]
                            result_q.put(("sync", sync_val))
                            print(f"Found Sync: {sync_val}")
                        except (IndexError, ValueError):
                            print("can't extract Sync Port from the Resource Map:", line)

                    elif "Request UID" in line  and uid_val is None:
                        try:
                            uid_val = line.split()[2]
                            result_q.put(("uuid", uid_val))
                            print(f"Found Key: {uid_val}")
                        except IndexError:
                            print("can't extract UUID:", line)

                    if "Listeners:" in line and lstn_val is None:
                        try:
                            # Extract everything inside brackets using regex
                            match = re.search(r"\[([^\]]+)\]", line)
                            if match:
                                raw_list = match.group(1)  # Extract content inside brackets
                                # Extract only port numbers and remove extra quotes
                                lstn_val = [entry.split(":")[-1].strip("'").strip('"') for entry in raw_list.split(", ")]
                                result_q.put(("ports", lstn_val))
                                print(f"Found Ports: {', '.join(lstn_val)}") 
                            else:
                                print("Listeners format is incorrect:", line)

                        except (SyntaxError, ValueError) as e:
                            print(f"Can't parse the ports: {e} | in the line: {line}")

                #if uid_val and lstn_val and sync_val:
                if uid_val and lstn_val:
                    break

                time.sleep(1) 
            #print(result.stdout, flush=True)

        except Exception as e:
            print(f"Task failed: {e}")
            #return None  #None if no key is found




def c2cs(args, uuid, scistream_uuid, port_list, results_queue):

    from globus_compute_sdk import Executor, ShellFunction, Client
    from globus_compute_sdk.sdk.executor import ComputeFuture
    from concurrent.futures import ThreadPoolExecutor, as_completed
    import threading
    import signal
    from datetime import datetime
    import sys, socket, time, os

    command =   f"""
                timeout 60 bash -c '
                s2cs --verbose --port={args.sync_port} --listener-ip={args.c2cs_listener} --type={args.type} > /tmp/c2cs.log &
                '
                """

    shell_function = ShellFunction(command, walltime=60)

    with Executor(endpoint_id=uuid) as gce:
        future = gce.submit(shell_function)

        try:
            result = future.result(timeout=60)
            print(f"Stdout: \n{result.stdout}", flush=True)
            cln_stderr = "\n".join(line for line in result.stderr.split("\n") if "WARNING" not in line)
            if cln_stderr.strip():
                print(f"Stderr: {cln_stderr}", flush=True)
        except Exception as e:
            print(f"Task failed: {e}")





def conin(args, uuid, result_q):
    
    import time
    from globus_compute_sdk import Executor, Client, ShellFunction
    from concurrent.futures import ThreadPoolExecutor, as_completed
    from datetime import datetime
    import sys, socket, queue

    command =   f"""
                timeout 60 bash -c '
                sleep 5
                s2uc inbound-request --remote_ip 128.135.24.117 --s2cs 128.135.164.119:5000 > /tmp/conin.log & '
                """
                #s2uc inbound-request --remote_ip 128.135.24.117 --s2cs 128.135.164.119:5000 &

    shell_function = ShellFunction(command, walltime=60)

    with Executor(endpoint_id=uuid) as gce:
        future = gce.submit(shell_function)

        try:
            result = future.result(timeout=60)
            print(f"Stdout: \n{result.stdout}")
            cln_stderr = "\n".join(line for line in result.stderr.split("\n") if "WARNING" not in line)
            if cln_stderr.strip():
                print(f"Stderr: {cln_stderr}", flush=True)

            
        except Exception as e:
            print(f"Task failed: {e}")



def conout(args, uuid, scistream_uuid, port_list, results_queue):
    
    import time
    from globus_compute_sdk import Executor, Client, ShellFunction
    from concurrent.futures import ThreadPoolExecutor, as_completed
    from datetime import datetime
    import sys, socket, queue

    print(f" the uuid should not be null: {scistream_uuid}")

    command =   f"""
                timeout 60 bash -c '
                sleep 5
                s2uc outbound-request --remote_ip 128.135.164.119 --s2cs 128.135.24.120:5000  {scistream_uuid}  --receiver_ports=5100 128.135.164.119:5100  > /tmp/conout.log & '
                """
                #s2uc outbound-request --remote_ip 128.135.164.119 --s2cs 128.135.24.120:5000 d1d55174-eefd-11ef-ae06-aee3018ac00c --receiver_ports=5100  128.135.164.119:5100  &
                #s2uc outbound-request --remote_ip {args.p2cs_ip} --s2cs {args.c2cs_listener}:{args.sync_port} --receiver_ports {port_list[0]} {scistream_uuid}  {args.p2cs_ip}:{port_list[0]}  > /tmp/c2uc.log 2>&1 '

    shell_function = ShellFunction(command, walltime=60)

    with Executor(endpoint_id=uuid) as gce:
        future = gce.submit(shell_function)

        try:
            result = future.result(timeout=60)
            print(f"Stdout: \n{result.stdout}")
            cln_stderr = "\n".join(line for line in result.stderr.split("\n") if "WARNING" not in line)
            if cln_stderr.strip():
                print(f"Stderr: {cln_stderr}", flush=True)

            
        except Exception as e:
            print(f"Task failed: {e}")












"""
def con(args, uuid):
    
    import time
    from globus_compute_sdk import Executor, Client, ShellFunction
    from concurrent.futures import ThreadPoolExecutor, as_completed
    from datetime import datetime
    import sys, socket

    command =   f
                timeout 60 bash -c '
                sleep 5
                s2uc inbound-request --remote_ip 128.135.24.117 --s2cs 128.135.164.119:5000 & >> /tmp/c2us.log 2>&1 &
                sleep 5
                s2uc outbound-request --remote_ip 128.135.164.119 --s2cs 128.135.24.120:5000 d1d55174-eefd-11ef-ae06-aee3018ac00c --receiver_ports=5100  128.135.164.119:5100  & > /tmp/appctrl.log 2>&1 '
                

    shell_function = ShellFunction(command, walltime=60)

    with Executor(endpoint_id=uuid) as gce:
        future = gce.submit(shell_function)

        try:
            result = future.result(timeout=60)
            #print("CONS ---------------------------------")
            print(f"Stdout: \n{result.stdout}")
            cln_stderr = "\n".join(line for line in result.stderr.split("\n") if "WARNING" not in line)
            if cln_stderr.strip():
                print(f"Stderr: {cln_stderr}", flush=True)
            #print("CONS ---------------------------------")
        except Exception as e:
            print(f"Task failed: {e}")
"""


"""
from globus_compute_sdk import Client
gcc = Client()
task_id = gcc.get_worker_hardware_details(ep_uuid)
# wait some time...
print(gcc.get_result(task_id))

from globus_compute_sdk import Client

def expensive_task(task_arg):
    import time
    time.sleep(3600 * 24)  # 24 hours
    return "All done!"

ep_id = "<endpoint_id>"
gcc = Client()

print(f"Task Group ID for later reloading: {gcc.session_task_group_id}")
fn_id = gcc.register_function(expensive_task)
batch = gcc.create_batch()
for task_i in range(10):
    batch.add(fn_id, ep_id, args=(task_i,))
gcc.batch_run(batch)
"""












"""
                bash -c '
                stdbuf -oL -eL s2cs --verbose --port={args.sync_port} --listener-ip={args.p2cs_listener} --type={args.type} > /tmp/p2cs.log &      
                while ! grep -q "req started, with request uid:" /tmp/p2cs.log; do
                    sleep 1
                done
                echo "and conf path is $HAPROXY_CONFIG_PATH "
                sync_port=$(grep "Secure Server started on" /tmp/p2cs.log | head -n 1 | cut -d " " -f5)
                uid_key=$(grep "req started, with request uid:" /tmp/p2cs.log | head -n 1 | cut -d " " -f6)
                echo "Extracted UUID: $uid_key"
                echo "Extracted SYNC: $sync_port"
                while ! grep -q "Available ports:" /tmp/p2cs.log; do
                    sleep 1
                done
                listn_ports=$(grep "Available ports:" /tmp/p2cs.log | head -n 1 | cut -d " " -f3,4,5,6,7)
                echo "Extracted PORTS:  $listn_ports"
                '
                """


""" 
    timeout 60 bash -c '
    nohup s2cs --verbose --port={args.sync_port} --listener-ip={args.p2cs_listener} --type={args.type} > /tmp/p2cs.log 2>&1 &
    s2cs --verbose --port={args.sync_port} --listener-ip={args.p2cs_listener} --type={args.type} | tee /tmp/p2cs.log 2>&1
    cat /tmp/p2cs.log
    PID0=$(pgrep -f "nohup")
    stdbuf -oL echo "pid0 is nohup: " $PID0
    PID1=$!
    stdbuf -oL echo "pid1 is nohup: " $PID1
    PID2=$(pgrep -f "s2cs --verbose --port={args.sync_port}")
    stdbuf -oL echo "pid2 is s2cs: " $PID2
    PPID1=$(ps -o ppid= -p $PID | tail -n 1 | tr -d ' ')
    PPID2=$(ps -o ppid= -p $PID | awk 'NR==2 {print $1}')
    echo "p2cs pid and ppid1 and ppid2 are" $PID2 $PID1 $PPID1 $PPID2
    echo $PID1 $PID2 $PPID1 $PPID2 >> /tmp/p2cs.pids
    echo "S2CS PID in P2CS is " $!
    cat /tmp/p2cs.log
    sleep 50
    kill -9 $(cat /tmp/p2cs.pid)
    #rm -f /tmp/p2cs.pid
    cat /tmp/p2cs.log '

                echo "S2CS PID in P2CS is " $!
                echo "S2CS PID in pid file is " $! > /tmp/p2cs.pid
                cat /tmp/p2cs.pid

                        PPID1=$(ps -ep ppid= -p $PID1)
                    PPID2=$(ps -ep ppid= -p $PID2)




                    while ! pgrep -f "stunnel" > /dev/null; do
                    echo "waiting"
                    sleep 1
                done

                STUNNEL_PID=$(pgrep -f "stunnel")
                STUNNEL_PPID=$(ps -o ppid= -p $STUNNEL_PID | tr -d " ")

                stdbuf -oL echo "stunnel pid in p2cs is : " $STUNNEL_PID
                stdbuf -oL echo "stunnel ppid in p2cs is : " $STUNNEL_PPID




                s2cs --verbose --port={args.sync_port} --listener-ip={args.p2cs_listener} --type={args.type} > /tmp/p2cs.log &
                stdbuf -oL echo "s2cs pid in p2cs is : " $! && echo $! > /tmp/p2cs.pid
                stdbuf -oL echo "s2cs ppid in p2cs is : " $(ps -o ppid= -p $!) && echo $(ps -o ppid= -p $!) > /tmp/p2cs.ppid

                while ! grep -q "req started, with request uid:" /tmp/p2cs.log; do
                    sleep 1
                done
                key=$(grep "req started, with request uid:" /tmp/p2cs.log | head -n 1 | cut -d " " -f6)
                stdbuf -oL echo "Extracted Key: $key"

                STUNNEL_PID=$(pgrep -f "stunnel") && stdbuf -oL echo "stunnel pid in p2cs is : which is not working properly" $STUNNEL_PID
                STUNNEL_PPID=$(ps -o ppid= -p $STUNNEL_PID | tr -d " ") && stdbuf -oL echo "stunnel ppid in p2cs is : which is not working properly" $STUNNEL_PPID
                cat /tmp/p2cs.log
    """