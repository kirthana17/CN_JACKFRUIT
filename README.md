# CN_Jackfruit - Music Streaming App

Secure client-server music streaming app built with Python using SSL/TLS encryption and a Tkinter GUI.

## Features

- Secure SSL/TLS encrypted connection
- Real-time MP3 streaming
- Search and filter songs
- Download progress bar
- Multi-client support (threaded server)

## Project Structure

    CN_Jackfruit/
    ├── music-streaming/
    │   ├── client/
    │   │   └── client_gui.py
    │   └── server/
    │       ├── songs/        <- add your .mp3 files here
    │       ├── cert.pem      <- generate locally, not in repo
    │       ├── key.pem       <- generate locally, not in repo
    │       └── server.py
    ├── client1.py
    ├── server1.py
    ├── requirements.txt
    └── README.md

## Setup Instructions

### 1. Install dependencies

    pip install -r requirements.txt

### 2. Generate SSL certificates

Run this inside the server/ folder:

    openssl req -x509 -newkey rsa:2048 -keyout key.pem -out cert.pem -days 365 -nodes

### 3. Add songs

Place .mp3 files inside music-streaming/server/songs/

### 4. Run the server

    python music-streaming/server/server.py

### 5. Run the client

    python music-streaming/client/client_gui.py

## How to Use

1. Click Connect to connect to the server
2. Browse or search for a song
3. Click Play to stream it
4. Click Stop to stop playback

## Requirements

- Python 3.7+
- pygame
- OpenSSL for certificate generation