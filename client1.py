import socket
import tempfile
import os

SERVER_IP = "172.20.10.6"   # Change if needed
PORT = 5000
BUFFER_SIZE = 4096


def start_client():
    try:
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect((SERVER_IP, PORT))

        print("\n[CONNECTED TO SERVER]\n")

        # Receive song list
        song_list = client.recv(4096).decode()
        print("Available Songs:\n")
        print(song_list)

        choice = input("\nEnter song number: ")
        client.send(choice.encode())

        print("\n[STREAMING AUDIO...]\n")

        # Create temporary file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
        temp_filename = temp_file.name

        # Receive song data
        while True:
            data = client.recv(BUFFER_SIZE)
            if not data:
                break
            temp_file.write(data)

        temp_file.close()
        client.close()

        print("[PLAYING MUSIC]\n")

        # Open with default Windows media player
        os.startfile(temp_filename)

    except Exception as e:
        print("[ERROR]", e)


if __name__ == "__main__":
    start_client()
