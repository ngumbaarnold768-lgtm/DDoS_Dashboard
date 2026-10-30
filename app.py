from flask import Flask, render_template, jsonify
import psutil
import subprocess
import time

app = Flask(__name__)

# Store previous network stats to calculate speed
prev_net = psutil.net_io_counters()
prev_time = time.time()

def get_syn_recv_count():
    """Counts half-open TCP connections (SYN Flood indicator)"""
    try:
        # Using 'ss' which is standard on modern Ubuntu
        output = subprocess.check_output("ss -s | grep -i 'syn' | awk '{print $4}'", shell=True).decode()
        # Fallback to netstat if ss fails or output is empty
        if not output.strip():
            output = subprocess.check_output("netstat -an | grep SYN_RECV | wc -l", shell=True).decode()
        return int(output.strip())
    except:
        return 0

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/stats')
def stats():
    global prev_net, prev_time
    
    # 1. CPU Usage
    cpu_percent = psutil.cpu_percent(interval=0.1)
    
    # 2. SYN_RECV Connections
    syn_recv = get_syn_recv_count()
    
    # 3. Network Traffic (Calculate MB/s)
    current_net = psutil.net_io_counters()
    current_time = time.time()
    
    time_diff = current_time - prev_time
    bytes_sent = current_net.bytes_sent - prev_net.bytes_sent
    bytes_recv = current_net.bytes_recv - prev_net.bytes_recv
    
    mb_sent = (bytes_sent / time_diff) / (1024 * 1024) if time_diff > 0 else 0
    mb_recv = (bytes_recv / time_diff) / (1024 * 1024) if time_diff > 0 else 0
    
    prev_net = current_net
    prev_time = current_time

    return jsonify({
        'cpu': cpu_percent,
        'syn_recv': syn_recv,
        'mb_recv': round(mb_recv, 2),
        'mb_sent': round(mb_sent, 2)
    })

if __name__ == '__main__':
    # Running on 0.0.0.0 so you can access it from your Kali machine or host
    app.run(host='0.0.0.0', port=5000)
(1)