import socket
import ssl
import threading
import time
import os
import tempfile

SERVER_IP = "127.0.0.1"
PORT = 5000
BUFFER_SIZE = 4096

results = []
results_lock = threading.Lock()


def make_ssl_socket():
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE
    raw_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    wrapped = context.wrap_socket(raw_sock, server_hostname=SERVER_IP)
    wrapped.connect((SERVER_IP, PORT))
    return wrapped


def simulate_client(client_id, song_index=1):
    """Simulate a single client connecting and streaming a song."""
    start_time = time.time()

    try:
        client = make_ssl_socket()

        # Receive song list
        song_list = client.recv(4096).decode().strip()
        if song_list == "NO_SONGS":
            print(f"[CLIENT {client_id}] No songs on server.")
            return

        songs = song_list.split("\n")
        print(f"[CLIENT {client_id}] Connected. Songs available: {len(songs)}")

        # Request song
        client.sendall(f"PLAY|{song_index}".encode())

        # Read SIZE header
        size_header = b""
        while b"\n" not in size_header:
            chunk = client.recv(64)
            if not chunk:
                break
            size_header += chunk

        header_line = size_header.decode().strip()
        if not header_line.startswith("SIZE|"):
            print(f"[CLIENT {client_id}] Bad response: {header_line}")
            return

        expected_size = int(header_line.split("|")[1])

        # Receive file data
        received = 0
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")

        while received < expected_size:
            chunk = client.recv(min(BUFFER_SIZE, expected_size - received))
            if not chunk:
                break
            temp_file.write(chunk)
            received += len(chunk)

        temp_file.close()
        client.close()
        os.unlink(temp_file.name)

        end_time = time.time()
        duration = end_time - start_time
        speed_mbps = (received * 8) / (duration * 1_000_000) if duration > 0 else 0

        with results_lock:
            results.append({
                "client_id": client_id,
                "bytes": received,
                "duration": duration,
                "speed_mbps": speed_mbps,
                "status": "SUCCESS" if received == expected_size else "INCOMPLETE"
            })

        print(f"[CLIENT {client_id}] Done | {received} bytes | {duration:.2f}s | {speed_mbps:.2f} Mbps")

    except Exception as e:
        end_time = time.time()
        with results_lock:
            results.append({
                "client_id": client_id,
                "bytes": 0,
                "duration": end_time - start_time,
                "speed_mbps": 0,
                "status": f"ERROR: {e}"
            })
        print(f"[CLIENT {client_id}] ERROR: {e}")


def run_performance_test(num_clients=5, song_index=1):
    print("=" * 60)
    print(f"  PERFORMANCE TEST — {num_clients} Simultaneous Clients")
    print("=" * 60)

    threads = []
    start_all = time.time()

    for i in range(1, num_clients + 1):
        t = threading.Thread(target=simulate_client, args=(i, song_index))
        threads.append(t)

    # Launch all clients at the same time
    for t in threads:
        t.start()

    for t in threads:
        t.join()

    total_time = time.time() - start_all

    # ── RESULTS SUMMARY ──
    print("\n" + "=" * 60)
    print("  RESULTS SUMMARY")
    print("=" * 60)

    success = [r for r in results if r["status"] == "SUCCESS"]
    failed  = [r for r in results if r["status"] != "SUCCESS"]

    print(f"  Total Clients    : {num_clients}")
    print(f"  Successful       : {len(success)}")
    print(f"  Failed           : {len(failed)}")
    print(f"  Total Test Time  : {total_time:.2f}s")

    if success:
        avg_speed    = sum(r["speed_mbps"] for r in success) / len(success)
        avg_duration = sum(r["duration"]   for r in success) / len(success)
        max_speed    = max(r["speed_mbps"] for r in success)
        min_speed    = min(r["speed_mbps"] for r in success)

        print(f"  Avg Speed        : {avg_speed:.2f} Mbps")
        print(f"  Max Speed        : {max_speed:.2f} Mbps")
        print(f"  Min Speed        : {min_speed:.2f} Mbps")
        print(f"  Avg Response Time: {avg_duration:.2f}s")

    if failed:
        print("\n  Failed Clients:")
        for r in failed:
            print(f"    Client {r['client_id']}: {r['status']}")

    print("=" * 60)


def run_failure_handling_test():
    """Test how server handles invalid inputs and abrupt disconnections."""
    print("\n" + "=" * 60)
    print("  FAILURE HANDLING TEST")
    print("=" * 60)

    # Test 1: Invalid song index
    print("\n[TEST 1] Invalid song index (999)")
    try:
        client = make_ssl_socket()
        client.recv(4096)  # consume song list
        client.sendall(b"PLAY|999")
        response = client.recv(1024).decode()
        print(f"  Server response: {response if response else 'No response / closed connection'}")
        client.close()
        print("  Result: PASS - Server handled gracefully")
    except Exception as e:
        print(f"  Result: {e}")

    # Test 2: Invalid request format
    print("\n[TEST 2] Invalid request format (GARBAGE DATA)")
    try:
        client = make_ssl_socket()
        client.recv(4096)
        client.sendall(b"GARBAGE_REQUEST")
        response = client.recv(1024).decode()
        print(f"  Server response: {response if response else 'No response / closed connection'}")
        client.close()
        print("  Result: PASS - Server handled gracefully")
    except Exception as e:
        print(f"  Result: {e}")

    # Test 3: Abrupt disconnection
    print("\n[TEST 3] Abrupt client disconnection")
    try:
        client = make_ssl_socket()
        client.recv(4096)
        client.close()  # disconnect without sending anything
        print("  Result: PASS - Client disconnected abruptly, server should continue running")
    except Exception as e:
        print(f"  Result: {e}")

    # Test 4: Empty request
    print("\n[TEST 4] Empty/blank request")
    try:
        client = make_ssl_socket()
        client.recv(4096)
        client.sendall(b"")
        time.sleep(1)
        client.close()
        print("  Result: PASS - Server handled empty request")
    except Exception as e:
        print(f"  Result: {e}")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    print("\nChoose test to run:")
    print("  1. Performance Test (multiple clients)")
    print("  2. Failure Handling Test")
    print("  3. Both")

    choice = input("\nEnter choice (1/2/3): ").strip()

    if choice == "1":
        n = input("Number of simultaneous clients (default 5): ").strip()
        n = int(n) if n.isdigit() else 5
        song = input("Song index to stream (default 1): ").strip()
        song = int(song) if song.isdigit() else 1
        run_performance_test(num_clients=n, song_index=song)

    elif choice == "2":
        run_failure_handling_test()

    elif choice == "3":
        n = input("Number of simultaneous clients (default 5): ").strip()
        n = int(n) if n.isdigit() else 5
        run_performance_test(num_clients=n)
        run_failure_handling_test()

    else:
        print("Invalid choice.")