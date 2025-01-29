import time
from globus_compute_sdk import Executor, Client, ShellFunction
from datetime import datetime

# Initialize the Globus Compute Client
gcc = Client()

# Define the command to run
commands = "s2cs --verbose --port=5007 --listener-ip=128.135.24.119 --type=Haproxy"

# Endpoint ID
endpoint_id = "df1658eb-1c81-4bb1-bc46-3a74f30d1ce1"

# Wrap the command in a ShellFunction
shell_function = ShellFunction(commands)

# Submit the task to the endpoint
with Executor(endpoint_id=endpoint_id) as gce:
    print(f"Executing on endpoint {endpoint_id}...")
    future = gce.submit(shell_function)
    print(f"Task submitted to endpoint {endpoint_id} with Task ID: {task_id}")

# Monitor the task status and cancel it after a specific duration
try:
    # Specify the maximum time (in seconds) to wait before canceling the task
    max_runtime = 30  # Example: 30 seconds
    start_time = time.time()

    while True:
        # Check the task status periodically
        task_status = gcc.get_task(task_id)
        print(f"Task {task_id} status: {task_status['status']}")

        # If the task is completed, break out of the loop
        if task_status['status'] == 'SUCCEEDED':
            print("Task completed successfully!")
            break

        # If the task exceeds the maximum runtime, cancel it
        if time.time() - start_time > max_runtime:
            print(f"Task exceeded maximum runtime of {max_runtime} seconds. Canceling task...")
            gcc.cancel_task(task_id)
            print(f"Task {task_id} has been successfully canceled.")
            break

        # Wait before checking the status again
        time.sleep(5)

except Exception as e:
    print(f"An error occurred: {e}")

# Check the final task status
try:
    final_status = gcc.get_task(task_id)
    print(f"Final status of Task {task_id}: {final_status['status']}")
except Exception as e:
    print(f"Failed to retrieve final status for Task {task_id}: {e}")