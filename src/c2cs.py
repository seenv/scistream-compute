def c2cs():
    
    import time
    from globus_compute_sdk import Executor, Client, ShellFunction
    from concurrent.futures import ThreadPoolExecutor, as_completed
    from datetime import datetime
    import sys, socket

    #gcc = Client()


    commands = "s2cs --verbose --port=5007 --listener-ip=128.135.24.120 --type=Haproxy"

    endpoint_id = "c9485ce4-6af4-4fda-90cb-64aae4891432"

    shell_function = ShellFunction(commands)

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