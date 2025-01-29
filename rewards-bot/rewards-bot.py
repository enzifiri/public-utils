import json
import subprocess

def read_json(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            data = json.load(file)
            print(f"Read data: {data}")
            
            if isinstance(data, list):
                # Handle list of strings (addresses)
                if all(isinstance(x, str) for x in data):
                    return set(data)
                # Handle list of dictionaries
                return {entry["dym_address"] for entry in data 
                       if isinstance(entry, dict) and "dym_address" in entry}
            elif isinstance(data, dict) and "dym_address" in data:
                return {data["dym_address"]}
            else:
                print(f"Warning: Unexpected data format in {file_path}")
                return set()
    except FileNotFoundError:
        return set()
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON from {file_path}: {e}")
        return set()
    except Exception as e:
        print(f"Unexpected error reading {file_path}: {e}")
        return set()

def extract_txhash(stdout):
    """Extract transaction hash from the command output."""
    for line in stdout.split('\n'):
        if line.startswith('txhash:'):
            return line.split(':', 1)[1].strip()
    return None

def write_json(file_path, data):
    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4)

def send_tokens(binary_path, key_name, address, amount, keyring, chain_id, rpc):
    try:
        command = [
            binary_path,
            "tx",
            "bank",
            "send",
            key_name,
            address,
            amount,
            "--keyring-backend", keyring,
            "--chain-id", chain_id,
            "--node", rpc,
            "--fees", "0.001dym",
            "--yes" 
        ]
        print(f"Executing: {' '.join(command)}")

        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if result.returncode == 0:
            txhash = extract_txhash(result.stdout)
            return txhash
        else:
            print(f"Error: {result.stderr}")
            return None
    except Exception as e:
        print(f"Exception occurred: {e}")
        return None

def read_processed_addresses(file_path):
    """Read the processed addresses from the tracking file."""
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            data = json.load(file)
            print(f"Read processed addresses: {data}")
            # Handle list of strings (addresses)
            if isinstance(data, list) and all(isinstance(x, str) for x in data):
                return set(data)
            else:
                print(f"Warning: Unexpected format in processed addresses file {file_path}")
                return set()
    except FileNotFoundError:
        return set()
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON from {file_path}: {e}")
        return set()
    except Exception as e:
        print(f"Unexpected error reading {file_path}: {e}")
        return set()

def read_rewards_data(file_path):
    """Read the rewards data file containing addresses and amounts."""
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            data = json.load(file)
            print(f"Read rewards data from {file_path}")
            if isinstance(data, list):
                return [entry for entry in data 
                        if isinstance(entry, dict) 
                        and "dym_address" in entry 
                        and "rewards" in entry]
            else:
                print(f"Warning: Unexpected data format in {file_path}")
                return []
    except FileNotFoundError:
        print(f"File not found: {file_path}")
        return []
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON from {file_path}: {e}")
        return []
    except Exception as e:
        print(f"Unexpected error reading {file_path}: {e}")
        return []

if __name__ == "__main__":
    # Add tracking file for successful transactions
    processed_file = "processed_transactions.json"
    processed_addresses = read_processed_addresses(processed_file)

    binary_path = input("Enter the binary path: ").strip()
    key_name = input("Enter the key name: ").strip()
    keyring = input("Enter the keyring: ").strip()
    chain_id = input("Enter the chain ID: ").strip()
    rpc = input("Enter the RPC URL: ").strip()
    rewards_file = input("Enter the files to send rewards from: ").strip()

    rewards_data = read_rewards_data(rewards_file)
    for entry in rewards_data:
            address = entry["dym_address"]
            amount = f"{entry['rewards']}adym"
                
            if address in processed_addresses:
                print(f"Skipping already processed address: {address}")
                continue
                
            result = send_tokens(binary_path, key_name, address, amount, keyring, chain_id, rpc)
            if result != None:
                processed_addresses.add(address)
                # Store both address and tx hash
                processed_data = {
                    "address": address,
                    "tx_hash": result
                }
                write_json(processed_file, [processed_data])
