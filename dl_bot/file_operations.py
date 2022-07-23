import os
import subprocess


async def sanitise_filename(filename):
    return filename.replace("/", "-")


def get_new_files(reverse_order=True):
    search_dir = "./"
    files = filter(os.path.isfile, os.listdir(search_dir))
    files = [os.path.join(search_dir, f) for f in files]  # add path to each file
    files.sort(key=lambda x: os.path.getmtime(x), reverse=reverse_order)
    for file in files:
        if "s__" in file and ".mp3" in file:
            yield file


def split_large_file(filepath):
    file_size = os.path.getsize(filepath)
    if file_size >= 50000000:
        subprocess.call(["mp3splt", filepath, "-t", "30.0.0"])
        return True
    return False


if __name__ == "__main__":
    print([file for file in get_new_files()])
