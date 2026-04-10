import socket
import ssl
import tempfile
import os
import threading
import tkinter as tk
from tkinter import messagebox
import pygame

SERVER_IP = "127.0.0.1"
PORT = 5000
BUFFER_SIZE = 4096

pygame.mixer.init()

client = None
songs_list = []         # currently displayed (filtered) list
original_songs = []     # full list from server (e.g. "1. mysong.mp3")
is_playing = False


# ─────────────────────────────────────────────
# SSL CONNECTION HELPER
# ─────────────────────────────────────────────
def make_ssl_socket():
    """Create a new SSL-wrapped socket connected to the server."""
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    context.check_hostname = False      # self-signed cert
    context.verify_mode = ssl.CERT_NONE # skip verification for local dev

    raw_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    wrapped = context.wrap_socket(raw_sock, server_hostname=SERVER_IP)
    wrapped.connect((SERVER_IP, PORT))
    return wrapped


# ─────────────────────────────────────────────
# CONNECT TO SERVER — fetch song list
# ─────────────────────────────────────────────
def connect_server():
    global client, songs_list, original_songs

    try:
        client = make_ssl_socket()
        status_label.config(text="✅ Connected to Server", fg="#1db954")

        # Receive song list
        raw = client.recv(4096).decode().strip()

        if raw == "NO_SONGS":
            status_label.config(text="⚠️ No songs on server", fg="orange")
            return

        original_songs = raw.split("\n")
        songs_list = original_songs.copy()

        listbox.delete(0, tk.END)
        for song in songs_list:
            listbox.insert(tk.END, song)

        print(f"[GOT SONG LIST] {len(original_songs)} songs")

    except Exception as e:
        status_label.config(text="❌ Connection Failed", fg="red")
        print(f"[CONNECT ERROR] {e}")


# ─────────────────────────────────────────────
# RECEIVE AND PLAY SONG (runs in thread)
# ─────────────────────────────────────────────
def receive_and_play(song_client, expected_size):
    global is_playing

    try:
        print(f"[STREAMING] Expecting {expected_size} bytes...")

        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
        temp_filename = temp_file.name

        received = 0
        while received < expected_size:
            chunk = song_client.recv(min(BUFFER_SIZE, expected_size - received))
            if not chunk:
                break
            temp_file.write(chunk)
            received += len(chunk)

            # Update progress bar
            if expected_size > 0:
                pct = int((received / expected_size) * 100)
                root.after(0, lambda p=pct: progress_var.set(p))

        temp_file.close()
        print(f"[RECEIVED] {received}/{expected_size} bytes → {temp_filename}")

        root.after(0, lambda: status_label.config(text="▶️ Playing...", fg="#1db954"))

        pygame.mixer.music.load(temp_filename)
        pygame.mixer.music.play()
        is_playing = True

        # Wait for playback to end, then clean up
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(5)

        is_playing = False
        os.unlink(temp_filename)
        root.after(0, lambda: status_label.config(text="✅ Done", fg="white"))
        root.after(0, lambda: progress_var.set(0))

    except Exception as e:
        root.after(0, lambda: status_label.config(text="❌ Stream Error", fg="red"))
        print(f"[STREAM ERROR] {e}")


# ─────────────────────────────────────────────
# PLAY SONG
# ─────────────────────────────────────────────
def play_song():
    global client

    selected = listbox.curselection()
    if not selected:
        status_label.config(text="⚠️ Select a song first", fg="orange")
        return

    # Get the display name from listbox (e.g. "3. mysong.mp3")
    display_name = listbox.get(selected[0])

    # Find its real index in the original server list (1-based)
    try:
        server_index = original_songs.index(display_name) + 1
    except ValueError:
        status_label.config(text="❌ Song index error", fg="red")
        return

    try:
        # Stop any existing playback
        pygame.mixer.music.stop()

        # Each play needs a fresh connection (server closes after each stream)
        song_client = make_ssl_socket()

        # Consume the song list the server always sends first
        _ = song_client.recv(4096)

        # Request the song
        song_client.sendall(f"PLAY|{server_index}".encode())

        # Read size header: "SIZE|<bytes>\n"
        size_header = b""
        while b"\n" not in size_header:
            chunk = song_client.recv(64)
            if not chunk:
                break
            size_header += chunk

        header_line = size_header.decode().strip()
        if not header_line.startswith("SIZE|"):
            status_label.config(text="❌ Bad server response", fg="red")
            return

        expected_size = int(header_line.split("|")[1])

        status_label.config(text="⏳ Buffering...", fg="yellow")
        threading.Thread(
            target=receive_and_play,
            args=(song_client, expected_size),
            daemon=True
        ).start()

    except Exception as e:
        status_label.config(text="❌ Play Error", fg="red")
        print(f"[PLAY ERROR] {e}")


# ─────────────────────────────────────────────
# STOP SONG
# ─────────────────────────────────────────────
def stop_song():
    global is_playing
    pygame.mixer.music.stop()
    is_playing = False
    progress_var.set(0)
    status_label.config(text="⏹ Stopped", fg="white")


# ─────────────────────────────────────────────
# SEARCH / FILTER
# ─────────────────────────────────────────────
def filter_songs(*args):
    search = search_var.get().lower()
    listbox.delete(0, tk.END)
    for song in original_songs:
        if search in song.lower():
            listbox.insert(tk.END, song)


# ─────────────────────────────────────────────
# GUI SETUP
# ─────────────────────────────────────────────
root = tk.Tk()
root.title("🎵 Music Streaming Client")
root.geometry("420x580")
root.configure(bg="#121212")
root.resizable(False, False)

# Title
tk.Label(
    root, text="🎵 Music Streaming Client",
    fg="white", bg="#121212", font=("Arial", 15, "bold")
).pack(pady=12)

# Search bar
search_var = tk.StringVar()
search_var.trace("w", filter_songs)

search_frame = tk.Frame(root, bg="#121212")
search_frame.pack(fill="x", padx=20)
tk.Label(search_frame, text="🔍", bg="#121212", fg="white").pack(side="left")
tk.Entry(search_frame, textvariable=search_var, width=38, bg="#2a2a2a",
         fg="white", insertbackground="white", relief="flat").pack(side="left", padx=5, pady=5)

# Song listbox with scrollbar
list_frame = tk.Frame(root, bg="#121212")
list_frame.pack(padx=20, pady=5, fill="both", expand=True)

scrollbar = tk.Scrollbar(list_frame)
scrollbar.pack(side="right", fill="y")

listbox = tk.Listbox(
    list_frame, width=50, height=16,
    bg="#1e1e1e", fg="white",
    selectbackground="#1db954", selectforeground="black",
    activestyle="none", relief="flat",
    yscrollcommand=scrollbar.set
)
listbox.pack(side="left", fill="both", expand=True)
scrollbar.config(command=listbox.yview)

# Buttons
btn_frame = tk.Frame(root, bg="#121212")
btn_frame.pack(pady=10)

btn_style = {"font": ("Arial", 11, "bold"), "width": 10, "relief": "flat", "cursor": "hand2"}

tk.Button(btn_frame, text="Connect", command=connect_server,
          bg="#1db954", fg="white", **btn_style).grid(row=0, column=0, padx=8)

tk.Button(btn_frame, text="▶ Play", command=play_song,
          bg="#1db954", fg="white", **btn_style).grid(row=0, column=1, padx=8)

tk.Button(btn_frame, text="⏹ Stop", command=stop_song,
          bg="#ff4d4d", fg="white", **btn_style).grid(row=0, column=2, padx=8)

# Progress bar (manual, using Canvas)
progress_var = tk.IntVar(value=0)
progress_bg = tk.Canvas(root, width=380, height=10, bg="#2a2a2a", highlightthickness=0)
progress_bg.pack(pady=5)
progress_bar = progress_bg.create_rectangle(0, 0, 0, 10, fill="#1db954", width=0)

def update_progress_bar(*args):
    pct = progress_var.get()
    width = int(380 * pct / 100)
    progress_bg.coords(progress_bar, 0, 0, width, 10)

progress_var.trace("w", update_progress_bar)

# Status label
status_label = tk.Label(root, text="Not Connected", fg="white", bg="#121212", font=("Arial", 10))
status_label.pack(pady=8)

root.mainloop()