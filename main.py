import asyncio
import discord
import logging
import threading

import bot_set
from api_server import run_api
from db.database import engine
from db.models import Base

Base.metadata.create_all(bind=engine)

# Botを実行
threading.Thread(target=run_api, name="dashboard-api", daemon=True).start()
bot_set.bot_run()
