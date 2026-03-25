import socket
import select
import os
import sys

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
    server.listen(5)

    sockets_list = [server]
    clients = {}

    print(f"Select Server listening on {HOST}:{PORT}")

    def broadcast(msg, sender_sock=None):
        for sock in sockets_list:
            if sock != server and sock != sender_sock:
                try:
                    sock.send(msg.encode())
                except socket.error:
                    sock.close()
                    if sock in sockets_list: sockets_list.remove(sock)

    try:
        while True:
            read_sockets, _, exception_sockets = select.select(sockets_list, [], sockets_list)

            for sock in read_sockets:
                if sock == server:
                    conn, addr = server.accept()
                    sockets_list.append(conn)
                    clients[conn] = addr
                    print(f"Accepted connection from {addr}")
                    broadcast(f"Server: {addr} joined.", conn)
                else:
                    try:
                        data = sock.recv(BUFF_SIZE).decode()
                        
                        if not data:
                            print(f"Closed connection from {clients[sock]}")
                            sockets_list.remove(sock)
                            del clients[sock]
                            continue

                        if data.strip() == "/list":
                            files = os.listdir(SERVER_DIR)
                            file_list = "\n".join(files) if files else "Directory is empty."
                            sock.send(f"\n--- Files ---\n{file_list}\n-------------".encode())

                        elif data.startswith("/upload"):
                            _, fname, fsize_str = data.split(SEP)
                            fsize = int(fsize_str)
                            filepath = os.path.join(SERVER_DIR, os.path.basename(fname))
                            
                            with open(filepath, "wb") as f:
                                received = 0
                                while received < fsize:
                                    chunk = sock.recv(min(BUFF_SIZE, fsize - received))
                                    if not chunk: break
                                    f.write(chunk)
                                    received += len(chunk)
                            sock.send(b"Server: Upload successful.")

                        elif data.startswith("/download "):
                            fname = data.split(" ", 1)[1]
                            filepath = os.path.join(SERVER_DIR, os.path.basename(fname))
                            
                            if os.path.exists(filepath):
                                fsize = os.path.getsize(filepath)
                                sock.send(f"FILE_INCOME{SEP}{fname}{SEP}{fsize}".encode())
                                with open(filepath, "rb") as f:
                                    while True:
                                        chunk = f.read(BUFF_SIZE)
                                        if not chunk: break
                                        sock.sendall(chunk)
                            else:
                                sock.send(b"Error: File not found.")

                        else:
                            addr = clients[sock]
                            fmt_msg = f"[{addr[0]}:{addr[1]}] {data}"
                            print(fmt_msg)
                            broadcast(fmt_msg, sock)

                    except (ConnectionResetError, socket.error):
                        print(f"Connection error with {clients.get(sock, 'Unknown')}")
                        if sock in sockets_list: sockets_list.remove(sock)
                        if sock in clients: del clients[sock]

            for sock in exception_sockets:
                if sock in sockets_list: sockets_list.remove(sock)
                if sock in clients: del clients[sock]
                
    except KeyboardInterrupt:
        print("\nShutting down server...")
        server.close()
        sys.exit(0)

if __name__ == "__main__":
    main()