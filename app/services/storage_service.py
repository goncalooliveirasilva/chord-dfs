'''storage service'''
import os

STORAGE_FOLDER = "/app/storage"

os.makedirs(STORAGE_FOLDER, exist_ok=True)

def save_file(file, filename: str) -> str:
    '''Save a file to storage.'''
    file_path = os.path.join(STORAGE_FOLDER, filename)
    file.save(file_path)
    return file_path


def get_file_path(filename: str) -> str:
    '''Return the path to a file, or None if it doesn't exist.'''
    file_path = os.path.join(STORAGE_FOLDER, filename)
    if os.path.exists(file_path):
        return file_path
    return None


def delete_file(filename: str) -> bool:
    '''Delete a specific file. Returns True if deleted, False if not found.'''
    file_path = os.path.join(STORAGE_FOLDER, filename)
    if os.path.exists(file_path):
        os.remove(file_path)
        return True
    return False


def list_files() -> list[str]:
    '''List all files in storage.'''
    return os.listdir(STORAGE_FOLDER)


def delete_all_files() -> None:
    '''Delete all files in storage.'''
    for filename in list_files():
        delete_file(filename)
