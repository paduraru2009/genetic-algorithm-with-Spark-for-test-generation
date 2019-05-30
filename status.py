import os
import sys
import time

def clear():
    os.system('clear')

def print_info(logs_folder):
    full_path = os.path.abspath(logs_folder)
    print("Folder:", full_path)

    stats = {}
    for r, d, _ in os.walk(full_path):
        for folder in d:
            if 'generation' in folder:
                for _, _, files in os.walk(os.path.join(full_path, folder)):
                    stats[folder] = len(files)
            elif 'crash' in folder:
                stats[folder] = {}
                for _, crash_type_folders, _ in os.walk(os.path.join(full_path, folder)):
                    for crash_folder in crash_type_folders:
                        for _, _, files in os.walk(os.path.join(full_path, folder, crash_folder)):
                            stats[folder][crash_folder] = len(files)

    generations = { key : value for key, value in stats.items() if 'generation' in key}

    print('Current generations:')
    for generation in sorted(generations.keys()):
        print('\t', generation, 'contains', generations[generation], 'individuals')

    if 'crash' in stats:
        crashes = stats['crash']
        print('Crashes')
        for crash_type, count in crashes.items():
            print('\t', crash_type, ':', count)

def main(logs_folder, refresh_rate):
    clear()

    while True:
        print_info(logs_folder)
        time.sleep(1)

        clear()
   

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print('Usage: python ', sys.argv[0], 'logs_folder_path', 'refresh_rate')
        exit(-1)

    logs_folder = sys.argv[1]
    refresh_rate = int(sys.argv[2])
     
    main(logs_folder, refresh_rate)
