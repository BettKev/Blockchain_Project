import socket
import threading
import json

class BootstrapServer:
    def __init__(self, host="127.0.0.1", port=4000):
        self.host = host
        self.port = port
        self.peers = []

    def handle_client(self, client_socket):
        try:
            data = client_socket.recv(1024).decode('utf-8')
            message = json.loads(data)

            if message['type'] == 'register':
                peer = (message['host'], message['port'])
                if peer not in self.peers:
                    self.peers.append(peer)
                    print(f"New peer registered: {peer}")

            elif message['type'] == 'get_peers':
                client_socket.send(json.dumps(self.peers).encode('utf-8'))

        except Exception as e:
            print(f"Error handling client: {e}")
        finally:
            client_socket.close()

    def start(self):
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind((self.host, self.port))
        server_socket.listen(5)
        print(f"Bootstrap server listening on {self.host}:{self.port}")

        while True:
            client_socket, _ = server_socket.accept()
            threading.Thread(target=self.handle_client, args=(client_socket,)).start()

if __name__ == "__main__":
    BootstrapServer().start()
