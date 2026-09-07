import time
import re
import os

last_url = ""
while True:
    if os.path.exists('lhrun.log'):
        with open('lhrun.log', 'r') as f:
            content = f.read()
            match = re.search(r'https://([a-zA-Z0-9.-]+\.lhr\.life)', content)
            if match:
                url = match.group(0)
                if url != last_url:
                    last_url = url
                    with open('tunnel_url.txt', 'w') as out:
                        out.write(url)
                    print("Updated URL:", url)
    time.sleep(2)
