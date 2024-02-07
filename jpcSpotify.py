
import inspect

import time

import re
import json
import psutil
import subprocess
import platform

import spotipy
from spotipy.oauth2 import SpotifyOAuth

import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
import jpc_together_api


client_id = "0e11a862dde042bda82e6f3887ab66a7"
client_secret = "da8e697cb1c445a884e90131e88a38bb"
redirect_uri = "http://localhost:8888/callback"
spotify_path = "C:/Users/Jonas/AppData/Roaming/Spotify/Spotify.exe"




COMMANDS = [
    "playNow",
    "queueAdd",

    "pause",
    "continue",
    "skip",
    "previous",

    "getDevices",
    "getPlaying",

    "setShuffle",
    "setPlaybackDevice",
    "setVolume",
]

COMMAND_DESCRIPTIONS = {
    "playNow": "Starts playing track, album, playlist or artist. This is the default way of playing a song etc.",
    "queueAdd": "Adds track to the end of the queue, only works with single tracks, not albums, not artists, etc.",
    
    "pause": "Pauses whatever is playing right now.",
    "continue": "Continues playing whatever was playing before.",
    "skip": "Skips the current track.",
    "previous": "Reverts to previous track.",

    "getDevices": "Gets a list of currently available devices for Spotify playback. Returns their ID, name, volume, if they can be controlled and if they are active right now.",
    "getPlaying": "Gets all kind of information about what and how is currently playing. Song name, artist, shuffle state and so on.",

    "setShuffle": "Sets shuffle mode on or off.",

    "setPlaybackDevice": "Sets the current playback device.",
    "setVolume": "Sets the current playback devices Volume.",
}

COMMAND_QUERY = {
    "playNow": "(str): The track, artist, playlist or whatever else the user wants to be played",
    "queueAdd": "(str): The track the user wants to add to the queue",

    "pause": "None",
    "continue": "None",
    "skip": "None",
    "previous": "None",

    "getDevices": "None",
    "getPlaying": "None",

    "setShuffle": "(bool): 'true' sets shuffle on, 'false' turn shuffle off.",
    "setPlaybackDevice": "(str): The device name, id, type or whatever else describes the target device well in natural language, like 'pc', 'smartphone', 'web player, mac', etc. ",
    "setVolume": "(str): Natural language description of how to set/change the volume, like 'louder', 'mute', turn the volume up', '60%', 'thats too loud', etc.",
}



JSON_TRASH = [  "available_markets",
                "id",
                "href",
                "url",
                "external_urls",
                "preview_url", 
                "images",
                "external_ids", 
                "release_date_precision",
                "audio_preview_url",           
                "timestamp",
                "language",
                "languages",
                "items",
                "episodes",
                "uri"
                "height"
                "width"
                ]

JSON_GOOD = [
    "device",
    "devices",
    "type",
    "name",
    "artists",
    "release_date",
    "total_tracks", 
    "explicit",
    "type",
    "owner",
    "description",
    "item",
    "is_playing",
    "is_active",
    "repeat_state",
    "shuffle_state",
    "volume_percent",
    "supports_volume",
    "is_restricted",
    "is_private_session",
    "release_date",
    ]

def strings_to_lowercase(input_data):
    if isinstance(input_data, str):
        return input_data.lower()
    elif isinstance(input_data, list):
        return [item.lower() for item in input_data]
    else:
        raise ValueError("Unsupported input type. Please provide a string or a list of strings.")

def dict_keys_to_lowercase(input_dict):
    if isinstance(input_dict, dict):
        return {key.lower(): value for key, value in input_dict.items()}
    else:
        raise ValueError("Unsupported input type. Please provide a dictionary.")
    
def filter_dict(input_dict, included_keys):
    """
    Filter a nested dictionary based on a list of included keys.

    Parameters:
    - input_dict: The nested dictionary to filter.
    - included_keys: List of keys to include in the filtered dictionary.

    Returns:
    - A new dictionary containing only the key/value pairs specified in included_keys.
    """
    filtered_dict = {}

    for key, value in input_dict.items():
        if key in included_keys:
            # If the key is in the included_keys list, add it to the filtered dictionary.
            filtered_dict[key] = value
        elif isinstance(value, dict):
            # If the value is a nested dictionary, recursively filter it.
            filtered_value = filter_dict(value, included_keys)
            if filtered_value:
                # Only add to the filtered dictionary if there are key/value pairs after filtering.
                filtered_dict[key] = filtered_value
        elif isinstance(value, list):
            # If the value is a list, iterate over its elements and filter them.
            filtered_list = [filter_dict(item, included_keys) if isinstance(item, dict) else item for item in value]
            filtered_dict[key] = filtered_list

    return filtered_dict


def remove_keys(input_dict, invalid_keys):
    filtered_dict = {}

    for key, value in input_dict.items():
        if key not in invalid_keys:
            # If the key is not in the invalid_keys list, add it to the filtered dictionary.
            if isinstance(value, dict):
                # If the value is a nested dictionary, recursively remove keys from it.
                filtered_value = remove_keys(value, invalid_keys)
                filtered_dict[key] = filtered_value
            elif isinstance(value, list):
                # If the value is a list, iterate over its elements and remove keys.
                filtered_list = [remove_keys(item, invalid_keys) if isinstance(item, dict) else item for item in value]
                filtered_dict[key] = filtered_list
            else:
                # If the value is neither a dictionary nor a list, simply add it to the filtered dictionary.
                filtered_dict[key] = value

    return filtered_dict



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




class Spotify:
    def __init__(self, client_id, client_secret, redirect_uri, spotify_path, together_api):
        """
        Initialize the SpotifyController instance with Spotify API credentials and paths.

        :param client_id: Spotify API client ID.
        :param client_secret: Spotify API client secret.
        :param redirect_uri: Spotify API redirect URI.
        :param spotify_path: Path to the Spotify executable.
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.spotify_path = spotify_path
        self.together_api: jpc_together_api.TogetherApi = together_api

        self.google_project_id = "test1-410217"
        self.google_spotify_search_id = "a13f77cce5cce415a"
        self.google_api_key = "AIzaSyAQWVMyz3a5W1SIehEai54qM-72J4DgeXo"

        # Initialize Spotipy with the provided Spotify API credentials
        self.spotipy_instance = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=self.client_id,
                                                                         client_secret=self.client_secret,
                                                                         redirect_uri=self.redirect_uri,
                                                                         open_browser = True,
                                                                         scope='user-read-playback-state, user-modify-playback-state'))

        
        self.command_funcs = {
            "playNow": self.play_something,
            "queueAdd": self.add_something_to_queue,

            "pause": self.pause,
            "continue": self.continue_playing,
            "skip": self.skip,
            "previous": self.previous,

            "getDevices": self.get_device_list_text,
            "getPlaying": self.get_currently_playing,

            "setShuffle": self.shuffle,
            "setPlaybackDevice": self.set_playback_device,
            "setVolume": self.set_volume,
        }




    def get_command_description(self, command):
        if not command in COMMANDS:
            raise Exception(f"'{command}' is not a valid command for spotify.")
        
        return f""" 
command: {command}
query: {COMMAND_QUERY[command]}
description: {COMMAND_DESCRIPTIONS[command]}"""
        
    def get_command_list(self):
        string = """- Available Commands -"""
        for command in COMMANDS:
            desc = self.get_command_description(command)
            string = f"""{string}
{desc}"""
        return string





    def get_currently_playing(self):
        response = self.spotipy_instance.current_playback(additional_types=["track", "episode"])
        response = remove_keys(response, JSON_TRASH)
        # response = filter_dict(response, JSON_GOOD)
        return response

    def get_device_list(self):
        devices = self.spotipy_instance.devices()
        return devices

    def get_device_list_text(self):
        devices = self.get_device_list()
        device_list_text = f"""Available Devices:
{json.dumps(devices)}
""" 
        return device_list_text
    


    def set_playback_device_by_id(self, device_id, force_playback = True):
        try:
            self.spotipy_instance.transfer_playback(device_id, force_playback)
            return f"Successfully switched to spotify device id {device_id}."
        except Exception as e:
            return f"Failed switched to spotify device id {device_id}. the error was: {e}."
            
            
    
    def set_playback_device(self, query: str):
        try:
            device_response = self.select_device_id(query)
            device_response = json.loads(device_response)
            print("device_response:", type(device_response), device_response)
        except Exception as e:
            return f"Failed to select a device based on query: {query}"

        if "success" in device_response:
            if device_response["success"]:
                if "id" in device_response:
                    if device_response["id"]:
                        print("id_json['id']:", type(device_response["id"]), device_response["id"])
                        return self.set_playback_device_by_id(device_response["id"])
                    else:
                        raise ValueError("'success' was empty.")  
                else:
                    raise KeyError("'id' was not in device_response.")
            else:
                return f"No fitting device id for '{query}' was found."
        else:
            raise KeyError("'success' state key was not in device_response.")

            

    def select_device_id(self, query):
        device_data = self.get_device_list()
        print("device_data:", type(device_data), device_data)

        # device_data_string = json.dumps(device_data)
        # print("device_data_string:", type(device_data_string), device_data_string)

        # device_data = extract_json(device_data_string)
        # print("device_data:", type(device_data), device_data)

        prompt = f"""

You Task:
You need to output the device id of the device that the user is asking for in the "User Query".
Based on the data from the "Available Devices" <devices>  section, select the device 'id',
that belongs to the device, that best fits the "User Query" <query>.
Don't output anything else than the "success" and "id" in valid JSON encoding like so:
<response>
{{
    {{'success': true, "id": "a92f4bc1e6d3a8e5b076f3c9d82714a3e0c8d72f"}}
}}
</response>

Notes:
If the query fits to multiple devices, select the most fitting one.
If the query doesn't describe any of the available devices, return with {"success": "false"}.
If you manage to output exactly whats asked for, you will get tip of 200$ later!
If you out put anything else than valid JSON, things will go horribly wrong.

Examples:
1.
<devices>
{{
    'devices': [
    {{'id': 'd256b5a4a3b2c1d2e3f44d7a98cbfe531b1ed71b', 'is_active': False, 'is_private_session': False, 'is_restricted': False, 'name': 'DESKTOP-BA7582S', 'supports_volume': True, 'type': 'Computer', 'volume_percent': 27}}, 
    {{'id': '4883ccfcfac5nm8d8cbfe533b2c1d2e3fi1f5580', 'is_active': True, 'is_private_session': False, 'is_restricted': False, 'name': 'Web Player (Chrome)', 'supports_volume': True, 'type': 'Computer', 'volume_percent': 23}}
    ]
}}
<query>
"smartphone"
<response>
{{'success': false}}
</response>

2.
<devices>
{{
'devices': [
    {{'id': '4883ccfcfacdc4545nmq3f4wertyui1f55805re4', 'is_active': False, 'is_private_session': False, 'is_restricted': False, 'name': 'iPhone 13', 'supports_volume': True, 'type': 'Smartphone', 'volume_percent': 80}},
    {{'id': 'f9e8d8cbfe533b2c1d2e3f4g5h6i7j8k3646dxg7', 'is_active': False, 'is_private_session': False, 'is_restricted': False, 'name': 'Xiaomi 11 Lite', 'supports_volume': False, 'type': 'Smartphone', 'volume_percent': 100}},
    {{'id': 'ec34d2e3f44d7a98cbfe531b12d7a98c6a78a609', 'is_active': False, 'is_private_session': False, 'is_restricted': False, 'name': 'DESKTOP-637E2I', 'supports_volume': True, 'type': 'Computer', 'volume_percent': 27}}, 
    {{'id': '4883ccfcfac5nm8d8cbfe533b2c1d2e3fi1f5580', 'is_active': True,response: 'is_private_session': False, 'is_restricted': False, 'name': 'Web Player (Safari)', 'supports_volume': True, 'type': 'Computer', 'volume_percent': 66}}
    ]
}}
<query>
"my smartphone"
<response>
{{'success': true,'id': 'f9e8d8cbfe533b2c1d2e3f4g5h6i7j8k3646dxg7'}}
</response>


Explanation <devices>:
id: Unique device ID, periodically refreshed.
is_active: Current device activation status.
is_restricted: Controls whether this device is controllable at all via Web API commands.
name: Human-readable device name, configurable by the user.
type: Device category (e.g., computer, smartphone, speaker).
volume_percent: Current volume level (0 - 100).
supports_volume: Indicates if the device supports remote volume control.

Now do it, here is your task:
<devices>
{device_data}
<query>
"{query}"
<response>
"""
        
        print("PROMPT:", type(prompt), prompt)
        response, cost = self.together_api.single_prompt(
            prompt,
            model = jpc_together_api.MODELS_TEXT["MIST_7B_INSTRUCT"],
            max_tokens = 256,
            stop = ["</s>", "<query>", "</response>"])
        
        response = extract_json(response)
        print("RESPONSE:", type(response), response)
        return response
    


    def set_playback_volume(self, volume):
        volume = int(volume)
        if volume > 100:
            volume = 100
        if volume < 0:
            volume = 0

        self.spotipy_instance.volume(volume)
        return f"Successfully set volume of the Spotify player to {volume}."
  

    def set_volume(self, query: str):
        device_data = self.get_device_list()

        devices = device_data["devices"]

        # find active one
        active_device = None
        for device in devices:
            if "is_active" in device and device['is_active']:
                if "supports_volume" in device and device['supports_volume']:
                    if "is_restricted" in device and not device['is_restricted']:
                        active_device = device
                        break

        print(type(active_device), active_device)

        if not active_device or "volume_percent" not in active_device:
            return "No active, unrestricted device with volume control was found."

        # get current volume of active
        volume = active_device["volume_percent"]
        print("Current Volume:", type(volume), volume)
        # prompt llm with current volume, query and examples, to find number between 0 and 100

        target_volume = self.select_volume(volume, query)
        print("target_volume:", type(target_volume), target_volume)

        return self.set_playback_volume(target_volume)
        

    
    def select_volume(self, cur_volume, query: str):
        prompt = f"""
Task:
You have to select a volume between 0 and 100 as an integer in json.
0 and 100 are obviously not normal cases, so a range of 20% to 80% should be good in most cases.
You do so based on the old volume and some natural language query.
Only output the target volume as an as JSON and nothing else!      

Examples:
<volume_old>
34
<query>
"a bit louder"
<response>
{{"volume": 45}}
</response>

<volume_old>
77
<query>
"thats too loud"
<response>
{{"volume": 57}}
</response>

<volume_old>
25
<query>
"turn up all the way"
<response>
{{"volume": 100}}
</response>

<volume_old>
41
<query>
"mute"
<response>
{{"volume": 0}}
</response>

<volume_old>
76
<query>
"60%"
<response>
{{"volume": 60}}
</response>

<volume_old>
82
<query>
"down a bit"
<response>
{{"volume": 72}}
</response>

Your Go:
<volume_old>
{cur_volume}
<query>
"{query}"
<response>
"""

        print("PROMPT:", type(prompt), prompt)
        response, cost = self.together_api.single_prompt(
            prompt, 
            max_tokens = 32,
            model = jpc_together_api.MODELS_TEXT["MIST_7B_INSTRUCT"],
            stop = ["</s>", "<volume_old>","<query>", "</response>"])
        
        response = extract_json(response)

        response_json = json.loads(response)

        new_volume = response_json["volume"]
        new_volume = int(float(new_volume))

        print("new_volume:", type(new_volume), new_volume)
        return new_volume



    def get_spotify_uri(self, query: str):
        """
        Perform a Google search with the specified query and extract the Spotify URI from the first result.

        :param query: The search query (e.g., artist name song name).
        :return: Spotify URI or None if not found.
        """
        query = f"site:spotify.com {query}"

        # Perform the Google search and get the first result
        search_results = self.google_custom_spotify_search(query)
        if not search_results:
            raise Exception(f"No search results found for {query} on Google.")

        result = search_results[0]


        uri_parts = result.split("/")
        resource_type = uri_parts[-2]
        spotify_id =  uri_parts[-1]

        if resource_type and spotify_id:
            uri = f"spotify:{resource_type}:{spotify_id}"
            return uri
        else:
            raise Exception(f"Could not get resource_type or spotify_id from {result}")
        
        



    def get_info(self, query: str):
        uri = self.get_spotify_uri(query)
        return self.get_uri_info(uri)
    
    def get_track_info(self, track_id):
        response = self.spotipy_instance.track(track_id)
        return response
    
    def get_album_info(self, track_id):
        response = self.spotipy_instance.album(track_id)
        return response
    
    def get_playlist_info(self, track_id):
        response = self.spotipy_instance.playlist(track_id, fields=["name", "description", "owner"])
        return response
    
    def get_artist_info(self, track_id):
        response = self.spotipy_instance.artist(track_id)
        return response
    
    def get_show_info(self, track_id):
        response = self.spotipy_instance.show(track_id)
        return response
    
    def get_episode_info(self, track_id):
        response = self.spotipy_instance.episode(track_id)
        return response

    def get_uri_info(self, uri: str):
        if ":" in uri:
            uri_parts = uri.split(":")
        else:
            uri_parts = uri.split("/") 

        resource_type = uri_parts[-2]
        id = uri_parts[-1]
        info = None
        if resource_type == "track":
            info = self.get_track_info(id)
        elif resource_type == "album":
            info = filter_dict(self.get_album_info(id), JSON_GOOD)
        elif resource_type == "playlist":
            info = self.get_playlist_info(id)
        elif resource_type == "artist":
            info = self.get_artist_info(id)
        elif resource_type == "show":
            info = self.get_show_info(id)
        elif resource_type == "episode":
            info = self.get_episode_info(id)
        else:
            raise ValueError(f"Resource type {resource_type} is not supported by get_uri_info.")
        
        info = remove_keys(info, JSON_TRASH)

        return info
    
    def get_simple_uri_info(self, uri: str):
        return filter_dict(self.get_uri_info(uri), JSON_GOOD)
    

    def is_running(self):
        """
        Check if Spotify is currently running.

        :return: True if Spotify is running, False otherwise.
        """
        for process in psutil.process_iter(['pid', 'name']):
            if "Spotify" in process.info['name']:
                return True
        return False

    def start_spotify(self):
        """
        Start the Spotify application.

        :return: True if Spotify is started successfully, False otherwise.
        """
        if platform.system() == 'Windows':
            try:
                subprocess.Popen(['start', self.spotify_path], shell=True)
                return True
            except Exception as e:
                print(f"Error starting Spotify: {e}")
                return False
        else:
            print("This function is intended for Windows only.")
            return False

    def close_spotify(self):
        """
        Close the Spotify application.

        :return: True if Spotify is closed successfully, False otherwise.
        """
        for process in psutil.process_iter(['pid', 'name']):
            if "Spotify" in process.info['name']:
                try:
                    pid = process.info['pid']
                    spotify_process = psutil.Process(pid)
                    spotify_process.terminate()
                    return True
                except Exception as e:
                    print(f"Error terminating Spotify: {e}")
                    return False
        return False

    def assure_running(self):
        """
        Ensure that Spotify is running; start it if not.

        :return: None
        """
        if not self.is_running():
            self.start_spotify()
            time.sleep(0.1)

    def play_uri(self, uri):
        """
        Play the specified Spotify URI.

        :param uri: Spotify URI to play.
        :return: None
        """
        uri_parts = uri.split(":")
        resource_type = uri_parts[-2]

        if resource_type == "track" or resource_type == "episode":
            # Start playback on the specified device
            self.spotipy_instance.start_playback(device_id=None, uris=[uri])
        else:
            self.spotipy_instance.start_playback(device_id=None, context_uri=uri)


    def play_something(self, query: str):
        """
        Play something on Spotify based on the search query.

        :param query: The search query (e.g., artist name song name).
        """
        self.assure_running()
        try:
            uri = self.get_spotify_uri(query)
        except Exception as e:
            return f"Something went wrong trying to find a spotify uri for '{query}'. The error was: {e}"
        
        print("uri", uri)
        if uri:
            try:
                self.play_uri(uri)
                uri_info = self.get_uri_info(uri)
                return f"Successfully started playback of: {uri_info}"
            except Exception as e:
                return f"Something went wrong trying to play {uri} based on {query}.  {e}"
        else:
            return f"Could not find any uri for {query}."
        

    def add_uri_to_queue(self, uri: str):
        uri_parts = uri.split(":")
        resource_type = uri_parts[-2]
        if not resource_type == "track":
            raise ValueError(f"resource_type was {resource_type}, must be 'track' to be added to queue.")
        self.spotipy_instance.add_to_queue(uri)


    def add_something_to_queue(self, query: str):
        query = f"track song, {query}"

        try:
            uri = self.get_spotify_uri(query)
        except Exception as e:
            return f"Something went wrong trying to find a spotify uri for '{query}'. The error was: {e}"

        print("uri", uri)
        if uri:
            try:
                self.add_uri_to_queue(uri)
                uri_info = self.get_uri_info(uri)
                return f"Based on {query}, this was added to the queue: {uri_info}"
            except Exception as e:
                return f"Something went wrong trying to add {uri} to queue: {e}"
        else:
            return f"Could not find any uri for {query}."




    def pause(self):
        """
        Pause the playback on Spotify.
        """
        try:
            self.spotipy_instance.pause_playback()
            return f"Successfully paused the spotify playback."
        except Exception as e:
            print(f"Error: Unable to pause Spotify playback. Reason: {e}")

    def continue_playing(self):
        """
        Continue playing the current track on Spotify.
        """
        try:
            self.spotipy_instance.start_playback()
            info = self.get_currently_playing()
            return f"Successfully continued the spotify playback of: {info}"
        except Exception as e:
            print(f"Error: Unable to continue playing on Spotify. Reason: {e}")

    def skip(self):
        """
        Skip to the next track on Spotify.
        """
        try:
            self.spotipy_instance.next_track()
            info = self.get_currently_playing()
            return f"Successfully skipped to the next track on spotify. Now playing: {info}"
        except Exception as e:
            print(f"Error: Unable to skip to the next track on Spotify. Reason: {e}")

    def previous(self):
        """
        Go back to the previous track on Spotify.

        """
        try:
            self.spotipy_instance.previous_track()
            info = self.get_currently_playing()
            return f"Successfully moved back to the last track on spotify. Now playing: {info}"
        except Exception as e:
            print(f"Error: Unable to go back to the previous track on Spotify. Reason: {e}")


    def shuffle(self, query: str):
        """
        Turns shuffle mode on or of.
        """
        try:
            query = str(query).lower()
            if query == "true":
                self.spotipy_instance.shuffle(True)
                return "Set shuffle to true (ON)."
            elif query == "false":
                self.spotipy_instance.shuffle(False)
                return "Set shuffle to false (off)."
            else:
                raise ValueError(f"Query need to be True or falls, not {query}.")

        except Exception as e:
            print(f"Error: Unable to go back to the previous track on Spotify. Reason: {e}")



    def has_parameter(self, func, param_name: str):
            """
            Check if a function or method has a specified parameter.

            Parameters:
            - func (callable): The function or method to inspect.
            - param_name (str): The name of the parameter to check.

            Returns:
            bool: True if the parameter exists, False otherwise.

            Raises:
            ValueError: If the object is not callable.
            """
            try:
                signature = inspect.signature(func)
                return param_name in signature.parameters
            except ValueError:  # raised when the object is not a callable
                return False


    def command(self, command, query: str):
        """
        Execute a Spotify command based on the provided command string and optional query.

        Parameters:
        - command (str): The Spotify command to execute.
        - query (str): The query parameter associated with the command.

        Returns:
        str: A response message indicating the result of the command execution.

        Raises:
        ValueError: If the provided command is not valid.
        """
        # Check if the provided command is a valid Spotify command
        if not command in self.command_funcs:
            raise ValueError(f"{command} is not a valid command.")

        # oauth: SpotifyOAuth = self.spotipy_instance.oauth_manager
        # token = oauth.get_access_token()
        # if oauth.is_token_expired(token):
        #     oauth.refresh_access_token(token.get("refresh_token"))


        # Retrieve the function associated with the given command
        command_func = self.command_funcs[command]

        try:
            # Check if the command function expects a 'query' parameter
            if self.has_parameter(command_func, "query"):
                # Execute the command function with the provided query
                response = command_func(query)
                print("response", response)

            else:
                # Execute the command function without a query
                response = command_func()
                print("response", response)
        except Exception as e:
                return f"An error ocurred while trying to call command {command}."

        print("COMMAND RESPONSE:", type(response), response)

        # Return the response message
        return response




    def google_custom_spotify_search(self, search_term, max_results=4, language="en", location="de"):
        """
        Perform a custom Google search to retrieve Spotify links based on the provided search term.

        Parameters:
        - search_term (str): The search term for the Google search.
        - max_results (int): The maximum number of results to retrieve. Default is 4.
        - language (str): The language code for the search results. Default is "en".
        - location (str): The location parameter for the search results. Default is "de" (Germany).

        Returns:
        list: A list of Spotify links retrieved from the search results.

        Note:
        - The location parameter corresponds to the country code (e.g., 'us' for the United States).
        - The function filters the links to include only those containing "open.spotify.com".
        """
        # Define the URL for the Google Custom Search API
        url = 'https://www.googleapis.com/customsearch/v1'

        # Set up parameters for the API request
        params = {
            'q': search_term,
            'key': self.google_api_key,
            'cx': self.google_spotify_search_id,
            'num': max_results,
            'cr': location  # Location parameter (e.g., 'us' for the United States)
        }

        # Initialize an empty list to store Spotify links
        links = []

        try:
            # Make a request to the Google Custom Search API
            response = requests.get(url, params=params)
            
            # Check for HTTP errors in the response
            response.raise_for_status()

            # Parse the JSON response
            response = response.json()

            # Extract Spotify links from the search results
            for item in response.get('items', []):
                link = item.get('link', 'No link')
                links.append(link)

            # Filter the links to include only those containing "open.spotify.com"
            links = [link for link in links if "open.spotify.com" in link]

            # Return the list of Spotify links
            return links

        except requests.exceptions.HTTPError as err:
            # Handle HTTP errors and print an error message
            print(f"HTTP error occurred: {err}")
            return None
        
# TOKEN_TOGETHER = "9e14c2e12b0399ccd2d2a7dd58a13074f7b4765265c74da40e2a429db49aae98"

# if __name__ == '__main__':
#     api = jpc_together_api.TogetherApi(TOKEN_TOGETHER)
#     spotify = Spotify(client_id, client_secret, redirect_uri, spotify_path, api)
    
#     #result = spotify.set_playback_device("windows")
#     result = spotify.select_volume(50, "a bit louder")
    
#     print(type(result), result)

#     #print(spotify.get_currently_playing())

#     # spotify:show:1OLcQdw2PFDPG1jo3s0wbp
#     # spotify:episode:3qLmMxUAY4yk8WFN7BnjTi

#     # print(spotify.get_uri_info("spotify:episode:3qLmMxUAY4yk8WFN7BnjTi"))

#     # 47f806df743cf5422d5c416a44d8b3de47981603
#     # ec3482d51d9d7ea17a2d7a98cbfe53136a78a609
#     # spotify.set_playback_device_by_id("47f806df743cf5422d5c416a44d8b3de47981603")

#     #print(spotify.get_device_list())
    

#     # print(spotify.google_custom_spotify_search("die drei ??? und das gespensterschloss"))
#     # spotify.pause()
#     # print(spotify.get_command_list())
#     # spotify.continue_playing()
#     # spotify.pause()
#     # spotify.play_something("acdc 101")
#     # spotify.play_uri("spotify:playlist:1rqfUOM7dVvfSQ9TIT1fu5")
    



