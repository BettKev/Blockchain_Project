# blockchain_management.py

import time
from blockchain import Transaction, Block

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
