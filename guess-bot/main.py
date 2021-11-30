import json
import os
import threading
import shutil
import time
import datetime
import random
import discord
from discord.ext import commands
from discord.ext import tasks


# TODO

# Add statistics based on how many guesses you got right
# Add statistics based on many messages someone sent overall
# Make message downloading threaded
# Add points
# Add bonuses for guessing multiple in a row

BOT_TOKEN = "ODk5MDQxMzI3MzQwMjA0MDYy.YWs_ew.4K_rur8qREegxMYwdqIJfqfNceM"

if os.path.exists("sync_times.json") != True:
    file = open("sync_times.json","w")
    json.dump({},file)
    file.close()

EMOJI_TABLE = [
    "1️⃣",
    "2️⃣",
    "3️⃣",
    "4️⃣"
]

bot = commands.Bot(command_prefix = "!")

bot.prompts = {}
bot.threads = {}

def load_messages(data_path):
    bot.server_data = {}

    for json_file in os.listdir(data_path):

        guild_id = json_file.split(".")[0]

        print(guild_id)

        # For every json file in the server_data folder, load
        # data then add to server_data dictionary
        file = open(f"{data_path}/{json_file}","r")
        data = json.load(file)
        file.close()

        message_count = len(data["active_messages"])

        print(f"Loading {guild_id}.json with {message_count} messages")

        bot.server_data.update(
            {
                guild_id : data
            }
        )
        #else:
            #bot.server_data[guild_id].append(data)

# This will create a new JSON file containing only filtered messages
# It will also contain statistics about the messages
def filter_json(raw_directory):

    start_time = time.time()

    # We could potentially use structural pattern matching in
    # the future if we have more fail states

    for json_file in os.listdir(raw_directory):

        with open(f"{raw_directory}/{json_file}","rb") as file:
            raw_data = json.load(file)

        filtered_data = {
            "guild_id": raw_data["guild"]["id"],
            "stats": {},
            "valid_users": [],
            "active_messages": [],
            "inactive_messages": []
        }

        # Create stats
        for message in raw_data["messages"]:

            if message["author"]["name"] not in filtered_data["stats"]:
                filtered_data["stats"][message["author"]["name"]] = { # This is barely readable
                    "message_count": 1
                }

            else:
                filtered_data["stats"][message["author"]["name"]]["message_count"] += 1 # Neither is this

        filter_results = {
            "less than 20 messages": 0,
            "bot author": 0,
            "deleted user": 0,
            "link": 0,
            "contains @": 0,
            "command": 0,
            "attention": 0,
            "attachments": 0
        }

        # Removes messages that don't pass the filter
        for count, message in enumerate(raw_data["messages"]):

            # We copy the original message so we can modify it with the filter
            filtered_message = message

            if filtered_data["stats"][message["author"]["name"]]["message_count"] < 20:
                filter_results["less than 20 messages"] += 1
                filtered_message = None # We set the filtered message to none because we just want to delete it

            elif message["author"]["isBot"] == True:
                filter_results["bot author"] += 1
                filtered_message = None

            elif message["author"]["name"] == "Deleted User":
                filter_results["deleted user"] += 1
                filtered_message = None

            elif "http" in message["content"]:
                filter_results["link"] += 1
                filtered_message = None

            elif "@" in message["content"]:
                filter_results["contains @"] += 1
                filtered_message["content"] = message["content"].replace("@","[@]")

            elif message["content"].startswith("!") or message["content"].startswith("-"):
                filter_results["command"] += 1
                filtered_message = None

            elif message["content"].startswith("@") and message["content"].count(" ") == 0:
                filter_results["attention"] += 1
                filtered_message = None


            elif message["attachments"] != []:
                filter_results["attachments"] += 1
                filtered_message = None

            else: # Don't really need an else statement anymore as passing the filter is implicit
                pass # This is here for readabilty. Might do something with it later

            # If the message passes the filter
            if filtered_message != None: # We don't add the filtered message to the list if we just want to delete it

                filtered_data["active_messages"].append(filtered_message)

                if message["author"]["name"] not in filtered_data["valid_users"]:
                    filtered_data["valid_users"].append(message["author"]["name"])

        # Prints out the results of the filtering
        buffer = ""
        for issue, count in filter_results.items():
            buffer += f"{issue}: {count}\n"
        print(buffer)

        # Dumps the filtered data
        with open(f"server_data/{filtered_data['guild_id']}.json","w") as file:
            json.dump(filtered_data,file,sort_keys=True, indent=4)

        # Makes a backup of the original raw data
        shutil.copyfile(f"{raw_directory}/{json_file}",f"raw_data_backup/{json_file}")

        # Deletes the raw data
        os.remove(f"{raw_directory}/{json_file}")

    # Calculates the time taken to complete filtering
    elapsed_time = time.time() - start_time

    print(f"Finished filtering in {elapsed_time} seconds")

def download_messages(channel_id,token,output_directory):
    exit_code = os.system(f"dotnet libraries/chat_exporter/DiscordChatExporter.Cli.dll export -b -t '{token}' -c {channel_id} -f Json -o '{output_directory}/%g.json'")

    print(f"Finished downloading messages for {channel_id}")

@bot.event
async def on_ready():
    print("Loading JSON data")

    filter_json("raw_data")

    load_messages("server_data")

@bot.command()
async def guss(ctx):
    await ctx.send("https://static.wikia.nocookie.net/breakingbad/images/a/ab/BCS_S3_GusFringe.jpg/revision/latest?cb=20170327185354")

@bot.command()
async def gus(ctx):
    await ctx.send("https://cdn.discordapp.com/attachments/769958337474461737/910308645424746506/IMG_0005.jpg")

@bot.command()
async def sync(ctx):

    # We need the guild id as a str because json doesnt support int keys
    guild_id = str(ctx.guild.id)

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
    data = bot.server_data[guild_id]

    # Messages are pre-filtered now!
    message = random.choice(data["active_messages"])

    # Add the correct answer to the list of choices
    choices = [message["author"]["name"]]

    # We use this to generate wrong answers
    users = data["valid_users"]

    # Generate wrong answers
    while len(choices) < 4: # Generate 3 wrong answers
        random_user = random.choice(users)

        if random_user not in choices:
            choices.append(random_user)

    # Shuffles the list so the right answer won't always be first
    random.shuffle(choices)

    # We get the emoji that correlates to the correct answer
    # correct_emoji = EMOJI_TABLE[choices.index(message["author"]["name"])]

    # Generates the actual string of choices that will be put in the message
    choices_string = ""

    for number, choice in enumerate(choices):
        choices_string += f"{EMOJI_TABLE[number]}: {choice}\n"

    prompt_message = await ctx.send(f"Who sent:\n||Author||: {message['content']}\n\n{choices_string}\n")

    for emoji in EMOJI_TABLE:
        await prompt_message.add_reaction(emoji)

    # Saves the message in the prompts dictionary
    if guild_id in bot.prompts:
        bot.prompts[guild_id].append(
            {
                "prompt_message": prompt_message,
                "guess_message": message,
                "choices": choices
            }
        )

    else: # Create list of prompts if it doesnt yet exist for this guild
        bot.prompts[guild_id] = [
            {
                "prompt_message": prompt_message,
                "guess_message": message,
                "choices": choices
            }
        ]

@bot.command()
async def debug(ctx):
    await ctx.send(f"""**CTX guild ID**: {ctx.guild.id}\n
    **CTX author ID**: {ctx.message.author.id}\n""")

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
            filter_json("raw_data")
            load_messages("server_data")

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

            correct_choice = choices.index(guess_message["author"]["name"])

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

                print(correct_users)

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

                # Deletes the prompts from list of active prompts
                bot.prompts[guild].remove(prompt)

prompt_checker.start()
download_checker.start()

bot.run(BOT_TOKEN)
