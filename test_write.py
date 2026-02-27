import os
import sys

try:
    with open('test_log.txt', 'w') as f:
        f.write("Test OK\n")
        f.write(f"CWD: {os.getcwd()}\n")
        f.write(f"FILE: {__file__}\n")
    print("File written successfully")
except Exception as e:
    print(f"Error: {e}")
