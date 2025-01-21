from globus_compute_sdk import Executor
import os

"""def run_py(path):
    import subprocess
    result = subprocess.run([path], capture_output=True, text=True)
    return {"stdout": result.stdout, "stderr": result.stderr, "returncode": result.returncode}
"""
"""
Executor.submit() expects a callable function
(not the result of calling the function)
so it won't work
"""

def run_py(path):
    import subprocess
    try:
        result = subprocess.run(['python3', path], capture_output=True, text=True)
        return {
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode
        }
    except Exception as e:
        return {"error": str(e)}



code_path = '/home/seena/globus-stream/globus-compute/test/test.py'
this_gce_id = '77d689b7-080a-480e-b356-1fc8047e443e'
swell_gce_id = 'fb0f280f-dc0f-4bd6-83d0-83153ca9df4d'
neat_gce_id = '007cb806-29a8-4fb6-a587-7244be75cb8f'

with Executor(endpoint_id=neat_gce_id) as gce:
    future = gce.submit(run_py, code_path)

    result = future.result()

if "error" in result:
    print(f"Error: {result['error']}")
else:
    print(f"Return Code: {result['returncode']}")
    print(f"Stdout: {result['stdout']}")
    print(f"Stderr: {result['stderr']}")