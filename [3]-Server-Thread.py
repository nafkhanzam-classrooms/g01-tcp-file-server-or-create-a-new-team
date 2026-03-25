import socket
import threading
import os
import sys

HOST = '0.0.0.0'
PORT = 5000
BUFF_SIZE = 4096
SEP = "<SEP>"
SERVER_DIR = "server_files"

clients = {}
clients_lock = threading.Lock()

def broadcast(msg, sender_conn=None):
    with clients_lock:
        for conn in list(clients.keys()):
            if conn != sender_conn:
                try: 
                    conn.send(msg.encode())
                except socket.error:
                    pass

def handle_client(conn, addr):
    print(f"New connection from {addr}")
    broadcast(f"Server: {addr} joined the room.", conn)
    
    while True:
        try:
            data = conn.recv(BUFF_SIZE).decode()
            if not data: 
                break
            
            if data.strip() == "/list":
                files = os.listdir(SERVER_DIR)
                file_list = "\n".join(files) if files else "Directory is empty."
                conn.send(f"\n--- Files ---\n{file_list}\n-------------".encode())
                
            elif data.startswith("/upload"):
                _, fname, fsize_str = data.split(SEP)
                fsize = int(fsize_str)
                filepath = os.path.join(SERVER_DIR, os.path.basename(fname))
                
                with open(filepath, "wb") as f:
                    received = 0
                    while received < fsize:
                        chunk = conn.recv(min(BUFF_SIZE, fsize - received))
                        if not chunk: break
                        f.write(chunk)
                        received += len(chunk)
                conn.send(b"Server: Upload complete.")
                
            elif data.startswith("/download "):
                fname = data.split(" ", 1)[1]
                filepath = os.path.join(SERVER_DIR, os.path.basename(fname))
                if os.path.exists(filepath):
                    fsize = os.path.getsize(filepath)
                    conn.send(f"FILE_INCOME{SEP}{fname}{SEP}{fsize}".encode())
                    with open(filepath, "rb") as f:
                        while True:
                            chunk = f.read(BUFF_SIZE)
                            if not chunk: break
                            conn.sendall(chunk)
                else:
                    conn.send(b"Error: File not found.")
            else:
                fmt_msg = f"[{addr[0]}:{addr[1]}] {data}"
                print(fmt_msg)
                broadcast(fmt_msg, conn)
                
        except (ConnectionResetError, socket.error):
            break
        except Exception as e:
            print(f"Unexpected error with {addr}: {e}")
            break
            
    print(f"Connection closed for {addr}.")
    with clients_lock:
        if conn in clients: 
            del clients[conn]
    conn.close()
    broadcast(f"Server: {addr} left the room.")

def main():
    if not os.path.exists(SERVER_DIR): 
        os.makedirs(SERVER_DIR)

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    try:
        server.bind((HOST, PORT))
        server.listen(5)
        print(f"Threaded Server listening on {HOST}:{PORT}")
    except socket.error as e:
        print(f"Failed to bind: {e}")
        sys.exit(1)

    try:
        while True:
            conn, addr = server.accept()
            with clients_lock:
                clients[conn] = addr
            
            t = threading.Thread(target=handle_client, args=(conn, addr))
            t.daemon = True
            t.start()
    except KeyboardInterrupt:
        print("\nShutting down server...")
        server.close()
        sys.exit(0)

if __name__ == "__main__":
    main()