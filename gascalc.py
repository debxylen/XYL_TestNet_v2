gas_price_gwei = 69  # gas price in Gwei
xyl_cost = 0.003469   # desired cost in Xyl
wei_per_xyl = 10**18  # Wei per Xyl
gwei_to_wei = 10**9   # Wei per Gwei

# Convert the gas price to Wei
gas_price_wei = gas_price_gwei * gwei_to_wei

# Calculate the total cost in Wei
total_cost_wei = xyl_cost * wei_per_xyl

# Calculate the number of gas units needed
gas_units = total_cost_wei / gas_price_wei
print(gas_units)
