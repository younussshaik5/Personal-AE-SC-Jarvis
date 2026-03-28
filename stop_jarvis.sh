#!/bin/bash
# JARVIS v2 - Stop all services

echo "Stopping JARVIS..."

for pidfile in .jarvis.pid .mcp_observer.pid .ui.pid; do
    if [ -f "$pidfile" ]; then
        PID=$(cat "$pidfile")
        if kill -0 "$PID" 2>/dev/null; then
            kill "$PID"
            echo "  Stopped $(basename $pidfile .pid): PID $PID"
        fi
        rm -f "$pidfile"
    fi
done

echo "JARVIS stopped."
