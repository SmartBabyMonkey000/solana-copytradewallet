import os, sys
import json


def storeToken(amm, tokenmint, pair_address, buyprice, profit):

    file_path = os.path.join(sys.path[0], 'data', 'already_bought.json')

    # Define the settings
    settings = {
            'amm': amm,
            'tokenmint': tokenmint,
            'pair_address': pair_address,
            'buyprice': buyprice,
            'profit': profit
    }

    # Load the JSON file
    with open(file_path, 'r') as file:
        data = json.load(file)

    # Append the settings to the JSON object
    data[tokenmint] = settings

    # Write the updated data back to the file
    with open(file_path, 'w') as file:
        json.dump(data, file, indent=4)

    print("Settings saved in 'already_bought.json'.")

def soldToken(desired_token_address):
    print("Deleting saved token from already_bought.json...")
    file_path = os.path.join(sys.path[0], 'data', 'already_bought.json')
    # Load the JSON file
    with open(file_path, 'r') as file:
        data = json.load(file)

    # Check if the 'desired_token_address' key exists in the JSON object
    if desired_token_address in data:
        # If it exists, delete it
        del data[desired_token_address]

    # Write the updated data back to the file
    with open(file_path, 'w') as file:
        json.dump(data, file, indent=4)

    print("Deleting saved token from already_bought.json...")
    file_path = os.path.join(sys.path[0], 'data', 'already_bought.json')
    # Load the JSON file
    with open(file_path, 'r') as file:
        data = json.load(file)

    # Check if the 'tokens' key exists in the JSON object
    if 'tokens' in data:
        # If it exists, check if the token is in the list
        if desired_token_address in data['tokens']:
            # If it is, remove it
            data['tokens'].remove(desired_token_address)

    # Write the updated data back to the file
    with open(file_path, 'w') as file:
        json.dump(data, file, indent=4)
