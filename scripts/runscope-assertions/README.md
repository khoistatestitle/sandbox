# Runscope JS script assertion generator for Fee Collaboration
This little tool allows quick JS assertion code for use in Runscope functional tests. Give it a JSON structure of fees and tell it which SettlementTypeID's to look for and it will generate the assertion code.

## Usage
python3 <script_name> "{json_file} [list_of_settlement_type_ids]"

### Example
$ python3 json_to_asserts.py --file sample.json 401 901 1001 1004


## Future improvements
Instead of feeding it a JSON file, the script should just fetch the fees from ResWare API+ directly.
