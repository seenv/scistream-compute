"""import time
    def testing(i):
    print("Test script started.")
    for i in range(5):
        print(f"Iteration {i + 1}")
        time.sleep(2)
    print("Test script finished.")"""

import time
from globus_compute_sdk import Executor, Client
import sys

def run_pub(script_path, i):
    import subprocess
    import time
    import sys
    
    try:
        #command = ["python3", script_path, str(i)]
        #command = ["python3", "-u", script_path, str(i)]        #the script runs in unbuffered mode 
        command = ["stdbuf", "-oL", "python3", script_path, str(i)]         #disable buffering (Linux Only)
        proc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1)

        stdout = []
        stderr = []

        """  its  not working! 1st shouldn't wait for the result
             then we don't need a new process for just running the commands!
             just use the tested fomat later if need it!!!
               
        for line in iter(proc.stdout.readline, ''):
            stdout.append(line.strip())
            print(f"STDOUT: {line.strip()}", flush=True)  # Print in real-time

        for line in iter(proc.stderr.readline, ''):
            stderr.append(line.strip())
            print(f"STDERR: {line.strip()}", flush=True)  # Print in real-time

        proc.wait()  # Wait for process to complete

        return {
            "pid": proc.pid,
            "stdout": "\n".join(stdout),
            "stderr": "\n".join(stderr),
            "returncode": proc.returncode
        }"""
    except Exception as e:
        return {"error": str(e)}


def get_uuid(client, name):
    # Fetch all endpoints
    endpoints = client.get_endpoints()
    for ep in endpoints:
        endpoint_name = ep.get('name', '').strip()
        if endpoint_name == name.strip().lower():
            return ep.get('uuid')
    return None


gcc = Client()
x = 5

func_id = gcc.register_function(run_pub)
endpoint_name = "swell-guy"
endpoint_id = get_uuid(gcc, endpoint_name)
test_script_path = "/home/seena/testing.py"

with Executor(endpoint_id=endpoint_id) as gce:
    future = gce.submit(run_pub, test_script_path, x)
    result = future.result()

"""
# Use the .done() method to check the status of the function without
# blocking; this will return a Bool indicating whether the result is ready
print("Status: ", future.done())
print (result)
"""

"""try:
    print(future.result())
except Exception as exc:
    print(f"Oh no!  The task raised an exception: {exc}")"""


if "error" in result:
    print(f"Error: {result['error']}")
else:
    print(f"Process started successfully!")
    print(f"PID: {result['pid']}")
    print(f"Return Code: {result['returncode']}")
    print(f"Stdout:\n{result['stdout']}")
    print(f"Stderr:\n{result['stderr']}")




"""
test format:
def run_remote(command):
    import subprocess
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    stdout, stderr = process.communicate()
    return {"stdout": stdout, "stderr": stderr, "returncode": process.returncode}

ep_id = "ep-id"

with Executor(endpoint_id=ep-id) as ex:
    future = ex.submit(run_remote_command, "python3 /home/seena/testing.py 4")
    result = future.result()
    print("result:", result)
"""