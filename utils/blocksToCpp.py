
from utils.blocks.convert import generate_function

def declaration():
    return '''

'''


def create_thread_calls(hats: dict, blocks: dict, nameForError: str) -> str:
    script = "\t\tint errormsg = 0;\n"
    #if flag clicked run this code
    if "event_whenflagclicked" in hats:
        script += "\t\tif (events.flagClicked)\n\t\t{\n"
        i = 1
        for block in hats["event_whenflagclicked"]:
            script += f'\t\t\tstep_{blocks[block]["opcode"]}_{str(i)}.step = 0;\n'
            i += 1
        script += "\t\t};\n"
        #call threads  of event_whenflagclicked
        i = 1
        for block in hats["event_whenflagclicked"]:
            script += f'\t\tif (step_{blocks[block]["opcode"]}_{str(i)}.step >= 0) errormsg += thread_{blocks[block]["opcode"]}_{str(i)}(step_{blocks[block]["opcode"]}_{str(i)});\n'
        i += 1
        
    
    if "event_whenthisspriteclicked" in hats:
        #if sprite is touch reset every SpriteClickedBlock
        script += "\t\tif (events.hit)\n\t\t\t{\n"
        script += "\t\t\tint ax = parent->x - (parent->xSize() / 2.0);\n"
        script += "\t\t\tint bx = parent->x + (parent->xSize() / 2.0);\n"
        script += "\t\t\tint ay = parent->y - (parent->Size() / 2.0);\n"
        script += "\t\t\tint by = parent->y + (parent->ySize() / 2.0);\n"
        script += "\t\t\tif (events.touchX > ax && events.touchX < bx && events.touchY > ay && events.touchY < by)\n\t\t\t{\n"
        i = 1
        for block in hats["event_whenthisspriteclicked"]:
            script += f'\t\t\t\tstep_{blocks[block]["opcode"]}_{str(i)}.step = 0;\n'
        i += 1
        script += "\t\t\t};\n"
        script += "\t\t};\n"
        #call threads  of event_whenthisspriteclicked
        i = 1
        for block in hats["event_whenthisspriteclicked"]:
            script += f'\t\t\tif (step_{blocks[block]["opcode"]}_{str(i)}.step >= 0) errormsg += thread_{blocks[block]["opcode"]}_{str(i)}(step_{blocks[block]["opcode"]}_{str(i)});\n'
        i += 1
        script += "\n\n"
        
    
    if "control_start_as_clone" in hats:
        script += f"\t\tif (parent->isClone)\n\t\t{{\n"
        #call threads  of control_start_as_clone
        i = 1
        for block in hats["control_start_as_clone"]:
            script += f'\t\t\tif (step_{blocks[block]["opcode"]}_{str(i)}.step >= 0) errormsg += thread_{blocks[block]["opcode"]}_{str(i)}(step_{blocks[block]["opcode"]}_{str(i)});\n'
        i += 1
        script += "\t\t};\n\n"
    
    if "event_whenbroadcastreceived" in hats:
        #call threads  of control_start_as_clone
        i = 1
        for block in hats["event_whenbroadcastreceived"]:
            broadcast = blocks[block]
            #check if broadcastblock is correct
            if "fields" not in broadcast or type(broadcast["fields"]) is not dict:
                return error("Missing data in Broadcastblock in Sprite: " + nameForError)
            broadcast = broadcast["fields"]
            if "BROADCAST_OPTION" not in broadcast or type(broadcast["BROADCAST_OPTION"] ) is not list or not len(broadcast["BROADCAST_OPTION"]) > 0:
                return error("Missing data in Broadcastblock in Sprite: " + nameForError)
            broadcast = broadcast["BROADCAST_OPTION"][0]
            if type(broadcast) is not str:
                return error("Wrong data type in Broadcast in Sprite: " + nameForError)
            #add code
            script += f"\t\t//check if broadcast: '{broadcast}' was send or block is currently active\n"
            script += f'\t\tif (std::find(events.getBroadcasts().begin(), events.getBroadcasts().end(), "{broadcast}")!=events.getBroadcasts().end() or step_{blocks[block]["opcode"]}_{str(i)}.step > 0) errormsg += thread_{blocks[block]["opcode"]}_{str(i)}(step_{blocks[block]["opcode"]}_{str(i)});\n'
        i += 1
    
    script += "\t\treturn errormsg;\n"
    return script

def get_hats(blocks: dict, name:str) -> dict:
    hats = {}

    for key, block in blocks.items():
        #are block right
        if "parent" not in block or "next" not in block or "opcode" not in block or "topLevel" not in block:
            
            return error("Error in the Blocks of Sprite: " + name)
        if not(isinstance(block["next"], str) or block["next"] is None) or not(isinstance(block["parent"], str) or block["parent"] is None) or not isinstance(block["opcode"], str) or not isinstance(block["topLevel"], bool):
            return error("Error in the Blocks of Sprite: " + name)
        
        if not block["topLevel"]:
            continue
        if not block["opcode"] in hats.items():
            hats[block["opcode"]] = []
        hats[block["opcode"]].append(key)
    return {"success": True, "hats": hats}


def generate_script(sprite) -> dict:
    '''{"success": True, "public": public, "private": private}'''
    private = ""
    public = "\n\t\tSprite *parent;\n"
    if "blocks" not in sprite or type(sprite["blocks"]) is not dict:
        return error("Missing code in sprite: " + sprite["name"])
    blocks = sprite["blocks"]

    #get hats
    result = get_hats(blocks, sprite["name"])
    if not result["success"]:
        return result
    hats = result["hats"]

    result = generate_function(hats, blocks, sprite)
    if not result["success"]:
        return result
    public += result["def"]
    private += result["func"]
    
    public += "\n\tint run(LayerManager &manager, Events &events) override\n\t{\n"
    public += create_thread_calls(hats, blocks, sprite["name"])
    public += "\t}\n\n"

    return {"success": True, "public": public, "private": private}


def error(msg: str) -> dict:
    '''
    msg is the error message that gets returned:\n
    return {"success": False, "msg": msg}
    '''
    return {"success": False, "msg": msg}
