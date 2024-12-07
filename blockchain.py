import hashlib
import time
import json
import socket
import threading
import random

class Transaction:
    def __init__(self, sender, recipient, amount):
        self.sender = sender
        self.recipient = recipient
        self.amount = amount

    def __str__(self):
        return f"{self.sender}->{self.recipient}:{self.amount}"

    def is_valid(self):
        return self.sender and self.recipient and isinstance(self.amount, (int, float)) and self.amount > 0

class Block:
    def __init__(self, index, previous_hash, timestamp, transactions, difficulty, miner_address=None):
        self.index = index
        self.previous_hash = previous_hash
        self.timestamp = timestamp
        self.transactions = transactions
        self.difficulty = difficulty
        self.nonce = 0
        self.hash = self.calculate_hash()
        self.miner_address = miner_address  # Address of the miner who mined the block

    def calculate_hash(self):
        sha = hashlib.sha256()
        transaction_data = ''.join(str(tx) for tx in self.transactions)
        sha.update(
            f"{self.index}{self.previous_hash}{self.timestamp}{transaction_data}{self.difficulty}{self.nonce}".encode('utf-8')
        )
        return sha.hexdigest()

    def mine_block(self):
        target = '0' * self.difficulty
        while not self.hash.startswith(target):
            self.nonce += 1
            self.hash = self.calculate_hash()

        # Add a miner reward transaction after mining the block
        reward_transaction = Transaction("System", self.miner_address, 50)  # Reward of 50 coins
        self.transactions.append(reward_transaction)

class Blockchain:
    def __init__(self):
        self.difficulty = 4
        self.chain = [self.create_genesis_block()]
        self.pending_transactions = []
        self.adjustment_interval = 10
        self.block_generation_interval = 1

    def create_genesis_block(self):
        return Block(0, "0", time.time(), [Transaction("None", "None", 0)], self.difficulty)

    def get_latest_block(self):
        return self.chain[-1]

    def create_transaction(self, transaction):
        if transaction.is_valid():
            self.pending_transactions.append(transaction)
            return True
        return False

    def add_block(self, miner_address=None):
        latest_block = self.get_latest_block()
        new_block = Block(
            index=len(self.chain),
            previous_hash=latest_block.hash,
            timestamp=time.time(),
            transactions=self.pending_transactions,
            difficulty=self.difficulty,
            miner_address=miner_address
        )
        new_block.mine_block()

        if self.is_block_valid(new_block, latest_block):
            self.chain.append(new_block)
            self.pending_transactions = []
            self.adjust_difficulty()
            return True
        return False

    def is_block_valid(self, new_block, previous_block):
        if new_block.previous_hash != previous_block.hash:
            print("Invalid block: Previous hash does not match")
            return False

        if new_block.hash != new_block.calculate_hash():
            print("Invalid block: Hash does not match the calculated hash")
            return False

        if not new_block.hash.startswith('0' * new_block.difficulty):
            print("Invalid block: Hash does not meet the difficulty target")
            return False

        return True

    def is_chain_valid(self):
        for i in range(1, len(self.chain)):
            current = self.chain[i]
            previous = self.chain[i - 1]

            if current.hash != current.calculate_hash():
                return False

            if current.previous_hash != previous.hash:
                return False

            if not current.hash.startswith('0' * current.difficulty):
                return False

        return True

    def adjust_difficulty(self):
        if len(self.chain) % self.adjustment_interval == 0:
            start_time = self.chain[-self.adjustment_interval].timestamp
            end_time = self.chain[-1].timestamp
            time_taken = end_time - start_time
            expected_time = self.block_generation_interval * self.adjustment_interval

            if time_taken < expected_time:
                self.difficulty += 1
            elif time_taken > expected_time:
                self.difficulty = max(1, self.difficulty - 1)

    def replace_chain(self, new_chain):
        if len(new_chain) > len(self.chain) and self.is_chain_valid(new_chain):
            self.chain = new_chain

    def print_chain(self):
        for block in self.chain:
            print(f"Index: {block.index}")
            print(f"Previous Hash: {block.previous_hash}")
            print(f"Timestamp: {block.timestamp}")
            print("Transactions:")
            for tx in block.transactions:
                print(f"  {tx}")
            print(f"Hash: {block.hash}")
            print(f"Nonce: {block.nonce}")
            print("-" * 30)

import socket
import json
import threading
import time


class Node:
    def __init__(self, host="127.0.0.1", port=5000, bootstrap=("127.0.0.1", 4000)):
        self.host = host
        self.port = port
        self.bootstrap = bootstrap
        self.peers = []
        # Placeholder for blockchain; assuming `Blockchain` and related classes are defined
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
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.connect(peer)
            client.send(json.dumps(data).encode('utf-8'))
            client.close()
        except Exception as e:
            print(f"Failed to connect to peer {peer}: {e}")

    def discover_peers(self):
        """
        Broadcast a peer discovery message to all known peers.
        """
        discovery_message = {
            'type': 'peer_discovery',
            'peers': [(self.host, self.port)]
        }
        for peer in self.peers:
            self.send_to_peer(peer, discovery_message)

    def start(self):
        """
        Start the node by launching the server, registering with the bootstrap server,
        fetching the initial peer list, and periodically discovering new peers.
        """
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

# Example usage
if __name__ == "__main__":
    random_port = random.randint(5000, 5100)
    node = Node(host="127.0.0.1", port=random_port)
    node.start()
    # threading.Thread(target=node.start_server).start()
    # node.peers.append(("127.0.0.1", 5000))
    # node.discover_peers()  # Announce itself to known peers
    # transaction = Transaction("Alice", "Bob", 10)
    # node.blockchain.create_transaction(transaction)
    # node.broadcast_transaction(transaction)
