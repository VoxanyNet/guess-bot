# This module works to translate the back-end
# JSON stats to human readable outputs
import math

basedness_conversions = {
    5: "EXTREMELY CRINGE",
    10: "Sheep",
    15: "Moderatly Cringe",
    20: "Uncringe",
    30: "Free Thinker",
    40: "Based",
    50: "Extremely Based",
    60: "Dangerously Based",
    70: "Out of Control",
    80: "Goofy/Silly",
    90: "Nationwide Basedness Epidemic",
    100: "Global Lockdown"
}

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

    def top_usage(self,range):

        # Unpacks range
        range_floor, range_ceiling = range

        word_usage = self.user_stats["word_usage"]

        # Returns a list of word strings ordered most used -> least used
        word_rankings = sorted(word_usage, key=word_usage.get, reverse=True)

        result = ""

        basedness = 0
        most_used_word_count = word_usage[word_rankings[0]]

        for word in word_rankings[range_floor:range_ceiling]:
            ranking = word_rankings.index(word)

            result += f"{ranking + 1}: **{word}** ({word_usage[word]})\n"

            # Estimation calculation
            # (most used word's word count) * 1/(the word we want to estimate's rank)
            # This is a simplified equation
            # https://youtu.be/fCn8zs912OE?t=125
            # This will calculate the estimated usage count based on Zipf's law
            estimated_word_usage = (1 / (ranking + 1)) * 100


            # Calculates the difference between the estimated word usage and the actual word usage
            estimation_delta = (((word_usage[word] / most_used_word_count)*100) - int(estimated_word_usage)) **2

            # Basedness increases as you deviate more from the mean
            basedness += estimation_delta

        basedness = int(math.sqrt(basedness/(range_ceiling - range_floor)))

        result += f"\nBasedness: **{basedness}%**"

        for maximum_value, conversion in basedness_conversions.items():
            if basedness < maximum_value:
                result += f"\nRank: **{conversion}**"
                break

        return result
