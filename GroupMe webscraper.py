# -*- coding: utf-8 -*-
"""
Created on Fri Mar 11 22:45:32 2022

@author: qedgary
"""
import requests
import os
import shutil
import emoji
import re
import json # for saving lists to local computer
from datetime import datetime
from dateutil import tz # for time zones
import numpy as np
from PIL import Image, ImageDraw # for cropping images to circles

# `GroupID` is an eight-digit number unique to a GroupMe group chat
# `token`   is an API request token linked to your GroupMe account, and it should
#           look like a bunch of gibberish letters and numbers
# the `groupID` and `token` below are fake
groupID        = "12345678" 
token          = "a0bc1defghi2jklmn34567opq8rs9tuvwxyzab0c" 
chatURL        = "https://api.groupme.com/v3/groups/" + groupID + "/messages?token="

messages       = []               # a list to contain all the messages
Jan_1_2022     = 1640995200       # 2022 January 1 as a UNIX time. Change this to match your needs
from_zone      = tz.gettz('UTC')
to_zone        = tz.gettz('America/New_York') # set local time zone

groupme = requests.get(
    chatURL,
    params = {
        "limit": 1, # grab one message at a time
        "since_id": Jan_1_2022 # grab the messages that happened after since this time
    }
)

# basically, because of the limitations in GroupMe's API, we're simply requesting messages from
# GroupMe in reverse chronological order. That is, we'll request the most recent message, then the 
# message immediately before that, then the one before that, and then before that, and then before
# that...
while groupme.status_code == 200:
    previous_message = groupme.json()["response"]["messages"]
    previous_message_id = previous_message[0]["id"]
    messages += previous_message  
    
    groupme = requests.get(
        chatURL,
        params = {
            "limit": 1, # grab one message at a time
            "before_id": previous_message_id # only grab messages before the current one
        }
    )
    
    #if(len(messages) > 70):
        #break 
        # If you simply want to test out whether this program works, you can grab the 70 
        # most recent messages just to see what you'll get

messages = [m for m in reversed(messages)]

with open("saved_messages.json", 'w') as f:
    json.dump(messages, f, indent=2) 

distinctUsers = [] 
imageList     = []

# We'll loop through `messages` to perform some pre-processing before we actually manipulate the content of the messages
for m in messages:
    
    # let's create a list of distinct users in the chat
    if distinctUsers:
        isDistinct = True
        for user in distinctUsers: 
            isDistinct = isDistinct and (user[0] != m["name"])
        if isDistinct:
            distinctUsers.append((m["name"], m["user_id"], m["avatar_url"]))
    else:
        distinctUsers.append((m["name"], m["user_id"], m["avatar_url"]))

    # download images via requests.get and save to a folder
    if len(m["attachments"]) > 0:
        for attachment in m["attachments"]:
            if attachment["type"] == "image":    
                # Download image
                img = requests.get(attachment["url"], stream = True)
                
                if img.status_code == 200:
                    img.raw.decode_content = True
                    
                    if ".jpg" in attachment["url"] or ".jpeg" in attachment["url"]:
                        extension = ".jpg"
                    elif ".png" in attachment["url"]:
                        extension = ".png"
                    elif ".gif" in attachment["url"]:
                        extension = ".gif" 
                    
                    filename = "GroupMe_img/" + m["id"] + extension
                    with open(filename,'wb') as f: # save the file to a local location
                        shutil.copyfileobj(img.raw, f)
                        
                    if extension == ".gif": # save GIFs as PNGs so that they work in LaTeX
                        img = Image.open(filename).convert("RGB")
                        img.save("GroupMe_img/" + m["id"] + ".png")



def circleImage(filename):
    """
    Crops an image to a circle, then saves it to a local folder. Returns nothing.
    
    Adapted from https://stackoverflow.com/a/51487201 - I changed this function
    so that it centers the circle around the center of the image, rather than
    stretching the circle to fit the image
    
    This function alone is CC BY-SA 4.0. You can read more about the CC BY-SA 4.0
    license at https://creativecommons.org/licenses/by-sa/4.0/
    """
    img  = Image.open(filename).convert("RGB")
    w, h = img.size
    if h > w: # if the image isn't square, crop it until it's square
        img = img.crop((0, (h - w) // 2, w, (h - w) // 2 + w))
    elif h < w:
        img = img.crop(((w - h) // 2, 0, (w - h) // 2 + h, h))
        
    if h > 300 or w > 300:
        img = img.resize((300,300),Image.ANTIALIAS)
        
    h, w = img.size
    npImage = np.array(img)
    
    # Create same size alpha layer with circle
    alpha   = Image.new('L', img.size,0)
    draw    = ImageDraw.Draw(alpha)
    draw.pieslice([0,0,h,w], 0, 360, fill = 255)
    
    # Convert alpha Image to numpy array
    npAlpha = np.array(alpha)
    
    # Add alpha layer to RGB
    npImage = np.dstack((npImage,npAlpha))
    
    imgName = filename.split(".")[0]
    
    # Save with alpha
    Image.fromarray(npImage).save(imgName + "_circle.png")

for user in distinctUsers:
    profileImgURL = user[2]
    if user[0] != "GroupMe" and profileImgURL != None:
        img = requests.get(user[2], stream = True)
        
        if img.status_code == 200:
            img.raw.decode_content = True
            
            if ".jpg" in profileImgURL or ".jpeg" in profileImgURL:
                extension = ".jpg"
            elif ".png" in profileImgURL:
                extension = ".png"
            elif ".gif" in profileImgURL:
                extension = ".gif"
            
            filename = "GroupMe_img/user" + user[1] + extension
            if not os.path.exists(filename): # if profile picture doesn't already exist
                with open(filename,'wb') as f: # save the file to a local location
                    shutil.copyfileobj(img.raw, f)
            
            # now crop the image to the shape of a circle
            circleImage(filename)


# Run below this line if you aren't able to connect to the web
# ------------------------------------------------------------

with open("saved_messages.json", 'r') as f:
    messages = json.load(f)

# Now, we translate our list of messages into a string that LaTeX can read
output = "%!TeX root = GroupMe webscraper output.tex\n%!TeX program = XeLaTeX\n\n"

failureStr = "" # for any sort of failures

prev_m = {'attachments': [],  'avatar_url': '', 'created_at': 0, 'favorited_by': [], 'group_id': '84353221', 'id': '',  'name': "", 'sender_id': '',  'sender_type': 'user', 'source_guid': '', 'system': False,  'text': '',  'user_id': '', 'platform': 'gm'}

mostWords       = prev_m
mostChars       = prev_m
oneCharList     = []
coolSubstr      = "among us"
mostSubstr      = prev_m
mostSubstr_list = []
mostChars_no_e  = prev_m


def getUser(userID):
    """
    Given a user ID, returns the tuple of the user's name, user_id, and avatar_url,
    or returns the string "unknown user" if no user is found
    """
    for user in distinctUsers:
        if user[1] == userID:
            return user
    return ("unknown user", 0, "")

def getMessage(messageID):
    """
    Given a message ID, returns the message as a dictionary, or if no message is found, 
    returns a dictionary with mostly empty fields and an error
    """
    for m in messages:
        if m["id"] == messageID:
            return m
    return {'attachments': [],  'avatar_url': '', 'created_at': 0, 'favorited_by': [], 'group_id': '84353221', 'id': '',  'name': "", 'sender_id': '',  'sender_type': 'user', 'source_guid': '', 'system': False,  'text': 'ERROR GRABBING MESSAGE',  'user_id': '', 'platform': 'gm'}

for k in range(len(messages)): # traverse all messages
    m = messages[k]
    if k != 0:
        prev_m = messages[k - 1] # if this isn't the first message, we'll define the previous message
        
    try:
        if m["name"] == "GroupMe": # for GroupMe system messages
            output +="\n\\GroupMe{"
        elif m["text"]: # for all other messages, compute our fun stats
            if len(m["text"]) > len(mostChars["text"]): # what message is longest in characters?
                mostChars = m
            if "e" not in m["text"].lower() and len(m["text"]) > len(mostChars_no_e["text"]):
                mostChars_no_e = m
            if len(m["text"].split()) > len(mostWords["text"].split()): # what message has most words?
                mostWords = m
            if len(m['text']) == 1:
                oneCharList.append(m)
            if m["text"].lower().count(coolSubstr) > mostSubstr["text"].lower().count(coolSubstr):
                mostSubstr = m # what message has most instances of `coolSubstr?
                mostSubstr_list = [m]
            elif m["text"].lower().count(coolSubstr) == mostSubstr["text"].lower().count(coolSubstr):
                mostSubstr_list.append(m)
        
        imagePresent = "" # if an image is present, we'll save it here, to add to `output` later
        filePresent  = "" # same thing if a file is attached
        
        if len(m["attachments"]) > 0:
            for attachment in m["attachments"]:
                if attachment["type"] == "reply":
                    output += "\n\\reply{" + getUser(attachment["user_id"])[0] + "}{"
                    
                    # what is the ID of the message being replied to?
                    replyID = attachment["reply_id"] 
                    # grab text of replied message, then split it into individual words
                    repliedMessageWords = getMessage(replyID)["text"].split() 
                    # keep track of the length, in characters, of our reply
                    replyToLength = 0
                    for k in range(len(repliedMessageWords)):
                        output += repliedMessageWords[k] + " "
                        replyToLength += len(repliedMessageWords[k])
                        if replyToLength > 70:
                            output += " $\\ldots$"
                            break
                    
                    output += "}\n"
                if attachment["type"] == "image":
                    imagePresent = "\\includegraphics[width=7cm]{GroupMe_img/" + m["id"] + "}"
                if attachment["type"] == "file":
                    filePresent  = "\\fileattached{" + attachment["file_id"] + "}"
        
        if m["name"] != "GroupMe" and prev_m["name"] != m["name"]: # if a person sends multiple messages
            output += "\\begin{senderFirstMessage}" # create a minipage environment
        
            # add profile pictures
            if m["avatar_url"]: # profile picture exists
                output += "\n\\profilePic{user" + m["sender_id"] + "_circle.png}"
            else: # no profile picture (aka user has default profile picture)
                output += "\n\\genericProfilePic{" + m["name"][0] + "}"

            # set person name
            output += "\n\\sender{" + m['name'] + "}" 

            
            # set date and time
            UTC_time = datetime.strptime(datetime.utcfromtimestamp(m["created_at"]).strftime('%Y-%m-%d %H:%M:%S'), '%Y-%m-%d %H:%M:%S')
            UTC_time = UTC_time.replace(tzinfo = from_zone)
            EST_time = UTC_time.astimezone(to_zone).strftime('%Y %B %d at %H:%M')
            
            output += "\\datetime{" + EST_time + "}"

        if m["text"] == None: # if there is no text in the message (e.g. it's all an image)
            m["text"] = ""
            
        messageContent = m["text"].replace("\n", "\\\\")
        
        # Emojis --------------------------------------------
        emojiContent = [c for c in messageContent if c in emoji.UNICODE_EMOJI['en']] 
        if emojiContent: # if the message has emojis
            for e in emojiContent: # then transform them into LaTeX-readable commands
                TeXemoji = emoji.demojize(e)[1:-1] # demojize, then remove colons at front and end
                TeXemoji = TeXemoji.replace("_", ' ') # replace underscores with spaces
                TeXemoji = "\\raisebox{-0.2em}{\\Large\\texttwemoji{" + TeXemoji + "}}"
                messageContent = messageContent.replace(e, TeXemoji)
        
        # URLs ---------------------------------------------
        if "https://" in messageContent or "http://" in messageContent:
            messageContent = re.sub(r"(https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*))", r"\\url{\1}", messageContent)

        # Process remaining text ---------------------------
        messageContent = messageContent.replace("^", "\\textasciicircum ")
        messageContent = messageContent.replace("Created new poll", "\\itshape Created new poll")
        messageContent = messageContent.replace("Shared a document: ", "\\par\\vspace{1ex}\\raisebox{-1em}{\\includegraphics[height = 3em]{GroupMe_img/file_icon}}\\ \\emph{Shared a document: }")
        
        if "\\url" not in messageContent:
            # If there isn't a URL in the message, replace the hashtag and ampersand characters
            # with their LaTeX equivalents. This is a bit of a workaround, and it's easy to
            # think of examples where this heuristic fails, but realistically, it'll work most
            # of the time
            messageContent = messageContent.replace("#", "\\#")
            messageContent = messageContent.replace("&", "\\&")
            messageContent = messageContent.replace("%", "\\%")

        # Add message content ------------------------------
        output += "\n" + messageContent + "\n"
        
        # Attach images and files --------------------------
        # if filePresent:
        #     output += "\n" + filePresent + "\n"
        if imagePresent:
            output += "\n" + imagePresent + "\n"

        
        if m["name"] != "GroupMe":
            if prev_m["name"] != m["name"]:
                output += "\\end{senderFirstMessage}\n"
        else:
            output += "}\n"
            
        if m["favorited_by"]:
            output += "\n\\heart{" + ", ".join([getUser(user)[0] for user in m["favorited_by"]]) + "}\n"
        
    except:
        failureStr += m["text"] + "\n\n"
        
        
#print(output)


if failureStr:
    print("UH OH! THIS DIDN'T WORK:\n===================================")
    print(failureStr)
    # a useful debugging tool that tells us which messages trigger errors in the code above
    print("===================================\n")


f = open("GroupMeInput.tex", "w", encoding="utf-8")
f.write(output)
f.close()

# Uncomment these for some fun stuff :)
# mostWords       # what message has the most words?
# mostChars       # what message has the most characters?
# oneCharList     # what messages were exactly one character long?
# mostSubstr_list # what messages contained the substring `coolSubstr` the most times? Case is ignored
# mostChars_no_e  # what was the longest message that didn't contain the letter e?