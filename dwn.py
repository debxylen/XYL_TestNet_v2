import requests

def fetch_and_write_binary(url, file_path):
    try:
        # Fetch content from the URL
        response = requests.get(url)
        response.raise_for_status()  # Raise an error for bad status codes
        
        # Write the binary content to the file (overwriting it)
        with open(file_path, 'wb') as file:
            file.write(response.content)
        
        print(f"Binary content from {url} has been written to {file_path}.")
    except requests.exceptions.RequestException as e:
        print(f"Failed to fetch content from {url}: {e}")


# Example usage
url = "https://cdn.glitch.global/0662dbd3-821c-4827-bab2-e7c910d690da/blockchain?v=1732169100647"
file_path = "blockchain"
fetch_and_write_binary(url, file_path)

url = "https://cdn.glitch.global/0662dbd3-821c-4827-bab2-e7c910d690da/balances?v=1732169104276"
file_path = "balances"
fetch_and_write_binary(url, file_path)

url = "https://cdn.glitch.global/0662dbd3-821c-4827-bab2-e7c910d690da/contract_manager?v=1732169096447"
file_path = "contract_manager"
fetch_and_write_binary(url, file_path)
