from rich import print
from dropbox.exceptions import ApiError
import os
import warnings
import dropbox
import posixpath

try:
    from secrets import DROPBOX_KEY
    localsecret = True
except ImportError:
    warnings.warn('local_settings failed to import', ImportWarning)
    localsecret = False
    DROPBOX_KEY = os.environ.get('DROPBOX_KEY')

def process_folder_entries(current_state, entries):
    for entry in entries:
        if isinstance(entry, dropbox.files.FileMetadata):
            current_state[entry.path_lower] = entry
        elif isinstance(entry, dropbox.files.DeletedMetadata):
            current_state.pop(entry.path_lower, None) # ignore KeyError if missing
    return current_state

def path_exists(path):
    try:
        dbx.files_get_metadata(path)
        return True
    except ApiError as e:
        if e.error.get_path().is_not_found():
            return False
        raise

print("Initializing [bold]Dropbox API...[/bold]")
dbx = dropbox.Dropbox(DROPBOX_KEY)

print("Scanning for expense files...")
result = dbx.files_list_folder(path="/escuela/",recursive=True)
files = process_folder_entries({}, result.entries)

# check for and collect any additional entries
while result.has_more:
    print("Collecting additional files...")
    result = dbx.files_list_folder_continue(result.cursor)
    files = process_folder_entries(files, result.entries)

counter=0
for entry in files.values():
    counter = counter+1
    # use modified time of file to build destination path
    destination_path = posixpath.join(
        "/FOTOS/Años/" + str(entry.client_modified.year) ,
        str(entry.client_modified.strftime("%Y%m")) 
        #    str(entry.client_modified.month)
    )

    # check to see if we need to create the destination folder
    if not path_exists(destination_path):
        print("Creating folder: {}".format(destination_path))
        dbx.files_create_folder(destination_path)

    print(str(counter) + "/" + str(len(files.values())) + "- Moving {} to {}".format(entry.path_display, destination_path))
    dbx.files_move_v2(entry.path_lower, destination_path + "/" + entry.name,autorename=True)
print("Complete!")
