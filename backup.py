import zipfile
import os
import datetime

def create_backup_folder(backup_folder_path):
    """
    Create a backup folder if it doesn't exist.
    """
    if not os.path.exists(backup_folder_path):
        os.makedirs(backup_folder_path)
        print(f"Backup folder created at: {backup_folder_path}")
    
    logs_folder_path = os.path.join(backup_folder_path, "logs")
    if not os.path.exists(logs_folder_path):
        os.makedirs(logs_folder_path)
        print(f"Logs folder created at: {logs_folder_path}")
    else:
        print(f"Logs folder already exists at: {logs_folder_path}")
    
    return logs_folder_path  # Return logs folder path for later use

def backup_server_files(server_folder_path, backup_folder_path, log_file_path):
    """
    Backup server files to the backup folder, excluding mc_server.py.
    """
    backup_datetime = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

    try:
        # Create a zip file of the server folder
        zip_file_path = os.path.join(backup_folder_path, f"server_backup_{backup_datetime}.zip")
        with zipfile.ZipFile(zip_file_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(server_folder_path):
                for file in files:
                    # Skip mc_server.py
                    if file == "mc_server.py":
                        continue
                    
                    file_path = os.path.join(root, file)
                    zipf.write(file_path, os.path.relpath(file_path, server_folder_path))
        print(f"Backup created at: {zip_file_path}")
        write_to_log(f"Backup created at: {zip_file_path}", log_file_path)
    except Exception as e:
        print(f"Error creating backup: {e}")
        write_to_log(f"Error creating backup: {e}", log_file_path)

def delete_old_backups(backup_folder_path, days, log_file_path):
    """
    Delete backups older than the specified number of days.
    """
    now = datetime.datetime.now()
    try:
        for filename in os.listdir(backup_folder_path):
            file_path = os.path.join(backup_folder_path, filename)
            
            if os.path.isfile(file_path) and filename.endswith(".zip"):  # Only delete .zip files
                file_creation_time = datetime.datetime.fromtimestamp(os.path.getctime(file_path))
                if (now - file_creation_time).days > days:
                    os.remove(file_path)
                    print(f"Deleted old backup: {file_path}")
                    write_to_log(f"Deleted old backup: {file_path}", log_file_path)
            else:
                print(f"Skipping non-file or non-zip: {file_path}")
    except Exception as e:
        print(f"Error deleting old backups: {e}")
        write_to_log(f"Error deleting old backups: {e}", log_file_path)

def write_to_log(message, log_file_path):
    """
    Write a message to the log file.
    """
    try:
        # Ensure the log directory exists
        log_dir = os.path.dirname(log_file_path)
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        with open(log_file_path, 'a') as log_file:
            log_file.write(f"{datetime.datetime.now()}: {message}\n")
        print(f"Log written: {message}")
    except Exception as e:
        print(f"Error writing to log: {e}")

if __name__ == '__main__':
    server_folder_path = r"C:\Users\PC\Desktop\GHAST"  # Use the absolute path to the "GHAST" directory
    backup_folder_path = r"C:\Users\PC\Desktop\MinecraftServerBackups"  # Use an absolute path here
    log_file_path = os.path.join(create_backup_folder(backup_folder_path), "backup_log.txt")  # Get logs folder path
    
    backup_server_files(server_folder_path, backup_folder_path, log_file_path)
    delete_old_backups(backup_folder_path, days=7, log_file_path=log_file_path)
