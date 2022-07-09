import os
import subprocess


def get_new_files():
    for root, dirs, files in os.walk(".", topdown=False):
        for file in files:
            if 's__' in file and '.mp3' in file:
                yield file


def split_large_file(filepath):
    file_size = os.path.getsize(filepath)
    if file_size >= 50000000:    
        subprocess.call(['mp3splt', filepath, '-t', '30.0.0'])
        return True
    return False


if __name__ == "__main__":
    print([file for file in get_new_files()])
