import time
import subprocess
import os

output = ""
p = subprocess.run("pkill -f main.py", shell=True, text=True, capture_output=True, check=True)
output += p.stdout
time.sleep(2)   #Time to recover and kill task
os.system("python main.py")
print(output)