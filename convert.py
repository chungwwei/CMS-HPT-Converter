import json
import csv

def to_headers_json(headers, headers_values):
    mp = {}
    first_empty_index = headers.index("")
    headers = headers[:first_empty_index]
    headers_values = headers_values[:first_empty_index]
    for index, (header, value) in enumerate(zip(headers, headers_values)):
        if header == "hospital_address" or header == "hospital_location":
            mp[header] = value.split('|')
        elif "license_number" in header:
            mp["license_information"] = {
                "license_number": value,
                "state": header.split("|")[1]
            }
        elif index == len(headers) - 1:
            mp["affirmation"] = {
                "affirmation": header,
                "confirm_affirmation": bool(value)
            }
        elif header == None or header == "":
            break
        else:
            mp[header] = value
        
    return mp

def create_standard_charge(charges, headers):
    PREFIX = "standard_charge"
    rename_mp = {
        f'{PREFIX}|gross': "gross_charge",
        f'{PREFIX}|discounted_cash': "discounted_cash",
        f'{PREFIX}|minimum': "minimum",
        f'{PREFIX}|maximum': "maximum",
        f'{PREFIX}|negotiated_dollar': "standard_charge_dollar",
        f'{PREFIX}|negotiated_percentage': "standard_charge_percentage",
        f'{PREFIX}|negotiated_algorithm': "standard_charge_algorithm",
        f'{PREFIX}|methodology': "methodology",
        "additional_generic_notes": "additional_payer_notes",
    }

    for i in range(len(headers)):
        key = headers[i]
        if key in rename_mp:
            headers[i] = rename_mp[key]
    
    PAYER_FIELDS = [
        "payer_name",
        "plan_name",
        "modifiers",
        f"{PREFIX}_dollar",
        f"{PREFIX}_percentage",
        f"{PREFIX}_algorithm",
        "estimated_amount",
        "methodology",
        "additional_payer_notes",
    ]

    CHARGES_FIELDS = [
        "minimum",
        "maximum",
        "gross_charge",
        "discounted_cash",
        "setting",
    ]

    res = {}
    payers_information = []
    for charge in charges:
        payer_info = {}
        for header, value in zip(headers, charge):
            if header in CHARGES_FIELDS and value:
                is_numeric = header in ["minimum", "maximum", "gross_charge", "discounted_cash"]
                res[header] = formatTrailingZeros(float(value)) if is_numeric else value
            if header in PAYER_FIELDS and value:
                is_numeric = header in ["estimated_amount", "standard_charge_dollar", "standard_charge_percentage"]
                payer_info[header] = formatTrailingZeros(float(value)) if is_numeric else value
        payers_information.append(payer_info)
        res["payers_information"] = payers_information
    return res


def formatTrailingZeros(num):
    if num % 1 == 0:
        return int(num)
    return num



def main():
    with open('./tall_csv_data.csv', 'r') as f:
        reader = csv.reader(f)
        headers = next(reader)
        headers_values = next(reader)
        charges_headers = next(reader)
        # get the rest of the lines
        lines = []
        for line in reader:
            lines.append(line)
    
    mp = to_headers_json(headers, headers_values)


    group_charges = {}
    for line in lines:
        if line[1] not in group_charges:
            group_charges[line[1]] = []
        group_charges[line[1]].append(line)

    charges_information = []
    for key, lines in group_charges.items():
        code_information = []
        code_information_set = set()
        standard_charge = {}
        for index, line in enumerate(lines):
            if index == 0:
                standard_charge["description"] = line[0]
            if line[1] and line[2] and (line[1], line[2]) not in code_information_set:
                code_information_set.add((line[1], line[2]))
                code_information.append({
                    "code": line[1],
                    "code_type": line[2]
                })
            if line[3] and line[4] and (line[3], line[4]) not in code_information_set:
                code_information_set.add((line[3], line[4]))
                code_information.append({
                    "code": line[3],
                    "code_type": line[4]
                })

        group_by_setting = {}
        setting_index = charges_headers.index("setting")
        for line in lines:
            if line[setting_index] not in group_by_setting:
                group_by_setting[line[setting_index]] = []
            group_by_setting[line[setting_index]].append(line)
        
        for setting in group_by_setting:
            std_charge = create_standard_charge(group_by_setting[setting], headers=charges_headers)
        
        standard_charge["code_information"] = code_information
        standard_charge["standard_charge"] = std_charge
        charges_information.append(standard_charge)
            


    mp["standard_charge_information"] = charges_information

    
    


    json.dump(mp, open('./data.json', 'w'), indent=4)
    




if __name__ == '__main__':
    main()