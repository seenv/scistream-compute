import os
import json
import pandas as pd
from datetime import datetime
from pathlib import Path



def human_readable_bytes(num):
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if abs(num) < 1024.0:
            return f"{num:.2f} {unit}"
        num /= 1024.0
    return f"{num:.2f} PB"

def human_readable_bps(num):
    for unit in ['bps', 'Kbps', 'Mbps', 'Gbps', 'Tbps']:
        if abs(num) < 1000.0:
            return f"{num:.2f} {unit}"
        num /= 1000.0
    return f"{num:.2f} Pbps"


def cons_iperf_jsons(file_path, base_dir):
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)

        start = data.get("start", {})
        end = data.get("end", {})
        test_start = start.get("test_start", {})
        cpu = end.get("cpu_utilization_percent", {})

        timestamp = start.get("timestamp", {}).get("time", "")
        timestamp = datetime.strptime(timestamp, "%a, %d %b %Y %H:%M:%S %Z").isoformat()

        rel_path = str(Path(file_path).relative_to(base_dir))

        sent = end.get("sum_sent", {})
        received = end.get("sum_received", {})

        connected = start.get("connected", [{}])[0]  # local/remote host info

        return {
            "path": rel_path,
            "timestamp": timestamp,

            "local_host": connected.get("local_host", ""),
            "remote_host": connected.get("remote_host", ""),
            "tcp_mss_default": start.get("tcp_mss_default"),
            #"sndbuf_actual": start.get("sndbuf_actual"),
            #"rcvbuf_actual": start.get("rcvbuf_actual"),

            "blksize": test_start.get("blksize"),
            "duration": (test_start.get("duration")),
            "omit": test_start.get("omit"),
            "protocol": test_start.get("protocol"),
            "num_streams": test_start.get("num_streams"),
            "reverse": test_start.get("reverse"),
            "port": start.get("connecting_to", {}).get("port"),
            "congestion": end.get("sender_tcp_congestion"),

            "bytes_sent": human_readable_bytes(sent.get("bytes", 0)),
            "bps_sent": human_readable_bps(sent.get("bits_per_second", 0)),
            "retransmissions": sent.get("retransmits", 0),

            "bytes_received": human_readable_bytes(received.get("bytes", 0)),
            "bps_received": human_readable_bps(received.get("bits_per_second", 0)),

            "host_cpu_total": round(cpu.get("host_total", 0), 1),
            "host_user": round(cpu.get("host_user", 0), 1),
            "host_system": round(cpu.get("host_system", 0), 1),
            "remote_cpu_total": round(cpu.get("remote_total", 0), 1),
            "remote_user": round(cpu.get("remote_user", 0), 1),
            "remote_system": round(cpu.get("remote_system", 0), 1),
        }

    except Exception as e:
        print(f"[ERROR] Failed to parse {file_path}: {e}")
        return None


"""def find_cons_iperf_jsons(base_dir):
    files = []
    for root, _, filenames in os.walk(base_dir):
        for name in filenames:
            if name.endswith(".json") and "iperf" in name:
                files.append(os.path.join(root, name))
    return files"""

def find_cons_iperf_jsons(base_dir):
    """Find all iperf JSON files within the experiment directory."""
    base_dir = os.path.expanduser(base_dir)
    iperf_jsons = []
    for root, _, files in os.walk(base_dir):
        for file in files:
            if file.startswith("iperf_") and file.endswith(".json"):
                full_path = os.path.join(root, file)
                print(f"[DEBUG] Found iperf JSON: {full_path}")
                iperf_jsons.append(full_path)
    return iperf_jsons


def cons_all_iperf_jsons(base_dir):
    iperf_files = find_cons_iperf_jsons(base_dir)
    print(f"[INFO] Discovered {len(iperf_files)} iperf JSON files.")

    records = []
    for i, file in enumerate(iperf_files, 1):
        print(f"[{i}/{len(iperf_files)}] Processing: {file}")
        record = cons_iperf_jsons(file, base_dir)
        if record:
            records.append(record)

    print(f"[INFO] Successfully parsed {len(records)} records.")

    df = pd.DataFrame(records)
    if not df.empty:
        df = df.sort_values(by="path").reset_index(drop=True)
        #print("\n[PREVIEW] Sorted DataFrame:")
        #print(df.head(20))
    else:
        print("\n[WARNING] No valid iperf records found.")

    print("\n[FINISHED] Extraction complete.")
    return df


if __name__ == "__main__":
    BASE_DIR = Path("/home/seena/Projects/chameleon/chi_mnt/exps/exp2/cons")
    df_iperf = cons_all_iperf_jsons(BASE_DIR)

    OUTPUT_DIR = BASE_DIR / "datas"
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    df_iperf.to_csv(OUTPUT_DIR / "extract_data_1.csv", index=False)
    print(f"[INFO] Saved full DataFrame to {OUTPUT_DIR / 'extract_data_1.csv'}")
