import subprocess
import re
import sys
import time

def start_tunnel(port):
    print(f"Starting tunnel on port {port}...")
    proc = subprocess.Popen(
        ['ssh', '-R', f'80:localhost:{port}', '-o', 'StrictHostKeyChecking=no', 'nokey@localhost.run'],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )
    url = None
    for line in iter(proc.stdout.readline, ''):
        print("TUNNEL:", line.strip())
        match = re.search(r'https://[a-zA-Z0-9.-]+\.lhr\.life', line)
        if match:
            url = match.group(0)
            print(f"FOUND TUNNEL URL: {url}")
            with open("tunnel_url.txt", "w") as f:
                f.write(url)
            break
            
    if url:
        # Keep process alive
        proc.wait()
    else:
        print("Failed to find tunnel URL.")

if __name__ == "__main__":
    start_tunnel(8080)
