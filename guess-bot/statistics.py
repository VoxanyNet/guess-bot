# This module works to translate the back-end
# JSON stats to human readable outputs

class User:
    def __init__(self, user_stats):
        self.user_stats = user_stats

    def message_count(self):
        message_count = self.user_stats["message_count"]

        result = f"You have sent **{message_count}** messages."

        return result

    def word_count(self,keyword):
        word_usage = self.user_stats["word_usage"]

        if keyword not in word_usage:
            result = f"You have never said __{keyword}__."

        else:
            count = word_usage[keyword]
            result = f"You have said __{keyword}__ **{count}** times!"

        return result

    def top_usage(self):
        word_usage = self.user_stats["word_usage"]

        word_rankings = sorted(word_usage, key=word_usage.get, reverse=True)

        result = ""

        for ranking, word in enumerate(word_rankings[:10]):
            result += f"{ranking + 1}: **{word}**\n"

        return result
