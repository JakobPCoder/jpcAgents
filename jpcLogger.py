

import os
import json
from datetime import datetime

class Logger:
    def __init__(self):
        # Get the current script's directory
        self.current_directory = os.path.dirname(os.path.realpath(__file__))
        # Create a 'logs' directory if it doesn't exist
        self.logs_directory = os.path.join(self.current_directory, 'logs')
        if not os.path.exists(self.logs_directory):
            os.mkdir(self.logs_directory)
        self.log_file = os.path.join(self.logs_directory, 'log.json')
        
    def reset_log(self):
        # Reset (delete content) of the log file
        with open(self.log_file, 'w') as file:
            file.write('[]')

    def log(self, items):
        # Ensure the log file exists or create it if not
        if not os.path.exists(self.log_file):
            with open(self.log_file, 'w') as file:
                file.write('[]')

        # Load existing log data
        with open(self.log_file, 'r') as file:
            log_data = json.load(file)
        
        # Get current time in HH:MM:SS format
        current_time = datetime.now().strftime('%H:%M:%S')
        
        # Convert items to strings and prepend current time and script path
        log_entry = [current_time] + [str(item) for item in items]
        
        # Append the log entry to the log data
        log_data.append(log_entry)
        
        # Write the updated log data back to the file
        with open(self.log_file, 'w') as file:
            json.dump(log_data, file, indent=4)

