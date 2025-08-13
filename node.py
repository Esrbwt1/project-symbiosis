import requests
import time
import sys

# The address of our central orchestrator (the Flask app)
ORCHESTRATOR_URL = "http://127.0.0.1:5000"

def register_with_orchestrator(node_address):
    """Sends a registration request to the orchestrator."""
    try:
        response = requests.post(f"{ORCHESTRATOR_URL}/register_node", json={"node_address": node_address})
        response.raise_for_status() # Raises an exception for bad status codes (4xx or 5xx)
        print(f"Successfully registered with orchestrator. Server response: {response.json()}")
        return True
    except requests.exceptions.RequestException as e:
        print(f"Error: Could not connect to the orchestrator at {ORCHESTRATOR_URL}.")
        print(f"Please ensure the main app.py server is running.")
        print(f"Details: {e}")
        return False

def start_node(port):
    """Starts the node and registers it."""
    node_address = f"http://127.0.0.1:{port}"
    print(f"--- Starting Symbiosis Compute Node ---")
    print(f"Node Address: {node_address}")
    
    if register_with_orchestrator(node_address):
        print("Node is now active and part of the network (simulation).")
        print("In a real system, this node would listen for compute jobs.")
        print("Press Ctrl+C to shut down the node.")
        try:
            while True:
                # Keep the node alive, heartbeat can be implemented here
                time.sleep(10)
        except KeyboardInterrupt:
            print("\nNode shutting down.")

if __name__ == '__main__':
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
            start_node(port)
        except ValueError:
            print("Invalid port number. Please provide an integer.")
    else:
        # Default port if none is provided
        start_node(8001)