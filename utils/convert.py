import os
import json
import zipfile
import unicodedata
import random
import string
from utils.generate_file import generate_cpp
from PIL import Image
SUCCESS = {"success": True}

import zipfile
from PIL import Image
import io

def convert_to_png(zip_file, path: str, dataFormat: str, sprite_name: str, image_name: str, output: str = "/example/path/") -> dict:
    full_path = path + "." + dataFormat
    try:
        if full_path not in zip_file.namelist():
            return error(f"Image not found in ZIP: {image_name} (filename: {full_path})")
            
        with zip_file.open(full_path) as file_in_zip:
            image_data = file_in_zip.read()
            image_stream = io.BytesIO(image_data)
                
            with Image.open(image_stream) as bild:
                bild = bild.convert("RGBA")
                os.makedirs(os.path.dirname(output), exist_ok=True)  # Verzeichnisse anlegen, falls nötig
                bild.save(output + image_name + ".png", format="PNG")
                return SUCCESS

    except Exception as e:
        return error(f"Error converting image: '{image_name}' from Sprite: '{sprite_name}' with error: {e}")


#sound not implemented yet
def load_sound(sprite: dict, temp: str, zip_file) -> dict:
    return SUCCESS


def load_costume(sprite: dict, temp: str, zip_file) -> dict:
    costumes = sprite["costumes"]
    for costume in costumes:
        if (type(costume) is not dict or "name" not in costume or "dataFormat" not in costume or "assetId" not in costume or
            type(costume["name"]) is not str or type(costume["dataFormat"]) is not str or type(costume["assetId"]) is not str):
            print(costume)
            return error(f"wrong or missing data in costume(s) of sprite: {sprite['name']}")
        if costume["dataFormat"] == "svg":
            return error(f"The costume '{costume['name']}' of the sprite '{sprite['name']}' is in SVG format. Please convert it to PNG using the editor. SVG files are not supported.")
        result = convert_to_png(zip_file, costume["assetId"], costume["dataFormat"], sprite["name"], costume["name"], temp + "gfx/")
        with open(temp + "gfx/" + costume["name"] + ".t3s", "w") as t3s:
            t3s.write(f"-f RGBA -z auto\n{costume['name']}.png")
        if not result["success"]:
            return result
        
    
    
    return {"success": True, "costume": costumes[sprite["currentCostume"]]["name"]}

def sanitize_string(input_str: str) -> str:
    special_map = {
        '☁': 'cloud',
        ' ': '_'
    }

    output = "var_"

    for char in input_str:
        if char in special_map:
            output += special_map[char]
        elif char.isalnum():
            output += char
        else:
            code = ord(char)
            output += f"_{code}_"  # Unicode-Codepoint als eindeutige ID

    return output


def sort(data: dict, sortname: str) -> list:
    return sorted(
            data.keys(),
            key=lambda k: data[k][sortname]
        )
        


def get_stage_and_sprites(data: list) -> dict:
    stage = {}
    sprites = {}
    for stage_or_sprite in data:
        if type(stage_or_sprite) is not dict:
            return error("Wrong format of object(s) in porject.json in the sb3 file")
        if "name" not in stage_or_sprite:
            return error("missing name in Object")
        if ("isStage" not in stage_or_sprite or "variables" not in stage_or_sprite or "lists" not in stage_or_sprite 
            or "broadcasts" not in stage_or_sprite or "blocks" not in stage_or_sprite or "currentCostume" not in stage_or_sprite or 
            "costumes" not in stage_or_sprite or "layerOrder" not in stage_or_sprite):
            return error(f"Missing data in Object: {str(stage_or_sprite['name'])} in porject.json in the sb3 file")
        if (type(stage_or_sprite["isStage"]) is not bool or type(stage_or_sprite["variables"]) is not dict or 
            type(stage_or_sprite["lists"]) is not dict or type(stage_or_sprite["broadcasts"]) is not dict or 
            type(stage_or_sprite["blocks"]) is not dict or type(stage_or_sprite["currentCostume"]) is not int or 
            type(stage_or_sprite["costumes"]) is not list or type(stage_or_sprite["layerOrder"]) is not int):
            return error(f"Wrong data in Object(s): {str(stage_or_sprite['name'])} in porject.json in the sb3 file")
        
        #is stage
        if stage_or_sprite["isStage"]:
            if stage == {}:
                stage = stage_or_sprite
            else:
                return error("The project contains two Stages")
        else:
            if stage_or_sprite["name"] in data:
                return error("There are sprites with the same name")
            sprites[stage_or_sprite["name"]] = stage_or_sprite
    return {"success": True, "stage": stage, "sprites": sprites}




def convert(data: zipfile.ZipFile, settings: dict) -> dict:
    "Do not call this function, use ScratchToNintendo3ds instead"
    
    #generate foldername
    base = "temp"
    i = 0
    while i < 20:
        foldername = "".join(random.choices(string.ascii_letters, k=12))
        temp = os.path.join(base, foldername)
        if not os.path.isdir(temp):
            os.makedirs(temp)
            i = 0
            break
        i += 1
    if i == 20:
        return error("File system or server overloaded")
    temp = temp + "/"
    #exist the project.json
    if "project.json" not in data.namelist():
        return error("Missing project.json in the sb3 file")
    
    #open project.json and load it as dict
    project = {}
    with data.open("project.json") as project_str:
        if not project_str:
            return error("project.json in the sb3 file is not a valid json")
        project = json.loads(project_str.read().decode('utf-8'))
        if not project:
            return error("project.json in the sb3 file can not converted to a dict")
        if "targets" not in project or type(project["targets"]) is not list:
            return error("project.json in the sb3 file does not contain the right 'targets'")
        project = project["targets"]

    #get all sprites and the stage
    result = get_stage_and_sprites(project)
    if not result["success"]:
        return result
    stage = result["stage"]
    sprites = result["sprites"]
    layers = sort(sprites, "layerOrder")

    #load all costumes and sounds
    result = load_costume(stage, temp, data)
    if not result["success"]:
        return result
    on_start_costumes = [result["costume"]]
    result = load_sound(stage, temp, data)
    if not result["success"]:
        return result
    for sprite_key in layers:
        sprite = sprites[sprite_key]
        result = load_costume(sprite, temp, data)
        if not result["success"]:
            return result
        on_start_costumes.append(result["costume"])
        result = load_sound(sprite, temp, data)
        if not result["success"]:
            return result
    
    result = generate_cpp(temp, stage, sprites, layers, settings, on_start_costumes)
    if not result["success"]:
            return result

    return SUCCESS

def ScratchToNintendo3ds(settings: dict) -> dict:
    "To Convert the Scratch game into a fully working C++ script for the 3ds"
    path = settings["game"]
    if not os.path.isfile(path):
        return error("sb3 file does not exist")
    with open(path, "r") as data:
        if not data:
            return error("Error by open sb3 file")
        with zipfile.ZipFile(path, "r") as zip_file:
            if not zip_file:
                return error("cant open sb3 as zip archive")
            return convert(zip_file, settings)
            


    return SUCCESS

def error(msg: str) -> dict:
    '''
    msg is the error message that gets returned:\n
    return {"success": False, "msg": msg}
    '''
    return {"success": False, "msg": msg}


if __name__ == "__main__":
    settings = {
                "game": "GOAL.sb3",
                "screen": 1,
                "name": "GAME",
                "description": "description",
                "author": "author",
                "icon": True
                }
    result = ScratchToNintendo3ds(settings)
    if result["success"]:
        print("Success")
    else:
        print(result["msg"])