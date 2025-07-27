#from utils.convert import error
import os
from utils.blocksToCpp import generate_script
SUCCESS = {"success": True}

def generate_main(layers:list, costumes: list, screen_mode: int) -> str:
    main = '//main script\nint main(int argc, char *argv[]) {\n\n\tinitGraphics();\n\tint close = 0;\n\n\t//define Screens\n'
    if screen_mode == 1:
        main += "\tC3D_RenderTarget* topScreen = C2D_CreateScreenTarget(GFX_TOP, GFX_LEFT);\n"
    elif screen_mode == 2:
        main += "\tC3D_RenderTarget* bottomScreen = C2D_CreateScreenTarget(GFX_BOTTOM, GFX_LEFT);\n"
    else:
        main += "\tC3D_RenderTarget* topScreen = C2D_CreateScreenTarget(GFX_TOP, GFX_LEFT);\n\tC3D_RenderTarget* bottomScreen = C2D_CreateScreenTarget(GFX_BOTTOM, GFX_LEFT);\n"
    main += "\tImageCache cache;\n\tLayerManager layers;\n"
    for costume in costumes:
        main += f'\tcache.loadImage("{costume}");\n'
    main += "\n"
    for layer in layers:
        main += f"\tCLASS_{layer} {layer};\n"
        main += f'\tlayers.addSprite(&{layer});\n'
    
    main += "\n"
    main += '''
    // create Events
    Events events;
    // start Flag
    events.flagClicked = true;
    // Main Loop
	while (aptMainLoop())
	{
		hidScanInput();
		u32 kDown = hidKeysDown();
		if (kDown & KEY_START) break;

        //start buffer
		C3D_FrameBegin(C3D_FRAME_SYNCDRAW);
		C2D_TargetClear(topScreen, C2D_Color32(0, 0, 0, 255));
        
        //add Sprites to buffer\n
'''
    if screen_mode == 1:
        main += "\t\tC2D_TargetClear(topScreen, C2D_Color32(0, 0, 0, 255));\n\t\tC2D_SceneBegin(topScreen);\n\t\tclose = tick(layers, cache, events, 0);\n"
    elif screen_mode == 2:
        main += "\t\tC2D_TargetClear(bottomScreen, C2D_Color32(0, 0, 0, 255));\n\t\tC2D_SceneBegin(bottomScreen);\n\t\tclose = tick(layers, cache, events, 1);\n"
    elif screen_mode == 3:
        main += "\t\tC2D_TargetClear(topScreen, C2D_Color32(0, 0, 0, 255));\n\t\tC2D_SceneBegin(topScreen);\n\t\tclose = tick(layers, cache, events, 2);\n\t\tC2D_TargetClear(bottomScreen, C2D_Color32(0, 0, 0, 255));\n\t\tC2D_SceneBegin(bottomScreen);\n\t\tdrawing(layers, cache, events, 3);\n"
    main += '''
        ///deactivate flag
        events.flagClicked = false;

        //App was closed in Scratch via the "Stop All" block or due to an error
        if (close > 0)
        {
            break;
        };


        //draw buffer on screem
		C3D_FrameEnd(0);
	}

	// Clean up
	C2D_Fini();
	C3D_Fini();
	gfxExit();
	romfsExit();
	return 0;
}
'''
    return main
    

def file_snippets(snip: str) -> str:
    '''
    -include\n
    -sprite\n
    -layer\n
    -image\n
    -tick\n
    -graphics\n
    -events\n
    -steps
    '''
    match snip:
        case "include":
            return '''
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <3ds.h>
#include <citro2d.h>
#include <vector>
#include <string>
#include <utility>
#include <algorithm>
#include <list>
#include <cmath>\n\n
'''
        case "sprite":
            return '''
//sprite class with all important functions
class Sprite {
    public:
        //Sprite
        std::string name = "Empty";

        //settings
        int x = 0, y = 0;
        int direction = 90;
        int size = 100;
        bool visible = true;
        int volume = 100;
        
        //every sprite gets an id
        int id = 0;

        //clones
        bool isClone = false;

        //creating
        Sprite() = default;
        Sprite(std::string n) : name(std::move(n)) {}

        //Costumes
        std::vector<std::string> costumes; //list of all costumes that one Sprite has
        int currentCostumeIndex = 0; //the current costume that is used by the Sprite

        //Scripts
        virtual int run(LayerManager &manager, Events &events) {return 0;};

        virtual ~Sprite() = default;

        void draw(ImageCache& cache, int screen) {
            //is not visible or has no
            if (!visible || costumes.empty()) {
                return;
            }
            //topscreen single
            int y_offset = 120;
            int x_offset = 200;
            if (screen == 1)
            {
                //bottomscreen single
                x_offset = 160;
            }else if (screen == 2)
            {
                //topscreen using both
                y_offset = 240;
            }else if (screen == 3)
            {
                //bottomscreen using both
                y_offset = 0;
                x_offset = 160;
            }

            C2D_Image image = cache.getImage(costumes[currentCostumeIndex]);
            if (image.subtex) C2D_DrawImageAtRotated(image, x + x_offset, y_offset - y, 0, direction - 90, nullptr, float(size/200.0), float(size/200.0));
        }
};\n\n
'''
        case "graphics":
            return '''
void initGraphics() {
    romfsInit();
    gfxInitDefault();

    //consoleInit(GFX_BOTTOM, NULL); //debugg zweck

    C3D_Init(C3D_DEFAULT_CMDBUF_SIZE);
    C2D_Init(C2D_DEFAULT_MAX_OBJECTS);
    C2D_Prepare();
}\n\n
'''
        case "tick":
            return '''
int tick(LayerManager &manager, ImageCache cache, Events &events, int screen)
{
    auto spritesCopy = manager.getAllSprites();
    for (auto sprite : spritesCopy)
    {
    int result = sprite->run(manager, events);
    if (result == 1)
    {
        return 1;
    };
    sprite->draw(cache, screen);
    }
    return 0;
}

void drawing(LayerManager &manager, ImageCache cache, Events &events, int screen)
{
    auto spritesCopy = manager.getAllSprites();
    for (auto sprite : spritesCopy)
    {
    sprite->draw(cache, screen);
    }
    return;
}\n\n
'''
        case "layer": 
            return '''
class LayerManager
{
private:
    std::vector<Sprite *> layers;

public:
    const std::vector<Sprite *>& getAllSprites()
    {
        return layers;
    }

    void addSprite(Sprite *sprite)
    {
        if (std::find(layers.begin(), layers.end(), sprite) == layers.end())
        {
            layers.push_back(sprite);
        }
    }

    void removeSprite(Sprite *sprite)
    {
        auto it = std::find(layers.begin(), layers.end(), sprite);
        if (it != layers.end())
        {
            layers.erase(it);
        }
    }

    int getLayer(Sprite *sprite)
    {
        for (size_t i = 0; i < layers.size(); ++i)
        {
            if (layers[i] == sprite)
                return static_cast<int>(i);
        }
        return -1;
    }

    bool moveUp(Sprite *sprite)
    {
        int index = getLayer(sprite);
        if (index < 0 || index >= static_cast<int>(layers.size()) - 1)
            return false;

        std::swap(layers[index], layers[index + 1]);
        return true;
    }

    bool moveDown(Sprite *sprite)
    {
        int index = getLayer(sprite);
        if (index <= 0)
            return false;
        std::swap(layers[index], layers[index - 1]);
        return true;
    }
};\n\n
'''
        case "image": 
            return '''//costum struct to save and unload the images
struct CostumeCacheEntry
{
    std::string name;
    C2D_SpriteSheet sheet;
    C2D_Image image;
};

//to hold just the right amount of images
class ImageCache {
public:

    // load new image if needed
    int loadImage(std::string name) {
        // already loaded?
        auto it = std::find_if(cache.begin(), cache.end(), [&](const CostumeCacheEntry& e){ return e.name == name; });
        if (it != cache.end()) {
            // Move entry to the back (LRU logic)
            cache.splice(cache.end(), cache, it);
            return 1; // already in cache
        }
        

        // too many sprites? max 2 here, adjust as needed
        if (cache.size() > 20) {
            removedImages.push_back(cache.front().name);
            C2D_SpriteSheetFree(cache.front().sheet);
            cache.pop_front();         // efficiently remove the oldest entry
        }

        // create path and load image
        std::string path = "romfs:/gfx/" + name + ".t3x";
        C2D_SpriteSheet sheet = C2D_SpriteSheetLoad(path.c_str());
        if (!sheet) return -1;// error loading image

        C2D_Image image = C2D_SpriteSheetGetImage(sheet, 0);

        // save data
        CostumeCacheEntry entry;
        entry.name = name;
        entry.image = image;

        auto ait = std::find(removedImages.begin(), removedImages.end(), name);
        if (ait != removedImages.end()) {
            removedImages.erase(ait);
        }

        cache.push_back(entry);
        return 0;// successfully loaded
    };

    // return the image by name, or empty if not found
    const C2D_Image getImage(const std::string& name) {
        for (const auto& entry : cache) {
            if (entry.name == name) {
                return entry.image;
            }
        }
        return {0};// empty image if not found
    }

    // remove an image from the cache by name
    int removeImage(const std::string& name) {
        auto it = std::find_if(cache.begin(), cache.end(), [&](const CostumeCacheEntry& e){ return e.name == name; });
        if (it != cache.end()) {
            removedImages.push_back(it->name);
            C2D_SpriteSheetFree(it->sheet);
            cache.erase(it);
            //now storoage is free than the image can load that is used the most but not that much to be loaded currently
            if (!removedImages.empty()){
                std::string newName = removedImages.front();
                // create path and load image
                std::string path = "romfs:/gfx/" + newName + ".t3x";
                C2D_SpriteSheet sheet = C2D_SpriteSheetLoad(path.c_str());
                if (!sheet) return -1;// error loading image
                // save data
                C2D_Image image = C2D_SpriteSheetGetImage(sheet, 0);
                CostumeCacheEntry entry;
                entry.name = newName;
                entry.image = image;
                cache.insert(cache.begin(), entry);
                //delete image in removedImages
                removedImages.erase(removedImages.begin());
            }
            return 1;// success
        }
        return 0;// not found
    }

    // clear the entire cache and image list
    void clean() {
        for (auto i = cache.begin(); i != cache.end(); ++i) C2D_SpriteSheetFree(i->sheet);
        cache.clear();
        removedImages.clear();
    }

private:
    std::list<CostumeCacheEntry> cache;    // efficient erase and move operations
    std::vector<std::string> removedImages;    // store all image names in order
};\n\n
'''
        case "events":
            return '''
struct Broadcast {
    std::string message;
    int received = 0;
    int over = 0;
};

class Events {
private:
    std::list<Broadcast> broadcasts;

public:
    std::vector<Sprite*> Clones = {};
    bool flagClicked = false;
    int touchX = 0;
    int touchY = 0;
    bool pressed = false;
    bool hit = false;
    std::string BackdropSwitchedTo = "";

    bool sendBroadcast(const std::string& message) {
        Broadcast newMessage;
        newMessage.message = message;
        broadcasts.push_back(newMessage);
        return true;
    }

    const std::list<Broadcast>& getBroadcasts() const {
        return broadcasts;
    }

    bool deleteBroadcast(const std::string& message) {
        auto it = std::remove_if(broadcasts.begin(), broadcasts.end(),
            [&](const Broadcast& b) {
                return b.message == message;
            });

        if (it != broadcasts.end()) {
            broadcasts.erase(it, broadcasts.end());
            return true;
        }

        return false; // kein Broadcast mit dieser Nachricht gefunden
    }
};\n\n'''
        case "steps":
            return '''
struct ExecutionContext {
    int step = 0;
    std::vector<s64> loopCounters;
    bool finished = false;
};\n\n
'''
    return ""
 
def generate_sprite_class(sprite, name, completename, x, y, direction, size, visible, volume):
    '''{"success": True, "script": pack}'''
    attributes = f'\t\t\tname = "{completename}";\n'
    if x != 0:
        attributes += f'\t\t\tx = {int(x)};\n'
    if y != 0:
        attributes += f'\t\t\ty = {int(y)};\n'
    if direction != 90:
        attributes += f'\t\t\tdirection = {int(direction)};\n'
    if size != 100:
        attributes += f'\t\t\tsize = {int(size)};\n'
    if not visible:
        attributes += f'\t\t\tvisible = {int(visible)};\n'
    if volume != 100:
        attributes += f'\t\t\tvolume = {int(volume)};\n'

    result = generate_script(sprite)
    if not result["success"]:
        return result

    #script overide
    pack = f'class CLASS_{name} : public Sprite\n{{\n\tpublic:\n'
    #data overide
    pack += f'\t\tCLASS_{name}()\n\t\t{{\n'
    pack += "\t\t\tcostumes = {"
    for costume in sprite["costumes"]:
        pack += f'"{costume["name"]}", '
    pack = pack[:-2]
    pack += "};\n"
    for attrbute in attributes:
        pack += attrbute
    pack += "\t\t};"
    pack += result["public"]
    #is there any relevant code
    if result["private"] != "":
        pack += "private:\n"
        pack += result["private"]
    pack += "};\n"
    return {"success": True, "script": pack}

def generate_cpp(temp: str, stage: dict, sprites: dict, layers: list, settings: dict, costumes: list) -> dict:
    
    includes = file_snippets("include")
    ExecutionContent = file_snippets("steps")
    cache = file_snippets("image")
    mainSprite = file_snippets("sprite")
    graphics = file_snippets("graphics")
    events = file_snippets("events")
    tick = file_snippets("tick")
    layerManager = file_snippets("layer")
    mainFunction = generate_main(layers, costumes, settings["screen"])


    #generate every sprite
    script = ""
    for layer in layers:
        
        sprite = sprites[layer]
        result = generate_sprite_class(sprite, layer, sprite["name"], sprite["x"], sprite["y"], sprite["direction"], sprite["size"], sprite["visible"], sprite["volume"])
        if not result["success"]:
            return result
        script += result["script"] + "\n\n"
    cppFile = includes + "\nclass LayerManager;\nclass Sprite;\n" + cache + ExecutionContent + events + mainSprite + script + layerManager + tick + graphics + mainFunction
    os.makedirs(temp + "source", exist_ok=True)
    with open(temp + "source/main.cpp", "w") as openFile:
        openFile.write(cppFile)




    return SUCCESS

if __name__ == "__main__":
    generate_cpp("temp/test/", {}, {}, [])