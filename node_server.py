import json
import socket
import threading
import time

class Node:
    def __init__(self, host="127.0.0.1", port=5000, bootstrap=("127.0.0.1", 4000)):
        self.host = host
        self.port = port
        self.bootstrap = bootstrap
        self.peers = []
        # Placeholder for blockchain; assuming `Blockchain` and related classes are defined
        self.blockchain = None

    def initialize_blockchain(self):
        from blockchain import Blockchain  # Delayed import
        self.blockchain = Blockchain()

    def start_server(self):
        """
        Start a server to handle incoming connections from peers or clients.
        """
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind((self.host, self.port))
        server.listen(5)
        print(f"Node listening on {self.host}:{self.port}")

        while True:
            client, address = server.accept()
            threading.Thread(target=self.handle_client, args=(client,)).start()

    def handle_client(self, client):
        """
        Handle incoming client connections and process their requests.
        """
        try:
            from blockchain import Transaction, Block #Delayed import here
            data = client.recv(1024).decode('utf-8')
            request = json.loads(data)

            if request['type'] == 'transaction':
                transaction = Transaction(
                    sender=request['sender'],
                    recipient=request['recipient'],
                    amount=request['amount']
                )
                if self.blockchain.create_transaction(transaction):
                    print(f"Transaction from {transaction.sender} to {transaction.recipient} is valid.")
                    self.broadcast_transaction(transaction)
                else:
                    print("Received an invalid transaction.")

            elif request['type'] == 'new_block':
                block = request['block']
                new_block = Block(
                    index=block['index'],
                    previous_hash=block['previous_hash'],
                    timestamp=block['timestamp'],
                    transactions=[Transaction(**tx) for tx in block['transactions']],
                    difficulty=block['difficulty'],
                    miner_address=block['miner_address']
                )
                if self.blockchain.is_block_valid(new_block, self.blockchain.get_latest_block()):
                    self.blockchain.add_block(new_block)
                    print("New block added to the blockchain.")
                    self.broadcast_new_block(new_block)
                else:
                    print("Received an invalid block.")

            elif request['type'] == 'peer_discovery':
                new_peers = request['peers']
                for peer in new_peers:
                    if peer not in self.peers and peer != (self.host, self.port):
                        self.peers.append(peer)
                print(f"Updated peer list: {self.peers}")
                self.discover_peers()

        except Exception as e:
            print(f"Error handling client: {e}")
        finally:
            client.close()

    def register_with_bootstrap(self):
        """
        Register this node with the bootstrap server to initialize the peer list.
        """
        try:
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.connect(self.bootstrap)
            registration_data = {
                'type': 'register',
                'host': self.host,
                'port': self.port
            }
            client.send(json.dumps(registration_data).encode('utf-8'))
            print(f"Registered with bootstrap server at {self.bootstrap}")
            client.close()
        except Exception as e:
            print(f"Failed to register with bootstrap server: {e}")

    def fetch_peers(self):
        """
        Fetch a list of peers from the bootstrap server.
        """
        try:
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.connect(self.bootstrap)
            request_data = {'type': 'get_peers'}
            client.send(json.dumps(request_data).encode('utf-8'))
            data = client.recv(1024).decode('utf-8')
            self.peers = json.loads(data)
            print(f"Discovered peers: {self.peers}")
            client.close()
        except Exception as e:
            print(f"Failed to fetch peers: {e}")

    def broadcast_transaction(self, transaction):
        """
        Broadcast a transaction to all known peers.
        """
        for peer in self.peers:
            self.send_to_peer(peer, {
                'type': 'transaction',
                'sender': transaction.sender,
                'recipient': transaction.recipient,
                'amount': transaction.amount
            })

    def broadcast_new_block(self, block):
        """
        Broadcast a new block to all known peers.
        """
        for peer in self.peers:
            self.send_to_peer(peer, {
                'type': 'new_block',
                'block': block.__dict__
            })

    def send_to_peer(self, peer, data):
        """
        Send data to a specific peer.
        """
        try:
            # Validate that peer is a tuple of (host, port)
            if not isinstance(peer, tuple) or len(peer) != 2:
                raise ValueError("Peer must be a tuple of (host, port)")

            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.connect(peer)
            client.send(json.dumps(data).encode('utf-8'))
            client.close()
            print(f"Sent data to peer {peer}: {data}")
        except Exception as e:
            print(f"Failed to send data to peer {peer}: {e}")

    def discover_peers(self):
        """
        Share the updated peer list with all peers to ensure connectivity.
        """
        for peer in self.peers:
            self.send_to_peer(peer, {
                'type': 'peer_discovery',
                'peers': self.peers
            })

    def start(self):
        """
        Start the node by launching the server, registering with the bootstrap server,
        fetching the initial peer list, and periodically discovering new peers.
        """
        self.initialize_blockchain()  # Initialize the blockchain before anything else
        threading.Thread(target=self.start_server).start()
        self.register_with_bootstrap()
        self.fetch_peers()
        threading.Thread(target=self.peer_discovery_loop).start()

    def peer_discovery_loop(self):
        """
        Continuously discover new peers at regular intervals.
        """
        while True:
            self.discover_peers()
            time.sleep(30)  # Adjust interval as needed
