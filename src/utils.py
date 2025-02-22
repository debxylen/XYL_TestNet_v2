def hex_to_string(hex_string):
    # Remove '0x' prefix if present
    hex_string = str(hex_string)
    if hex_string.startswith("0x"):
        hex_string = hex_string[2:]
    return bytes.fromhex(hex_string).decode('utf-8')
  
def string_to_hex_with_prefix(input_string):
    input_string = str(input_string)
    return "0x" + input_string.encode('utf-8').hex()

def find_actual_amount(y: int, gas: int):
    multiplier = 1 - gas
    x = y / multiplier
    return x

def round_to_valid_amount(amount):
    # Round the amount to the nearest valid value (1 million wei in this case)
    valid_amount = 1000000
    return (amount // valid_amount) * valid_amount