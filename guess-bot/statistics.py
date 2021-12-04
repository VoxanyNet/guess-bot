class User:
    def __init__(self, guild_data, user_id):

        self.user_messages = []

        for message in guild_data["active_messages"]:
            if message["author"]["id"] == user_id:
                self.user_messages.append(message)

        # Later this will just go through the raw data instead
        for message in guild_data["inactive_messages"]:
            if message["author"]["id"] == user_id:
                self.user_messages.append(message)

    def word_count(self,keyword):
        count = 0

        for message in self.user_messages:
            if keyword in message["content"]:
                count += 1

        return count
