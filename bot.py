import discord, json, pytz, os
from discord.ext import commands, tasks
from datetime import datetime
from leetcode_api import get_recent_accepted_problems, fetch_random_problem

TOKEN = os.environ['TOKEN']
CHANNEL_ID =  int(os.environ['channel'])
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

def load_json(file):
    if not os.path.exists(file):
        with open(file, 'w') as f:
            json.dump({}, f)
    with open(file, 'r') as f:
        return json.load(f)

def save_json(file, data):
    with open(file, 'w') as f:
        json.dump(data, f, indent=4)

@bot.event
async def on_ready():
    print(f"{bot.user} is online!")
    if not post_daily_kata.is_running():
        post_daily_kata.start()
        hourly_check.start()

@tasks.loop(minutes=1)
async def post_daily_kata():
    jordan_time = datetime.now(pytz.timezone('Asia/Amman'))
    if jordan_time.hour == 9 and jordan_time.minute == 0:
        channel = bot.get_channel(CHANNEL_ID)
        challenges = load_json('challenges.json')

        # fallback to LeetCode random if no challenges left
        if not challenges.get('daily_kata'):
            today = fetch_random_problem()
            challenges['current_kata'] = today
            save_json('challenges.json', challenges)
            await channel.send(f"📝 **Today's Random LeetCode Problem:** [{today['title']}]({today['url']})")
        else:
            today = challenges['daily_kata'].pop(0)
            challenges['current_kata'] = today
            save_json('challenges.json', challenges)
            await channel.send(f"📝 **Today's Daily Problem:** [{today['title']}]({today['url']})")

@bot.command()
async def register(ctx, username):
    users = load_json('users.json')
    users[str(ctx.author.id)] = {"username": username, "streak": 0, "last_solved": "", "points": 0}
    save_json('users.json', users)
    await ctx.send(f"{ctx.author.mention} registered as `{username}`!")

@bot.command()
async def check(ctx):
    challenges = load_json('challenges.json')
    kata = challenges['current_kata']['title']
    users = load_json('users.json')
    results = []
    today_str = str(datetime.now(pytz.timezone('Asia/Amman')).date())

    for uid, data in users.items():
        username = data['username']
        recent_problems = get_recent_accepted_problems(username)
        solved_daily = kata.lower() in [p.lower() for p in recent_problems]
        solved_any = len(recent_problems) > 0

        if data.get('last_solved') != today_str:
            points = 0
            if solved_daily:
                data['streak'] += 1
                points = 30
                data['last_solved'] = today_str
                results.append(f"<@{uid}> +30 points for Daily Kata! 🔥 Streak: {data['streak']} Total: {data['points'] + points}")
            elif solved_any:
                points = 5
                data['last_solved'] = today_str
                results.append(f"<@{uid}> +5 points for solving any problem! Total: {data['points'] + points}")
            data['points'] += points
    save_json('users.json', users)
    await ctx.send("\n".join(results) if results else "No one solved anything today!")

@bot.command()
async def leaderboard(ctx):
    users = load_json('users.json')
    sorted_users = sorted(users.items(), key=lambda x: x[1]['points'], reverse=True)
    board = [f"<@{uid}>: {data['points']} pts | {data['streak']}🔥" for uid, data in sorted_users]
    await ctx.send("🏆 **Leaderboard** 🏆\n" + "\n".join(board))

@bot.command()
async def force_daily(ctx):
    """Force send today's kata manually and set it if not set yet."""
    challenges = load_json('challenges.json')

    # If current kata is empty, pop a new one
    if not challenges.get('current_kata') or not challenges['current_kata'].get('title'):
        if challenges.get('daily_kata'):
            today = challenges['daily_kata'].pop(0)
            challenges['current_kata'] = today
            save_json('challenges.json', challenges)
        else:
            today = fetch_random_problem()
            challenges['current_kata'] = today
            save_json('challenges.json', challenges)
            await ctx.send("⚠️ No kata in list, fetched random problem.")

    current = challenges['current_kata']
    await ctx.send(f"📝 **Forced Daily Kata:** [{current['title']}]({current['url']})")

@bot.command()
async def current(ctx):
    """Show the current daily problem info."""
    challenges = load_json('challenges.json')
    current = challenges.get('current_kata', {})
    if current and current.get('title'):
        await ctx.send(f"📌 **Current Daily Problem:** [{current['title']}]({current['url']})")
    else:
        await ctx.send("⚠️ No daily problem currently active.")


@tasks.loop(hours=1)
async def hourly_check():
    channel = bot.get_channel(CHANNEL_ID)
    await check(channel)

bot.run(TOKEN)
