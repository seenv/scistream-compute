import time
from globus_compute_sdk import Executor, Client, ShellFunction
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime


def run_executor(endpoint_id, bf, code):
    print(f"start on {endpoint_id} with: {code}")
    with Executor(endpoint_id=endpoint_id) as gce:
        print(f"execute on {endpoint_id}: {code}")
        future = gce.submit(bf)

        return future
        

def get_uuid(client, name):
    try:
        endpoints = client.get_endpoints()
        for ep in endpoints:
            endpoint_name = ep.get('name', '').strip()
            if endpoint_name == name.strip().lower():
                return ep.get('uuid')
    except Exception as e:
        print(f"error fetching {name}: {str(e)}")
    return None


gcc = Client()
endpoints = {"vagrant": "that-prod"}

endpoint_ids = {key: get_uuid(gcc, name) for key, name in endpoints.items()}


commands = {"vagrant": "python3 /home/vagrant/testing.py 4"}

shell_functions = {key: ShellFunction(cmd) for key, cmd in commands.items()}

with ThreadPoolExecutor(max_workers=len(endpoints)) as executor:
    future_to_endpoint = {
        executor.submit(run_executor, endpoint_ids[key], shell_func, commands[key]): key
        for key, shell_func in shell_functions.items()}

for future in as_completed(future_to_endpoint):
    endpoint_name = future_to_endpoint[future]
    try:
        result_future = future.result() 
        result = result_future.result() 
        print(f"Task completed for endpoint {endpoint_name}:")
        print(f"Stdout: {result.stdout}")
        print(f"Stderr: {result.stderr}")
    except Exception as e:
        print(f"Task failed for endpoint {endpoint_name}: {e}")