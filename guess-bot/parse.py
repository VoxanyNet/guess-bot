# This module is responsible for filtering messages
# and generating user stats
import os
import shutil
import time
import json
from collections import defaultdict

DEFAULT_STATS = {
    "message_count": 0,
    "word_usage": defaultdict(int)
}

# Change to this work on on just one JSON
# instead of every single one
def filter_json(raw_directory,backup_path):

    start_time = time.time()

    # We could potentially use structural pattern matching in
    # the future if we have more fail states

    for json_file in os.listdir(raw_directory):

        with open(f"{raw_directory}/{json_file}","rb") as file:
            raw_data = json.load(file)

        filtered_data = {
            "guild_id": raw_data["guild"]["id"],
            "valid_users": [],
            "active_messages": [],
            "inactive_messages": []
        }

        # Create message count
        message_counts = defaultdict(int)

        for message in raw_data["messages"]:

            message_counts[message["author"]["id"]] += 1



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

            if message_counts[message["author"]["id"]] < 20:
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

                if filtered_message["author"]["id"] not in filtered_data["valid_users"]:
                    filtered_data["valid_users"].append(filtered_message["author"]["id"])

        # Prints out the results of the filtering
        buffer = ""
        for issue, count in filter_results.items():
            buffer += f"{issue}: {count}\n"
        print(buffer)

        # Dumps the filtered data
        with open(f"server_data/{filtered_data['guild_id']}.json","w") as file:
            json.dump(filtered_data,file,sort_keys=True, indent=4)

        # Makes a backup of the original raw data
        shutil.copyfile(f"{raw_directory}/{json_file}",f"{backup_path}/{json_file}")

        # Deletes the raw data
        os.remove(f"{raw_directory}/{json_file}")

    # Calculates the time taken to complete filtering
    elapsed_time = time.time() - start_time

    print(f"Finished filtering in {elapsed_time} seconds")

# We want this parsing to happen on data entirely in memory
# We will save elswhere in the code
def generate_stats(guild_data):
    # We want to generate more general stats

    stats = defaultdict(lambda: DEFAULT_STATS)

    guild_messages = guild_data["active_messages"] + guild_data["inactive_messages"]

    for message in guild_messages:
        author_id = message["author"]["id"]

        # WORD USAGE
        words = message["content"].split()

        for word in words:
            stats[author_id]["word_usage"][word] += 1

        # MESSAGE COUNT
        stats[author_id]["message_count"] += 1

    return stats
