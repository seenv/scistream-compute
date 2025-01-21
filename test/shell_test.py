"""
globus_compute_shell_function.py
from globus_compute_sdk import ShellFunction, Executor

ep_id = "<SPECIFY_ENDPOINT_ID>"
# The cmd will be formatted with kwargs at invocation time
bf = ShellFunction("echo '{message}'")
with Executor(endpoint_id=ep_id) as ex:
    for msg in ("hello", "hola", "bonjour"):
        future = ex.submit(bf, message=msg)
        shell_result = future.result()  # ShellFunctions return ShellResults
        print(shell_result.stdout)


From:  https://globus-compute.readthedocs.io/en/latest/executor.html#shell-functions
"""


import time
from globus_compute_sdk import Executor, Client, ShellFunction


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

endpoint_name = "swell-guy"
endpoint_id = get_uuid(gcc, endpoint_name)

msg = "python3 /home/seena/testing.py 3"
bf = ShellFunction('{message}')

"""with Executor(endpoint_id=ep_id) as ex:
    for msg in ("hello", "hola", "bonjour"):
        future = ex.submit(bf, message=msg)
        shell_result = future.result()  # ShellFunctions return ShellResults
        print(shell_result.stdout)"""

with Executor(endpoint_id=endpoint_id) as gce:
    future = gce.submit(bf, message=msg)
    shell_result = future.result()
    print(shell_result.stdout, flush=True)


"""    if "error" in result:
        print(f"Error: {result['error']}")
    else:
        print(f"Process started successfully!")
        print(f"PID: {result['pid']}")
        print(f"Return Code: {result['returncode']}")
        print(f"Stdout:\n{result['stdout']}")
        print(f"Stderr:\n{result['stderr']}")"""
