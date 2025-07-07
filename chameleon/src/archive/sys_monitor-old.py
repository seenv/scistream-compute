import psutil
import time, csv, json, os
from datetime import datetime
import argparse




def parse_args():
    parser = argparse.ArgumentParser(description="description",)
    parser.add_argument("--log_file", type=str, required=True, help="Path to the log file for storing stats.")
    parser.add_argument("--devname", type=str, default="eno1np0", help="Network interface name to monitor.")
    parser.add_argument("--timestep", type=int, default=1, help="Time interval in seconds for logging stats.")

    return parser.parse_args()

def trans_rate(rx_bytes, tx_bytes, dev, timestep):
    """Return the transmission rate of an interface under Linux in MB/s"""
    
    """
    /sys/class/net/{}/statistics/
    collisions  rx_compressed   rx_errors   rx_length_errors    rx_over_errors       
    tx_bytes    tx_dropped  tx_heartbeat_errors multicast   rx_crc_errors        
    rx_fifo_errors  rx_missed_errors    rx_packets  tx_carrier_errors              
    tx_packets  rx_bytes    rx_dropped  rx_frame_errors rx_nohandler    tx_errors 
    tx_compressed   tx_fifo_errors  tx_window_errors    tx_aborted_errors   
    """
    
    rx_path = "/sys/class/net/{}/statistics/rx_bytes".format(dev)
    tx_path = "/sys/class/net/{}/statistics/tx_bytes".format(dev)

    with open(rx_path, "r") as rx_f:
        rx_bytes[:] = rx_bytes[-1:] + [int(rx_f.read())]

    with open(tx_path, "r") as tx_f:
        tx_bytes[:] = tx_bytes[-1:] + [int(tx_f.read())]

    RX = (((rx_bytes[-1] - rx_bytes[-2]) / timestep) / (1024 * 1024) if len(rx_bytes) > 1 else 0)
    TX = (((tx_bytes[-1] - tx_bytes[-2]) / timestep) / (1024 * 1024) if len(tx_bytes) > 1 else 0)

    return RX, TX

def retrans(rx_dropped, tx_dropped, dev):
    """Return the transmission rate of an interface under Linux in MB/s"""

    rx_path = "/sys/class/net/{}/statistics/rx_dropped".format(dev)
    tx_path = "/sys/class/net/{}/statistics/tx_dropped".format(dev)

    with open(rx_path, "r") as rx_f:
        rx_dropped[:] = rx_dropped[-1:] + [int(rx_f.read())]

    with open(tx_path, "r") as tx_f:
        tx_dropped[:] = tx_dropped[-1:] + [int(tx_f.read())]
        
    RX_DROP = (True if rx_dropped[-1] - rx_dropped[-2] else False) if len(rx_dropped) > 1 else False
    TX_DROP = (True if tx_dropped[-1] - tx_dropped[-2] else False) if len(tx_dropped) > 1 else False
 
    return RX_DROP, TX_DROP

def mem_cpu(prev_disk):
    """Get CPU, memory, and disk read/write since last check."""
    indiv_cpu = psutil.cpu_percent(percpu=True, interval=None)
    total_cpu = psutil.cpu_percent(percpu=False)
    total_mem = psutil.virtual_memory().percent

    disk = psutil.disk_io_counters()
    total_disk_read = (disk.read_bytes - prev_disk.read_bytes) / (1024 * 1024)
    total_disk_write = (disk.write_bytes - prev_disk.write_bytes) / (1024 * 1024)

    return indiv_cpu, total_cpu, total_mem, total_disk_read, total_disk_write, disk

"""
exp = "iperfP3_5100_5102"
log_file = "/home/seena/pcap/perf3.18_capture/{}/rss_stats.csv".format(exp)
#log_file = '/home/seena/Projects/globus-stream/scistream-compute/src/analysis/rss_stats.csv'
#devname = "enp0s31f6" 
timestep = 1
"""


def main():
    args = parse_args()

    rx_bytes, tx_bytes = [0], [0]
    rx_dropped, tx_dropped = [0], [0]
    prev_disk = psutil.disk_io_counters()
    logs = path.join(args.log_file, 'sys_stats.json')
    
    with open(args.log_file, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "Timestamp", "Total CPU (%)", "Total Memory (%)",
            "Total Disk Read (MB)", "Total Disk Write (MB)",
            "Total Net RX (MB)", "Total Net TX (MB)", 
            "RX Dropped", "TX Dropped"
        ])

        #print("Logging system-wide stats... Press Ctrl + C to stop.")
        next_run = time.time()

        try:
            while True:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                indiv_cpu, total_cpu, total_mem, total_disk_read, total_disk_write, prev_disk = mem_cpu(prev_disk)
                RX, TX = trans_rate(rx_bytes, tx_bytes, args.devname, args.timestep)
                RX_DROP, TX_DROP = retrans(rx_dropped, tx_dropped, args.devname)
                
                writer.writerow([
                    timestamp, total_cpu, total_mem,
                    total_disk_read, total_disk_write,
                    RX, TX, RX_DROP, TX_DROP, indiv_cpu
                ])
                f.flush()

                print(f"{timestamp} - CPU: {total_cpu}% | Mem: {total_mem:.1f}% | "
                    f"Disk R/W: {total_disk_read:.2f}/{total_disk_write:.2f} MB | "
                    f"NET RX/TX: {RX:.2f}/{TX:.2f} MB | "
                    f"RX Dropped: {RX_DROP} | TX Dropped: {TX_DROP} | "
                    f"Individual CPU: {indiv_cpu}"
                )

                # Wait until the next scheduled run time
                next_run += args.timestep
                sleep_time = next_run - time.time()
                if sleep_time > 0:
                    time.sleep(sleep_time)

        except KeyboardInterrupt:
            print(f"\nLogging stopped. Data saved in {logs}")
        
        
if __name__ == "__main__":
    main()