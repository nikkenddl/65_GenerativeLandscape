import os
from time import time


def create_incremented_file(path, threshold, default_filename="autocreated_log_000.txt"):
    """
    Check the size of the specified file, and:
    - If the path is a directory, create an empty file with the default name in the directory.
    - If the path is a file and its size exceeds the threshold, create an empty file in the same directory with a
      3-digit padded incremented number at the end of the file name.

    :param path: Path to the original file or directory
    :param threshold: File size threshold in bytes
    :param default_filename: Default name to use if the path is a directory
    :return: The original path if the file size is below the threshold, or the path of the newly created file
    """
    if os.path.isdir(path):
        # If the path is a directory, create a file with the default name
        path = os.path.join(path, default_filename)
        if not os.path.isfile(path):
            open(path, 'w').close()
            return path
        

    if not os.path.isfile(path):
        # If the path is neither a file nor a directory, try to create file
        try:
            open(path, 'w').close()
            return path
        except:
            raise Exception("fail to create path")

    # Get the file size
    file_size = os.path.getsize(path)
    if file_size < threshold:
        # Return the original path if size is below the threshold
        return path

    # Split the original directory, file name, and extension
    dir_name, base_name = os.path.split(path)
    file_name, file_ext = os.path.splitext(base_name)

    # Process to append an incremented, zero-padded number to the file name
    i = 1
    while True:
        if "_" in file_name:
            try:
                # Parse existing numbers and increment
                base, num = file_name.rsplit("_", 1)
                i = int(num) + 1
                file_name = "{}_{:03d}".format(base, i)
            except ValueError:
                file_name = "{}_{:03d}".format(file_name, i)
        else:
            file_name = "{}_{:03d}".format(file_name, i)

        new_file_name = file_name + file_ext
        new_file_path = os.path.join(dir_name, new_file_name)

        if os.path.exists(new_file_path):
            # Check the size of the existing file
            existing_file_size = os.path.getsize(new_file_path)
            if existing_file_size >= threshold:
                # Increment only if the existing file size is above the threshold
                i += 1
                continue
            else:
                # Existing file is below the threshold, reuse it
                return new_file_path
        else:
            # If the file does not exist, use this name
            break

    # Create an empty file
    open(new_file_path, 'w').close()

    # Return the path of the newly created empty file
    return new_file_path
    
def write(path, content):
    """
    Appends the specified string to the file at the given path.
    
    :param path: Path to the file where the content will be written
    :param content: The string to append to the file
    :return: True if the operation was successful, False otherwise
    """
    try:
        # Open the file in append mode and write the content
        with open(path, 'a') as file:
            file.write(content)
        return True
    except Exception as e:
        # Log error details for debugging
        print("Error while appending to file: {}".format(e))
        return False
    



class Timer(object):
    def __init__(self):
        self.records = [] # record comment and elapsed time tuple ((com1,time1)...(com_n,time_n))

    class TimerContext(object):  #context manager
        def __init__(self, timer, comment=None):
            self.timer = timer
            self.comment = comment

        def __enter__(self):
            self.start_time = time()
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            self.end_time = time()
            elapsed = self.end_time - self.start_time
            self.timer.records.append((self.comment, elapsed))  # record

    def with_comment(self, comment):
        return self.TimerContext(self, comment)  # return context manager to record comment and time.

    def flush(self):
        # flush all records via stdout
        for i, (comment, elapsed) in enumerate(self.records):
            if comment:
                print("Task {} ({}): {:.2f} seconds".format(i + 1, comment, elapsed))
            else:
                print("Task {}: {:.2f} seconds".format(i + 1, elapsed))