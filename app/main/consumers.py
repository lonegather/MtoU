# -*- coding: utf-8 -*-
# from channels import Group
# from channels.auth import channel_session_user, channel_session_user_from_http
import asyncio
import json
from django.contrib.auth import get_user_model
from channels.consumer import AsyncConsumer
from channels.db import database_sync_to_async


class MainConsumer(AsyncConsumer):
    async def websocket_connect(self, event):
        print('connected', event)

    async def websocket_receive(self, event):
        print('received', event)

    async def websocket_disconnect(self, event):
        print('disconnected', event)


"""
# Connected to websocket.connect
@channel_session_user_from_http
def ws_add(message):
    # Accept connection
    message.reply_channel.send({"accept": True})
    # Add them to the right group
    Group(message.user.username).add(message.reply_channel)


# Connected to websocket.receive
@channel_session_user
def ws_message(message):
    Group(message.user.username).send({
        "text": message['text'],
    })


# Connected to websocket.disconnect
@channel_session_user
def ws_disconnect(message):
    Group(message.user.username).discard(message.reply_channel)
"""