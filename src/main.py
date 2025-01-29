import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from p2cs import p2cs
from c2cs import c2cs
from pub import pub
from con import con

if __name__ == "__main__":
    endpoint_functions = {"pub": pub, "p2cs": p2cs, "c2cs": c2cs, "con": con}

    endpoints = ["pub", "p2cs", "c2cs", "con"]
    with ThreadPoolExecutor(max_workers=len(endpoints)) as executor:
        futures = {
            executor.submit(endpoint_functions[role]): role for role in endpoints
        }
        for future in as_completed(futures):
            role = futures[future]
            try:
                future.result()
                print(f"Task for {role} completed successfully.")
            except Exception as e:
                print(f"Task for {role} failed: {e}")