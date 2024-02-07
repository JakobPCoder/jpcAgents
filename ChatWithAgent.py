
import os
from pathlib import Path
import json

from jpcAgents import Agent
from jpcChat import Chat
from jpc_openai_api import OpenApi
from jpc_together_api import TogetherApi

import logging


import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters



script_directory = os.path.dirname(os.path.abspath(__file__))

SAVE_MODE = False
TOKEN_TELEGRAM = "6839820053:AAF2cGAYvEUumIdDGQd9lSalEN0cXQTAbs4"
TOKEN_TOGETHER = "9e14c2e12b0399ccd2d2a7dd58a13074f7b4765265c74da40e2a429db49aae98"
TOKEN_OPENAI = "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"

# logging.basicConfig(
#     format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
#     level=logging.INFO
# )


def read_config_entry(key, file_path):
    try:
        with open(file_path, 'r') as file:
            data = json.load(file)
            if key in data:
                return data[key]
            else:
                return None  # Key not found in the JSON file
            
    except FileNotFoundError:
        return None  # File not found
    except json.JSONDecodeError:
        return None  # JSON parsing error


class ChatWithAgent:
    def __init__(self, chat_ref, agent_ref):
        self.chat: Chat = chat_ref
        self.agent: Agent = agent_ref

        self.telegram_app = ApplicationBuilder().token(TOKEN_TELEGRAM).build()
        self.config_path = os.path.join(os.path.dirname(__file__), "config", "config.json")
      
        # on different commands - answer in Telegram
        self.telegram_app.add_handler(CommandHandler("start", self.start))
        self.telegram_app.add_handler(CommandHandler("stop", self.stop))
        self.telegram_app.add_handler(CommandHandler("reset", self.reset))
        self.telegram_app.add_handler(CommandHandler("help", self.help_command))

        self.telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_text))
        self.telegram_app.add_handler(MessageHandler(filters.VOICE, self.handle_audio))

        self.is_running = False


    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Send a message when the command /start is issued."""
        if self.is_running:
            await update.message.reply_text('JARVIS is already Online!')
        else:
            self.start_chat()
            await update.message.reply_text('JARVIS Online!')

    async def stop(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Send a message when the command /stop is issued."""
        self.stop_chat()
        await update.message.reply_text('JARVIS Offline.')

    async def reset(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        await update.message.reply_text('JARVIS Offline')
        await update.message.reply_text('Chat history removed...')
        self.stop_chat()
        self.chat.messages.clear()
        self.agent.restart()
        self.start_chat()
        await update.message.reply_text('JARVIS Online!')

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Send a message when the command /help is issued."""

        text = f"""
*{self.agent.name} Help Screen*
Welcome to the chat interface of {self.agent.name}\!
{self.agent.name} is a conversational AI assistant that can control...

List of available commands:
/help, this.
/start, start the agent.
/reset, restarts the agent, deleting chat history.
/stop, stops the agent, it will no longer answer until start or reset is used.

List of tools {self.agent.name} can use:
{self.agent.get_tool_descriptions()}
        """



        await update.message.reply_text(text)


    async def respond(self, text, update: Update, context: ContextTypes.DEFAULT_TYPE):
        self.chat.send_message(text)

        if SAVE_MODE:
            try:
                agent_response, cost = self.agent()  
            except Exception as e:
                agent_response, cost = (f"An unhandled error occurred: {e} ", 0)
        else:  # for debugging
            agent_response, cost = self.agent()  

        print(f"Agent Call Cost: {cost * 100} $Cent.")

        print(f"{self.agent.name}: ", agent_response)
        self.chat.send_message(agent_response, role="assistant")
        await update.message.reply_text(agent_response)



    async def handle_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not self.is_running:
            return
        user = update.effective_user
        user_name = user.mention_markdown_v2()
        text = update.message.text
        await self.respond(text, update, context)

    async def handle_audio(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle incoming audio messages."""
        if not self.is_running:
            return
        
        in_voice_enable = read_config_entry("inVoiceEnable", self.config_path)
        print(f"inVoiceEnable value from config: {in_voice_enable}")  # Debugging message
        if not bool(in_voice_enable.lower() == "true"):
            await update.message.reply_text(f"""Audio Transcription is turned off, so i can't understand voice message at this time.
If you want to enable this feature, please set "inVoiceEnable" to "true" in the config or ask me to do so for you via text.""")
            return
        
        user = update.effective_user
        audio_message = update.message.voice
        id = audio_message.file_id

        if audio_message:  
            audio_file = await context.bot.get_file(id)
            file_path = Path(os.path.join(script_directory, "voice.ogg"))
            await audio_file.download_to_drive(file_path)
            text = self.agent.openaiApi.speech_to_text(file_path)  # Use await when calling an async method

            # Your logic to handle the audio message goes here

            # Respond to the user (you can customize this part)
            inVoiceTranscriptionEnable = read_config_entry("inVoiceTranscriptionEnable", self.config_path)
            print(f"inVoiceTranscriptionEnable value from config: {in_voice_enable}")  # Debugging message
            if bool(inVoiceTranscriptionEnable.lower() == "true"):
                await update.message.reply_text(f"Audio Transcription: {text}")
            await self.respond(text, update, context)


    def start_chat_loop(self):
        self.start_chat()
        self.telegram_app.run_polling()        

    def start_chat(self):
        self.is_running = True
        print("JARVIS Online.")

    def stop_chat(self):
        self.is_running = False
        print("JARVIS Offline.")



if __name__ == "__main__":

    # Create an instance of the Chat class
    chat_instance = Chat()
    
    # Create an instance of the Agent tell class (You may need to provide necessary parameters)
    agent_instance = Agent(
        TOKEN_TOGETHER,
        TOKEN_OPENAI,
        role="assistant", 
        name = "JARVIS", 
        jpc_chat_ref = chat_instance, 
        max_thought_steps = 1, 
        recent_chat_memory = 16)
    
    # Create an instance of ChatWithAgent and start the conversation
    chat_with_agent = ChatWithAgent(chat_instance, agent_instance)

    chat_with_agent.start_chat_loop()
