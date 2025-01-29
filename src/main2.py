import argparse
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from p2cs2 import p2cs
from c2cs2 import c2cs
from pub import pub
from con import con

"""if __name__ == "__main__":
    endpoint_functions = {"pub": pub, "p2cs": p2cs, "c2cs": c2cs, "con": con}
    log_files = {"p2cs": "p2cs_output.log", "c2cs": "c2cs_output.log", "pub": "pub_output.log", "con": "con_output.log"}

    endpoints = ["pub", "p2cs", "c2cs", "con"]

    with ThreadPoolExecutor(max_workers=len(endpoints)) as executor:
        futures = {executor.submit(endpoint_functions[role]): role for role in endpoints}

        log_threads = [threading.Thread(target=tail_log, args=(log_files[role],), daemon=True) for role in endpoints]
        for t in log_threads:
            t.start()

        for future in as_completed(futures):
            role = futures[future]
            try:
                future.result()
                print(f"Task for {role} completed successfully.")
            except Exception as e:
                print(f"Task for {role} failed: {e}")"""


if __name__ == "__main__":
    # Map endpoint names to functions
    endpoint_functions = {"p2cs": p2cs, "pub": pub, "c2cs": c2cs, "con": con}

    endpoints = ["p2cs", "pub", "c2cs", "con"]

    threads = []

    # Run each function in a separate thread for real-time stdout streaming
    for role in endpoints:
        thread = threading.Thread(target=endpoint_functions[role], daemon=True)
        thread.start()
        threads.append(thread)

    # Wait for all tasks to complete
    for thread in threads:
        thread.join()