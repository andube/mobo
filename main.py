import discord, random, os, asyncio, markovify, brain
from discord.ext import commands
from replit import db
from keep_alive import keep_alive
from io import BytesIO
from PIL import Image, ImageFont, ImageDraw
from gtts import gTTS

intents = discord.Intents().all()
bot = commands.Bot(command_prefix = ["give ", "Give"], intents = intents, allowed_mentions = discord.AllowedMentions(everyone = False, roles = False, users = False), owner_ids={815350320959193128, 760524332300107788})

lists = db["lists"]
font = ImageFont.truetype("impact.ttf", 36)

def sync_list():
  db["lists"] = lists

def db_init():
  if 'models' not in db: 
    db['models'] = {}
    print("db 'models' created")
  if 'opt' not in db:
    db['opt'] = {}
    print("db 'opt' created")
  

def generate_sentence(guild, short=False, return_model=False):

  #bro who's gonna mess this up :skull:
  # You.
  if short and return_model:
    raise ValueError('how do you think that would work honestly')
  
  model = markovify.NewlineText("\n".join(lists[str(guild)]), state_size=1, well_formed=False)
    
  if short:
    return model.make_short_sentence(test_output=False, min_chars=10, max_chars=35)
  elif return_model:
    return model
  else:
    return model.make_sentence(test_output=False)

@bot.event
async def on_ready(): print("\033c mobo in da house"); discord.opus.load_opus("./libopus.so.0.8.0")


@bot.event
async def on_message(message):

  if message.author.bot or len(message.content) <= 1: # much simpler isn't it
    return # yess

  if str(message.guild.id) not in lists.keys():
    lists.update({str(message.guild.id): []})
  elif str(message.author.id) in db["opt"].keys() and db["opt"][str(message.author.id)] and "http" not in message.content:
      
    lists[str(message.guild.id)].append(message.content.lower())
    lists[str(message.guild.id)] = list(set(lists[str(message.guild.id)]))
      
    sync_list()

  if random.randint(1, 10) == 7:

    bot_message = None
    
    if "bout" in message.channel.name: bot_message = "bout"
    else: bot_message = generate_sentence(message.guild.id)
    
    async with message.channel.typing():
      await asyncio.sleep(2)
      await message.channel.send(bot_message)
  
  if len(lists[str(message.guild.id)]) > 150:
    random.shuffle(lists[str(message.guild.id)])
    # removes 50 random items from the list (it was just shuffled)
    lists[str(message.guild.id)] = lists[str(message.guild.id)][0:100]

  
    sync_list()
      
  await bot.process_commands(message)

@bot.command()
async def sentence(ctx):
  if len(lists[str(ctx.message.guild.id)]) < 1:
    await ctx.send("not enough data :skull:")
    return

  await ctx.send(generate_sentence(ctx.guild.id))
  
@bot.command()
async def sentences(ctx, num: int):
  if num > 100000:
    await ctx.send(":skull::skull::skull::skull: too much :skull::skull::skull::skull:")
    
  elif num == None:
    await ctx.send("gonna need a number bro")

  elif len(lists[str(ctx.message.guild.id)]) < 1:
    await ctx.send("not enough data :skull:")

  else:
    content = ''
    markov_model = generate_sentence(ctx.guild.id, return_model=True)
    
    for i in range(num): 
      while True:
        try:
          content += markov_model.make_short_sentence(tries = 100, test_output = False, min_chars = 20, max_chars = 50) + "\n\n"
          break
        except:
          pass
  
    await ctx.send(file = discord.File(BytesIO(content.encode('utf-8')), "sf.txt"))

@sentences.error
async def sentences_error(ctx, error):
  if isinstance(error, commands.errors.BadArgument):
    return await ctx.send("use a number you :clown:")
  
  await ctx.send(f"{error}\n{type(error)}")
  
def opt_ion(opt):
  if opt.lower() in ['true', 'w', 'in', 'on', 'yes', 'y', '1', 't', 'real']:
    opt = True
  elif opt.lower() in ['false', 'l', 'out', 'off', 'no', 'n', '0', 'f', 'fake']:
    opt = False
  return opt


@bot.command()
async def opt(ctx, arg: opt_ion):
  # db["opt"][userid] is a bool for whether or not a user is opted in
  
  if str(ctx.author.id) in db["opt"].keys():
    author_opted = db["opt"][str(ctx.author.id)]
  else:
    author_opted = False

  if arg and author_opted:
    await ctx.send("you are already opted in bozo")
  elif arg:
    db["opt"][str(ctx.author.id)] = True
    await ctx.send("you're now opted in that is a giga moment")
  elif not arg and not author_opted:
    await ctx.send("you are already opted out :skull: please opt in")
  elif not arg:
    db["opt"][str(ctx.author.id)] = False
    await ctx.send("you opted out :clown::clown::skull::skull::nerd::nerd:")
  else:
    await ctx.send("bro just use the command properly you idiot")

@opt.error
async def opt_error(ctx, error):
  if isinstance(error, commands.MissingRequiredArgument):
    await ctx.send('what ! are ! you ! opting for?')

@bot.command()
async def probability(ctx, word):
  model = generate_sentence(ctx.guild.id, return_model=True).chain.model
  
  if (word,) not in model:
    await ctx.send("huh")
  else:
    # naive algorithm that shall be improved later
    total = sum(model[(word,)].values())
    counts = sorted(model[(word,)].items(), key=lambda following: following[1], reverse=True)
    message = ''

    
    for i in range(3):
      if i >= len(counts): return await ctx.send(message)
      message += f"{counts[i][0]} - {counts[i][1]/total * 100}%\n"
      
    # it won't make it to this part if there are too little words
    if len(counts) <= 5: return await ctx.send(message)
    
    message += f"{len(counts) - 5} words...\n{counts[-1][0]} - {counts[-1][1]/total * 100}%\n{counts[-2][0]} - {counts[-2][1]/total * 100}%"
    await ctx.send(message)

@bot.command()
async def image(ctx, user: discord.Member = None):

  if user == None:
    user = random.choice(ctx.guild.members)

  image = Image.open(BytesIO(await user.display_avatar.read())).resize((500, 500))
  draw = ImageDraw.Draw(image)
  bytes = BytesIO()

  # split by space so the splitting in half doesn't cut words
  item = generate_sentence(ctx.guild.id, short=True).split(" ")

  # the actual splitting in half is right here woah
  first_half, second_half = item[:int(len(item)/2)], item[int(len(item)/2):]
  first_half, second_half = " ".join(first_half), " ".join(second_half)
  
  '''
  # older version of the splitting code
  # item1 and item2 were first_half and second_half respectively
  for i, text in enumerate(item):
    if i < (len(item) - 1) / 2:
      item1 += text + " "
    else:
      item2 += text + " "
  '''
  
  width = font.getlength(first_half)
  width2 = font.getlength(second_half)
  
  # 250 is half the width of the image
  # this makes the center of the text line up with the center of the image
  draw.text((250 - width/2, 10), first_half, font = font, stroke_width = 2, stroke_fill = "black", fill = "white")
  draw.text((250 - width2/2, 440), second_half, font = font, stroke_width = 2, stroke_fill = "black", fill = "white")

  image.save(bytes, 'PNG')
  
  await ctx.send(file = discord.File(BytesIO(bytes.getvalue()), "prongler.png"))

@image.error
async def imgerr(ctx, error):
  if isinstance(error, commands.errors.MemberNotFound):
    await ctx.send('that person is stupid')
  else:
    print(error)
    await ctx.send(str(error))

  
@bot.command()
async def play(ctx):

  if not ctx.author.voice: return await ctx.send('join a vc, pringles man')
  channel = ctx.author.voice.channel

  if ctx.guild.voice_client:
    vc = ctx.guild.voice_client
  else:
    vc = await channel.connect()

  #vc.play(discord.FFmpegPCMAudio('mobo.wav'))

  text = generate_sentence(ctx.guild.id, short=True)
  
  audio = BytesIO()
  tts = gTTS(text = text, lang = "en")

  tts.write_to_fp(audio)
  
  source = discord.FFmpegPCMAudio(audio.getvalue(), pipe=True, before_options='-f mp3') #what the alabama

  #source = discord.FFmpegPCMAudio(audio.read())
  vc.play(source)# do not question the thing
  await vc.disconnect() #go to discord thats a thing

@bot.command()
async def crazy_play(ctx):

  if not ctx.author.voice: return await ctx.send('join a vc, pringles man')
  channel = ctx.author.voice.channel

  if ctx.guild.voice_client:
    vc = ctx.guild.voice_client
  else:
    vc = await channel.connect()
  
  text = generate_sentence(ctx.guild.id, short=True)
  
  tts = gTTS(text = text, lang = "en")
  tts.save("crazy.mp3")
  
  source = discord.FFmpegPCMAudio(open('crazy.mp3').read())

  vc.play(source) #higgle
  await vc.disconnect()
    

@commands.is_owner()
@bot.command()
async def kill(ctx):
  try:
    await ctx.send(content="kill 1", file=discord.File("kill.jpg"))
  finally:
    os.system("kill 1")

@commands.is_owner()
@bot.command()
async def shout(ctx, *, words):
  for channel in ctx.guild.channels:
    await asyncio.sleep(2)
    if not isinstance(channel, discord.CategoryChannel):
      await channel.send(words)

@commands.is_owner()
@bot.command()
async def servers(ctx):
  await ctx.send(f"I am in {len(bot.guilds)} servers")
  message = ''
  for guild in bot.guilds:
    message += f"{guild.name} which has {len(guild.members)} members\n"
  await ctx.send(message)

'''@commands.is_owner()
@bot.command()
async def learntest(ctx, *, sentence):
  brain.learn(sentence, 'TEST')
  guild_data = brain.get_guild_data('TEST')
  
  await ctx.send(f"count table length\n{len(guild_data)}")

@commands.is_owner()
@bot.command()
async def probabilitytest(ctx, word):
  # guild_data = brain.get_guild_data('TEST')

  await ctx.send(f"sorry I have to rewrite this")

@commands.is_owner()
@bot.command()
async def sentencetest(ctx):
  await ctx.send(brain.write_sentence('TEST'))

@commands.is_owner()
@bot.command()
async def bulklearntest(ctx, guild):
  await ctx.send('I crunch on data like chips')

  chips = ' END START '.join(lists[str(guild)])
  
  brain.learn(chips, 'TEST')
  await ctx.send('data crunched')

@commands.is_owner()
@bot.command()
async def wipetestdata(ctx):
  del db['guild_data']['TEST']
  await ctx.send('data wiped')'''

@bot.command()
async def jerry(ctx):
  print("\n".join(lists[str(ctx.guild.id)]))
  await ctx.send("\n".join(lists[str(ctx.guild.id)]))
  

keep_alive()

@jerry.error
async def jerror(ctx, error):
  await ctx.send('too...big...')

while True:
  try:
    bot.run(os.getenv('TOKEN'))
    
    #bot.run("NTM5MDE5NjgyOTY4MjQwMTI4.Mzc1N.a2QivCPm3Mf5mhtb1PwBT8eVTCia4IgSBqKZV8HEM")
  except:
    os.system("kill 1")