import socket
import select
import os
import sys

def main():
    if not hasattr(select, 'poll'):
        print("Error: Syscall 'poll' is not supported on this OS.")
        print("Please run this script on a UNIX-like system (Linux/WSL).")
        sys.exit(1)

    HOST = '0.0.0.0'
    PORT = 5000
    BUFF_SIZE = 4096
    SEP = "<SEP>"
    SERVER_DIR = "server_files"

    if not os.path.exists(SERVER_DIR): 
        os.makedirs(SERVER_DIR)

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen(5)

    poller = select.poll()
    poller.register(server, select.POLLIN)

    fd_to_socket = {server.fileno(): server}
    clients = {} 

    print(f"Poll Server listening on {HOST}:{PORT}")

    def broadcast(msg, sender_fd=None):
        for fd, sock in list(fd_to_socket.items()):
            if fd != server.fileno() and fd != sender_fd:
                try: 
                    sock.send(msg.encode())
                except socket.error: 
                    pass

    try:
        while True:
            events = poller.poll()
            for fd, flag in events:
                if fd == server.fileno():
                    conn, addr = server.accept()
                    poller.register(conn, select.POLLIN)
                    fd_to_socket[conn.fileno()] = conn
                    clients[conn.fileno()] = addr
                    print(f"Accepted connection from {addr}")
                    broadcast(f"Server: {addr} joined.", conn.fileno())
                
                elif flag & select.POLLIN:
                    sock = fd_to_socket[fd]
                    try:
                        data = sock.recv(BUFF_SIZE).decode()
                        if not data: 
                            raise ConnectionResetError
                        
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
                            addr = clients[fd]
                            fmt_msg = f"[{addr[0]}:{addr[1]}] {data}"
                            print(fmt_msg)
                            broadcast(fmt_msg, fd)
                            
                    except (ConnectionResetError, socket.error):
                        print(f"Closed connection from {clients.get(fd)}")
                        poller.unregister(fd)
                        sock.close()
                        del fd_to_socket[fd]
                        if fd in clients: del clients[fd]
                        
    except KeyboardInterrupt:
        print("\nShutting down server...")
        server.close()
        sys.exit(0)

if __name__ == "__main__":
    main()