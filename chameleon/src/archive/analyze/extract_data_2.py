import pandas as pd
from pathlib import Path
import re


def parse_path_info(path_str):
    parts = Path(path_str).parts
    congestion_proxy = parts[0].split("_")
    parallel = parts[1]
    test_info = parts[2]
    port_file = parts[3]

    proxy = congestion_proxy[1]
    p_val = int(parallel[1:])

    match = re.match(r"T(\d+)_R(\d+)", test_info)
    run = int(match.group(2))

    return {
        "proxy": proxy,
        "parallel": p_val,
        "run": run
    }


def parse_bytes(val):
    if isinstance(val, str):
        num, unit = val.split()
        num = float(num)
        return num * {"B": 1, "KB": 1024, "MB": 1024**2, "GB": 1024**3}.get(unit, 1)
    return val


def parse_bps(val):
    if isinstance(val, str):
        num, unit = val.split()
        num = float(num)
        return num * {"bps": 1, "Kbps": 1e3, "Mbps": 1e6, "Gbps": 1e9}.get(unit, 1)
    return val


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


def summarize_iperf_dataframe(csv_path):
    df = pd.read_csv(csv_path)

    # Extract structured metadata from path
    path_info_df = df["path"].apply(parse_path_info).apply(pd.Series)
    df[path_info_df.columns] = path_info_df

    # Parse numeric bytes/bps
    for col in ["bytes_sent", "bytes_received"]:
        df[col] = df[col].apply(parse_bytes)
    for col in ["bps_sent", "bps_received"]:
        df[col] = df[col].apply(parse_bps)

    # Group
    df_grouped = (
        df.groupby(["congestion", "proxy", "parallel", "duration", "run"])
        .agg({
            "bytes_sent": "sum",
            "bps_sent": "sum",
            "retransmissions": "sum",
            "bytes_received": "sum",
            "bps_received": "sum",
            "host_cpu_total": "mean",
            "host_user": "mean",
            "host_system": "mean",
            "remote_cpu_total": "mean",
            "remote_user": "mean",
            "remote_system": "mean",
        })
        .reset_index()
    )

    # Format: bytes, bps → human readable; float cols → 1 decimal
    df_grouped["bytes_sent"] = df_grouped["bytes_sent"].apply(human_readable_bytes)
    df_grouped["bps_sent"] = df_grouped["bps_sent"].apply(human_readable_bps)
    df_grouped["bytes_received"] = df_grouped["bytes_received"].apply(human_readable_bytes)
    df_grouped["bps_received"] = df_grouped["bps_received"].apply(human_readable_bps)

    for col in [
        "host_cpu_total", "host_user", "host_system",
        "remote_cpu_total", "remote_user", "remote_system"
    ]:
        df_grouped[col] = df_grouped[col].round(1)

    return df_grouped


if __name__ == "__main__":
    BASE_DIR = Path("/home/seena/Projects/chameleon/chi_mnt/exps/exp2/cons")
    csv_input_path = BASE_DIR / "datas" / "extract_data_1.csv"

    df_summary = summarize_iperf_dataframe(csv_input_path)

    OUTPUT_DIR = BASE_DIR / "datas"
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    output_path = OUTPUT_DIR / "extract_data_2.csv"
    df_summary.to_csv(output_path, index=False)

    print(f"[INFO] Saved readable summary to {output_path}")