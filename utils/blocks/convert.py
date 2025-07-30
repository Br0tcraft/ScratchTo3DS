

def convert_start(next, blocks, sprite) -> dict:
    return {"success": False, "msg": "Not loaded yet"}

def generate_function(hats: dict, blocks: dict, sprite: dict, SECURE: bool, isStage) -> dict:
    '''{"success": True, "def": definitions, "func": ""}'''
    definitions = ""
    function = ""
    
    for key, block_ids  in hats.items():
        i = 1
        data = {"functionName": "", "loopCounter": 0, "vars": sprite["variables"], "secure": SECURE, "isStage": isStage}
        for block in block_ids:
            data["functionName"] = f"thread_{key}_{str(i)}(ctx, pubVars)"
            definitions += f"\t\tExecutionContext step_{key}_{str(i)};\n"
            result = convert_start(blocks[block]["next"], blocks, sprite, data)
            function += f'\tint thread_{key}_{str(i)}(ExecutionContext& ctx, std::unordered_map<std::string, std::string> &pubVars)\n'
            function += '\t{\n'
            if not result["success"]:
                return result
            function += result["func"]
            function += '\t};\n'
            i += 1

    return {"success": True, "def": definitions, "func": function}


def convert_stack(nextId, blocks, sprite, data) -> dict:
    code = []
    #block is correct
    block = ""
    if nextId is None:
        return {"success": True, "func": "\t\treturn 0;"}
    block = blocks[nextId]
    while True:
        if type(block) is not dict or "opcode" not in block or "next" not in block or "inputs" not in block or "fields" not in block or "topLevel" not in block:   
            return error("Missing Blockdata in sprite: " + sprite["name"])
        if type(block["opcode"]) is not str or not(type(block["next"]) is str or block["next"] == None) or type(block["inputs"]) is not dict or type(block["fields"]) is not dict or type(block["topLevel"]) is not bool or block["topLevel"] == True:   
            return error("Wrong Blockdata in sprite: " + sprite["name"])

        result = one_block_detection(blocks, block, sprite, data)
        if not result["success"]:
            return result
        code = code + result["code"]
        if block["next"] == None:
            break
        block = blocks[block["next"]]
    if len(code) == 0:
        return {"success": True, "func": "\t\treturn 0;"}
    return {"success": True, "func": code}

def convert_start(nextId, blocks, sprite, data) -> dict:
    '''{"success": True, "func": code}'''
    
    script = "\t\tif (ctx.finished) return 0;\n"
    script += "\t\tswitch (ctx.step)\n\t\t{\n"
    i = 0#
    code = convert_stack(nextId, blocks, sprite, data)
    if not code["success"]:
        return code
    for el in code["func"]:
        script += f"\t\t\tcase {str(i)}:\n"
        script += el + "\n\t\t\t\tbreak;\n"
        i += 1
    script += "\t\t\tdefault:\n"
    script += "\t\t\t\tctx.step = -1;\n"
    script += "\t\t\t\tctx.finished = true;\n"
    script += "\t\t\t\treturn 0;\n"
    script += "\t\t};\n"
    script += "\t\tctx.step++;\n"
    script += "\t\treturn 0;\n"
    return {"success": True, "func": script}


def get_value(blocks: dict, cont, variables: list, complexeScanForInt = True) -> str:
    '''1: String; 2: Bool; 3: Number; 4 Int
        {"success": True, "content": result}'''

    #content exist is correct
    if type(cont) is not list:
        return "0"
    if len(cont) < 2:
        return "0"
    
    #Detect Type
    if type(cont[1]) is list:
        if len(cont[1]) > 2:
            #than it is a Variable Block
            #is it private ior public var
            if cont[1][1] in variables:
                #it is private
                return f'vars["{str(cont[1][1])}"]'
            else:
                #probalby public var (or it does not exist)
                return f'puVars["{str(cont[1][1])}"]'
        elif len(cont[1]) > 1:
            return f'"{cont[1][1]}"'
        else:
            return "0"#error -> replacing with 0 (false; string: "0"; or number 0)
    elif type(cont[1]) is str:
        #it is a nested Block
        if cont[1] not in blocks:
            #something wrong with the Blocks
            return "0"
        if complexeScanForInt:
            return "SaveCalc::safeStringToInt(" + get_nested_block(blocks, blocks[cont[1]], variables, ) + ")"
        return get_nested_block(blocks, blocks[cont[1]], variables, complexeScanForInt)
        

def get_nested_block(blocks: dict, cont, variables: list, complexeScanForInt = True) -> str:
    if "opcode" not in cont:
        return "0"
    match cont["opcode"]:
        case "operator_add":
            if "inputs" not in cont:
                return "0"
            value1 = ""
            if "NUM1" in cont["inputs"]:
                value1 = get_value(blocks, cont["inputs"]["NUM1"], variables, complexeScanForInt)
            value2 = ""
            if "NUM2" in cont["inputs"]:
                value2 = get_value(blocks, cont["inputs"]["NUM2"], variables, complexeScanForInt)

            if complexeScanForInt:
                return f'SaveCalc::add({value1}, {value2})'
            return f'(std::stoi({value1}) + std::stoi({value2}))'
        case "operator_subtract":
            if "inputs" not in cont:
                return "0"
            value1 = ""
            if "NUM1" in cont["inputs"]:
                value1 = get_value(blocks, cont["inputs"]["NUM1"], variables, complexeScanForInt)
            value2 = ""
            if "NUM2" in cont["inputs"]:
                value2 = get_value(blocks, cont["inputs"]["NUM2"], variables, complexeScanForInt)
            if complexeScanForInt:
                return f'SaveCalc::sub({value1}, {value2})'
            return f'(std::stoi({value1}) - std::stoi({value2}))'
        case "operator_multiply":
            if "inputs" not in cont:
                return "0"
            value1 = ""
            if "NUM1" in cont["inputs"]:
                value1 = get_value(blocks, cont["inputs"]["NUM1"], variables, complexeScanForInt)
            value2 = ""
            if "NUM2" in cont["inputs"]:
                value2 = get_value(blocks, cont["inputs"]["NUM2"], variables, complexeScanForInt)
            if complexeScanForInt:
                return f'SaveCalc::mul({value1}, {value2})'
            return f'(std::stoi({value1}) * std::stoi({value2}))'
        case "operator_divide":
            if "inputs" not in cont:
                return "0"
            value1 = ""
            if "NUM1" in cont["inputs"]:
                value1 = get_value(blocks, cont["inputs"]["NUM1"], variables, complexeScanForInt)
            value2 = ""
            if "NUM2" in cont["inputs"]:
                value2 = get_value(blocks, cont["inputs"]["NUM2"], variables, complexeScanForInt)
            if complexeScanForInt:
                return f'SaveCalc::div({value1}, {value2})'
            return f'(std::stoi(({value1}) / std::stoi(({value2}))'
        case "operator_mod":
            if "inputs" not in cont:
                return "0"
            value1 = ""
            if "NUM1" in cont["inputs"]:
                value1 = get_value(blocks, cont["inputs"]["NUM1"], variables, complexeScanForInt)
            value2 = ""
            if "NUM2" in cont["inputs"]:
                value2 = get_value(blocks, cont["inputs"]["NUM2"], variables, complexeScanForInt)
            if complexeScanForInt:
                return f'SaveCalc::mod({value1}, {value2})'
            return f'(std::stoi(({value1}) % std::stoi(({value2}))'
        case "operator_random":
            if "inputs" not in cont:
                return "0"
            value1 = ""
            if "FROM" in cont["inputs"]:
                value1 = get_value(blocks, cont["inputs"]["FROM"], variables, complexeScanForInt)
            value2 = ""
            if "TO" in cont["inputs"]:
                value2 = get_value(blocks, cont["inputs"]["TO"], variables, complexeScanForInt)
            return f'SaveCalc::random({value1}, {value2})'
        case "operator_and":
            if "inputs" not in cont:
                return "0"
            if "OPERAND1" not in cont["inputs"] or "OPERAND2" not in cont["inputs"]:
                return "0"
            value1 = get_value(blocks, cont["inputs"]["OPERAND1"], variables, complexeScanForInt)
            value2 = get_value(blocks, cont["inputs"]["OPERAND2"], variables, complexeScanForInt)
            return f'SaveCalc::andOp({value1}, {value2})'
        case "operator_or":
            if "inputs" not in cont:
                return "0"
            value1 = "0"
            if "OPRAND1" in cont["inputs"]:
                value1 = get_value(blocks, cont["inputs"]["OPRAND1"], variables, complexeScanForInt)
            value2 = "0"
            if "OPRAND2" in cont["inputs"]:
                value2 = get_value(blocks, cont["inputs"]["OPRAND2"], variables, complexeScanForInt)
            return f'SaveCalc::orOp({value1}, {value2})'
        case "operator_not":
            if "inputs" not in cont:
                return "1"
            if "OPERAND" not in cont["inputs"]:
                return "1"
            value = get_value(blocks, cont["inputs"]["OPERAND"], variables, complexeScanForInt)
            return f'SaveCalc::notOp(std::to_string({value}))'
        case "operator_gt":
            if "inputs" not in cont:
                return "0"
            value1 = "0"
            if "OPRAND1" in cont["inputs"]:
                value1 = get_value(blocks, cont["inputs"]["OPRAND1"], variables, complexeScanForInt)
            value2 = "0"
            if "OPRAND2" in cont["inputs"]:
                value2 = get_value(blocks, cont["inputs"]["OPRAND2"], variables, complexeScanForInt)
            return f'SaveCalc::gt({value1}, {value2})'
        case "operator_lt":
            if "inputs" not in cont:
                return "0"
            value1 = "0"
            if "OPRAND1" in cont["inputs"]:
                value1 = get_value(blocks, cont["inputs"]["OPRAND1"], variables, complexeScanForInt)
            value2 = "0"
            if "OPRAND2" in cont["inputs"]:
                value2 = get_value(blocks, cont["inputs"]["OPRAND2"], variables, complexeScanForInt)
            return f'SaveCalc::lt({value1}, {value2})'
        case "operator_equals":
            if "inputs" not in cont:
                return "0"
            value1 = "0"
            if "OPRAND1" in cont["inputs"]:
                value1 = get_value(blocks, cont["inputs"]["OPRAND1"], variables, complexeScanForInt)
            value2 = "0"
            if "OPRAND2" in cont["inputs"]:
                value2 = get_value(blocks, cont["inputs"]["OPRAND2"], variables, complexeScanForInt)
            return f'SaveCalc::eq({value1}, {value2})'
        case "operator_join":
            if "inputs" not in cont:
                return '""'
            value1 = ""
            if "STRING1" in cont["inputs"]:
                value1 = get_value(blocks, cont["inputs"]["STRING1"], variables, complexeScanForInt)
            value2 = ""
            if "STRING2" in cont["inputs"]:
                value2 = get_value(blocks, cont["inputs"]["STRING2"], variables, complexeScanForInt)
            return f'{value1} + {value2}'
        case "operator_letter_of":
            if "inputs" not in cont:
                return '""'
            value1 = ""
            if "STRING" in cont["inputs"]:
                value1 = get_value(blocks, cont["inputs"]["STRING"], variables, complexeScanForInt)
            value2 = "0"
            if "LETTER" in cont["inputs"]:
                value2 = get_value(blocks, cont["inputs"]["LETTER"], variables, complexeScanForInt)
            if complexeScanForInt:
                return f'SaveCalc::letterOf({value1}, {value2})'
            return f'std::string(1, {value1}[std::stoi({value2}) - 1])'
        case "operator_length":
            if "inputs" not in cont:
                return "0"
            value1 = ""
            if "STRING" in cont["inputs"]:
                value1 = get_value(blocks, cont["inputs"]["STRING"], variables, complexeScanForInt)
            return f'lenght({value1})'
        case "operator_contains":
            if "inputs" not in cont:
                return "0"
            value1 = ""
            if "STRING1" in cont["inputs"]:
                value1 = get_value(blocks, cont["inputs"]["STRING1"], variables, complexeScanForInt)
            value2 = ""
            if "STRING2" in cont["inputs"]:
                value2 = get_value(blocks, cont["inputs"]["STRING2"], variables, complexeScanForInt)
            return f'(std::to_string{value1}).contains({value2})'
        case "operator_round":
            if "inputs" not in cont:
                return "0"
            value1 = ""
            if "NUM" in cont["inputs"]:
                value1 = get_value(blocks, cont["inputs"]["NUM"], variables, complexeScanForInt)
            if complexeScanForInt:
                return f'SaveCalc::round({value1})'
            return f'round(std:stoi({value1}))'
        case "operator_mathop":
            if "fields" not in cont or "OPERATOR" not in cont["fields"]:
                return "0"
            if "inputs" not in cont:
                return "0"
            match cont["fields"]["OPERATOR"]:
                case "abs":
                    value1 = ""
                    if "NUM" in cont["inputs"]:
                        value1 = get_value(blocks, cont["inputs"]["NUM"], variables, complexeScanForInt)
                    if complexeScanForInt:
                        return f'SaveCalc::abs({value1})'
                    return f'abs({float(value1)})'
                case "floor":
                    value1 = ""
                    if "NUM" in cont["inputs"]:
                        value1 = get_value(blocks, cont["inputs"]["NUM"], variables, complexeScanForInt)
                    if complexeScanForInt:
                        return f'SaveCalc::floor({value1})'
                    return f'floor({float(value1)})'
                case "ceiling":
                    value1 = ""
                    if "NUM" in cont["inputs"]:
                        value1 = get_value(blocks, cont["inputs"]["NUM"], variables, complexeScanForInt)
                    if complexeScanForInt:
                        return f'SaveCalc::ceiling({value1})'
                    return f'ceil({float(value1)})'
                case "sqrt":
                    value1 = ""
                    if "NUM" in cont["inputs"]:
                        value1 = get_value(blocks, cont["inputs"]["NUM"], variables, complexeScanForInt)
                    if complexeScanForInt:
                        return f'SaveCalc::sqrt({value1})'
                    return f'sqrt({float(value1)})'
                case "ln":
                    value1 = ""
                    if "NUM" in cont["inputs"]:
                        value1 = get_value(blocks, cont["inputs"]["NUM"], variables, complexeScanForInt)
                    if complexeScanForInt:
                        return f'SaveCalc::ln({value1})'
                    return f'log({float(value1)})'
                case "log":
                    value1 = ""
                    if "NUM" in cont["inputs"]:
                        value1 = get_value(blocks, cont["inputs"]["NUM"], variables, complexeScanForInt)
                    if complexeScanForInt:
                        return f'SaveCalc::log({value1})'
                    return f'log10({float(value1)})'
                case "sin":
                    value1 = ""
                    if "NUM" in cont["inputs"]:
                        value1 = get_value(blocks, cont["inputs"]["NUM"], variables, complexeScanForInt)
                    if complexeScanForInt:
                        return f'SaveCalc::sin({value1})'
                    return f'sin({float(value1)})'
                case "cos":
                    value1 = ""
                    if "NUM" in cont["inputs"]:
                        value1 = get_value(blocks, cont["inputs"]["NUM"], variables, complexeScanForInt)
                    if complexeScanForInt:
                        return f'SaveCalc::cos({value1})'
                    return f'cos({float(value1)})'
                case "tan":
                    value1 = ""
                    if "NUM" in cont["inputs"]:
                        value1 = get_value(blocks, cont["inputs"]["NUM"], variables, complexeScanForInt)
                    if complexeScanForInt:
                        return f'SaveCalc::tan({value1})'
                    return f'tan({float(value1)})'
                case "asin":
                    value1 = ""
                    if "NUM" in cont["inputs"]:
                        value1 = get_value(blocks, cont["inputs"]["NUM"], variables, complexeScanForInt)
                    if complexeScanForInt:
                        return f'SaveCalc::asin({value1})'
                    return f'asin({float(value1)})'
                case "acos":
                    value1 = ""
                    if "NUM" in cont["inputs"]:
                        value1 = get_value(blocks, cont["inputs"]["NUM"], variables, complexeScanForInt)
                    if complexeScanForInt:
                        return f'SaveCalc::acos({value1})'
                    return f'acos({float(value1)})'
                case "atan":
                    value1 = ""
                    if "NUM" in cont["inputs"]:
                        value1 = get_value(blocks, cont["inputs"]["NUM"], variables, complexeScanForInt)
                    if complexeScanForInt:
                        return f'SaveCalc::atan({value1})'
                    return f'atan({float(value1)})'
                case "10 ^":
                    value1 = ""
                    if "NUM" in cont["inputs"]:
                        value1 = get_value(blocks, cont["inputs"]["NUM"], variables, complexeScanForInt)
                    if complexeScanForInt:
                        return f'SaveCalc::pow10({value1})'
                    return f'pow(10, {float(value1)})'
                case "e ^":
                    value1 = ""
                    if "NUM" in cont["inputs"]:
                        value1 = get_value(blocks, cont["inputs"]["NUM"], variables, complexeScanForInt)
                    if complexeScanForInt:
                        return f'SaveCalc::powE({value1})'
                    return f'pow(M_E, {float(value1)})'













def control(blocks, block, data, sprite) -> dict:
    opcode = block["opcode"]
    result = []
    match opcode:
        case "control_wait":
            value = 0
            if "DURATION" in block["inputs"]:
                value = get_value(blocks, block["inputs"]["DURATION"], data["vars"], data["secure"])
                if data["secure"]:
                    value = f'std::max(0, SaveCalc::safeStringToInt({value}))'
                else:
                    value = f'std::max(0, std::stoi({value}))'
            else:
                value = {"success": True, "content": "0"}
            result.append(f'\t\t\t\tctx.loopCounters.push_back(osGetTime() + ({value} * 1000));\n\t\t\t\tctx.step++;\n\t\t\t\treturn {data["functionName"]};\n')
            result.append(f'\t\t\t\tif (osGetTime() < (u64)ctx.loopCounters[{data}]) \n\t\t\t\t{{\n\t\t\t\t\treturn 0;\n\n\t\t\t\t\t}}\n\t\t\t\tctx.loopCounters.pop_back();\n')
        
        case "control_repeat":
            value = 0
            if "TIMES" in block["inputs"]:
                value = get_value(blocks, block["inputs"]["TIMES"], data["vars"], data["secure"])
                if data["secure"]:
                    value = f'std::max(0, SaveCalc::safeStringToInt({value}))'
                else:
                    value = f'std::max(0, std::stoi({value}))'
            else:
                value = 0
            
            if "SUBSTACK" in block["inputs"] and type(block["inputs"]["SUBSTACK"]) is list and len(block["inputs"]["SUBSTACK"]) > 1 and type(block["inputs"]["SUBSTACK"][1]) is str and block["inputs"]["SUBSTACK"][1] in blocks:
                data["loopCounter"] += 1
                newCode = convert_stack(block["inputs"]["SUBSTACK"][1], blocks, sprite, data)
                data["loopCounter"] -= 1
                if not newCode["success"]:
                    return newCode
            else:
                newCode = {"success": True, "func": ""}
            result.append(f'\t\t\t\tctx.loopCounters.push_back({value});\n\t\t\t\tctx.step++;\n\t\t\t\treturn {data["functionName"]};\n')
            step = []
            count = 1
            for el in newCode["func"]:
                step.append(el)
                count += 1
            step.append(f'\t\t\t\tctx.loopCounters[{data["loopCounter"]}]--;\n\t\t\t\tctx.step -= {count};\n\t\t\t\treturn {data["functionName"]};\n')
            result.append(f'\t\t\t\tif (ctx.loopCounters[{data["loopCounter"]}] == 0)\n\t\t\t\t{{\n\t\t\t\t\tctx.loopCounters.pop_back();\n\t\t\t\t\tctx.step += {count + 1};\n\t\t\t\treturn 0;\n\n\t\t\t\t}}\n')
            result += step
           
        case "control_forever":
            if "SUBSTACK" in block["inputs"] and type(block["inputs"]["SUBSTACK"]) is list and len(block["inputs"]["SUBSTACK"]) > 1 and type(block["inputs"]["SUBSTACK"][1]) is str and block["inputs"]["SUBSTACK"][1] in blocks:
                newCode = convert_stack(block["inputs"]["SUBSTACK"][1], blocks, sprite, data)
                if not newCode["success"]:
                    return newCode
            else:
                newCode = {"success": True, "func": ""}
            step = []
            count = 0
            for el in newCode["func"]:
                step.append(el)
                count += 1
            step.append(f'\t\t\t\tctx.step -= {count};\n\t\t\t\treturn {data["functionName"]};\n')
            result += step

        case "control_if":
            if "CONDITION" in block["inputs"]:
                condition = get_value(blocks, block["inputs"]["CONDITION"], 2)
                if not condition["success"]:
                    return condition

    return {"success": True, "code": result}




def motion(blocks, block, data) -> dict:
    opcode = block["opcode"]
    result = []
    match opcode:

        case "motion_movesteps":
            value = 0
            if "STEPS" in block["inputs"]:
                value = get_value(blocks, block["inputs"]["STEPS"], data["vars"], data["secure"])
                if data["secure"]:
                    result.append(f'\t\t\t\tx += SaveCalc::safeStringToInt({value});\n')
                else:
                    result.append(f'\t\t\t\tx += std::stoi({value});\n')
            else:
                result.append("\t\t\t\tx += 0;")

        case "motion_turnright":
            value = 0
            if "DEGREES" in block["inputs"]:
                value = get_value(blocks, block["inputs"]["DEGREES"], data["vars"], data["secure"])
                if data["secure"]:
                    result.append(f'\t\t\t\tdirection += SaveCalc::safeStringToInt({value});\n')
                else:
                    result.append(f'\t\t\t\tdirection += std::stoi({value});\n')
            else:
                result.append("\t\t\t\tdirection += 0;")

        case "motion_turnleft":
            value = 0
            if "DEGREES" in block["inputs"]:
                value = get_value(blocks, block["inputs"]["DEGREES"], data["vars"], data["secure"])
                if data["secure"]:
                    result.append(f'\t\t\t\tdirection -= SaveCalc::safeStringToInt({value});\n')
                else:
                    result.append(f'\t\t\t\tdirection -= std::stoi({value});\n')
            else:
                result.append("\t\t\t\tdirection -= 0;")
        #EDIT
        case "motion_goto":
            value = 0
            if "TO" in block["inputs"]:
                value = get_value(blocks, block["inputs"]["TO"], data["vars"], data["secure"])
                if data["secure"]:
                    result.append(f'\t\t\t\tdirection -= SaveCalc::safeStringToInt({value});\n')
                else:
                    result.append(f'\t\t\t\tdirection -= std::stoi({value});\n')
            else:
                result.append(f'\t\t\t\tdirection -= 0;\n')

        case "motion_gotoxy":
            value = 0
            step = ""
            if "X" in block["inputs"]:
                value = get_value(blocks, block["inputs"]["X"], data["vars"], data["secure"])
                if data["secure"]:
                    step += f'\t\t\t\tx = SaveCalc::safeStringToInt({value});\n'
                else:
                    step += f'\t\t\t\tx = std::stoi({value});\n'
            else:
                step += "\t\t\t\tx = 0;\n"
            if "Y" in block["inputs"]:
                value = get_value(blocks, block["inputs"]["Y"], data["vars"], data["secure"])
                if data["secure"]:
                    step += f'\t\t\t\ty = SaveCalc::safeStringToInt({value});\n'
                else:
                    step += f'\t\t\t\ty = std::stoi({value});\n'
            else:
                step += "\t\t\t\ty = 0;"
            result.append(step)
        #Edit
        case "motion_glideto":
            value = 0
            if "TO" in block["inputs"]:
                value = get_value(blocks, block["inputs"]["TO"], data["vars"], data["secure"])
                if data["secure"]:
                    result.append(f'\t\t\t\tdirection -= SaveCalc::safeStringToInt({value});\n')
                else:
                    result.append(f'\t\t\t\tdirection -= std::stoi({value});\n')
            else:
                result.append(f'\t\t\t\tdirection -= 0;\n')

        case "motion_glidesecstoxy":
            value = 0
            Xvalue = 0
            Yvalue = 0
            step = ""
            if "X" in block["inputs"]:
                Xvalue = get_value(blocks, block["inputs"]["X"], data["vars"], data["secure"])
                if data["secure"]:
                    Xvalue = f'SaveCalc::safeStringToInt({Xvalue})'
                else:
                    Xvalue = f'std::stoi({Xvalue})'
            else:
                Xvalue = "0"
            
            if "Y" in block["inputs"]:
                Yvalue = get_value(blocks, block["inputs"]["Y"], data["vars"], data["secure"])
                if data["secure"]:
                    Yvalue = f'SaveCalc::safeStringToInt({Yvalue})'
                else:
                    Yvalue = f'std::stoi({Yvalue})'
            else:
                Yvalue = "0"
            
            if "SECS" in block["inputs"]:
                value = get_value(blocks, block["inputs"]["SECS"], data["vars"], data["secure"])
                if data["secure"]:
                    value = f'std::max(0, SaveCalc::safeStringToInt({value}))'
                else:
                    value = f'std::max(0, std::stoi({value}))'
            else:
                value = "0"
            step += f'\t\t\t\tctx.loopCounters.push_back(osGetTime() + {value} * 1000);\n'
            step += f'\t\t\t\tctx.loopCounters.push_back(x);\n'
            step += f'\t\t\t\tctx.loopCounters.push_back({Xvalue});\n'
            step += f'\t\t\t\tctx.loopCounters.push_back(y);\n'
            step += f'\t\t\t\tctx.loopCounters.push_back({Yvalue});\n'
            step += f'\t\t\t\tctx.step++;\n'
            step += f'\t\t\t\treturn {data["functionName"]};\n'
            result.append(step)
            step = f'\t\t\t\tif (osGetTime() < (u64)ctx.loopCounters[{data["loopCounter"]}])\n\t\t\t\t{{\n\t\t\t\t\tx = ctx.loopCounters[{data["loopCounter"] + 1}] + (ctx.loopCounters[{data["loopCounter"] + 2}] - ctx.loopCounters[{data["loopCounter"] + 1}]) * (1.0f - float((u64)ctx.loopCounters[{data["loopCounter"]}] - osGetTime()) / (1000.0f * {value}));\n\t\t\t\t\ty = ctx.loopCounters[{data["loopCounter"] + 3}] + (ctx.loopCounters[{data["loopCounter"] + 4}] - ctx.loopCounters[{data["loopCounter"] + 3}]) * (1.0f - float((u64)ctx.loopCounters[{data["loopCounter"]}] - osGetTime()) / (1000.0f * {value}));\n\t\t\t\t\treturn 0;\n\n\t\t\t\t}}\n'
            step += f'\t\t\t\telse\n\t\t\t\t{{\n\t\t\t\t\tx = ctx.loopCounters[{data["loopCounter"] + 2}];\n\t\t\t\t\ty = ctx.loopCounters[{data["loopCounter"] + 4}];\n\t\t\t\t\tctx.loopCounters.pop_back();\n\t\t\t\t\tctx.loopCounters.pop_back();\n\t\t\t\t\tctx.loopCounters.pop_back();\n\t\t\t\t\tctx.loopCounters.pop_back();\n\t\t\t\t\tctx.loopCounters.pop_back();\n\t\t\t\t}}'
            result.append(step)

        case "motion_pointindirection":
            value = 0
            if "DIRECTION" in block["inputs"]:
                value = get_value(blocks, block["inputs"]["DIRECTION"], data["vars"], data["secure"])
                if data["secure"]: 
                    result.append(f'\t\t\t\tdirection = SaveCalc::safeStringToInt({value});\n')
                else:
                    result.append(f'\t\t\t\tdirection = std::stoi({value});\n')
            else:
                result.append("\t\t\t\tdirection = 0;")
        #edit
        case "motion_pointtowards":
            value = 0
            if "TOWARDS" in block["inputs"]:
                value = get_value(blocks, block["inputs"]["TOWARDS"], data["vars"], data["secure"])
                result.append(f'\t\t\t\tdirection = {value};\n')
            else:
                result.append("\t\t\t\tdirection = 0;")
        
        case "motion_changexby":
            value = 0
            if "DX" in block["inputs"]:
                value = get_value(blocks, block["inputs"]["DX"], data["vars"], data["secure"])
                if data["secure"]:
                    result.append(f'\t\t\t\tx += SaveCalc::safeStringToInt({value});\n')
                else:
                    result.append(f'\t\t\t\tx += std::stoi({value});\n')
            else:
                result.append("\t\t\t\tx += 0;")
        case "motion_changeyby":
            value = 0
            if "DY" in block["inputs"]:
                value = get_value(blocks, block["inputs"]["DY"], data["vars"], data["secure"])
                if data["secure"]:
                    result.append(f'\t\t\t\ty += SaveCalc::safeStringToInt({value});\n')
                else:
                    result.append(f'\t\t\t\ty += std::stoi({value});\n')
        
        case "motion_setx":
            value = 0
            if "X" in block["inputs"]:
                value = get_value(blocks, block["inputs"]["X"],data["vars"], data["secure"])
                if data["secure"]:
                    result.append(f'\t\t\t\tx = SaveCalc::safeStringToInt({value});\n')
                else:
                    result.append(f'\t\t\t\tx = std::stoi({value});\n')
            else:
                result.append("\t\t\t\tx = 0;")
        
        case "motion_sety":
            value = 0
            if "Y" in block["inputs"]:
                value = get_value(blocks, block["inputs"]["Y"], data["vars"], data["secure"])
                if data["secure"]:
                    result.append(f'\t\t\t\ty = SaveCalc::safeStringToInt({value});\n')
                else:
                    result.append(f'\t\t\t\ty = std::stoi({value});\n')
            else:
                result.append("\t\t\t\ty = 0;")
        case _:
            return error("Unknown motion block: " + opcode)
    return {"success": True, "code": result}













def one_block_detection(blocks, block, sprite, data: dict) -> dict:
    '''{"success": True, "code": [move, move, etc]}'''
    opcode = block["opcode"]
    result = {"success": False, "msg": "unknown block: " + opcode}
    match opcode.split("_")[0]:
        case "control":
            result = control(blocks, block, data, sprite)
        case "motion":
            if data["isStage"]:
                return error("Motion blocks are not allowed in stage scripts")
            result = motion(blocks, block, data)
            
    
    return result
    

def error(msg: str) -> dict:
    '''
    msg is the error message that gets returned:\n
    return {"success": False, "msg": msg}
    '''
    return {"success": False, "msg": msg}