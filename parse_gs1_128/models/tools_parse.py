# -*- coding: utf-8 -*-

"""
    Set of tools to parse GS1-128 codes.
    The code in this file is under GPLv3.
"""

def pairs_stack(string, pairs = {'[': ']', '{': '}', '(': ')'}):
    opening = list(pairs.keys())
    closing = list(pairs.values())
    
    match = list()
    found = False

    for s in string:
        if s in opening:
            match.insert(0, s)
        elif s in closing:
            if len(match) == 0:
                return False
            if match[0] == opening[closing.index(s)]:
                match.pop(0)
                if not found:
                    found = True
            else:
                return False

    if len(match) == 0 and found:
        return True

    return False

def parse_gs1_128(s):
    exists = pairs_stack(s, pairs = {'(': ')'})
    
    records = []
    
    if not exists:
        list_of_ai = ["01", "17", "10", "21"]
        list_ai_length = [14, 6, 20, 20]
        
        code = s[:2]
        while code in list_of_ai:
            data = s[2:2+list_ai_length[list_of_ai.index(code)]]
            
            records.append({
                'code': code,
                'data': data
            })
            
            s = s[2+list_ai_length[list_of_ai.index(code)]:]
            
            code = s[:2]
            
    else:
        while exists:
            code = ""
            data = ""
            i1 = s.find("(")
            i2 = s.find(")")

            code = s[i1+1:i2]
            s = s[i2+1:]

            exists = pairs_stack(s, pairs = {'(': ')'})

            if exists:
                data = s[:s.find("(")]
                s = s[s.find("("):]
            else:
                data = s

            records.append({
                'code': code,
                'data': data
            })

    return records
