#!/bin/bash
echo "=== SYSTEM DIAGNOSIS ==="
echo "Date: $(date)"
echo "Hostname: $(hostname)"
echo ""

echo "--- UPTIME ---"
uptime
echo ""

echo "--- DISK USAGE ---"
df -h
echo ""

echo "--- MEMORY USAGE ---"
free -m
echo ""

echo "--- TOP PROCESSES (CPU) ---"
ps aux --sort=-%cpu | head -n 6
echo ""

echo "--- LAST 10 DMESG ---"
dmesg | tail -n 10
echo ""
echo "=== END DIAGNOSIS ==="
