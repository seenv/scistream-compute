import psutil
import json
import subprocess, os, argparse, time
from datetime import datetime
from pyroute2 import IPRoute
import struct

def parse_args():
    parser = argparse.ArgumentParser(description="Network and system stats logger")
    parser.add_argument("--log_file", type=str, default='./', help="Path to stats log")
    parser.add_argument("--devname", type=str, default="eno1np0", help="Network interface name to monitor")
    parser.add_argument("--timestep", type=int, default=1, help="Time interval in seconds for logging stats")
    return parser.parse_args()

def read_stat(path):
    with open(path) as f:
        return int(f.read().strip())

def get_sysctl_value(param):
    try:
        return subprocess.check_output(["sysctl", "-n", param], encoding="utf-8").strip()
    except subprocess.CalledProcessError:
        return "N/A"

def get_mtu(interface):
    stats = psutil.net_if_stats()
    return stats[interface].mtu if interface in stats else "N/A"

def net_stats(devname):
    RX = read_stat(f"/sys/class/net/{devname}/statistics/rx_bytes")
    TX = read_stat(f"/sys/class/net/{devname}/statistics/tx_bytes")
    RX_DROP = read_stat(f"/sys/class/net/{devname}/statistics/rx_dropped")
    TX_DROP = read_stat(f"/sys/class/net/{devname}/statistics/tx_dropped")
    return RX, TX, RX_DROP, TX_DROP

def mem_cpu(prev_disk):
    per_cpu = psutil.cpu_percent(percpu=True, interval=None)
    total_mem = psutil.virtual_memory().percent

    disk = psutil.disk_io_counters()
    total_disk_read = (disk.read_bytes - prev_disk.read_bytes) / (1024 * 1024)
    total_disk_write = (disk.write_bytes - prev_disk.write_bytes) / (1024 * 1024)

    return per_cpu, total_mem, total_disk_read, total_disk_write, disk

def parse_fq_options(raw_bytes):
    fields = {
        'limit': (0, '<I'),
        'flow_limit': (4, '<I'),
        'quantum': (8, '<I'),
        'initial_quantum': (12, '<I'),
        'maxrate': (16, '<I'),
        'low_rate_threshold': (20, '<I'),
        'refill_delay': (24, '<I'),
        'timer_slack': (28, '<I'),
        'horizon': (32, '<I'),
        'horizon_drop': (36, '<I'),
    }

    results = {}
    for name, (offset, fmt) in fields.items():
        try:
            value = struct.unpack_from(fmt, raw_bytes, offset)[0]
            results[name] = value
        except struct.error:
            results[name] = None

    results['quantum'] = f"{results['quantum']} bytes"
    results['initial_quantum'] = f"{results['initial_quantum']} bytes"
    results['maxrate'] = f"{(results['maxrate'] * 8 / 1e9):.1f} Gbit" if results['maxrate'] else None
    results['low_rate_threshold'] = f"{(results['low_rate_threshold'] * 8 / 1e3):.0f} Kbit" if results['low_rate_threshold'] else None
    results['refill_delay'] = f"{results['refill_delay']} ms"
    results['timer_slack'] = f"{results['timer_slack']} µs"
    results['horizon'] = f"{results['horizon'] / 1000} s"
    results['horizon_drop'] = f"{results['horizon_drop']}" 
    return results

def main():
    print("Starting system and network stats logger-------------------------------------")
    args = parse_args()
    prev_disk = psutil.disk_io_counters()
    #logs = os.path.join(args.output_dir, 'sys_stats.jsonl')
    logs = args.log_file
    print(f"-------------------------------- logs address {logs}\n")

    # gather fq qdisc metadata
    ip = IPRoute()
    links = ip.link_lookup(ifname=args.devname)
    qdiscs = ip.get_qdiscs(links[0]) if links else []
    parsed = {}
    for q in qdiscs:
        if q.get('kind') == 'fq':
            for attr in q['attrs']:
                if attr[0] == 'TCA_OPTIONS':
                    hexstr = attr[1]
                    if isinstance(hexstr, str):
                        raw_bytes = bytes.fromhex(hexstr.replace(":", ""))
                        parsed = parse_fq_options(raw_bytes)

    metadata = {
        "tcp_congestion_control": get_sysctl_value("net.ipv4.tcp_congestion_control"),
        "rmem_max": get_sysctl_value("net.core.rmem_max"),
        "wmem_max": get_sysctl_value("net.core.wmem_max"),
        "tcp_rmem": get_sysctl_value("net.ipv4.tcp_rmem"),
        "tcp_wmem": get_sysctl_value("net.ipv4.tcp_wmem"),
        "interface_mtu": get_mtu(args.devname),
        "default_qdisc": get_sysctl_value("net.core.default_qdisc"),
        "quantum": parsed.get('quantum', 'N/A')
    }

    try:
        with open(logs, "a") as f:
            f.write(json.dumps({"metadata": metadata}) + "\n")
            f.flush()

            # init counter read
            RX1, TX1, RX_DROP1, TX_DROP1 = net_stats(args.devname)
            #t1 = time.time()               #to measure more accurately 
            next_run = time.time() + args.timestep

            while True:
                # leep so that log interval matches timestep, regardless of processing delays
                sleep_time = next_run - time.time()
                if sleep_time > 0:
                    time.sleep(sleep_time)
                actual_time = time.time()
                time_delta = args.timestep
                
                #time.sleep(args.timestep)              #to measure more accurately 
                #t2 = time.time()
                #RX2, TX2, RX_DROP2, TX_DROP2 = net_stats(args.devname)
                #time_delta = t2 - t1
                #rx_gbps = (RX2 - RX1) * 8 / time_delta / 1e9

                # read again
                RX2, TX2, RX_DROP2, TX_DROP2 = net_stats(args.devname)

                # throughput (Gbps)
                rx_gbps = (RX2 - RX1) * 8 / time_delta / 1e9
                tx_gbps = (TX2 - TX1) * 8 / time_delta / 1e9

                # packet drops per second (true rate)
                rx_drop_rate = (RX_DROP2 - RX_DROP1) / time_delta
                tx_drop_rate = (TX_DROP2 - TX_DROP1) / time_delta

                # total drop stats
                total_rx_drop = RX_DROP2
                total_tx_drop = TX_DROP2

                timestamp = datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S")

                per_cpu, total_mem, total_disk_read, total_disk_write, prev_disk = mem_cpu(prev_disk)
                total_cpu = sum(per_cpu) / len(per_cpu)

                log_entry = {
                    "timestamp": timestamp,
                    "total_cpu": round(total_cpu, 2),
                    "total_memory": round(total_mem, 2),
                    "disk_read_MB": round(total_disk_read, 2),
                    "disk_write_MB": round(total_disk_write, 2),
                    "net_rx_Gbps": round(rx_gbps, 2),
                    "net_tx_Gbps": round(tx_gbps, 2),
                    "rx_drop/s": rx_drop_rate,
                    "tx_drop/s": tx_drop_rate,
                    "total_rx_dropped": total_rx_drop,
                    "total_tx_dropped": total_tx_drop,
                    "per_cpu": [round(cpu, 2) for cpu in per_cpu]
                }
                f.write(json.dumps(log_entry) + "\n")
                f.flush()

                # next interval
                RX1, TX1, RX_DROP1, TX_DROP1 = RX2, TX2, RX_DROP2, TX_DROP2
                next_run += args.timestep
                
        print("SAVING THE system and network stats logger------------------------------------- \n")
    except KeyboardInterrupt:
        logging.info(f"\nLogging stopped. Data saved in {logs}")

if __name__ == "__main__":
    main()
