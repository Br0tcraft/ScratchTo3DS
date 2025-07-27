

def convert_start(next, blocks, sprite) -> dict:
    return {"success": False, "msg": "Not loaded yet"}

def generate_function(hats: dict, blocks: dict, sprite: dict) -> dict:
    '''{"success": True, "def": definitions, "func": ""}'''
    definitions = ""
    function = ""
    
    for key, block_ids  in hats.items():
        i = 1
        data = {"functionName": "", "loopCounter": 0}
        for block in block_ids:
            data["functionName"] = f"thread_{key}_{str(i)}(ctx)"
            definitions += f"\t\tExecutionContext step_{key}_{str(i)};\n"
            result = convert_start(blocks[block]["next"], blocks, sprite, data)
            function += f'\tint thread_{key}_{str(i)}(ExecutionContext& ctx)\n'
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


def get_value(blocks, cont, need: int, posOrNegativ = "negativ"):
    '''1: String; 2: Bool; 3: Number; 4 Int
        {"success": True, "content": result}'''
    print("KONVERT BLOCK")
    print(cont)
    print("TYPE")
    print(cont[0])
    result = calc_value(blocks, cont)
    if not result["success"]:
        return result
    value = result["values"]
    result = ""
    print("OUPT")
    print(value["calc"])
    print(value["calc"] is not None or value["calc"] is None)
    if value["calc"] is not None or value["calc"] is None:
        print(type(cont[0]))
        if need == 1:
            result = f'"{str(value["calc"])}"'
        elif need == 2:
            print("BOOL")
            if str(value["calc"]) <= "0":
                 result = "false"
            else:
                result = "true"
        elif need == 3:
            try:
                result = str(float(str(value["calc"])))
            except:
                result = "0"
            if posOrNegativ == "positiv":
                if float(result) < 0:
                    result = "0"
        elif need == 4:
            try:
                print(f"##{value['calc']}##")
                result = str(int(float(str(value['calc']))))
            except:
                result = "0"
            if posOrNegativ == "positiv":
                if int(result) < 0:
                    result = "0"
    return {"success": True, "content": result}
    #
def calc_value(blocks, cont) -> dict:
    values = {}
    print("CONTENT")
    print(cont)
    if type(cont) is not list:
        return error("Wrong input type in one of the Blocks")
    if type(cont[1]) is list:
        if len(cont[1]) > 2:
            print("IS VARIABLE")
            #it is a variable
            values = {"type": "variable", "value": str(cont[1][1]), "calc": None}
        else:
            print("IS STRING OR NUMBER")
            values = {"type": "input", "value": str(cont[1][1]), "calc": str(cont[1][1])}
    if type(cont[1]) is str:
        if cont[1] not in blocks:
            return error("Missing or wrong block id found")
        print("IS NESTED BLOCK")
        result = iterate_values(blocks, blocks[cont[1]])
        if not result["success"]:
            return result
        print(result["values"])
        values = result["values"]
    return {"success": True, "values": values}
#1 bei text
#2 bei bool
#3 bei Zahl
def iterate_values(blocks, block):
    print("NESTED:")
    if type(block) is not dict or "opcode" not in block or "inputs" not in block or "fields" not in block or "topLevel" not in block:
        return error("Missing Blockdata")
    if type(block["opcode"]) is not str or type(block["inputs"]) is not dict or type(block["fields"]) is not dict or type(block["topLevel"]) is not bool or block["topLevel"] == True:   
        return error("Wrong Blockdata")
    match block["opcode"]:
        case "operator_add":
            print("ADD BLOCK")
            part1 = {"type": "input", "value": "0", "calc": "0"}
            if "NUM1" in block["inputs"]:
                print("NUM1")
                part1 = calc_value(blocks, block["inputs"]["NUM1"])
                print(part1["values"])
                if not part1["success"]:
                    return part1
                part1 = part1["values"]
                if part1["calc"] is not None and not part1["calc"].replace(".", "").isdigit()or str(part1["calc"]).count(".") > 1:
                    part1["calc"] = "0"

            part2 = {"type": "input", "value": "0", "calc": "0"}
            if "NUM2" in block["inputs"]:
                part2 = calc_value(blocks, block["inputs"]["NUM2"])
                if not part2["success"]:
                    return part2
                part2 = part2["values"]
                if part2["calc"] is not None and not part2["calc"].replace(".", "").isdigit() or str(part2["calc"]).count(".") > 1:
                    part2["calc"] = "0"

            result = None
            if part1["calc"] is not None and part2["calc"] is not None:
                result = str(float(part1["calc"]) + float(part2["calc"]))
            return {"success": True, "values": {"type": "add", "1": part1, "2": part2, "calc": result}}
            












def control(blocks, block, data, sprite) -> dict:
    opcode = block["opcode"]
    result = []
    match opcode:
        case "control_wait":
            value = 0
            if "DURATION" in block["inputs"]:
                value = get_value(blocks, block["inputs"]["DURATION"], 3, "positiv")
                if not value["success"]:
                    return value
            else:
                value = {"success": True, "content": "0"}
            result.append(f'\t\t\t\tctx.loopCounters.push_back(osGetTime() + ({value["content"]} * 1000));\n\t\t\t\tctx.step++;\n\t\t\t\treturn {data["functionName"]};\n')
            result.append(f'\t\t\t\tif (osGetTime() < (u64)ctx.loopCounters[{data["loopCounter"]}]) \n\t\t\t\t{{\n\t\t\t\t\treturn 0;\n\n\t\t\t\t\t}}\n\t\t\t\tctx.loopCounters.pop_back();\n')
        
        case "control_repeat":
            value = 0
            if "TIMES" in block["inputs"]:
                value = get_value(blocks, block["inputs"]["TIMES"], 4, "positiv")
                if not value["success"]:
                    return value
            else:
                value = {"success": True, "content": "0"}
            data["loopCounter"] += 1
            if "SUBSTACK" in block["inputs"] and type(block["inputs"]["SUBSTACK"]) is list and len(block["inputs"]["SUBSTACK"]) > 1 and type(block["inputs"]["SUBSTACK"][1]) is str and block["inputs"]["SUBSTACK"][1] in blocks:
                newCode = convert_stack(block["inputs"]["SUBSTACK"][1], blocks, sprite, data)
                if not newCode["success"]:
                    return newCode
            else:
                newCode = {"success": True, "func": ""}
            result.append(f'\t\t\t\tctx.loopCounters.push_back({value["content"]});\n\t\t\t\tctx.step++;\n\t\t\t\treturn {data["functionName"]};\n')
            step = []
            count = 1
            for el in newCode["func"]:
                step.append(el)
                count += 1
            step.append(f'\t\t\t\tctx.loopCounters[{data["loopCounter"]}]--;\n\t\t\t\tctx.step -= {count};\n\t\t\t\treturn {data["functionName"]};\n')
            result.append(f'\t\t\t\tif (ctx.loopCounters[{data["loopCounter"]}] == 0)\n\t\t\t\t{{\n\t\t\t\t\tctx.loopCounters.pop_back();\n\t\t\t\t\tctx.step += {count + 1};\n\t\t\t\treturn 0;\n\n\t\t\t\t}}\n')
            result += step
    return {"success": True, "code": result}




def motion(blocks, block, data) -> dict:
    opcode = block["opcode"]
    result = []
    match opcode:

        case "motion_movesteps":
            value = 0
            if "STEPS" in block["inputs"]:
                value = get_value(blocks, block["inputs"]["STEPS"], 4)
                if not value["success"]:
                    return value
                result.append(f'\t\t\t\tx += {value["content"]};\n')
            else:
                result.append("\t\t\t\tx += 0;")

        case "motion_turnright":
            value = 0
            if "DEGREES" in block["inputs"]:
                value = get_value(blocks, block["inputs"]["DEGREES"], 4)
                if not value["success"]:
                    return value
                result.append(f'\t\t\t\tdirection += {value["content"]};\n')
            else:
                result.append("\t\t\t\tdirection += 0;")

        case "motion_turnleft":
            value = 0
            if "DEGREES" in block["inputs"]:
                value = get_value(blocks, block["inputs"]["DEGREES"], 4)
                if not value["success"]:
                    return value
                result.append(f'\t\t\t\tdirection -= {value["content"]};\n')
            else:
                result.append("\t\t\t\tdirection -= 0;")
        #EDIT
        case "motion_goto":
            value = 0
            if "TO" in block["inputs"]:
                value = get_value(blocks, block["inputs"]["TO"], 1)
                if not value["success"]:
                    return value
                result.append(f'\t\t\t\tdirection -= {value["content"]};\n')

        case "motion_gotoxy":
            value = 0
            step = ""
            if "X" in block["inputs"]:
                value = get_value(blocks, block["inputs"]["X"], 4)
                if not value["success"]:
                    return value
                step += f'\t\t\t\tx = {value["content"]};\n'
            else:
                step += "\t\t\t\tx = 0;"
            if "Y" in block["inputs"]:
                value = get_value(blocks, block["inputs"]["Y"], 4)
                if not value["success"]:
                    return value
                step += f'\t\t\t\ty = {value["content"]};\n'
            else:
                step += "\t\t\t\ty = 0;"
        #Edit
        case "motion_glideto":
            value = 0
            if "TO" in block["inputs"]:
                value = get_value(blocks, block["inputs"]["TO"], 1)
                if not value["success"]:
                    return value
                result.append(f'\t\t\t\tdirection -= {value["content"]};\n')

        case "motion_glidesecstoxy":
            value = 0
            Xvalue = 0
            Yvalue = 0
            step = ""
            if "X" in block["inputs"]:
                Xvalue = get_value(blocks, block["inputs"]["X"], 4)
                if not Xvalue["success"]:
                    return Xvalue
                Xvalue = Xvalue["content"]
            else:
                Xvalue = "0"
            
            if "Y" in block["inputs"]:
                Yvalue = get_value(blocks, block["inputs"]["Y"], 4)
                if not Yvalue["success"]:
                    return Yvalue
                Yvalue = Yvalue["content"]
            else:
                Yvalue = "0"
            
            if "SECS" in block["inputs"]:
                value = get_value(blocks, block["inputs"]["SECS"], 4, "positiv")
                if not value["success"]:
                    return 
                value = value["content"]
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
            step += f'\t\t\t\telse\n\t\t\t\t{{\n\t\t\t\t\tx = {Xvalue};\n\t\t\t\t\ty = {Yvalue};\n\t\t\t\t\tctx.loopCounters.pop_back();\n\t\t\t\t\tctx.loopCounters.pop_back();\n\t\t\t\t\tctx.loopCounters.pop_back();\n\t\t\t\t\tctx.loopCounters.pop_back();\n\t\t\t\t\tctx.loopCounters.pop_back();\n\t\t\t\t}}'
            result.append(step)

        case "motion_pointindirection":
            value = 0
            if "DIRECTION" in block["inputs"]:
                value = get_value(blocks, block["inputs"]["DIRECTION"], 4)
                if not value["success"]:
                    return value
                result.append(f'\t\t\t\tdirection = {value["content"]};\n')
            else:
                result.append("\t\t\t\tdirection = 0;")
        #edit
        case "motion_pointtowards":
            value = 0
            if "TOWARDS" in block["inputs"]:
                value = get_value(blocks, block["inputs"]["TOWARDS"], 1)
                if not value["success"]:
                    return value
                result.append(f'\t\t\t\tdirection = {value["content"]};\n')
            else:
                result.append("\t\t\t\tdirection = 0;")
        
        case "motion_changexby":
            value = 0
            if "DX" in block["inputs"]:
                value = get_value(blocks, block["inputs"]["DX"], 4)
                if not value["success"]:
                    return value
                result.append(f'\t\t\t\tx += {value["content"]};\n')
            else:
                result.append("\t\t\t\tx += 0;")
        
        case "motion_changeyby":
            value = 0
            if "DY" in block["inputs"]:
                value = get_value(blocks, block["inputs"]["DY"], 4)
                if not value["success"]:
                    return value
                result.append(f'\t\t\t\ty += {value["content"]};\n')
            else:
                result.append("\t\t\t\ty += 0;")
        
        case "motion_setx":
            value = 0
            if "X" in block["inputs"]:
                value = get_value(blocks, block["inputs"]["X"], 4)
                if not value["success"]:
                    return value
                result.append(f'\t\t\t\tx = {value["content"]};\n')
            else:
                result.append("\t\t\t\tx = 0;")
        
        case "motion_sety":
            value = 0
            if "Y" in block["inputs"]:
                value = get_value(blocks, block["inputs"]["Y"], 4)
                if not value["success"]:
                    return value
                result.append(f'\t\t\t\ty = {value["content"]};\n')
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
            result = motion(blocks, block, data)
            
    
    return result
    

def error(msg: str) -> dict:
    '''
    msg is the error message that gets returned:\n
    return {"success": False, "msg": msg}
    '''
    return {"success": False, "msg": msg}