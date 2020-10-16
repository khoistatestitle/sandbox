from typing import List
import json
import sys


# Exclude these fields from the generated output
ATTRIBUTES_TO_SKIP = {'CommonSettlementID'}


def if_statement(fee: dict) -> str:
    """ Generates a JS 'if' statement
    """
    return f'\tif (fee.SettlementTypeID === {fee.get("SettlementTypeID")}) {{\n'
    

def else_if_statement(fee: dict) -> str:
    """ Generates a JS 'else if' statement
    """
    return f'\telse if (fee.SettlementTypeID === {fee.get("SettlementTypeID")}) {{\n'


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
    file_name, ids = get_command_line_arguments()

    with open(file_name, 'r') as file:
        contents = json.loads(file.read())

    with open('output.js', 'w') as output_file:
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

            output_file.write(statement)
            for pair in fee.items():
                key, value = pair
                if key in ATTRIBUTES_TO_SKIP:
                    continue
                if type(value) is str or type(value) is float:
                    output_file.write(f'\t\tassert.equal(fee.{key}, "{value}");\n')
                else:
                    output_file.write(f'\t\tassert.equal(fee.{key}, {value});\n')
            output_file.write('\t}\n')


if __name__ == "__main__":
    main()
