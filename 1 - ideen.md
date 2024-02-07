

# Agent
- restore multi step thought
- fix tool selection prompt to allow only doing part of te problem

# Audio Speech Module
- plays through windows on specified device, but can also be used to send audio replies via telegram
- 



# Tools
## New Tool ideas
- app/program manager
    - start stuff
    - end stuff
    - find out if something is open
- browser
    - search basic idea
        - for y queries find x results each,
        - get html text sections 
        - make 

- code writer / interpreter
    - module that writes code based on query
    - module that executes code
    - module that takes code and error and writes new code
    - can be called separately or in a loop

- image generation


## key setting and checking
- check if need api's are inited or not on the fly, check if key exists, if not, ask for key setting via prompt
- maybe simple context interface
- maybe nice llm tool

## Spotify
- get queue
- dynamical creating queue based on user request using llm.
- create and manage playlists
- crete playlist/queue from recommendations
- replace google search with spotify search
- just search for stuff without adding/starting it


## Windows Media control
- Buttons
    - media_play_pause      VK_MEDIA_PLAY_PAUSE
    - next                  VK_MEDIA_NEXT_TRACK
    - previous              VK_MEDIA_PREV_TRACK
    - stop                  VK_MEDIA_STOP
    - mute                  VK_VOLUME_MUTE
- Volume
    - get volume for app or system
    - set volume smart, dynamic using llm


- ALL COMMANDS TO LOWER CASE !!!
- Character / token limits for all llm calls
- proper tracking and logging of costs of full agent calls and sessions
- get currently playing only return meta data atm... bad
- handlers for message types that include attachments, images, file, contacts etc. 

- prompt user to confirm things: https://developers.sinch.com/docs/conversation/message-types/choice-message/#telegram

