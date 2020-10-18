from typing import List, Tuple
import argparse
import json
import sys


# Exclude these fields from the generated output
ATTRIBUTES_TO_SKIP = {'CommonSettlementID'}


def generate_preamble() -> str:
    """ Create non-asserting JS code
    """
    return '''// check for specific status code
assert.equal(response.status, 200, "status was 200 OK");

// parse JSON response body into object
var data = JSON.parse(response.body);
var fees = data.fees;
var updated_fees = 0;
for (var i in fees) {
var fee = fees[i]
'''

def generate_end(num_fees: int) -> str:
    return f'''}}\nassert.equal(updated_fees, {num_fees});'''

    
def if_statement(fee: dict) -> str:
    """ Generates a JS 'if' statement
    """
    return f'\tif (fee.SettlementTypeID === {fee.get("SettlementTypeID")}) {{\n'
    

def else_if_statement(fee: dict) -> str:
    """ Generates a JS 'else if' statement
    """
    return f'\telse if (fee.SettlementTypeID === {fee.get("SettlementTypeID")}) {{\n'


def parse_command_line_arguments() -> Tuple[str, List[int]]:
    """ Parse command line arguments
    """
    parser = argparse.ArgumentParser(description='Generate Runscope test assertions')
    parser.add_argument(
        '--file', dest='file_name', help='Input file containing JSON to convert to assertions'
    )
    parser.add_argument(
        'integers', metavar='N', type=int, nargs='+', help='Integer that represents a SettlementTypeID'
    )
    args = parser.parse_args()
    return args.file_name, args.integers


def get_command_line_arguments() -> List[int]:
    """ Get from stdin a string containing file name followed by Settlement Type IDs, space delimited.

        Example: sample.json 401 901

        @returns: a list of Settlement Type IDs as integers
    """
    prev_line = None
    for line in sys.stdin:
        line = line.rstrip()
        if not line:
            break
        prev_line = line

    file_name, *ids = prev_line.split(' ')
    return file_name, list(map(int, ids))


def main():
    """ Convert JSON payload obtained from ResWare API+ GET /fees
        to JavaScript assertion statements for use in Runscope tests
    """
    file_name, ids = parse_command_line_arguments()

    with open(file_name, 'r') as file:
        contents = json.loads(file.read())

    with open('output.js', 'w') as output_file:
        output_file.write(generate_preamble())

        num_fees = 0
        first_if = True
        fees = contents.get('fees')
        for fee in fees:
            if fee.get('SettlementTypeID') not in ids:
                continue

            if first_if:
                statement = if_statement(fee)
            else:
                statement = else_if_statement(fee)
            first_if = False

            num_fees += 1
            output_file.write(statement)
            for pair in fee.items():
                key, value = pair
                if key in ATTRIBUTES_TO_SKIP:
                    continue
                if type(value) is str or type(value) is float:
                    output_file.write(f'\t\tassert.equal(fee.{key}, "{value}");\n')
                else:
                    # Convert None to JS null
                    safe_value = 'null' if value is None else value
                    output_file.write(f'\t\tassert.equal(fee.{key}, {safe_value});\n')
            output_file.write('\t\t++updated_fees;\n')
            output_file.write('\t}\n')

        output_file.write(generate_end(num_fees))


if __name__ == "__main__":
    main()
