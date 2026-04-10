import socket
import ssl
import threading
import os
import time

HOST = 'localhost'
PORT = 5000
CHUNK_SIZE = 4096

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SONG_FOLDER = os.path.join(BASE_DIR, "songs")

CERT_FILE = os.path.join(BASE_DIR, "cert.pem")
KEY_FILE = os.path.join(BASE_DIR, "key.pem")

connected_clients = 0
lock = threading.Lock()


def handle_client(conn, addr):
    global connected_clients

    with lock:
        connected_clients += 1
        print(f"[CONNECTED] {addr} | Active Clients: {connected_clients}")

    try:
        # ---- SEND SONG LIST ----
        if not os.path.exists(SONG_FOLDER):
            os.makedirs(SONG_FOLDER)

        songs = sorted([s for s in os.listdir(SONG_FOLDER) if s.endswith(".mp3")])

        if not songs:
            conn.send(b"NO_SONGS")
            print(f"[INFO] No songs found in {SONG_FOLDER}")
            return

        song_list = "\n".join(f"{i+1}. {song}" for i, song in enumerate(songs))
        conn.sendall(song_list.encode())
        print(f"[SENT SONG LIST] {len(songs)} songs to {addr}")

        # ---- RECEIVE REQUESTS IN A LOOP ----
        while True:
            try:
                request = conn.recv(1024).decode().strip()
            except Exception:
                break

            if not request:
                break

            if request == "DISCONNECT":
                print(f"[DISCONNECT REQUEST] {addr}")
                break

            if not request.startswith("PLAY|"):
                print(f"[UNKNOWN REQUEST] {request} from {addr}")
                conn.sendall(b"ERROR|INVALID_REQUEST")
                continue

            try:
                index = int(request.split("|")[1]) - 1
            except (ValueError, IndexError):
                conn.sendall(b"ERROR|INVALID_INDEX")
                continue

            if index < 0 or index >= len(songs):
                conn.sendall(b"ERROR|OUT_OF_RANGE")
                continue

            selected_song = os.path.join(SONG_FOLDER, songs[index])
            file_size = os.path.getsize(selected_song)
            print(f"[STREAMING] {songs[index]} ({file_size} bytes) to {addr}")

            # Send file size header so client knows when transfer is done
            conn.sendall(f"SIZE|{file_size}\n".encode())

            total_bytes = 0
            start_time = time.time()

            with open(selected_song, "rb") as f:
                while True:
                    data = f.read(CHUNK_SIZE)
                    if not data:
                        break
                    conn.sendall(data)
                    total_bytes += len(data)

            end_time = time.time()
            duration = end_time - start_time

            if duration > 0:
                speed = (total_bytes * 8) / (duration * 1_000_000)
                print(f"[PERFORMANCE] {addr} | {songs[index]} | {speed:.2f} Mbps | {total_bytes} bytes in {duration:.2f}s")
            else:
                print(f"[COMPLETE] {addr} | {songs[index]}")

    except Exception as e:
        print(f"[ERROR] {addr}: {e}")

    finally:
        try:
            conn.close()
        except Exception:
            pass

        with lock:
            connected_clients -= 1
            print(f"[DISCONNECTED] {addr} | Active Clients: {connected_clients}")


def start_server():
    if not os.path.exists(CERT_FILE) or not os.path.exists(KEY_FILE):
        print("[ERROR] SSL cert/key not found!")
        print("Generate them with:")
        print("  openssl req -x509 -newkey rsa:2048 -keyout key.pem -out cert.pem -days 365 -nodes")
        return

    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(certfile=CERT_FILE, keyfile=KEY_FILE)

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((HOST, PORT))
    sock.listen(5)

    print(f"[SECURE SERVER STARTED] Listening on {HOST}:{PORT}")
    print(f"[SONG FOLDER] {SONG_FOLDER}")

    try:
        with context.wrap_socket(sock, server_side=True) as ssock:
            while True:
                conn, addr = ssock.accept()
                thread = threading.Thread(target=handle_client, args=(conn, addr), daemon=True)
                thread.start()
    except KeyboardInterrupt:
        print("\n[SERVER STOPPED]")


if __name__ == "__main__":
    start_server()