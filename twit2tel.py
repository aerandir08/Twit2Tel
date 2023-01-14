import tweepy
import json
import telegram
import asyncio
import re
import sys

CONFIG_FILE = "config.json"
async def get_ids(bot: telegram.Bot, config: dict) -> dict:
    async with bot:
        updates = await bot.get_updates()
    for update in updates:
        if update.message != None:
            id = update.message.chat.id
            if id not in config["telegram_users"]:
                config["telegram_users"].append(id)

    return config

async def send_telegram_message(bot: telegram.Bot, config: dict, message: str):
    async with bot:
        for user_id in config["telegram_users"]:
            await bot.send_message(text=message, chat_id=user_id, parse_mode=telegram.constants.ParseMode.HTML)

def main() -> None:
    if len(sys.argv) == 2:
        filepath = sys.argv[1]
    else:
        filepath = CONFIG_FILE
    with open(filepath, "r") as file:
        config = json.load(file)
    bot = telegram.Bot(config["telegram_token"])
    api = tweepy.Client(config["twitter_bearer"])

    config = asyncio.run(get_ids(bot, config))

    # Get Twitter user ids
    for username in config["twitter_users"]:
        if username not in config["last_tweets"].keys():
            id = api.get_user(username=username).data.id
            config["last_tweets"][username] = (id, 0)

    for user_name, (user_id, tweet_id) in config["last_tweets"].items():
        last_tweet = api.get_users_tweets(user_id).data[0]
        if last_tweet.text.startswith("RT "):
            break
        if last_tweet.id != tweet_id:
            """
            Text Layout:
            <username> bold
            <text from tweet> without any links
            <link to tweet>
            """
            text = f"<b>{username}</b>\n{last_tweet.text}"
            text = re.sub(r'http\S+', '', text)
            text += f"\nhttps://twitter.com/{user_name}/status/{last_tweet.id}"
            asyncio.run(send_telegram_message(bot, config, text))
            config["last_tweets"][username] = (user_id, last_tweet.id)

    data = json.dumps(config, indent=4)
    with open(filepath, "w") as file:
        file.write(data)


if __name__ == "__main__":
    main()
