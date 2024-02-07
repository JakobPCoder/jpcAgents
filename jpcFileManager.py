
import os
import time
import re
import json

FORMATS_LOAD = [
    "txt", "log", "toml", "properties",
    "py", "js", "php", "rb", "sql", "pl", "sh", "bat", "ps1", "vbs",
    "h", "hpp", "cpp", "c", "java", "cs", "ts", "makefile", "dockerfile",
    "css", "html", "xml", "json", "yaml", "yml", "ini", "cfg", "conf",
    "md", "markdown", "r", "swift", "perl", "groovy", "scala", "rust",
    "go", "dart", "kotlin", "vb", "as", "aspx", "jsp", "jsx", "tsx",
    "coffee", "scss", "less", "sass", "tpl", "twig", "liquid", "jsp",
    "pug", "ejs", "elm", "erl", "haskell", "lua", "matlab", "nim",
    "pascal", "prolog", "racket", "scheme", "tcl", "vhdl", "verilog",
    "fortran", "cobol", "ada", "lisp", "d", "f#", "ocaml", "powershell",
    "batch", "shell",
    "html", "css", "jsp", "asp", "rss", "svg", "jsonld",
    "csv", "rtf", "tex"
]


class CommandInfo:
    def __init__(self, name, description, query_description):
        self.name = name
        self.description = description
        self.query_description = query_description


class FileManager:
    def __init__(self):
        self.commands = [
            CommandInfo("LoadTextFile", "Loads a text based filefile from a given path.", "Path to the text file to be loaded."),
            CommandInfo("StoreTextFile", "Stores text data into a file at a given path.", "Path to store the text file and the text data to be stored.")
        ]

    def get_command_list(self):
        return [command.name for command in self.commands]

    def get_command_description(self, command_name):
        for command in self.commands:
            if command.name == command_name:
                return command.description
        return "Command not found."

    def load_text_file(self, file_path):
        # Implementation for loading a text file
        pass  # Replace with actual implementation

    def store_text_file(self, file_path, text_data):
        # Implementation for storing a text file
        pass  # Replace with actual implementation

    def execute_command(self, command_name, *args):
        if command_name == "LoadTextFile":
            return self.load_text_file(*args)
        elif command_name == "StoreTextFile":
            return self.store_text_file(*args)
        else:
            raise ValueError("Invalid command name")
        

    def __call__(self, input):
        print("input", type(input), input)

        return "test"
 
