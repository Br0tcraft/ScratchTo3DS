import os
import re
from utils.convert import ScratchToNintendo3ds as convert

def print_header():
    print("="*50)
    print("Scratch to 3DS Project Generator")
    print("="*50)
    print("\nNOTE: This tool does NOT generate a complete `.3dsx` file.\n"
          "Instead, it creates a DevkitPro-compatible C++ project, which\n"
          "you can manually compile into a 3DS executable using DevkitPro.\n"
          "See official documentation here: [WEBSITE LINK]\n")

def find_sb3_files():
    print("Scanning for `.sb3` project files in the current directory...\n")
    files = [f for f in os.listdir('.') if f.endswith('.sb3')]
    if not files:
        print("No Scratch (.sb3) projects found.\n")
    else:
        print("Found the following projects:")
        for f in files:
            print(f"- {f}")
    return files

def choose_file(files):
    if not files:
        return None
    print("\nPlease enter the number of the project you'd like to convert:")
    for i, file in enumerate(files):
        print(f"  [{i + 1}] {file}")
    while True:
        choice = input("Your choice: ").strip()
        if choice.isdigit() and 1 <= int(choice) <= len(files):
            return files[int(choice) - 1]
        else:
            print("Invalid selection. Please enter a valid number.")

def choose_screen_mode():
    print("\nSelect screen layout for rendering:")
    print("[1] Top Screen (400x240)")
    print("[2] Bottom Screen (320x240)")
    print("[3] Dual Screen (400x480 - mapped split)")
    while True:
        choice = input("Your choice: ").strip()
        if choice in {'1', '2', '3'}:
            return int(choice)
        print("Please select a valid option.")

def get_game_name():
    print("\nEnter the name of your game (letters only, case-sensitive):")
    while True:
        name = input("Game name: ").strip()
        if re.fullmatch(r"[A-Za-z]+", name):
            return name
        print("Invalid name. Only letters A-Z and a-z are allowed.")

def get_game_description():
    print("\nEnter a short description of your game (optional):")
    return input("Description: ").strip()

def get_author():
    author = input("\nEnter author name (default: Scratch2Nintendo3DS): ").strip()
    return author if author else "Scratch2Nintendo3DS"

def check_for_icon():
    exists = os.path.isfile("icon.png")
    if exists:
        print("✔ 'icon.png' found in current directory.")
    else:
        print("⚠ No 'icon.png' found. Default icon will be used.")
    return exists

def secure_mode():
    print("\nEnable secure mode? (Recommended for projects using fallbacks or dynamic variable types)")
    print("Secure mode adds runtime type checking but may impact performance.")
    print("[1] Yes")
    print("[2] No")
    while True:
        choice = input("Your choice: ").strip()
        if choice in {'1', '2'}:
            return choice == '1'
        print("Please select a valid option.")
    return 1
def confirm_start():
    response = input("\nReady to generate the DevkitPro project? (y/n): ").strip().lower()
    return response == 'y'

def main():
    print_header()
    sb3_files = find_sb3_files()
    if not sb3_files:
        print("ERROR by reading folder")
        return

    selected_file = choose_file(sb3_files)
    if not selected_file:
        print("No file selected. Exiting.")
        return

    screen_mode = choose_screen_mode()
    game_name = get_game_name()
    description = get_game_description()
    author = get_author()
    icon_exists = check_for_icon()
    secure = secure_mode()
    settings =  {
                "game": selected_file,
                "screen": screen_mode,
                "name": game_name,
                "description": description,
                "author": author,
                "icon": icon_exists,
                "SECURE": True if secure == 1 else False
                }


    if confirm_start():
        print("\nGenerating project files...")
        result = convert(settings)
        if result["success"]:
            print("✔ Done. Project generated.")
        else:
            print("Error:\n" + result["msg"])
    else:
        print("Operation cancelled by user.")

if __name__ == "__main__":
    main()
