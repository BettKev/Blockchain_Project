import socket
import json

def send_transaction(sender, recipient, amount, peers):
    transaction_data = {
        'type': 'transaction',
        'sender': sender,
        'recipient': recipient,
        'amount': amount
    }

    for peer in peers:
        try:
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.connect(peer)
            client.send(json.dumps(transaction_data).encode('utf-8'))
            print(f"Transaction sent from {sender} to {recipient} for amount {amount} to {peer}")
            client.close()
        except Exception as e:
            print(f"Failed to send transaction to {peer}: {e}")

if __name__ == "__main__":
    sender = input(f"Enter sender name: ")
    recipient = input(f"Enter recipient name: ")
    amount = int(input(f"Enter amount to send: "))
    # peers = [("127.0.0.1", 4000), ]  # Add all known peer addresses

    import random

# Generate a random list of peer tuples
def generate_random_peers(ip="127.0.0.1", start_port=5000, end_port=5010, num_peers=10):
    """
    Generate a list of random peer tuples with the format (ip, port).
    :param ip: The IP address to use for all peers.
    :param start_port: The starting port number (inclusive).
    :param end_port: The ending port number (inclusive).
    :param num_peers: The number of random peers to generate.
    :return: A list of tuples (ip, port).
    """
    ports = random.sample(range(start_port, end_port + 1), num_peers)
    return [(ip, port) for port in ports]

# Example usage
peers = generate_random_peers()
print(peers)


send_transaction(sender, recipient, amount, peers)
