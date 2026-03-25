import socket
import threading
import os
import sys
import time

HOST = '127.0.0.1'
PORT = 5000
BUFF_SIZE = 4096
SEP = "<SEP>"

def receive_msg(sock):
    while True:
        try:
            data = sock.recv(BUFF_SIZE).decode()
            if not data:
                print("\nConnection closed by server.")
                os._exit(0)

            if data.startswith("FILE_INCOME"):
                _, fname, fsize_str = data.split(SEP)
                fsize = int(fsize_str)
                print(f"\nDownloading {fname} ({fsize} bytes)...")
                
                received = 0
                with open(f"dl_{fname}", "wb") as f:
                    while received < fsize:
                        chunk = sock.recv(min(BUFF_SIZE, fsize - received))
                        if not chunk: 
                            break
                        f.write(chunk)
                        received += len(chunk)
                print(f"Download {fname} complete.\n> ", end="")
            else:
                print(f"\n{data}\n> ", end="")
                
        except socket.error:
            print("\nSocket error. Disconnected.")
            os._exit(1)
        except Exception as e:
            print(f"\nError: {e}")
            os._exit(1)

def main():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.connect((HOST, PORT))
        print(f"Connected to {HOST}:{PORT}")
    except socket.error as err:
        print(f"Connection failed: {err}")
        sys.exit(1)

    t = threading.Thread(target=receive_msg, args=(s,))
    t.daemon = True
    t.start()

    print("Commands: /list | /upload <file> | /download <file>\n")

    while True:
        try:
            msg = input("> ")
            if not msg: continue

            if msg.startswith("/upload "):
                parts = msg.split(" ", 1)
                if len(parts) < 2: continue
                fname = parts[1]
                
                if not os.path.exists(fname):
                    print(f"Error: {fname} not found.")
                    continue
                
                fsize = os.path.getsize(fname)
                header = f"/upload{SEP}{fname}{SEP}{fsize}"
                s.send(header.encode())
                
                # Prevent TCP stickiness
                time.sleep(0.5)
                
                print(f"Uploading {fname}...")
                with open(fname, "rb") as f:
                    while True:
                        chunk = f.read(BUFF_SIZE)
                        if not chunk: break
                        s.sendall(chunk)
                print("Upload complete.")

            else:
                s.send(msg.encode())
                
        except KeyboardInterrupt:
            print("\nExiting...")
            s.close()
            sys.exit(0)

if __name__ == "__main__":
    main()