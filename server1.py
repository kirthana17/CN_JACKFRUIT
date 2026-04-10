import socket
import ssl
import threading
import os
import time

HOST = '0.0.0.0'
PORT = 5000
CHUNK_SIZE = 4096

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SONG_FOLDER = os.path.join(BASE_DIR, "songs")

connected_clients = 0
lock = threading.Lock()


def handle_client(conn, addr):
    global connected_clients

    with lock:
        connected_clients += 1
        print(f"[CONNECTED] {addr} | Active Clients: {connected_clients}")

    try:
        # ---- PROTOCOL: SEND SONG LIST ----
        songs = [s for s in os.listdir(SONG_FOLDER) if s.endswith(".mp3")]

        if not songs:
            conn.send(b"NO_SONGS")
            return

        song_list = "\n".join(f"{i+1}. {song}" for i, song in enumerate(songs))
        conn.send(song_list.encode())

        # ---- RECEIVE PLAY REQUEST ----
        request = conn.recv(1024).decode().strip()
        # Expected format: PLAY|2

        if not request.startswith("PLAY|"):
            return

        index = int(request.split("|")[1]) - 1
        if index < 0 or index >= len(songs):
            return

        selected_song = os.path.join(SONG_FOLDER, songs[index])
        print(f"[STREAMING] {songs[index]} to {addr}")

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
            print(f"[PERFORMANCE] {addr} Speed: {speed:.2f} Mbps")

        print(f"[COMPLETE] {addr}")

    except Exception as e:
        print("[ERROR]", e)

    conn.close()

    with lock:
        connected_clients -= 1
        print(f"[DISCONNECTED] {addr} | Active Clients: {connected_clients}")


def start_server():
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(certfile="cert.pem", keyfile="key.pem")

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind((HOST, PORT))
    sock.listen(5)

    print(f"[SECURE SERVER STARTED] Port {PORT}")

    with context.wrap_socket(sock, server_side=True) as ssock:
        while True:
            conn, addr = ssock.accept()
            thread = threading.Thread(target=handle_client, args=(conn, addr))
            thread.start()


if __name__ == "__main__":
    start_server()