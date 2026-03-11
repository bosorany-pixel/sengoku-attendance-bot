import dotenv
import os
from datetime import date
dotenv.load_dotenv(os.getenv("ENV_FILE", ".env"))

GUILD_IDS = {
    1355240968621658242,
    600703179360829483
    }
DISBAND_MESSAGES = {'дизбанд', 'диз', 'disband', 'dis'}
TREASURY_MESSAGES = {'казну', 'казна'}
FROM_HOURS = 26
TO_HOURS = 23
NAME_LINE = r".*?<@&?(.*?)>.*?"
REACTION_YES = '✅'
REACTION_NO = '❌'
MIN_USERS = 4
TREASURY_POINTS = 15
CHANNELS = {
    1478101710487425117: 2, # lfg
    1479081748544487424: 2, # group camps
    1479081712997634164: 2, # static
    1479081771634135122: 2, # hunt
    1479081790076358739: 3, # gang
    1479081830358581441: 3, # roum
    1478101709921194105: 4, # ava-dungeon
}

HIDDEN = {
    1345611337559965737: 4, # gru-morning
    1345611509127970906: 4, # gru-day
    1345611851026792500: 4, # gru-evening
    1345611986033180683: 4, # gru-night
}
POINTS_GROUP_MAP = 2
RENTOR_NAME = 'Rentor'
GROUP_MAP_NAMES = ['группики', 'групики', 'карты']
REACT_TO_MESSAGES = os.getenv("REACT_TO_MESSAGES")
if REACT_TO_MESSAGES is None:
    REACT_TO_MESSAGES = True
else:
    REACT_TO_MESSAGES = str(REACT_TO_MESSAGES).strip().lower() in ("1", "true", "yes", "y", "on")

MONTHLY_CALC = os.getenv("MONTHLY_CALC")
if MONTHLY_CALC is None:
    MONTHLY_CALC = False
else:
    MONTHLY_CALC = str(MONTHLY_CALC).strip().lower() in ("1", "true", "yes", "y", "on")

REPORT_CHANNEL_ID = 1355432420320739429
# Channel ID for logging new achievements (set via env LOGS_CHANNEL_ID; if unset, no messages sent)
_logs_channel = os.getenv("LOGS_CHANNEL_ID")
LOGS_CHANNEL_ID = int(_logs_channel) if _logs_channel and _logs_channel.strip() else None
ADMIN_ROLES = {
    "Rentor": 0,
    "Officer": 2,
    "Mentor": 3,
    "Recruiter": 4
}
TODAY = date.today()

MEMBER_ROLE = os.getenv("MEMBER_ROLE", 'Half Orc')