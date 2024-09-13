from solcx import get_installable_solc_versions

#---------------------------Solidity Compiler Versions------------------------------------------------------
# Fetch the list of installable Solidity compiler versions
versions = get_installable_solc_versions()

# Print the available Solidity compiler versions
print("Available installable Solidity compiler versions:")
print(versions)
