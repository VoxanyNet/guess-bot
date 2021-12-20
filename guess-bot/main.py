import json
import os
import threading
import shutil
import time
import datetime
import random
from collections import defaultdict
import discord
from discord.ext import commands
from discord.ext import tasks
import statistics
import parse

# class MessageGui:
#     def __init__(self,user_id):
#         self.user_id = user_id

async def reset_reaction(emoji_to_remove, message):

    users_to_remove = []

    # This creates a list of the users who reacted that doesn't include the bot
    for _reaction in message.reactions:
        if _reaction.emoji == emoji_to_remove:
            async for user in _reaction.users():
                # We only want to remove reactions from other users
                if user.id != message.author.id:
                    users_to_remove.append(user)

    for user_id in users_to_remove:
        await message.remove_reaction(emoji_to_remove,user)

class PageHandler():
    def __init__(self, owner_id,user_stats,creation_time):
        self.OWNER_ID = owner_id
        self.STATS = user_stats
        self.CREATION_TIME = creation_time

        # The range ceiling defines the highest ranking word we want to retrieve
        self.range_ceiling = 10

    # This needs to be a seperate method because __init__ doesn't support asyncio
    async def setup(self,message):
        # Adds the initial emoji for interfacing
        for emoji in ["🔼", "🔽"]:
            await message.add_reaction(emoji)

    async def update(self, reaction, user):

        # If the user who reacted is the bot, we ignore it
        if user.id == bot.user.id:
            pass

        # If the user who reacted is not the GUI owner, we ignore it
        if user.id != self.OWNER_ID:
            pass

        else:

            match reaction.emoji:
                case "🔼":
                    # Lower the range ceiling
                    self.range_ceiling -= 10

                case "🔽":
                    # Raise the range ceiling
                    self.range_ceiling += 10

                # If there are no emojis we have responses for, we do nothing.
                case _:
                    return

            # Returns a tuple with the range of results we want. We want 10 results, so we just subtract 10 from the range ceiling
            lookup_range = (self.range_ceiling - 10, self.range_ceiling)

            result = self.STATS.top_usage(lookup_range)

            #source = inspect.getsource(reaction.message.edit)

            await reaction.message.edit(content = result)

        # Resets all the interaction emojis to one
        for emoji in ["🔼", "🔽"]:
            await reset_reaction(emoji,reaction.message)

""" TODO

# Add statistics based on how many guesses you got right
# Add points
# Add bonuses for guessing multiple in a row

"""

def load_messages(data_path):
    server_data = {}

    for json_file in os.listdir(data_path):

        if ".json" not in json_file:
            continue
            # This is here because I needed to put a .gitignore file in this directory
            # I was very confused why my JSON wasn't loading
            # It was trying to load a .gitignore

        guild_id = json_file.split(".")[0]

        # For every json file in the server_data folder, load
        # data then add to server_data dictionary
        with open(f"{data_path}/{json_file}","r") as file:
            data = json.load(file)

        message_count = len(data["active_messages"])

        print(f"Loading {guild_id}.json with {message_count} messages")

        server_data[guild_id] = data

    return server_data

def download_messages(channel_id,token,output_directory):
    exit_code = os.system(f"dotnet libraries/chat_exporter/DiscordChatExporter.Cli.dll export -t {token} -b -c {channel_id} -f Json -o {output_directory}/%g.json")

    print(f"Finished downloading messages for {channel_id}")

BOT_TOKEN = "ODk5MDQxMzI3MzQwMjA0MDYy.YWs_ew.2VT5Bi0a3Xqx4wJ_8hYbM0OmPYA"
DATA_PATH = "server_data"
BACKUP_PATH = "raw_data_backup"
EMOJI_TABLE = [
    "1️⃣",
    "2️⃣",
    "3️⃣",
    "4️⃣"
]

# STARTUP ROUTINE
if os.path.exists("sync_times.json") != True:
    file = open("sync_times.json","w")
    json.dump({},file)
    file.close()

# Change this to be more modular
parse.filter_json("raw_data",BACKUP_PATH)

bot = commands.Bot(command_prefix = "!")

bot.server_data = load_messages(DATA_PATH)
bot.prompts = defaultdict(list)
bot.gui_sessions = {}
bot.threads = {}

time_start = time.time()
for guild_id, guild_data in bot.server_data.items():
    if "stats" not in guild_data:
        bot.server_data[guild_id]["stats"] = parse.generate_stats(guild_data)

        with open(f"{DATA_PATH}/{guild_id}.json","w") as file:
            json.dump(bot.server_data[guild_id],file, sort_keys = True, indent = 4)

time_elapsed = time.time() - time_start

print(f"Took {time_elapsed} seconds to generate stats")

@bot.event
async def on_ready():
    print("All done!")

@bot.command()
async def get_user(ctx,user_id):
    name = await bot.fetch_user(int(user_id))

    await ctx.send(name)

@bot.command()
async def guss(ctx):
    await ctx.send("https://static.wikia.nocookie.net/breakingbad/images/a/ab/BCS_S3_GusFringe.jpg/revision/latest?cb=20170327185354")

@bot.command()
async def gus(ctx):
    await ctx.send("https://cdn.discordapp.com/attachments/769958337474461737/910308645424746506/IMG_0005.jpg")

@bot.command()
async def stats(ctx, stat_type, keyword = None, user_id = None):

    if user_id == None:
        user_id = str(ctx.author.id)

    guild_id = str(ctx.guild.id)

    # Create user stats object
    user_data = bot.server_data[guild_id]["stats"][user_id]

    user_stats = statistics.User(user_data)

    match stat_type:
        case "count":

            if keyword == None:
                result = user_stats.message_count()

            else:
                result = user_stats.word_count(keyword)

            await ctx.send(result)

        case "top":
            # Create GUI message then add it to dictionary
            result = user_stats.top_usage((0,10))

            message = await ctx.send(result)

            # Creates PageHandler object that will be updated every
            # time a reaction is added to its corresponding message
            page_gui = PageHandler(ctx.author.id,user_stats,time.time())

            # This needs to be used because __init__ doesnt support asyncio
            await page_gui.setup(message)

            # Adds the PageHandler object the dictionary of GUI objects
            bot.gui_sessions[message.id] = page_gui

        case _:
            result = "Invalid statistic"

            await ctx.send(result)

@bot.command()
async def desync(ctx):

    guild_id = str(ctx.guild.id)

    try:
        os.remove(f"{DATA_PATH}/{ctx.guild.id}.json")
        os.remove(f"{BACKUP_PATH}/{ctx.guild.id}.json")

        del bot.server_data[guild_id]

    except FileNotFoundError:
        await ctx.send("Could not find any message data for this server")

    except:
        await ctx.send("Failed to remove message data.\nContact Voxany#4162 for support")
        raise

    else:
        await ctx.send("Successfully removed messsage data!")

@bot.command()
async def sync(ctx):

    # We need the guild id as a str because json doesnt support int keys
    guild_id = str(ctx.guild.id)

    if os.path.exists("sync_times.json") != True:
        file = open("sync_times.json","w")
        json.dump({},file)
        file.close()

    with open("sync_times.json", "r") as file:
        sync_data = json.load(file)
        print(sync_data)

    # Check to make sure they haven't synced recently
    if guild_id in sync_data:

        print("data found!")

        last_sync = sync_data[guild_id]

        time_remaining = (last_sync + 259200) - time.time()

        print(time_remaining)

        if time_remaining > 0:

            converted_time = datetime.timedelta(seconds = time_remaining)

            await ctx.send(f"You must wait 3 days between channel syncing.\nYou may sync again in **{converted_time.days + 1} day(s).**")

            return

    await ctx.send(f"Syncing guess messages with channel <#{ctx.channel.id}>\n**This will take a while!**")

    new_thread = threading.Thread(target = download_messages, args = (ctx.channel.id,BOT_TOKEN,"raw_data"), daemon = True)

    bot.threads[ctx.channel.id] = new_thread

    bot.threads[ctx.channel.id].start()


    sync_data[guild_id] = time.time()

    with open("sync_times.json", "w") as file:
        json.dump(sync_data,file)

@bot.command()
async def guess(ctx):
    guild_id = str(ctx.guild.id)

    if guild_id not in bot.server_data:
        await ctx.send("No message data found! Sync messages with !sync")
        return

    data = bot.server_data[guild_id]

    # Messages are pre-filtered now!
    message = random.choice(data["active_messages"])

    # Add the correct answer to the list of choices
    choices = [message["author"]["id"]]

    # We use this to generate wrong answers
    users = data["valid_users"]

    # First we shuffle all the users so don't always get the same possible answers
    random.shuffle(users)

    for user in users:

        if user in choices: # Make sure we aren't adding the correct user twice
            continue

        choices.append(user)

        if len(choices) == 4: # We only want to generate up to 4 possible answers
            break

    # Shuffles the list so the right answer won't always be first
    random.shuffle(choices)

    print(choices)

    # We get the emoji that correlates to the correct answer
    # correct_emoji = EMOJI_TABLE[choices.index(message["author"]["name"])]

    # Generates the actual string of choices that will be put in the message
    choices_string = ""

    for number, choice in enumerate(choices):
        # Converts user ID to the name
        user = await bot.fetch_user(choice)

        choices_string += f"{EMOJI_TABLE[number]}: {user.name}\n"

    prompt_message = await ctx.send(f"Who sent:\n||Author||: {message['content']}\n\n{choices_string}\n")

    for emoji in EMOJI_TABLE[:len(choices)]: # We only want to add an emoji for every possible answer. So if there are only 3 possible answers we only get 3 emoji choices
        await prompt_message.add_reaction(emoji)

    # Saves the message in the prompts dictionary
    bot.prompts[guild_id].append(
        {
            "prompt_message": prompt_message,
            "guess_message": message,
            "choices": choices
        }
    )

@bot.command()
async def debug(ctx):
    await ctx.send(f"""**CTX guild ID**: {ctx.guild.id}\n
    **CTX author ID**: {ctx.message.author.id}\n""")

    print(ctx.message.content)

@tasks.loop(seconds = 5)
async def download_checker():

    # A temporary list of threads that we need to delete from the dictionary once we are done iterating
    to_delete = []

    for channel_id, thread in bot.threads.items():
        if thread.is_alive():
            pass

        # If the download has finished we can filter and load the new data
        # We also notify the channel that the download has finished
        else:
            parse.filter_json("raw_data",DATA_PATH)
            bot.server_data = load_messages(DATA_PATH)

            for guild_id, guild_data in bot.server_data.items():
                if "stats" not in guild_data:
                    bot.server_data[guild_id]["stats"] = parse.generate_stats(guild_data)

                    with open(f"{DATA_PATH}/{guild_id}.json","w") as file:
                        json.dump(bot.server_data[guild_id],file, sort_keys = True, indent = 4)


            notify_channel = await bot.fetch_channel(channel_id)

            await notify_channel.send("Successfully synced messages!")

            to_delete.append(channel_id)

    for channel_id in to_delete:
        del bot.threads[channel_id]

@tasks.loop(seconds = 3)
async def prompt_checker():
    for guild, prompt_list in bot.prompts.items():
        for prompt in prompt_list:
            prompt_message = prompt["prompt_message"] # We use this message to check for new reactions. Discord.py message object
            guess_message = prompt["guess_message"] # We need all the data about the message they are trying to guess. JSON message object
            choices = prompt["choices"] # List of all possible choices. We use this to convert the numbered reaction to actual username

            correct_choice = choices.index(guess_message["author"]["id"])

            channel_id = prompt_message.channel.id
            message_id = prompt_message.id

            # We update the message object to get new reactions
            channel = await bot.fetch_channel(channel_id)
            message = await channel.fetch_message(message_id)

            # All the answers and who answered what
            guesses = {}

            for reaction in message.reactions:
                # If the reaction isnt related to an answer, we skip it
                if reaction.emoji not in EMOJI_TABLE:
                    continue
                else:
                    choice = EMOJI_TABLE.index(reaction.emoji) # Convert reaction emoji back into a numbered choice

                async for user in reaction.users():
                    # Check to make sure that the reaction isnt from the bot
                    if user.name == bot.user.name:
                        continue

                    # Make an entry for the user if they dont have one
                    # We allow users to react multiple times, but we check later and notify them
                    if user.name not in guesses.keys():
                        guesses.update(
                            {user.name: [choice]}
                        )
                    else:
                        guesses[user.name].append(choice)


            # Parses the list of reactions to determine if any got it right
            if guesses != {}:

                # List of users who guessed correctly
                correct_users = []

                # This won't activate unless there are reactions
                for user, guesses in guesses.items():
                    if len(guesses) > 1:
                        await channel.send(f"{user}, you may not answer more than once!")
                        continue

                    # User guesses correctly
                    if correct_choice in guesses:
                        correct_users.append(user)

                # Formats the message for message according to how many users guessed correctly
                if len(correct_users) == 0:
                    formatted_user_list = "Nobody"

                if len(correct_users) == 1:
                    formatted_user_list = correct_users[0]

                elif len(correct_users) > 1:
                    formatted_user_list = f"{', '.join(correct_users[:-1])} and {correct_users[-1]}"

                new_message_content = message.content.replace("||Author||",f"**{guess_message['author']['name']}**")
                new_message_content += f"\n\n**{formatted_user_list} guessed correctly.**" # Add timestamp

                await message.edit(content = new_message_content)
                await message.clear_reactions()

                # Copy message to the list of inactive messages
                bot.server_data[guild]["inactive_messages"].append(guess_message)

                # Removes message from the list of active questions
                bot.server_data[guild]["active_messages"].remove(guess_message)

                with open(f"server_data/{guild}.json","w") as file:
                    json.dump(bot.server_data[guild],file,sort_keys=True, indent=4)
                    print("Saved new updated server data")

                # Deletes the prompt from list of active prompts
                bot.prompts[guild].remove(prompt)

@bot.event
async def on_reaction_add(reaction, user):

    message_id = reaction.message.id

    if message_id in bot.gui_sessions:

        gui_session = bot.gui_sessions[message_id]
        await gui_session.update(reaction,user)

    else:
        pass

prompt_checker.start()
download_checker.start()

bot.run(BOT_TOKEN)
