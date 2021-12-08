# This module works to translate the back-end
# JSON stats to human readable outputs
import math
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

        basedness = 0
        sd = 0

        for ranking, word in enumerate(word_rankings[:30]):
            # Adds the word and its ranking to the string
            result += f"{ranking + 1}: **{word}** ({word_usage[word]})\n"

            #sd = actual number of times word is used - (amount of times word #1 is used/word ranking+1)
            sd = int((word_usage[word] - (word_usage[word_rankings[0]]/(ranking + 1) ))**2)

            basedness += sd

        basedness = str(int(math.sqrt(basedness/30)))
        result += f"Your Basedness: **{basedness}**"

        return result
