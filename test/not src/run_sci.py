from globus_compute_sdk import Executor
import os
from globus_ids import ids

#Clinet = client()



"""def run_py(path):
    import subprocess
    result = subprocess.run([path], capture_output=True, text=True)
    return {"stdout": result.stdout, "stderr": result.stderr, "returncode": result.returncode}
"""
"""
Executor.submit() needs a callable function
(not the result of calling the function)
so it won't work
"""

"""def run_pub(sci_path, *args):
    import subprocess
    try:
        command = [sci_path] + list(args)
        result = subprocess.run(command, capture_output=True, text=True)
        return {
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode
        }
    except Exception as e:
        return {"error": str(e)}

#def run_con():
will keep running in foreground and will wait until the process is done
"""

def run_pub(sci_path, *args):
    import subprocess
    import os
    import time
    try:
        command = [sci_path] + list(args)
        
        proc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        child_pids = []         #the process creates child processes
        try:
            with open(f"/proc/{proc.pid}/task/{proc.pid}/children") as f:
                child_pids = [int(pid) for pid in f.read().split()]
        except FileNotFoundError:
            # /proc/<pid>/task/<pid>/children may not be available on all systems
            pass

        stdout = []
        stderr = []
        while True:
            out = proc.stdout.readline()
            err = proc.stderr.readline()

            if out:
                stdout.append(out.strip())
                print(f"STDOUT: {out.strip()}")
            if err:
                stderr.append(err.strip())
                print(f"STDERR: {err.strip()}")

            if proc.poll() is not None:     #we need to check it the process is over or it won't quit
                break

            time.sleep(0.1)

        return {
            "pid": proc.pid,
            "child_pids": child_pids,
            "stdout": "\n".join(stdout),
            "stderr": "\n".join(stderr),
            "returncode": proc.returncode,
            "message": f"Process started with PID {proc.pid}",
        }
    except Exception as e:
        return {"error": str(e)}



sci_path = 's2cs'

pub_args = ['--verbose', '--port=5007', 'listener-ip=192.168.10.11', '--type=Haproxy']
con_args = ['arg1', 'arg2']


with Executor(endpoint_id=ids("p2cs_merrow")) as gce:
    future = gce.submit(run_pub, sci_path, *pub_args)
    result = future.result()

    if "error" in result:
        print(f"Error: {result['error']}")
    else:
        print(f"Process started successfully!")
        print(f"PID: {result['pid']}")
        print(f"Child PIDs: {result['child_pids']}")
        print(f"Return Code: {result['returncode']}")
        print(f"Stdout: {result['stdout']}")
        print(f"Stderr: {result['stderr']}")
