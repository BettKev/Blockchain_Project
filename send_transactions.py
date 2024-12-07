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
    peers = [("127.0.0.1", 5000), ("127.0.0.1", 5001), ("127.0.0.1", 5002), ("127.0.0.1", 5003)]  # Add all known peer addresses

    send_transaction(sender, recipient, amount, peers)
