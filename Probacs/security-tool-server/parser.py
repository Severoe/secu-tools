"""
parser.py: parser utility for user uploaded task file, 
            user uploaded profile file and user uploaded
            compiler configuration file
Author: Shipei Zhou
Email: shipeiz@andrew.cmu.edu
Date: May 27, 2018
"""

def parseTaskFile(filename):
    """
    args:
    filename: name of the user uploaded task file
    return:
    tuple, tuple[0] = parse message, None for no problem, string for any error
    tuple[1] = dict of parsed content
    """
    line_no = 0
    d = {}
    with open(filename) as file:
        while True:
            line_no += 1
            line = file.readline()
            if not line:
                break
            if ':' not in line:
                msg = "Malformatted line %d: no ':'' found"%line_no
                return msg, None
            
            tokens = filter(lambda x: x, line.split(":"))
            tokens = map(lambda x: x.strip(), tokens)
            
            if len(tokens) != 2:
                msg = "Malformatted line %d: must be in key:value format"%line_no
                return msg, None
            
            key, value = tokens
            
            if key in d:
                msg = "Duplicate key at line %d: %s already speficied"%(line_no, key)
                return msg, None
            
            if key == "profile":
                value = value.split(",")
                value = filter(lambda x: x, value)

            d[key] = value

    return None, d

