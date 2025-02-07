def daq (args, uuid):
    from globus_compute_sdk import Executor, ShellFunction
    import os, socket, time, datetime

    #home_dir = os.getenv("HOME")
    #command = f"""
    #            bash -c '
    #            sleep 30
    #            python /aps-mini-apps/build/python/streamer-daq/DAQStream.py --mode 1 --simulation_file /aps-mini-apps/data/tomo_00058_all_subsampled1p_s1079s1081.h5 --d_iteration 1 --publisher_addr tcp://*:50000 --iteration_sleep 1 --synch_addr tcp://*:50001 --synch_count 1'
    #            """

    command =   f"""
            bash -c '
            timeout 60 
            docker-compose -f /home/seena/mini/docker-compose.yaml up daq '
            """

    shell_function = ShellFunction(command, walltime=60)
    with Executor(endpoint_id=uuid) as gce:
        future = gce.submit(shell_function)

    try:
        result = future.result(timeout=60)
        print(f"StdoutL \n{result.stdout}", flush=True)
        cln_stderr = "\n".join(line for line in result.stderr.split("\n") if "WARNING" not in line)
        if cln_stderr.strip():
            print(f"Stderr: \n{cln_stderr}", flush=True)
    except Exception as e:
        print(f"Task failed: {e}")


def dist(args, uuid):
    from globus_compute_sdk import Executor, ShellFunction
    import os, socket, time, datetime

    #home_dir = os.getenv("HOME")
    #command = f"""
    #            bash -c '
    #            sleep 35
    #            python /aps-mini-apps/build/python/streamer-dist/ModDistStreamPubDemo.py --data_source_addr tcp://128.135.24.117:50000 --data_source_synch_addr tcp://128.135.24.117:50001 --cast_to_float32 --normalize --my_distributor_addr tcp://*:5074 --beg_sinogram 1000 --num_sinograms 2 --num_columns 2560'
    #            """

    command =   f"""
            bash -c '
            timeout 60 
            docker-compose -f /home/seena/mini/docker-compose.yaml up  '
            """

    shell_function = ShellFunction(command, walltime=60)

    with Executor (endpoint_id=uuid) as gce:
        future = gce.submit(shell_function)

    try:
        result = future.result(timeout=60)
        print(f"stdout: \n{result.stdout}", flush=True)
        cln_stderr = "\n".join(line for line in result.stderr.split("\n") if "WARNING" not in line)
        if cln_stderr.strip():
            print("Stderr: \n{cln_stderr}", flush=True)
    except Exception as e:
        print(f"Task failed: {e}")


def sirt(args, uuid):
    from globus_compute_sdk import Executor, ShellFunction
    import os, socket, time, datetime

    #home_dir = os.getenv("HOME")
    #command = f"""
    #            bash -c '
    #            sleep 40
    #            /aps-mini-apps/build/bin/sirt_stream --write-freq 4 --dest-host 128.135.164.120 --dest-port 5074 --window-iter 1 --window-step 4 --window-length 4 -t 2 -c 1427 --pub-addr tcp://*:52000 --recon-output-dir /output'
    #            """
    
    command =   f"""
                bash -c '
                timeout 60 
                docker-compose -f /home/seena/mini/docker-compose.yaml up '
                """

    shell_function = ShellFunction(command, walltime=60)
    with Executor(endpoint_id=uuid) as gce:
        future = gce.submit(shell_function)

    try:
        result = future.result(timeout=60)
        print(f"stdout: \n{result.stdout}", flush=True)
        cln_stderr = "\n".join(line for line in result.stderr.split("\n") if "WARNING" not in line)
        if cln_stderr.strip():
            print(f"Stderr: \n{cln_stderr}", flush=True)
    except Exception as e:
        print(f"Task failed: {e}")
