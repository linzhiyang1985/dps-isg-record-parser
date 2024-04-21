
import json
import os
import sys

# https://www.dps.org.hk/en/download/guideline/ISG_2016-ENG.pdf
# tool for parsing the deposit data file

first_segment_definition = (
    ('Record number', 10),
    ('deposit type code', 10),
    ('account number', 30),
    ('position reference number', 30),
    ('currency', 3),
    ('principal balance', 30),
    ('principal balance + accrued interest', 30),
    ('interest rate', 20),
    ('interest rate indicator', 1),
    ('% above/below benchmark rate', 20),
    ('last interest pay date', 8, "DDMMYYYY"),
    ('next interest pay date', 8, "DDMMYYYY"),
    ('value date', 8, "DDMMYYYY"),
    ('maturity date', 8, "DDMMYYYY"),
    ('number of depositor(s)', 3),
    ('trust/client Indicator', 1),
    ('encumbrances indicator', 1),
    ('deposit account status indicator', 1)
)
depositor_segment = (
    ('depositor name', 100),
    ('customer type', 1),
    ('identity document type indicator', 1),
    ('ID/passport number', 20),
    ('date of birth', 8, "DDMMYYYY"),
    ('BR/CI number', 20),
    ('BR number of sole proprietorship', 20),
    ('name of sole proprietor', 100),
    ('ID/passport number of sole proprietor', 20),
    ('BR number of partnership', 20),
    ('ATM card indicator', 1),
    ('internet banking indicator', 1),
    ('NOT IN USE', 3),
    ('address status indicator', 1),
    ('address 1', 50),
    ('address 2', 50),
    ('address 3', 50),
    ('address 4', 50),
    ('address 5', 50),
    ('telephone number', 20),
    ('mobile phone number', 20),
    ('email address', 50),
)

row_pos_cache = []

def scan_row_pos(file_path, from_pos=0, to_pos=-1):
    '''
    scan start position of each record row
    :param file_path: record file path
    :param from_pos: file pointer position to start seeking
    :param to_pos: scan up till position, any negative number means scan till end of file
    :return: None, will store scanning result in global row_pos_cache
    '''
    global row_pos_cache

    with open(file_path, 'r') as fp:
        fp.seek(from_pos) ### from_pos MUST be the beginning position of any line
        if from_pos == 0:
            # first row is header row, consume it
            row_content = fp.readline()
        next_row_pos = fp.tell()
        while next_row_pos < to_pos or to_pos < 0:
            row_pos_cache.append(next_row_pos)
            _ = fp.readline() # content is discarded
            if not _:
                # end of file reached, remove tail row start and end position
                row_pos_cache.pop()
                row_pos_cache.pop()
                break
            else:
                next_row_pos = fp.tell()
    row_pos_cache = sorted(list(set(row_pos_cache)))

def read_row(file_path, row_id):
    '''
    read one row at given row id, starting from 1
    :param file_path: record file path
    :param row_id: row id, starts from 1
    :return: row content in string
    '''
    global row_pos_cache
    row_index = row_id - 1 # row id starts from 1
    if row_index > len(row_pos_cache) - 1:
        scan_row_pos(file_path, from_pos=(0 if row_pos_cache==[] else row_pos_cache[-1]), to_pos=10000 * row_id)
    if row_index < len(row_pos_cache):
        # row exist
        with open(file_path, 'r') as fp:
            fp.seek(row_pos_cache[row_index])
            row_content = fp.readline()
            return row_content
    else:
        return ''

def parse_row(row_content):
    '''
    parse row content using DEPOSIT PROTECTION SCHEME
    :param row_content: string
    :return: dictionary of the parsed record
    '''
    if not row_content:
        return {}

    global first_segment_definition, depositor_segment
    dict_format = {}
    for field_def in first_segment_definition:
        field_name, *field_length_and_format = field_def
        length = field_length_and_format[0]
        dict_format[field_name] = row_content[:length]
        row_content = row_content[length:]
    # print(json.dumps(dict_format, indent=4))
    try:
        number_of_depositors = int(dict_format['number of depositor(s)'])
    except Exception as ex:
        print(dict_format)
    dict_format['depositors'] = []
    for _ in range(number_of_depositors):
        depositor_dict = {}
        for field_def in depositor_segment:
            field_name, *field_length_and_format = field_def
            length = field_length_and_format[0]
            depositor_dict[field_name] = row_content[:length]
            row_content = row_content[length:]
        dict_format['depositors'].append(depositor_dict)
        # print(json.dumps(dict_format, indent=4))
    return dict_format

def read_file_command(data_file, id):
    os.system('cls')
    print(f'Reading file {data_file}:')

    row_content = read_row(data_file, id)
    parsed_dict = parse_row(row_content)
    print(json.dumps(parsed_dict, indent=4))

def set_file_command(old_data_file, old_id):
    global row_pos_cache
    data_file = ''
    while not data_file or not os.path.exists(data_file):
        data_file = input('Please provide data file path (Q to quit):')
        if data_file and data_file[0].upper() == 'Q':
            if old_data_file:
                return old_data_file, old_id
            else:
                sys.exit()
    # a new valid file path is provided
    if (not old_data_file) or (os.path.abspath(old_data_file) != os.path.abspath(data_file)):
        # the selected file is different from the previous one
        old_id = 1
        row_pos_cache.clear()
    return data_file, old_id

if __name__ == '__main__':
    if len(sys.argv) > 1 and os.path.exists(sys.argv[1]):
        data_file = sys.argv[1]
    else:
        data_file = None
    id = 1

    while True:
        if data_file and os.path.exists(data_file):
            read_file_command(data_file, id)
        else:
            data_file, id = set_file_command(data_file, id)
            continue

        print(f'Commands supported: (Q)uit, (F)ile to read, (N)ext, (P)revious, record number')
        prompt_input = input(f"Please input the record number (current {id}):")
        if prompt_input:
            prompt_input = prompt_input.upper()
            if prompt_input[0] == 'Q':
                sys.exit()
            elif prompt_input[0] == 'F':
                data_file, id = set_file_command(data_file, id)
            elif prompt_input[0] == 'N':
                id += 1
            elif prompt_input[0] == 'P':
                id -= 1
                if id < 1:
                    id = 1
            else:
                try:
                    new_id = int(prompt_input)
                    if new_id > 0:
                        id = new_id
                except:
                    pass