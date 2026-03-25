import socket
import os

HOST = '0.0.0.0'
PORT = 5000
BUFF_SIZE = 4096
SEP = "<SEP>"
SERVER_DIR = "server_files"

def main():
    if not os.path.exists(SERVER_DIR): 
        os.makedirs(SERVER_DIR)

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen(1)

    print(f"Sync Server listening on {HOST}:{PORT}")

    while True:
        print("\nWaiting for a connection...")
        conn, addr = server.accept()
        print(f"Connected by {addr}")
        conn.send(b"Server: Welcome to Sync Mode. You are the only client.")

        while True:
            try:
                data = conn.recv(BUFF_SIZE).decode()
                if not data:
                    print(f"Client {addr} disconnected.")
                    break
                
                if data.strip() == "/list":
                    files = os.listdir(SERVER_DIR)
                    file_list = "\n".join(files) if files else "Directory is empty."
                    reply = f"\n--- Files on Server ---\n{file_list}\n-----------------------"
                    conn.send(reply.encode())
                    
                elif data.startswith("/upload"):
                    _, fname, fsize_str = data.split(SEP)
                    fsize = int(fsize_str)
                    filepath = os.path.join(SERVER_DIR, os.path.basename(fname))
                    
                    print(f"Receiving {fname} ({fsize} bytes)...")
                    with open(filepath, "wb") as f:
                        received = 0
                        while received < fsize:
                            chunk = conn.recv(min(BUFF_SIZE, fsize - received))
                            if not chunk: break
                            f.write(chunk)
                            received += len(chunk)
                    print(f"Saved {fname}.")
                    conn.send(b"Server: Upload successful.")
                    
                elif data.startswith("/download "):
                    fname = data.split(" ", 1)[1]
                    filepath = os.path.join(SERVER_DIR, os.path.basename(fname))
                    if os.path.exists(filepath):
                        fsize = os.path.getsize(filepath)
                        header = f"FILE_INCOME{SEP}{fname}{SEP}{fsize}"
                        conn.send(header.encode())
                        with open(filepath, "rb") as f:
                            while True:
                                chunk = f.read(BUFF_SIZE)
                                if not chunk: break
                                conn.sendall(chunk)
                    else:
                        conn.send(f"Error: {fname} not found on server.".encode())
                else:
                    print(f"[{addr[0]}:{addr[1]}] {data}")
                    conn.send(b"Server ACK: Message received.")
                    
            except ConnectionResetError:
                print(f"Client {addr} reset connection.")
                break
            except Exception as e:
                print(f"Error handling {addr}: {e}")
                break
                
        conn.close()

if __name__ == "__main__":
    main()