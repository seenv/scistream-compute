def con():
    
    import time
    from globus_compute_sdk import Executor, Client, ShellFunction
    from concurrent.futures import ThreadPoolExecutor, as_completed
    from datetime import datetime
    import sys, socket

    #gcc = Client()

    #command = "s2uc cons-req --s2cs 128.135.24.120:5007 4f8583bc-a4d3-11ee-9fd6-034d1fcbd7c3 128.135.164.119:5074 & sleep 5 && appctrl mock 4f8583bc-a4d3-11ee-9fd6-034d1fcbd7c3 128.135.24.120:5007 INVALID_TOKEN PROD 128.135.164.119"
    command = "s2uc cons-req --s2cs 128.135.24.120:5007 4f8583bc-a4d3-11ee-9fd6-034d1fcbd7c3 128.135.164.119:5074 &  appctrl mock 4f8583bc-a4d3-11ee-9fd6-034d1fcbd7c3 128.135.24.120:5007 INVALID_TOKEN PROD 128.135.164.119"

    endpoint_id = "efcb05ba-47aa-4c22-832f-21f3e23530a6"

    shell_function = ShellFunction(command)

    with Executor(endpoint_id=endpoint_id) as gce:
        print(f"Executing on endpoint {endpoint_id}...")
        future = gce.submit(shell_function)
        print(f"Task submitted to endpoint {endpoint_id} with Task ID: {future.task_id}")

    try:
        print("Waiting for task completion...\n")
        result = future.result()
        print("Task completed successfully!")
        print(f"Stdout: {result.stdout}")
        print(f"Stderr: {result.stderr}")
    except Exception as e:
        print(f"Task failed: {e}")