import threading
import time
import ssl
import socket
import tempfile
import os

SERVER_IP = "127.0.0.1"
PORT = 5000
BUFFER_SIZE = 4096

def make_ssl_socket():
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE
    raw = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    wrapped = context.wrap_socket(raw, server_hostname=SERVER_IP)
    wrapped.connect((SERVER_IP, PORT))
    return wrapped

def client_task(client_id):
    try:
        start = time.time()
        client = make_ssl_socket()
        song_list = client.recv(4096).decode().strip()
        client.sendall(b"PLAY|1")

        size_header = b""
        while b"\n" not in size_header:
            size_header += client.recv(64)

        expected = int(size_header.decode().strip().split("|")[1])
        received = 0
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")

        while received < expected:
            chunk = client.recv(min(BUFFER_SIZE, expected - received))
            if not chunk:
                break
            tmp.write(chunk)
            received += len(chunk)

        tmp.close()
        client.close()
        os.unlink(tmp.name)

        duration = time.time() - start
        speed = (received * 8) / (duration * 1_000_000)
        print(f"[CLIENT {client_id:02d}] ✅ {received} bytes | {duration:.2f}s | {speed:.2f} Mbps")

    except Exception as e:
        print(f"[CLIENT {client_id:02d}] ❌ {e}")

def run_load_test(n=10):
    print(f"\n{'='*50}")
    print(f"  LOAD TEST — {n} simultaneous clients")
    print(f"{'='*50}\n")
    threads = [threading.Thread(target=client_task, args=(i,)) for i in range(1, n+1)]
    start = time.time()
    for t in threads: t.start()
    for t in threads: t.join()
    print(f"\n Total time: {time.time()-start:.2f}s")
    print(f"{'='*50}")

if __name__ == "__main__":
    n = input("Number of clients to simulate (default 10): ").strip()
    run_load_test(int(n) if n.isdigit() else 10)