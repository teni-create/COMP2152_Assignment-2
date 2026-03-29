"""
Author: Ogun Oluwateniola
Assignment: #2
Description: Port Scanner — A tool that scans a target machine for open network ports
"""





# TODO: Import the required modules (Step ii)
# socket, threading, sqlite3, os, platform, datetime
import socket
import threading
import sqlite3
import os
import platform
import datetime

# TODO: Print Python version and OS name (Step iii)
print(f"Python Version: {platform.python_version()}")
print(f"Operating System: {os.name}")

# TODO: Create the common_ports dictionary (Step iv)
# Add a 1-line comment above it explaining what it stores

# This dictionary stores common port numbers and their associated service names.
common_ports = {
    21: "FTP",
    22: "SSH",
    23: "Telnet",
    25: "SMTP",
    53: "DNS",
    80: "HTTP",
    110: "POP3",
    143: "IMAP",
    443: "HTTPS",
    3306: "MySQL",
    3389: "RDP",
    8080: "HTTP-Alt"
}

# TODO: Create the NetworkTool parent class (Step v)
# - Constructor: takes target, stores as private self.__target
# - @property getter for target
# - @target.setter with empty string validation
# - Destructor: prints "NetworkTool instance destroyed"
class NetworkTool:
    def __init__(self, target):
        self.__target = target

# Q3: What is the benefit of using @property and @target.setter?
# Using @property and @target.setter lets the class control how the target
    # value is accessed and changed without exposing the private variable directly.
    # This makes the code safer because the setter can validate the new value first.
    # In this program, it prevents the target from being changed to an empty string.
    @property
    def target(self):
        return self.__target

    @target.setter
    def target(self, value):
        if value != "":
            self.__target = value
        else:
            print("Error: Target cannot be empty")

    def __del__(self):
        print("NetworkTool instance destroyed")


# Q1: How does PortScanner reuse code from NetworkTool?
# PortScanner reuses code from NetworkTool through inheritance instead of
# rewriting the same target-related code again. For example, when
# PortScanner calls super().__init__(target), the parent class handles
# storing the target value, so the child class can focus on scanning ports.
class PortScanner(NetworkTool):
    def __init__(self, target):
        super().__init__(target)
        self.scan_results = []
        self.lock = threading.Lock()

    def __del__(self):
        print("PortScanner instance destroyed")
        super().__del__()

# TODO: Create the PortScanner child class that inherits from NetworkTool (Step vi)
# - Constructor: call super().__init__(target), initialize self.scan_results = [], self.lock = threading.Lock()
# - Destructor: print "PortScanner instance destroyed", call super().__del__()
    def scan_port(self, port):
        sock = None

        # Q4: What would happen without try-except here?
        # Without try-except, a socket problem like a timeout or unreachable
        # machine could stop the whole program while scanning. That means one
        # bad connection could crash the scanner before it finishes the rest of
        # the ports. Using try-except makes the program more reliable and lets it continue scanning.
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex((self.target, port))

            if result == 0:
                status = "Open"
            else:
                status = "Closed"

            service_name = common_ports.get(port, "Unknown")

            self.lock.acquire()
            self.scan_results.append((port, status, service_name))
            self.lock.release()

        except socket.error as e:
            print(f"Error scanning port {port}: {e}")

        finally:
            if sock is not None:
                sock.close()

    def get_open_ports(self):
        return [result for result in self.scan_results if result[1] == "Open"]

    # Q2: Why do we use threading instead of scanning one port at a time?
    # We use threading so the program can scan many ports at the same time
    # instead of waiting for one port to finish before starting the next one.
    # If 1024 ports were scanned one by one, the program would be much slower,
    # especially because each connection attempt can take time to respond or timeout.
    def scan_range(self, start_port, end_port):
        threads = []

        for port in range(start_port, end_port + 1):
            thread = threading.Thread(target=self.scan_port, args=(port,))
            threads.append(thread)

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()


def save_results(target, results):
    conn = None

    try:
        conn = sqlite3.connect("scan_history.db")
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS scans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                target TEXT,
                port INTEGER,
                status TEXT,
                service TEXT,
                scan_date TEXT
            )
        """)

        for port, status, service in results:
            cursor.execute("""
                INSERT INTO scans (target, port, status, service, scan_date)
                VALUES (?, ?, ?, ?, ?)
            """, (target, port, status, service, str(datetime.datetime.now())))

        conn.commit()

    except sqlite3.Error as e:
        print(f"Database error: {e}")

    finally:
        if conn is not None:
            conn.close()


def load_past_scans():
    conn = None

    try:
        conn = sqlite3.connect("scan_history.db")
        cursor = conn.cursor()

        cursor.execute("SELECT target, port, status, service, scan_date FROM scans")
        rows = cursor.fetchall()

        if len(rows) == 0:
            print("No past scans found.")
        else:
            for row in rows:
                target, port, status, service, scan_date = row
                print(f"[{scan_date}] {target} : Port {port} ({service}) - {status}")

    except sqlite3.Error:
        print("No past scans found.")

    finally:
        if conn is not None:
            conn.close()


# ============================================================
# MAIN PROGRAM
# ============================================================
if __name__ == "__main__":
    target = input("Enter target IP address: ").strip()
    if target == "":
        target = "127.0.0.1"

    while True:
        try:
            start_port = int(input("Enter starting port number: "))
            if start_port < 1 or start_port > 1024:
                print("Port must be between 1 and 1024.")
                continue
            break
        except ValueError:
            print("Invalid input. Please enter a valid integer.")

    while True:
        try:
            end_port = int(input("Enter ending port number: "))
            if end_port < 1 or end_port > 1024:
                print("Port must be between 1 and 1024.")
                continue
            if end_port < start_port:
                print("End port must be greater than or equal to start port.")
                continue
            break
        except ValueError:
            print("Invalid input. Please enter a valid integer.")

    scanner = PortScanner(target)

    print(f"Scanning {target} from port {start_port} to {end_port}...")
    scanner.scan_range(start_port, end_port)

    open_ports = scanner.get_open_ports()

    print(f"--- Scan Results for {target} ---")
    for port, status, service in open_ports:
        print(f"Port {port}: {status} ({service})")
    print("------")
    print(f"Total open ports found: {len(open_ports)}")

    save_results(target, scanner.scan_results)

    choice = input("Would you like to see past scan history? (yes/no): ").strip().lower()
    if choice == "yes":
        load_past_scans()

# Q5: New Feature Proposal
# One feature I would add is a risk-level checker for open ports so the scanner
# can label them as high, medium, or low risk. I would use a nested if-statement
# to check each open port and assign a risk label based on the port number or service.
# Diagram: See diagram_101568492.png in the repository root
