#!/bin/bash

IFACE="eno1np0"
LOG_FILE="net_rate.log"

# Set up clean exit handler
trap "echo 'Monitoring stopped at $(date)' >> $LOG_FILE; exit" SIGINT SIGTERM

# Optional CSV header
echo "Timestamp,RX_Gbps,TX_Gbps,RX_Drop/s,TX_Drop/s,Total_RX_Drop,Total_TX_Drop" >> "$LOG_FILE"

while true; do
  T1=$(date +%s.%N)
  RX1=$(cat /sys/class/net/$IFACE/statistics/rx_bytes)
  TX1=$(cat /sys/class/net/$IFACE/statistics/tx_bytes)
  RX_DROP1=$(cat /sys/class/net/$IFACE/statistics/rx_dropped)
  TX_DROP1=$(cat /sys/class/net/$IFACE/statistics/tx_dropped)

  sleep 1

  T2=$(date +%s.%N)
  RX2=$(cat /sys/class/net/$IFACE/statistics/rx_bytes)
  TX2=$(cat /sys/class/net/$IFACE/statistics/tx_bytes)
  RX_DROP2=$(cat /sys/class/net/$IFACE/statistics/rx_dropped)
  TX_DROP2=$(cat /sys/class/net/$IFACE/statistics/tx_dropped)

  TIME_DELTA=$(echo "$T2 - $T1" | bc -l)

  RX_BYTES_DIFF=$((RX2 - RX1))
  TX_BYTES_DIFF=$((TX2 - TX1))
  RX_DROP_RATE=$((RX_DROP2 - RX_DROP1))
  TX_DROP_RATE=$((TX_DROP2 - TX_DROP1))

  RX_Gbps=$(echo "scale=4; $RX_BYTES_DIFF * 8 / $TIME_DELTA / 1000000000" | bc)
  TX_Gbps=$(echo "scale=4; $TX_BYTES_DIFF * 8 / $TIME_DELTA / 1000000000" | bc)

  TOTAL_RX_DROP=$RX_DROP2
  TOTAL_TX_DROP=$TX_DROP2

  TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
  echo "$TIMESTAMP,$RX_Gbps,$TX_Gbps,$RX_DROP_RATE,$TX_DROP_RATE,$TOTAL_RX_DROP,$TOTAL_TX_DROP" >> "$LOG_FILE"
done


