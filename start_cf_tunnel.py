import subprocess
import re

print("Starting cloudflared tunnel...")
proc = subprocess.Popen(
    ['./cloudflared-linux-amd64', 'tunnel', '--url', 'http://localhost:8080'],
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True
)

url = None
for line in iter(proc.stdout.readline, ''):
    print("TUNNEL:", line.strip())
    match = re.search(r'https://[a-zA-Z0-9.-]+\.trycloudflare\.com', line)
    if match:
        url = match.group(0)
        print(f"FOUND TUNNEL URL: {url}")
        with open("tunnel_url.txt", "w") as f:
            f.write(url)
        break

if url:
    # Continuously read and print so the buffer doesn't fill up
    for line in iter(proc.stdout.readline, ''):
        pass
    proc.wait()
