# Author: SerCom_KC
# Licensed under MIT License

from pyrogram.api import types
from pyrogram.api import functions
import time

def init():
    global message_list, user_list, chat_list, min_timestamp, max_timestamp
    message_list = []
    user_list = []
    chat_list = []
    min_timestamp = 0
    max_timestamp = 0

def updateTS(timestamp):
    global min_timestamp, max_timestamp
    if not isinstance(timestamp, int):
        return
    if min_timestamp == 0:
        min_timestamp = timestamp
    elif timestamp < min_timestamp:
        min_timestamp = timestamp
    if timestamp > max_timestamp:
        max_timestamp = timestamp

def processParticipant(response):
    participant_dict = response.__dict__
    data = {
        "user": findUser(participant_dict["user_id"]),
        "admin": None,
        "ban": None
    }
    if isinstance(response, types.ChannelParticipantAdmin):
        data["admin"] = participant_dict["admin_rights"].__dict__
    elif isinstance(response, types.ChannelParticipantBanned):
        data["ban"] = participant_dict["banned_rights"].__dict__

def processMessage(response, TSupdate=True):
    global message_list
    message_dict = response.__dict__
    data = {
        "service": None,
        "timestamp": 0,
        "id": message_dict["id"],
        "message": None
    }
    if isinstance(response, types.MessageEmpty):
        return data
    if TSupdate:
        updateTS(message_dict["date"])
    data["timestamp"] = message_dict["date"]
    message = {
        "content": None,
        "from_id": None,
        "via_id": None,
        "reply_id": None,
        "edit": None
    }
    if isinstance(response, types.MessageService):
        data["service"] = True
        message["content"] = None, # TO-DO
        if "from_id" in message_dict:
            message["from_id"] = findPeer(message_dict["from_id"])
        if "reply_to_msg_id" in message_dict:
            message["reply_id"] = message_dict["reply_to_msg_id"]
        message["edit"] = False
    elif isinstance(response, types.Message):
        data["service"] = False
        if message_dict["edit_date"] != None:
            data["timestamp"] = message_dict["edit_date"]
        message["content"] = message_dict["message"], # Entities TO-DO
        if "from_id" in message_dict:
            message["from_id"] = findPeer(message_dict["from_id"])
        if "via_bot_id" in message_dict:
            message["via_id"] = findUser(message_dict["via_bot_id"])
        if "reply_to_msg_id" in message_dict:
            message["reply_id"] = message_dict["reply_to_msg_id"]
        message["edit"] = True if message_dict["edit_date"] != None else False
    data["message"] = message
    if not data["service"] and not message["edit"]:
        message_list.append(data)
    return data

def processStickerSet(response):
    if isinstance(response, types.InputStickerSetEmpty):
        return None
    elif isinstance(response, types.InputStickerSetID):
        return response.__dict__["id"]
    elif isinstance(response, types.InputStickerSetShortName):
        return response.__dict__["short_name"]

def findPeer(id):
    data = findChat(id)
    if not data:
        return findUser(id)
    return data

def findChat(id):
    global chat_list
    for chat in chat_list:
        if chat["id"] == id:
            return chat
    return None

def findUser(id):
    global user_list
    for user in user_list:
        if user["id"] == id:
            return user
    return None

def processChat(response):
    chat_dict = response.__dict__
    data = {
        "id": chat_dict["id"],
        "title": None,
        "username": None
    }
    if not isinstance(response, types.ChatEmpty):
        data["title"] = chat_dict["title"]
    if "username" in chat_dict:
        data["username"] = chat_dict["username"]
    return data

def processUser(response):
    user_dict = response.__dict__
    data = {
        "id": user_dict["id"],
        "first_name": None,
        "last_name": None,
        "username": None,
        "bot": None
    }
    if isinstance(response, types.User):
        data["first_name"] = user_dict["first_name"]
        data["last_name"] = user_dict["last_name"]
        data["username"] = user_dict["username"]
        data["bot"] = user_dict["bot"]
    return data

def processAdminLog(response):
    global user_list, chat_list
    processed_events = []
    for user in response.__dict__["users"]:
        user_list.append(processUser(user))
    for chat in response.__dict__["chats"]:
        chat_list.append(processChat(chat))
    for event in response.__dict__["events"]:
        event_dict = event.__dict__
        updateTS(event_dict["date"])
        data = {
            "timestamp": 0,
            "user": None,
            "action": None
        }
        data["timestamp"] = event_dict["date"]
        data["user"] = findUser(event_dict["user_id"])
        action_dict = event_dict["action"].__dict__
        action = {
            "type": None,
            "old": None,
            "new": None
        }
        if isinstance(event_dict["action"], types.ChannelAdminLogEventActionChangeTitle):
            action["type"] = "ChangeTitle"
            action["old"] = action_dict["prev_value"]
            action["new"] = action_dict["new_value"]
        elif isinstance(event_dict["action"], types.ChannelAdminLogEventActionChangeAbout):
            action["type"] = "ChangeAbout"
            action["old"] = action_dict["prev_value"]
            action["new"] = action_dict["new_value"]
        elif isinstance(event_dict["action"], types.ChannelAdminLogEventActionChangeUsername):
            action["type"] = "ChangeUsername"
            action["old"] = action_dict["prev_value"]
            action["new"] = action_dict["new_value"]
        elif isinstance(event_dict["action"], types.ChannelAdminLogEventActionChangePhoto):
            action["type"] = "ChangePhoto"
            action["old"] = None #processPhoto(action_dict["prev_photo"])
            action["new"] = None #processPhoto(action_dict["new_photo"])
            # downloading and/or converting to file id not supported by Pyrogram yet
        elif isinstance(event_dict["action"], types.ChannelAdminLogEventActionToggleInvites):
            action["type"] = "ToggleInvites"
            action["old"] = not action_dict["new_value"]
            action["new"] = action_dict["new_value"]
        elif isinstance(event_dict["action"], types.ChannelAdminLogEventActionToggleSignatures):
            action["type"] = "ToggleSignatures"
            action["old"] = not action_dict["new_value"]
            action["new"] = action_dict["new_value"]
        elif isinstance(event_dict["action"], types.ChannelAdminLogEventActionUpdatePinned):
            action["type"] = "UpdatePinned"
            action["old"] = None
            action["new"] = processMessage(action_dict["message"])
        elif isinstance(event_dict["action"], types.ChannelAdminLogEventActionEditMessage):
            action["type"] = "EditMessage"
            action["old"] = processMessage(action_dict["prev_message"])
            action["new"] = processMessage(action_dict["new_message"])
        elif isinstance(event_dict["action"], types.ChannelAdminLogEventActionDeleteMessage):
            action["type"] = "DeleteMessage"
            action["old"] = processMessage(action_dict["message"])
            action["new"] = None
        elif isinstance(event_dict["action"], types.ChannelAdminLogEventActionParticipantJoin):
            action["type"] = "ParticipantJoin"
            action["old"] = None
            action["new"] = data["user"]
        elif isinstance(event_dict["action"], types.ChannelAdminLogEventActionParticipantLeave):
            action["type"] = "ParticipantLeave"
            action["old"] = data["user"]
            action["new"] = None
        elif isinstance(event_dict["action"], types.ChannelAdminLogEventActionParticipantInvite):
            action["type"] = "ParticipantInvite"
            action["old"] = None
            action["new"] = findUser(action_dict["participant"].__dict__["user_id"])
        elif isinstance(event_dict["action"], types.ChannelAdminLogEventActionParticipantToggleBan):
            action["type"] = "ParticipantToggleBan"
            action["old"] = processParticipant(action_dict["prev_participant"])
            action["new"] = processParticipant(action_dict["new_participant"])
        elif isinstance(event_dict["action"], types.ChannelAdminLogEventActionParticipantToggleAdmin):
            action["type"] = "ParticipantToggleAdmin"
            action["old"] = processParticipant(action_dict["prev_participant"])
            action["new"] = processParticipant(action_dict["new_participant"])
        elif isinstance(event_dict["action"], types.ChannelAdminLogEventActionChangeStickerSet):
            action["type"] = "ChangeStickerSet"
            action["old"] = processStickerSet(action_dict["prev_stickerset"])
            action["new"] = processStickerSet(action_dict["new_stickerset"])
        elif isinstance(event_dict["action"], types.ChannelAdminLogEventActionTogglePreHistoryHidden):
            action["type"] = "TogglePreHistoryHidden"
            action["old"] = not action_dict["new_value"]
            action["new"] = action_dict["new_value"]
        data["action"] = action
        processed_events.append(data)
    return processed_events

def processList(list):
    list = sorted(list, key=lambda element: element["timestamp"])
    return list

def exportFullLog(client, chat_id):
    init()
    global min_timestamp, max_timestamp, user_list, chat_list, message_list
    admin_log = client.send(functions.channels.GetAdminLog(channel=client.resolve_peer(chat_id),q="",max_id=0,min_id=0,limit=0))
    processed_admin_log = processAdminLog(admin_log)
    add_offset = 0
    flag = True
    while flag:
        response = client.send(functions.messages.GetHistory(peer=client.resolve_peer(chat_id), offset_id=0, offset_date=max_timestamp, add_offset=add_offset, limit=100, max_id=0, min_id=0, hash=0))
        for user in response.__dict__["users"]:
            processed_user = processUser(user)
            if not findUser(processed_user["id"]):
                user_list.append(processed_user)
        for chat in response.__dict__["chats"]:
            processed_chat = processChat(chat)
            if not findChat(processed_chat["id"]):
                chat_list.append(processed_chat)
        for message in response.__dict__["messages"]:
            processed_message = processMessage(message, TSupdate=False)
            debug_timestamp = processed_message["timestamp"]
            if processed_message["timestamp"] < min_timestamp:
                flag = False
                break
        add_offset += 100
        print("Current TS: %d, target TS: %d" % (debug_timestamp, min_timestamp))
        time.sleep(20)
    return processList(processed_admin_log + message_list)
