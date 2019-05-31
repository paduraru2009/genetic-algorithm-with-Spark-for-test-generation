import os
import sys
import struct

def tab_indent(times):
    tabs = ''
    for _ in range(times):
        tabs += '\t'
    return tabs

def print_files(root, folder, files, indent, files_cutoff=10, text_cutoff=50, binary_cutoff=20,visited=set()):
    files = files[:files_cutoff]
    for f in files:
        if f in visited:
            continue

        visited.add(f)

        print(tab_indent(indent), '\tPrinting file:', f[:text_cutoff], end=":\t")
        with open(os.path.join(root, folder) + '/' + f, 'rb') as bf:
            binary_data = bf.read()
            binary_data = binary_data[:binary_cutoff]
            print(binary_data)

def recurse(folder, indent, visited=set()):
    print(tab_indent(indent) + 'Folder:', os.path.basename(folder))
    for root, directories, files in os.walk(folder):
        print_files(root, folder, files, indent)
        for directory in sorted(directories):
            if directory in visited:
                continue

            visited.add(directory)
            recurse(os.path.join(root, directory), indent + 1)

def main(logs_folder):
    recurse(logs_folder, 0)

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('Usage: python ', sys.argv[0], 'logs_folder_path')
        exit(-1)

    logs_folder = sys.argv[1]
     
    main(logs_folder)
