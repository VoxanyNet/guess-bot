# This module works to translate the back-end
# JSON stats to human readable outputs

class User:
    def __init__(self, user_stats):
        self.user_stats = user_stats

    def word_count(self,keyword):
        word_usage = self.user_stats["word_usage"]

        if keyword not in word_usage:
            result = f"You have never said __{keyword}__."

        else:
            count = word_usage[keyword]
            result = f"You have said __{keyword}__ **{count}** times!"

        return result
