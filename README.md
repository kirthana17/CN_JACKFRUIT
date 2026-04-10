# 🎵 CN_Jackfruit — Music Streaming App

## 📌 Overview

This project implements a secure music streaming system using socket programming in Python.
It allows multiple clients to connect to a central server, browse songs, and stream MP3s in real time.

The system ensures secure communication using SSL/TLS encryption and supports multi-client
handling using threading.

---

## 🚀 Features

- 🔗 Multi-client server using TCP sockets
- 🔐 Secure communication using SSL/TLS
- 🧵 Concurrent client handling (multithreading)
- 🎵 Real-time MP3 streaming
- 🔍 Search and filter songs
- 📊 Download progress bar
- 🖥️ GUI-based client (Tkinter)

---

## 🏗️ Project Structure

    CN_Jackfruit/
    │
    ├── music-streaming/
    │   ├── client/
    │   │   └── client_gui.py       # Tkinter GUI client
    │   │
    │   └── server/
    │       ├── songs/              # Place .mp3 files here
    │       └── server.py           # Threaded SSL server
    │
    ├── tests/
    │   ├── load_test.py            # Simulates multiple clients
    │   └── performance_test.py     # Measures speed and response time
    │
    ├── certs/                      # SSL certificates (generate locally)
    │
    ├── README.md
    ├── requirements.txt
    └── .gitignore

---

## ⚙️ Technologies Used

- Python
- Socket Programming
- SSL/TLS (Secure Sockets Layer)
- Tkinter (GUI)
- Multithreading

---

## 🔧 Setup Instructions

### 1️⃣ Install dependencies

    pip install -r requirements.txt

### 2️⃣ Generate SSL certificates

Run this inside the certs/ folder:

    openssl req -x509 -newkey rsa:2048 -keyout key.pem -out cert.pem -days 365 -nodes

Then copy cert.pem and key.pem into music-streaming/server/

### 3️⃣ Add songs

Place .mp3 files inside:

    music-streaming/server/songs/

### 4️⃣ Run the server

    python music-streaming/server/server.py

### 5️⃣ Run the client

    python music-streaming/client/client_gui.py

### 6️⃣ Run Load Test (Optional)

    python tests/load_test.py

### 7️⃣ Run Performance Test (Optional)

    python tests/performance_test.py

---

## 🔐 Security

- Uses SSL/TLS encryption for all client-server communication
- Certificates generated locally and excluded from repository
- Protects data transmission between client and server

---

## 📊 Deliverables Achieved

### ✅ Deliverable 1
- Multi-client server implementation
- SSL/TLS secure communication
- Real-time MP3 streaming with Tkinter GUI
- Song search and filter
- Progress bar during streaming

### ✅ Deliverable 2
- Performance testing using multiple simultaneous clients
- Failure handling (invalid inputs, disconnections, bad requests)
- Optimization (buffer tuning, threaded client handling, socket reuse)

---

## 📈 Performance Insights

- Supports multiple concurrent clients
- Response time varies based on load
- Stable under multi-client conditions
- Average streaming speed tested at ~40-60 Mbps on localhost

---

## 🎯 Future Enhancements

- Web-based interface (Flask)
- Database integration (MySQL)
- Real-time updates using WebSockets
- User authentication and playlists
- Pause and resume streaming

---

## ⭐ Acknowledgment

This project was developed as part of a Computer Networks mini project,
focusing on distributed systems and secure communication.