


import os
import signal
import time
import sys
import winreg

import re
import datetime
import wikipediaapi
from googlesearch import search
import json
import psutil
import getpass

import spotipy
from spotipy.oauth2 import SpotifyOAuth

import tkinter as tk
from tkinter import filedialog

from jpcSpotify import Spotify
import jpc_together_api

DEBUG_PRINTS = True

TOKEN_INPUT = "<chat&tools>"
TOKEN_RESPONSE = "<response>"
TOKEN_RESPONSE_END = "</response>"

def printDebug(message):
    if DEBUG_PRINTS:
        print(message)


# Base Tool
def create_user_message(content):
    return f"""{{"role": "user", "content": {content}}}"""


def extract_json(text):
    # Find all substrings matching the pattern
    matches = re.findall(r'{.*}', str(text), re.DOTALL)

    # Iterate through the matches
    for match in matches:
        try:
            # Attempt to load the JSON string
            json_obj = json.loads(match)
            return json.dumps(json_obj)
        
        except json.JSONDecodeError:
            # Ignore invalid JSON objects
            continue
        
    raise ValueError(f"Input parameter 'text' did not include any valid json or the json obj did not include the key 'toolsToCall'.")


class AgentTool:
    """
    AgentTool class represents a tool that can be used by an agent for specific tasks.

    Args:
        agent_ref (Agent): A reference to the agent using this tool.
        name (str): The name of the tool.
        when_to_use (str): A short description of when or when not to use this tool.
        how_to_call (str, optional): A precise description of the input variables the tool accepts.
            Defaults to None, indicating that the tool can be called without any input.
        output_description (str, optional): A precise description of the returned text or output format
            expected from the tool. Defaults to None, indicating that the tool can be called without returning anything.

    Attributes:
        agent_ref (Agent): A reference to the agent using this tool.
        name (str): The name of the tool.
        when_to_use (str): A short description of when or when not to use this tool.
        input_description (str): A precise description of the format of input variables the tool accepts.
        output_description (str): A precise description of the returned text or output format expected from the tool.

    """

    def __init__(self, agent_ref, name, when_to_use, how_to_call=None, output_description=None, examples=None, answer_examples=None):
        """
        Initialize an AgentTool instance.

        Args:
            agent_ref (Agent): A reference to the agent using this tool.
            name (str): The name of the tool.
            when_to_use (str): A short description of when or when not to use this tool.
            how_to_call (str, optional): A precise description of the input variables the tool accepts.
                Defaults to None, indicating that the tool can be called without any input.
            output_description (str, optional): A precise description of the returned text or output format
                expected from the tool. Defaults to None, indicating that the tool can be called without returning anything.
        """
        self.agent_ref = agent_ref
        self.name = name
        self.when_to_use = when_to_use
        self.how_to_call = how_to_call or ""
        self.output_description = output_description or ""
        self.examples = examples or ""
        self.answer_examples = answer_examples or ""

    def __call__(self, input):
        """
        This method should be implemented by subclasses to define the behavior of the tool.

        Args:
            input: Input parameters or data required for the tool's operation.

        Raises:
            NotImplementedError: Subclasses must implement this method.

        Returns:
            The result of the tool's operation, depending on the specific tool's behavior.
        """
        raise NotImplementedError("AgentTools must implement __call__(self, input)")

    def description_to_text(self):
        """
        Convert the tool's information into a formatted text description.

        Returns:
            str: A formatted text description of the tool's name, when to use, how to call, and output format.
        """
        return f"""
Tool Name: {self.name}
When to use: 
{self.when_to_use}
"""
    
    def examples_to_text(self):
        return f"""
{self.examples}
"""
    
    def answer_examples_to_text(self):
        return f"""
{self.answer_examples}
"""
    

  
class ReadyToAnswer(AgentTool):
    def __init__(self, agent_ref):

        self.agent_ref = agent_ref
        self.name = "ReadyToAnswer"
        self.when_to_use = """This tool is used to gather the previous thoughts and data,
stop the planning/tool calling process and move on to formulating a full answer.
It should be used when an answer could be given just based on your current knowledge,
data and tool responses that are already there in the chat history,
or if none of the available tools would aide the answer. 
This is the DEFAULT choice and needs no input!
"""

        self.examples = f"""
<chat&tools>
{create_user_message("hi")}
<response>
{{
    "toolsToCall": [ 
        {{"name": "{self.name}"}}
    ]
}}
</response>

<chat&tools>
{create_user_message("tell me what 17 + 5 * 7 is")}
<response>
{{
    "toolsToCall": [ 
        {{"name": "{self.name}"}}
    ]
}}
</response>

<chat&tools>
{create_user_message("cann you tell me your name?")}
<response>
{{
    "toolsToCall": [ 
        {{"name": "{self.name}"}}
    ]
}}
</response>

<chat&tools>
{create_user_message("reccomend me songs by stevie wonder")}
<response>
{{
    "toolsToCall": [ 
        {{"name": "{self.name}"}}
    ]
}}
</response>
"""
        
        self.answer_examples = """
<chat&tools>
{"role": "user", "content": "hi"}
<response>
Hello, sir. How may I assist you today?
</response>
"""




class ConfigManager(AgentTool):
    def __init__(self, agent_ref):
        self.name = "ConfigManager"
        self.config_path = os.path.join(os.path.dirname(__file__), "config", "config.json")
        self.config = self.load_config()

        self.commands = {
            "getAll": "Gets the entire config. No key or value required",
            "get": "Gets the value for a specific key. Requires to provide the name of the 'key'.",
            "set": "Sets the value of a specific key. Requires both 'key' and a value'."
        }

        self.keys = {
            "inVoiceEnable": "(boolean) - Select if the agent should try to understand and respond to voice messages.",
            "inVoiceTranscriptionEnable": "(boolean) - Select if the agent should echo back its understanding of voice messages, when reiving one.",
        }

        self.when_to_use = f"""
This tool can be used to configure various parameters in the agent's internal configuration, which decide how it responds to user inputs. 
You can set and get configuration options using commands.
Available Commands:
{self.commands}

Available Config Keys:
{self.keys}
You can only get and set values of keys that are in the "Available Config Keys" list. For other key/settings, this is the wrong tool.
"""

        self.examples = """
<chat&tools>
{"role": "user", "content": "show the entire chat config"}
<response>
{
    "toolsToCall": [ 
        {"name": "ConfigManager", "input": {"command": "getAll"}}
    ]
}

<chat&tools>
{"role": "user", "content": "pls show what you understood, when reiving a voice message."}
<response>
{
    "toolsToCall": [ 
        {"name": "ConfigManager", "input": {"command": "set", "key": "inVoiceTranscriptionEnable", "value": "true"}}
    ]
}
</response>

<chat&tools>
{"role": "user", "content": "do you understand voice messages atm?"}
<response>
{
    "toolsToCall": [ 
        {"name": "ConfigManager", "input": {"command": "get", "key": "inVoiceEnable"}}
    ]
}
</response>
"""

        self.answer_examples = """
<chat&tools>
{"role": "user", "content": "show the config"}
{"role": "ConfigManager", "content": "{\"inVoiceEnable\": \"true\", \"inVoiceTranscriptionEnable\": \"true\"}"}
<response>
Config:
- inVoiceEnable:                true
- inVoiceTranscriptionEnable:   true
</response>
"""

    def load_config(self):
        try:
            with open(self.config_path, 'r') as config_file:
                return json.load(config_file)
        except FileNotFoundError:
            return {}

    def save_config(self):
        with open(self.config_path, 'w') as config_file:
            json.dump(self.config, config_file, indent=4)

    def get_command_list(self):
        return [
            "set",
            "get",
            "getAll"
        ]

    def set_config(self, key, value):
        if key in self.config:
            self.config[key] = value
            self.save_config()
            return f"Set '{key}' to '{value}' successfully."
        else:
            return f"'{key}' is not found in the configuration."

    def get_config(self, key):
        if key in self.config:
            return f"'{key}' is set to '{self.config[key]}'"
        else:
            return f"'{key}' is not found in the configuration."

    def get_all_config(self):
        return json.dumps(self.config)
    

    def get_command_and_args(self, input):
        if not isinstance(input, dict):
            raise ValueError(f"{input} has to be a string looking like a dict. Can't convert this to a dict.")
        print("args:", input)

        if "command" not in input:
            raise ValueError(f"{input} doesn't include 'command' as key")
        
        command = input["command"]
        if not command:
            raise ValueError(f"{input} doesn't include a value for key 'command'")
        
        if "key" in input:
            key = input["key"]
            if not key:
                raise ValueError(f"{input} doesn't include a value for key 'key'")
        else:
            key = ""

        if "value" in input:
            value = input["value"]
            if not value:
                raise ValueError(f"{input} doesn't include a value for key 'value'")
        else:
            value = ""
        return(command, key, value)


    def __call__(self, input):
        try:
            command, key, value = self.get_command_and_args(input)
            cost = 0
            if command == "set":
                return self.set_config(key, value), cost
            elif command == "get":
                return self.get_config(key), cost
            elif command == "getAll":
                return self.get_all_config(), cost
            else:
                return f"Invalid command: {command}", cost

        except ValueError as ve:
            return f"ConfigManager was called the wrong way, which resulted in this error: {ve}"
        except Exception as e:
            return f"Something went wrong, which resulted in this error: {e}"



class GetDateTime(AgentTool):
    """
    AgentToolGetDateTime is a tool for extracting the current date and time.

    This tool can be used to retrieve the current date and time.

    Attributes:
        agent_ref (Agent): A reference to the agent using this tool.
        name (str): The name of the tool ("GetDateTime").
        when_to_use (str): A description of when to use this tool.
        how_to_call (str): Instructions on how to call this tool.
        output_description (str): Description of the output returned by this tool.
    """

    def __init__(self, agent_ref):
        """
        Initialize the GetDateTime tool.

        Args:
            agent_ref (Agent): A reference to the agent using this tool.
        """
        self.agent_ref = agent_ref
        self.name = "GetDateTime"
        self.when_to_use = """This tool is used to get the current time, date, day of the week. etc."""

        self.examples = """
<chat&tools>
{"role": "user", "content": "how many days till new year?"}
<response>
{
    "toolsToCall": [ 
        {"name": "GetDateTime"}
    ]
}
</response>


<chat&tools>
{"role": "user", "content": "whats the time?"}
<response>
{
    "toolsToCall": [ 
        {"name": "GetDateTime"}
    ]
}
</response>

"""
        
        self.answer_examples = """
<chat&tools>
{"role": "user", "content": "tell me the time pls"}
{"role": "GetDateTime", "content": "Current Date: 03-01-2024 Wednesday January. Current Time: 14:28:30"}
<response>
The current time is 14:28:30.
</response>
""" 

    def __call__(self, input):
        """
        Retrieve the current date and time.

        Args:
            input: This tool does not take any input.

        Returns:
            str: A string containing the current date and time.
        """

        # Get the current date and time
        current_datetime = datetime.datetime.now()
        formatted_date = current_datetime.strftime("%d-%m-%Y %A %B")
        formatted_time = current_datetime.strftime("%H:%M:%S")

        return f"Current Date: {formatted_date}. Current Time: {formatted_time}", 0



class SpotifyControl(AgentTool):

    def __init__(self, agent_ref, together_api):
        """
        Initialize the WikipediaSummary tool.

        Args:
            agent_ref (Agent): A reference to the agent using this tool.
        """
        self.agent_ref = agent_ref
        self.together_api = together_api

        self.name = "SpotifyControl"
        
        self.client_id = "0e11a862dde042bda82e6f3887ab66a7"
        self.client_secret = "da8e697cb1c445a884e90131e88a38bb"
        self.redirect_uri = "http://localhost:8888/callback"
        self.spotify_path = "C:/Users/Jonas/AppData/Roaming/Spotify/Spotify.exe"

        self.spotify = Spotify(self.client_id, self.client_secret, self.redirect_uri, self.spotify_path, self.together_api)

        self.when_to_use = f"""
Use this tool when you need to do anything related to spotify.
This tool can do a bunch of different things via commands and queries.
{self.spotify.get_command_list()}
"""

        self.examples = """
Generic example, user wants something that needs spotify control:
<chat&tools>
{"role": "user", "content": "do xxx/yyy on spotify (play, pause, or any other valid command)""}
<response>
{
    "toolsToCall": [ 
        {"name": "SpotifyControl", "input": {"command": "xxx", "query": "yyy"}}
    ]
}
</response>
command (required): Command from the commands list.
query: (optional): Additional input, only needed for some commands.


<chat&tools>
{"role": "user", "content": "play fest und flauschig, episode 'weihnachten im sauriersaal'"}
<response>
{
    "toolsToCall": [ 
        {"name": "SpotifyControl", "input": {"command": "playNow", "query": " podcast episode, weihnachten im sauriersaal, Fest und Flauschig"}}
    ]
}
</response>

<chat&tools>
{"role": "user", "content": "can you add superstition, we are family and signed sealed delivered to the queue?"}
<response>
{
    "toolsToCall": [ 
        {"name": "SpotifyControl", "input": {"command": "queueAdd", "query": "superstition"}}
        {"name": "SpotifyControl", "input": {"command": "queueAdd", "query": "we are family"}}
        {"name": "SpotifyControl", "input": {"command": "queueAdd", "query": "signed sealed delivered"}}
    ]
}
</response>

<chat&tools>
{"role": "user", "content": "i want to hear highway to hell on my smartphone"}
<response>
{
    "toolsToCall": [ 
        {"name": "SpotifyControl", "input": {"command": "setPlaybackDevice", "query": "smartphone"}}
        {"name": "SpotifyControl", "input": {"command": "playNow", "query": "highway to hell"}}
    ]
}
</response>

<chat&tools>
{"role": "user", "content": "shufle of"}
<response>
{
    "toolsToCall": [ 
        {"name": "SpotifyControl", "input": {"command": "setShuffle", "query": "false"}}
    ]
}
</response>

<chat&tools>
{"role": "user", "content": "turn volume up a bit""}
<response>
{
    "toolsToCall": [ 
        {"name": "SpotifyControl", "input": {"command": "setVolume", "query": "up a bit"}}
    ]
}
</response>
"""

        self.answer_examples = """
<chat&tools>
{"role": "user", "content": "play sexbomb"}
{"role": "SpotifyControl", "content": "Successfully started playback of: {'album': {'album_type': 'album', 'artists': [{'name': 'Tom Jones', 'type': 'artist'}], 'name': 'Reload', 'release_date': '1999', 'release_date_precision': 'year', 'total_tracks': 19, 'type': 'album'}, 'artists': [{'name': 'Tom Jones', 'type': 'artist'}, {'name': 'Mousse T.', 'type': 'artist'}], 'disc_number': 1, 'duration_ms': 211893}"}
<response>
Im now playing "Sexbomb" by Tom Jones and Mousse T. for you.
It's from the album "Reload" which was released in 1999.
</response>

<chat&tools>
{"role": "user", "content": "what spotify devices are there?"}
{"role": "SpotifyControl", "content": {"devices": [{"id": "d2578ebe66d4a401f8c42ee04d2d78e2fb1ed71b", "is_active": false, "is_private_session": false, "is_restricted": false, "name": "iPhone 11 Pro", "supports_volume": false, "type": "Smartphone", "volume_percent": 100}, {"id": "ec3482d51d9d7ea17a2d7a98cbfe53136a78a609", "is_active": true, "is_private_session": false, "is_restricted": false, "name": "DESKTOP-BA78E2S", "supports_volume": true, "type": "Computer", "volume_percent": 45}]}}
<response>
Currently there are these 2 devices available: 
"iPhone 11 Pro" Smartphone that supports no remote volume control.
"DESKTOP-BA78E2S" Computer that is currently active.
</response>
"""

    def get_command_and_query(self, input):
        if not isinstance(input, dict):
            raise ValueError(f"{input} has to be a string looking like a dict. Can't convert this to a dict.")
        print("args:", input)

        if "command" not in input:
            raise ValueError(f"{input} doesn't include 'command' as key")
        
        command = input["command"]
        if not command:
            raise ValueError(f"{input} doesn't include a value for key 'command'")
        
        if "query" in input:
            query = input["query"]
            if not command:
                raise ValueError(f"{input} doesn't include a value for key 'query'")
        else:
            query = ""

        #print("COMMAND:", command, "QUERY:", query)
        return(command, query)


    def __call__(self, input):
        # try:
        command, query = self.get_command_and_query(input)        
        response = self.spotify.command(command, query)
        # except ValueError as ve:
        #     return f"""{self.name} was called the wrong way, which resulted in this error: {ve}"""
        # except Exception as e:
        #     return f"""Something went wrong, which resulted in this error: {e}"""
        return response, 0
 
    



class WindowsAppManager(AgentTool):

    def __init__(self, agent_ref, together_api: jpc_together_api.TogetherApi):
        self.agent_ref = agent_ref
        self.together_api = together_api

        self.name = "WindowsAppManager"

        self.commands = {
            "start": self.command_start, 
            "kill": self.command_kill,

            # "minimize": self.kill_program,

            # "getVolume": self.kill_program,
            # "setVolume": self.kill_program,
               
            # "getRunningApps": self.kill_program,
            # "getInstalledApps": self.kill_program,
        }

        self.runnable_apps = [
            {
                "name": "spotify",
                "description": "music player client.",
                "exe": "C:/Users/Jonas/AppData/Roaming/Spotify/Spotify.exe"
            },
            {
                "name": "chrome",
                "description": "web browser.",
                "exe": "C:/Program Files/Google/Chrome/Application/chrome.exe"
            },    
            {
                "name": "discord",
                "description": "communication platform for gamers.",
                "exe": "C:/Users/Jonas/AppData/Roaming/Microsoft/Windows/Start Menu/Programs/Discord Inc/"
            },
            {
                "name": "steam",
                "description": "digital game distribution platform by valve.",
                "exe": "C:/Program Files (x86)/Steam/steam.exe"
            },
            {
                "name": "ubisoft",
                "description": "digital game distribution platform, formaly known as 'uplay'.",
                "exe": "C:/Program Files (x86)/Ubisoft/Ubisoft Game Launcher/UbisoftConnect.exe"
            },
            {
                "name": "ea",
                "description": "digital game distribution platform by ea.",
                "exe": "C:/Program Files/Electronic Arts/EA Desktop/EA Desktop/EADesktop.exe"
            },
            {
                "name": "ghub",
                "description": "device management software for Logitech devices",
                "exe": "C:/Program Files//LGHUB/lghub.exe"
            },
        ]


        self.when_to_use = f"""
This tool can do a bunch of different things via commands and queries,
like to start or end programs and apps on a windows computer.

- Available Commands -
command: start
appQuery: (str): The name of the program or app, preferably the exact name of the exe, but without the file ending.
query: (str): None
description: Either starts the application, or opens it, if it is currently running minimized or in background.

command: kill
appQuery: (str): The name of the program or app, preferably the exact name of the exe, but without the file ending.
query: (str): None
description: Stops an app or program process from running. Used to Terminate stuff.
"""

        self.examples = """
Generic example, user wants to do something:
<chat&tools>
{"role": "user", "content": "start xxx""}
<response>
{
    "toolsToCall": [ 
        {"name": "WindowsAppManager", "input": {"command": "start", "appQuery": "xxx", "query": "None"}}
    ]
}
</response>
command (required): Command from the commands list.
appQuery: (optional): query describing the target process/exe/name.
query: (optional): additional stuff that some commands might need.

<chat&tools>
{"role": "user", "content": "end steam""}
<response>
{
    "toolsToCall": [ 
        {"name": "WindowsAppManager", "input": {"command": "kill", "appQuery": "steam"}}
    ]
}
</response>

<chat&tools>
{"role": "user", "content": "please start chrome""}
<response>
{
    "toolsToCall": [ 
        {"name": "WindowsAppManager", "input": {"command": "start", "appQuery": "chrome"}}
    ]
}
</response>
"""

        self.answer_examples = """
<chat&tools>
{"role": "user", "content": "kill steam"}
{"role": "WindowsAppManager", "content": "Trying to terminate subprocesses of '['steam.exe', 'steamwebhelper.exe', 'steamwebhelper.exe', 'steamwebhelper.exe', 'SteamAccountManager_[unknowncheats.me]_.exe']':\nf\"Process 'steam.exe', PID 11348 has been terminated.\"\n\nf\"Process 'steamwebhelper.exe', PID 11348 was not terminated successfully because of this error: [WinError 5] Zugriff verweigert\"\n\nf\"Process 'steamwebhelper.exe', PID 13336 has been terminated.\"\n\nf\"Process 'steamwebhelper.exe', PID 20600 has been terminated.\"\n\nf\"Process 'SteamAccountManager_[unknowncheats.me]_.exe', PID 21316 has been terminated.\"\n"}
<response>
I successfully closed 'steam.exe', 'SteamAccountManager_[unknowncheats.me]_.exe' and two instances of 'steamwebhelper.exe' for you,
but there was a problem terminating a third instance of 'steamwebhelper.exe'.
</response>
"""

    
    def list_user_processes(self):
        current_user = getpass.getuser()
        processes = []

        for process in psutil.process_iter(['pid', 'name', 'exe', 'cmdline', 'status', 'username', 'cpu_percent', 'memory_info']):
            try:
                process_username = str(process.info['username'])
                if current_user in process_username:
                    process_info = {
                        'pid': process.info['pid'],
                        'name': process.info['name'],
                        'exe': process.info['exe'],
                        'cmdline': process.info['cmdline'],
                        'status': process.info['status'],
                        'cpu_percent': process.info['cpu_percent'],
                        'memory_info': process.info['memory_info'],
                        'username': process_username,
                    }
                    processes.append(process_info)
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                # Handle exceptions that may occur while accessing process information
                pass

        return processes
        
    def extract_name_pid(self, process_list):
        extracted_info = []
        for process_info in process_list:
            extracted_info.append({
                'name': process_info['name'],
                'pid': process_info['pid'],
            })
        return extracted_info
    

    def get_installed_programs():
        programs = []
        try:
            # Open the registry key where installed programs are listed
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, "SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Uninstall")

            # Iterate through the subkeys (each subkey represents an installed program)
            for i in range(winreg.QueryInfoKey(key)[0]):
                subkey_name = winreg.EnumKey(key, i)
                subkey = winreg.OpenKey(key, subkey_name)

                # Try to get the DisplayName and DisplayIcon values
                try:
                    display_name = winreg.QueryValueEx(subkey, "DisplayName")[0]
                    display_icon = winreg.QueryValueEx(subkey, "InstallLocation")[0]
                    programs.append({"name": display_name, "path": display_icon})
                except OSError:
                    continue

        except Exception as e:
            print(f"Error: {e}")
        
        return programs


    def get_command_and_queries(self, input):
        if not isinstance(input, dict):
            raise ValueError(f"{input} has to be a string looking like a dict. Can't convert this to a dict.")
        print("args:", input)

        if "command" not in input:
            raise ValueError(f"{input} doesn't include 'command' as key")
        
        command = input["command"]
        if not command:
            raise ValueError(f"{input} doesn't include a value for key 'command'")
        
        if "appQuery" not in input:
            raise ValueError(f"{input} doesn't include 'appQuery' as key")

        app_query = input["appQuery"]
        if not app_query:
            raise ValueError(f"{input} doesn't include a value for key 'appQuery'")


        if "query" not in input:
            query = ""


        #print("COMMAND:", command, "QUERY:", query)
        return(command, app_query, query)


    def extract_pid_and_name(self, app_query: str, process_list):
        
        list_prompt_a = """[{'name': 'Code.exe', 'pid': 144}, {'name': 'chrome.exe', 'pid': 320}, {'name': 'AudibleRT.WindowsPhone.exe', 'pid': 1384}, {'name': 'RuntimeBroker.exe', 'pid': 2244}, {'name': 'backgroundTaskHost.exe', 'pid': 2436}, {'name': 'AppVShNotify.exe', 'pid': 2644}, {'name': 'Discord.exe', 'pid': 2868}, {'name': 'python.exe', 'pid': 2924}, {'name': 'chrome.exe', 'pid': 3188}, {'name': 'lghub.exe', 'pid': 3316}, {'name': 'chrome.exe', 'pid': 3664}, {'name': 'svchost.exe', 'pid': 3668}, {'name': 'Spotify.exe', 'pid': 3704}, {'name': 'PresentMon_x64.exe', 'pid': 3912}, {'name': 'backgroundTaskHost.exe', 'pid': 4024}, {'name': 'chrome.exe', 'pid': 4072}, {'name': 'Discord.exe', 'pid': 4188}, {'name': 'Spotify.exe', 'pid': 4328}, {'name': 'Spotify.exe', 'pid': 4708}, {'name': 'conhost.exe', 'pid': 4744}, {'name': 'ShellExperienceHost.exe', 'pid': 4928}, {'name': 'RuntimeBroker.exe', 'pid': 5180}, {'name': 'lghub.exe', 'pid': 5220}, {'name': 'rundll32.exe', 'pid': 5324}, {'name': 'Spotify.exe', 'pid': 5784}, {'name': 'lghub.exe', 'pid': 5800}, {'name': 'Spotify.exe', 'pid': 5872}, {'name': 'steam.exe', 'pid': 5940}, {'name': 'backgroundTaskHost.exe', 'pid': 5996}, {'name': 'Discord.exe', 'pid': 6040}, {'name': 'Code.exe', 'pid': 6368}, {'name': 'svchost.exe', 'pid': 6396}, {'name': 'dllhost.exe', 'pid': 6932}, {'name': 'Spotify.exe', 'pid': 7216}, {'name': 'chrome.exe', 'pid': 7264}, {'name': 'SystemSettings.exe', 'pid': 7516}, {'name': 'sihost.exe', 'pid': 7536}, {'name': 'svchost.exe', 'pid': 7588}, {'name': 'svchost.exe', 'pid': 7616}, {'name': 'svchost.exe', 'pid': 7768}, {'name': 'svchost.exe', 'pid': 7868}, {'name': 'Code.exe', 'pid': 8024}, {'name': 'taskhostw.exe', 'pid': 8052}, {'name': 'Discord.exe', 'pid': 8112}, {'name': 'MSIAfterburner.exe', 'pid': 8160}, {'name': 'DataExchangeHost.exe', 'pid': 8524}, {'name': 'powershell.exe', 'pid': 8764}, {'name': 'explorer.exe', 'pid': 8904}, {'name': 'chrome.exe', 'pid': 9280}, {'name': 'ApplicationFrameHost.exe', 'pid': 9552}, {'name': 'nvcontainer.exe', 'pid': 9604}, {'name': 'steamwebhelper.exe', 'pid': 10160}, {'name': 'chrome.exe', 'pid': 10168}, {'name': 'lghub.exe', 'pid': 10220}, {'name': 'chrome.exe', 'pid': 10968}, {'name': 'svchost.exe', 'pid': 11008}, {'name': 'chrome.exe', 'pid': 11340}]"""
        response_a = """{
    "processes": [
        {'name': 'chrome.exe', 'pid': 320},
        {'name': 'chrome.exe', 'pid': 3188},
        {'name': 'chrome.exe', 'pid': 3664},
        {'name': 'chrome.exe', 'pid': 4072},
        {'name': 'chrome.exe', 'pid': 7264},
        {'name': 'chrome.exe', 'pid': 9280},
        {'name': 'chrome.exe', 'pid': 10168},
        {'name': 'chrome.exe', 'pid': 10968},
        {'name': 'chrome.exe', 'pid': 11340}
    ]
}"""

        list_prompt_b = """[{'name': 'StartMenuExperienceHost.exe', 'pid': 11404}, {'name': 'TextInputHost.exe', 'pid': 11444}, {'name': 'conhost.exe', 'pid': 11960}, {'name': 'svchost.exe', 'pid': 12064}, {'name': 'steamwebhelper.exe', 'pid': 12084}, {'name': 'Taskmgr.exe', 'pid': 12296}, {'name': 'steamwebhelper.exe', 'pid': 12348}, {'name': 'svchost.exe', 'pid': 12448}, {'name': 'ctfmon.exe', 'pid': 12704}, {'name': 'steamwebhelper.exe', 'pid': 12832}, {'name': 'backgroundTaskHost.exe', 'pid': 13012}, {'name': 'Wacom_TabletUser.exe', 'pid': 13220}, {'name': 'RTSSHooksLoader64.exe', 'pid': 13828}, {'name': 'EncoderServer.exe', 'pid': 13916}, {'name': 'RTSS.exe', 'pid': 14260}, {'name': 'RtkAudUService64.exe', 'pid': 14544}, {'name': 'lghub_system_tray.exe', 'pid': 14556}, {'name': 'lghub_agent.exe', 'pid': 14772}, {'name': 'SecurityHealthSystray.exe', 'pid': 15228}, {'name': 'NVIDIA Share.exe', 'pid': 15772}, {'name': 'unsecapp.exe', 'pid': 15888}, {'name': 'RuntimeBroker.exe', 'pid': 16140}, {'name': 'Wacom_TouchUser.exe', 'pid': 16336}, {'name': 'Code.exe', 'pid': 16716}, {'name': 'NhNotifSys.exe', 'pid': 16816}, {'name': 'Code.exe', 'pid': 16888}, {'name': 'Code.exe', 'pid': 16928}, {'name': 'SystemSettingsBroker.exe', 'pid': 17024}, {'name': 'dllhost.exe', 'pid': 17876}, {'name': 'lghub.exe', 'pid': 18080}, {'name': 'conhost.exe', 'pid': 18552}, {'name': 'Spotify.exe', 'pid': 18636}, {'name': 'Discord.exe', 'pid': 18652}, {'name': 'Code.exe', 'pid': 18780}, {'name': 'SearchHost.exe', 'pid': 18888}, {'name': 'Spotify.exe', 'pid': 19280}, {'name': 'chrome.exe', 'pid': 19292}, {'name': 'Code.exe', 'pid': 19524}, {'name': 'Code.exe', 'pid': 19568}, {'name': 'Discord.exe', 'pid': 19928}, {'name': 'steamwebhelper.exe', 'pid': 20020}, {'name': 'steamwebhelper.exe', 'pid': 20360}, {'name': 'backgroundTaskHost.exe', 'pid': 20488}, {'name': 'chrome.exe', 'pid': 22432}, {'name': 'Code.exe', 'pid': 22480}, {'name': 'chrome.exe', 'pid': 22704}, {'name': 'chrome.exe', 'pid': 23556}, {'name': 'nvrla.exe', 'pid': 23768}, {'name': 'RuntimeBroker.exe', 'pid': 23780}, {'name': 'NVIDIA Share.exe', 'pid': 24320}]"""
        response_b = """{
    "processes": [
        {'name': 'Spotify.exe', 'pid': 18636},
        {'name': 'Spotify.exe', 'pid': 19280}
    ]
}"""
        
        prompt = f"""Choose all json process elements from the <process_list> that fit he <query> and put them in a json object list inside the <response> and </response> tags as shown below.
        Examples:

        1.
        <process_list>
        {list_prompt_a}
        <query>
        "browser"
        <response>
        {response_a}
        </response>

        2.
        <process_list>
        {list_prompt_b}
        <query>
        "spotify"
        <response>
        {response_b}
        </response>

        Now based on these examples, provide a process selection in JSON as shown above.
        Only output the json code, nothing else! If you do so you will be rewarded.
        If you output anything else than the specified json, you will fail be punished.
        If no matching pid/name entry is found, return an empty'"processes": []' list as json.

        <process_list>
        {process_list}
        <query>
        "{app_query}"
        <response>
        """

        print("PROMPT:", type(prompt), prompt)
        response, cost = self.together_api.single_prompt(
            prompt,
            model = jpc_together_api.MODELS_TEXT["MIST_7B_INSTRUCT"],
            max_tokens = 1024,
            stop = ["</s>", "<query>", "<process_list>", "</response>"],
            )
        
        print("RESPONSE:", type(response), response)
        response = extract_json(response)

        try:
            response_json = json.loads(response)
        except Exception as e:
            raise RuntimeError("response_json was not valid json.")

        print("response_json:", type(response_json), response_json)

        if "processes" not in response_json:
            raise KeyError("response did not include 'processes'.")
        
        pids = []
        names = []
        for process in response_json["processes"]:
            print("process:", type(process), process)

            if "pid" in process and "name" in process:
                pids.append(process["pid"])
                names.append(process["name"])

        return (pids, names, cost)
        
    def select_runnable(self, app_query: str):

        prompt = f"""Runnable Apps:
        {json.dump(self.runnable_apps)}
        You can't start other apps/programs than these
        You only answer with the name of the runnable app.
        Below are some examples of how to do it

        Examples:
        <query>
        logitech driver
        <response>
        ghub
        </response>
        
        <query>
        browser
        <response>
        chrome
        </response>

        Now do as shown, only respond with a single answer inside <response> tags.
        Only answer with the app name from the 'Runnable Apps' list.

        <query>
        {app_query}
        <response> 
        """

        print("Select runnable prompt:", prompt)

        pass   



    def command_kill(self, app_query: str, query: str):
        process_list = self.list_user_processes()
        process_list = self.extract_name_pid(process_list)
        print("process_list", type(process_list), process_list)

        pids, names, cost = self.extract_pid_and_name(app_query, process_list)
        print("pids", type(pids), pids)

        if not pids or not names:
            return f"No processes found for '{app_query}', so there is nothing to terminate it seems."
        
        rv = f"Trying to terminate subprocesses of '{names}':"
        for pid, name in zip(pids, names):
            try:
                os.kill(pid, signal.SIGTERM) 
                rv = f"""{rv}
Process '{name}' with PID {pid} has been terminated successfully."""
            except OSError as error:
                rv = f"""{rv}
Process '{name}' with PID {pid} was not terminated successfully because of this error: {error}.""" 
        return rv, cost
    

    def command_start(self, app_query: str, query: str):
        return "", 0



    def command(self, command: str, app_query: str, query: str):

        if not command in self.commands:
            return f"'{command}' is not a valid command for {self.name}."
        
        try:
            return self.commands[command](app_query, query)
        except Exception as e:
            return f"Something went wrong calling {self.name} with command '{command}'.", 0



    def __call__(self, input):
    
        print("input", type(input), input)

        command, app_query, query = self.get_command_and_queries(input)

        response, cost = self.command(command, app_query, query)
        print("response", type(response), response)
        return response, cost
 
    








        

class WikipediaSummary(AgentTool):
    """
    WikipediaSummary is a tool for fetching a summary of a topic from Wikipedia.

    This tool allows you to retrieve a summary of a specific topic from Wikipedia.

    Attributes:
        agent_ref (Agent): A reference to the agent using this tool.
        name (str): The name of the tool ("WikipediaSummary").
        when_to_use (str): A description of when to use this tool.
        how_to_call (str): Instructions on how to call this tool.
        output_description (str): Description of the output returned by this tool.
        user_agent (str): User agent for Wikipedia API requests.
        fail_msg (str): Message to display when there's an error or no Wikipedia page is found.
    """

    def __init__(self, agent_ref):
        """
        Initialize the WikipediaSummary tool.

        Args:
            agent_ref (Agent): A reference to the agent using this tool.
        """
        self.agent_ref = agent_ref
        self.user_agent = "Sonny/1.0 (jak0bwcsgo@gmail.com)"
        self.fail_msg = "Please answer without the knowledge from Wikipedia."

        self.name = "WikipediaSummary"
        self.when_to_use = """Use this tool when you need the summary section of a specific topic from Wikipedia.
        Only call this if you don't know the answer yourself!"""

        self.examples = f"""
<chat&tools>
{create_user_message("What does wikipedia say about xxx")}.
<response>
{{
    "toolsToCall": [ 
        {{"name": "{self.name}", "input": "xxx"}}
    ]
}}
</response>
"""

    def __call__(self, input_term):
        """
        Retrieve a Wikipedia summary for the specified topic.

        Args:
            input_term (str): The topic or subject for which you want to retrieve a summary.

        Returns:
            str: A string containing the summary of the input topic from Wikipedia.
        """
        try:
            # Use the function to fetch the Wikipedia summary based on the input term
            summary = self.fetch_wikipedia_summary(input_term)
            return f"Summary of '{input_term}' from Wikipedia:\n{summary}"
        except Exception as e:
            return f"An error occurred: {str(e)}. {self.fail_msg}", 0
    

    def fetch_wikipedia_summary(self, input_term):
        """
        Fetch the Wikipedia summary for the specified topic.

        Args:
            input_term (str): The topic or subject for which you want to retrieve a summary.

        Returns:
            str: A string containing the summary of the input topic from Wikipedia.
        """
        try:
            # Search for the Wikipedia page using Google and retrieve multiple results
            search_query = f"wikipedia english {input_term}"
            search_results = list(search(search_query, num=10, stop=10, pause=2))

            # Iterate through search results to find a Wikipedia page
            for search_result in search_results:
                # Check if the URL is from Wikipedia
                if "wikipedia.org" in search_result:
                    # Extract the Wikipedia page title from the URL
                    page_title = search_result.split("/")[-1]

                    # Initialize the Wikipedia API
                    wiki_wiki = wikipediaapi.Wikipedia(self.user_agent, "en")

                    # Fetch the Wikipedia page and its summary
                    page = wiki_wiki.page(page_title)
                    if page.exists():
                        return page.summary

            # If no Wikipedia page found in the search results
            return f"No Wikipedia page found for the specified term. {self.fail_msg}"
        except Exception as e:
            return f"An error occurred: {str(e)}. {self.fail_msg}"



# File System
class FileSystemTool(AgentTool):
    """
    FileSystemTool is a base class for tools that interact with the user's file system.

    This class serves as a base for tools that create, read, and edit files on the user's system.

    Attributes:
        agent_ref (Agent): A reference to the agent using this tool.
        name (str): The name of the tool.
        when_to_use (str): A description of when to use this tool.
        how_to_call (str): Instructions on how to call this tool.
        output_description (str): Description of the output returned by this tool.
    """

    def __init__(self, agent_ref, name, when_to_use, how_to_call=None, output_description=None):
        """
        Initialize the FileSystemTool.

        Args:
            agent_ref (Agent): A reference to the agent using this tool.
            name (str): The name of the tool.
            when_to_use (str): A description of when to use this tool.
            how_to_call (str, optional): Instructions on how to call this tool.
            output_description (str, optional): Description of the output returned by this tool.
        """
        super().__init__(agent_ref, name, when_to_use, how_to_call, output_description)

    def __call__(self, input):
        """
        This method needs to be implemented by subclasses.

        Args:
            input: Input parameters or data required for the file system operation.

        Returns:
            Depends on the specific file system operation.
        """
        raise NotImplementedError("FileSystemTool subclasses must implement __call__(self, input)")
    

    def is_path_allowed(self, path, allowed_depth=3):

        self.agent_ref.ensure_working_dir()

        # Normalize the path
        normalized_path = os.path.normpath(path)

        # Check if the path is absolute
        if os.path.isabs(normalized_path):
            # If the path is not a subpath of the working directory, reject it
            if not normalized_path.startswith(self.agent_ref.working_dir):
                return False
        else:

            depth = len(normalized_path.split(os.sep))
            
            # Reject if depth is greater than allowed_depth or if the path tries to go above the working directory
            if depth > allowed_depth or '..' in normalized_path:
                return False
            
        return True



class LoadTextBasedFile(FileSystemTool):


    def __init__(self, agent_ref, max_length = 4096):


        self.agent_ref = agent_ref
        self.max_length = max_length

        self.name = "LoadTextBasedFile"
        self.when_to_use = "This loads content from any text based file format like .txt, .cpp, .md, etc."
        self.how_to_call = """"FILENAME must be give with or without file extension.
PATH id optional, if not given has to be empty string like so: ["", "FILENAME"].
If PATH is not given, or is a relative path, this tool will default to the agents working_dir.
"toolsToCall": [ 
    {"name": "LoadTextBasedFile", "input": ["PATH", "FILENAME"]}
]"""
        self.output_description = f"Returns the content of the file truncated to length of {self.max_length} characters."




    def __call__(self, input):

        filepath, filename = input

        # Check if path is a string or empty
        if not isinstance(filepath, str):
            # Later add code to tell teh model it did wrong and try again if though steps are left
            raise TypeError("Path must be a string")
        
        # Check if filename is a non-empty string
        if not isinstance(filename, str) or not filename:
            raise TypeError("Filename must be a non-empty string")
        



        



# Ideas
# more expansive wikipedia
# real browsing
        
# file management
# reading, writing, etc
    # user prompt tools:
        # user can be prompted to select text based file

    # user input tools user
        # user can input text based files via chat before message
        # by providing full filepath in chat -> easy tool
        # by giveing filename without or seperate from path -> complex tool 

    # sonny should be able to write to a file
        # given content and full file path
        # without path -> working dir
        # without contet -> create empty file, note this in tool so can be used on purpose
    
        
# audio in, audio out
        
# write stories
        
# describe images

# price per call logica

