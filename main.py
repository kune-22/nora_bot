import asyncio
import discord
import logging

import bot_set
from db.database import engine
from db.models import Base

Base.metadata.create_all(bind=engine)

# Botを実行
bot_set.bot_run()