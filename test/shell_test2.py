

import time
from globus_compute_sdk import Executor, Client, ShellFunction
from concurrent.futures import ThreadPoolExecutor



def run_executor(endpoint_id, code):
    with Executor(endpoint_id=endpoint_id) as ex:
        future = ex.submit(code)
        try:
            shell_result = future.result()
            print(shell_result['stdout'], flush=True)

            if "error" in shell_result:
                print(f"Error: {shell_result['error']}")
            else:
                print(f"Process started successfully!")
                print(f"PID: {shell_result['pid']}")
                print(f"Return Code: {shell_result['returncode']}")
                print(f"Stdout:\n{shell_result['stdout']}", flush=True)
                print(f"Stderr:\n{shell_result['stderr']}")
        except Exception as e:
            print(f"Exception occurred: {str(e)}")




def get_uuid(client, name):
    # Fetch all endpoints
    endpoints = client.get_endpoints()
    for ep in endpoints:
        endpoint_name = ep.get('name', '').strip()
        if endpoint_name == name.strip().lower():
            return ep.get('uuid')
    return None



# Initialize Globus Compute Client
gcc = Client()

pub_ep = "this-guy"
pub_id = get_uuid(gcc, pub_ep)

sub_ep = "swell-guy"
sub_id = get_uuid(gcc, sub_ep)

#test_code = "python3 /home/seena/testing.py 3"
pub_code = "python3 /home/seena/globus-stream/src/multi-port.v.04/main.py --publish --num_subs 1 --num_conns 2"
sub_code = "python3 /home/seena/globus-stream/src/multi-port.v.04/main.py --pub_ip 128.135.24.117"


bf_pub = ShellFunction('{pub_code}')
bf_sub = ShellFunction('{sub_code}')


# Run both executors in parallel
with ThreadPoolExecutor() as executor:
    executor.submit(run_executor, pub_id, bf_pub)
    executor.submit(run_executor, sub_id, bf_sub)

