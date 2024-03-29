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
groupID    = "12345678" 
token      = "a0bc1defghi2jklmn34567opq8rs9tuvwxyzab0c" 
chatURL    = "https://api.groupme.com/v3/groups/" + groupID + "/messages?token=" + token

messages   = []               # a list to contain all the messages
start_time = 1661711400       # UNIX time for first message
from_zone  = tz.gettz('UTC')
to_zone    = tz.gettz('America/New_York') # set local time zone

# Fonts for different scripts
lang_font = {
    "jp" : "Yu Gothic",
    "zh" : "Microsoft YaHei",
    "ko" : "Malgun Gothic",
    "hi" : "Nirmala UI",
    "ta" : "Nirmala UI",
    "got": "Segoe UI Historic",
    "runic": "Segoe UI Historic",
    "ett": "Segoe UI Historic"
}

failureStr = "" # A string that records failures that occur

# Only run the stuff between this and the next commented row of hyphens if you're sure 
# you want to make API calls. This takes a long time to run, and requires an Internet
# connection.
# --------------------------------------------------------------------------------------


groupme = requests.get(
    chatURL,
    params = {
        "limit": 1, # grab one message at a time
        "since_id": start_time # grab the messages that happened after since this time
    }
)

# basically, because of the limitations in GroupMe's API, we're simply requesting messages from
# GroupMe in reverse chronological order. That is, we'll request the most recent message, then the 
# message immediately before that, then the one before that, and then before that, and then before
# that...
while groupme.status_code == 200:
    previous_message = groupme.json()["response"]["messages"]
    
    if previous_message[0]["created_at"] < start_time:
        # stop requesting messages if they precede our desired start time
        break
    
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

distinctUsers = [] # create a list of all the distinct users in the chat

def downloadImageFromAPI(url, downloadName):
    """
    Downloads an image from the GroupMe API, and saves it in the local folder (not the GroupMe_img folder).
    The two parameters are the url of the image, and the filename which the image will be saved as. The 
    download name must *not* contain the file extension—instead, the function automatically obtains the
    file type of the image when the API request is made.
    
    The function returns the path of the image after downloading. This is for later use with the function
    circleImage.
    """
    img = requests.get(url, stream = True)
    
    if img.status_code == 200:
        img.raw.decode_content = True
        
        if ".jpg" in url or ".jpeg" in url:
            extension = ".jpg"
        elif ".png" in url:
            extension = ".png"
        elif ".gif" in url:
            extension = ".gif" 
        
        if not os.path.exists(downloadName + extension): # if image doesn't already exist
            with open(downloadName + extension,'wb') as f: # save the file to a local location
                shutil.copyfileobj(img.raw, f)
        
        # Note that the "if image doesn't already exist" condition means that only the oldest profile photo of a user is downloaded
            
        if extension == ".gif": # save GIFs as PNGs so that they work in LaTeX
            img = Image.open(downloadName + extension).convert("RGB")
            img.save(downloadName + ".png")
            
            extension = ".png"
            
        return downloadName + extension

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
        # assign each attachment an index based on its position in the array, thereby
        # giving a unique file name to each attachment. This will matter when we include
        # images for each message
        attachmentIndex = 0 
        for attachment in m["attachments"]:
            downloadName = "GroupMe_img/" + m["id"] + "_" + str(attachmentIndex)
            if attachment["type"] == "image":
                downloadImageFromAPI(attachment["url"], downloadName)
                # TO DO - create an else statement in case an image can't be pulled
            elif attachment["type"] == "video":
                downloadImageFromAPI(attachment["preview_url"], downloadName)
            attachmentIndex += 1


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

# Download profile pictures
for user in distinctUsers:
    profileImgURL = user[2]
    if user[0] != "GroupMe" and profileImgURL != None:
        profilePhotoPath = downloadImageFromAPI(profileImgURL, "GroupMe_img/user" + user[1])
        try: # now crop the image to the shape of a circle
            circleImage(profilePhotoPath)
        except:
            failureStr += "Profile photo download error for user {} ({})\n".format(user[0],user[1])
            # This happens sometimes. This is a problem with GroupMe because it happens
            # even on the official GroupMe app


# Once you have your saved_messages.json file, run below this line if you aren't able to
# connect to the web, or you don't want to re-run the API calls (which take a long time)
# --------------------------------------------------------------------------------------

with open("saved_messages.json", 'r') as f:
    messages = json.load(f)

# Now, we translate our list of messages into a string that LaTeX can read
output = "%!TeX root = GroupMe webscraper output.tex\n%!TeX program = XeLaTeX\n\n" # TO DO - fix this naming convention so that people can choose their own file names

failureStr = "" # for any sort of failures

prev_m = {'attachments': [],  'avatar_url': '', 'created_at': 0, 'favorited_by': [], 'group_id': '84353221', 'id': '',  'name': "", 'sender_id': '',  'sender_type': 'user', 'source_guid': '', 'system': False,  'text': '',  'user_id': '', 'platform': 'gm'}

mostWords       = prev_m
mostChars       = prev_m
oneCharList     = []
coolSubstr      = "among us"
mostSubstr      = prev_m
mostSubstr_list = []
mostChars_no_e  = prev_m
mostLiked       = prev_m
mostLiked_list  = []
emojiList       = [] # if you want to find the most common emoji


def getUser(userID):
    """
    Given a user ID, returns the tuple of the user's name, user_id, and avatar_url.
    If no user is found, the tuple contains the string "unknown user", 0 for the 
    user_id, and an empty string for the avatar_url.
    """
    if type(userID) == int:
        userID = str(userID)
    for user in distinctUsers:
        if user[1] == userID:
            return user
    return ("unknown user", 0, "")

def getMessage(messageID):
    """
    Given a message ID, returns the message as a dictionary, or if no message is found, 
    returns a dictionary with mostly empty fields and an error
    """
    # ID's are strings by default, so just in case we want to input integers in this
    # function, we convert to string
    messageID = str(messageID)
    for m in messages:
        if m["id"] == messageID:
            return m
    return {'attachments': [],  'avatar_url': '', 'created_at': 0, 'favorited_by': [], 'group_id': '84353221', 'id': '',  'name': "", 'sender_id': '',  'sender_type': 'user', 'source_guid': '', 'system': False,  'text': 'ERROR GRABBING MESSAGE',  'user_id': '', 'platform': 'gm'}

# If we only ran the code below the "if you aren't able to connect to the web" line, then we need to
# regenerate the list of distinct users. If we already have a list of distinct users, this if-statement
# gets skipped
try:
    distinctUsers
except NameError:
    distinctUsers = []
    for m in messages:
        if distinctUsers:
            isDistinct = True
            for user in distinctUsers: 
                isDistinct = isDistinct and (user[0] != m["name"])
            if isDistinct:
                distinctUsers.append((m["name"], m["user_id"], m["avatar_url"]))
        else:
            distinctUsers.append((m["name"], m["user_id"], m["avatar_url"]))


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
        filePresent  = "" # same thing if a file is attached. Note:  currently, this doesn't do anything
        videoPresent = ""
        
        if len(m["attachments"]) > 0:
            attachmentIndex = 0
            for attachment in m["attachments"]:
                if attachment["type"] == "reply":
                    output += "\n\\reply{" + getUser(attachment["user_id"])[0] + "}{"
                    
                    # what is the ID of the message being replied to?
                    replyID = attachment["reply_id"] 
                    # grab text of replied message
                    repliedMessageWords = getMessage(replyID)["text"]
                    # next, we sanitize the text for TeX character codes. For instance, URLs will have #'s and
                    # %'s, but because URLs in the reply section are not surrounded by the \reply macro, we need
                    # to escape TeX character codes
                    repliedMessageWords = repliedMessageWords.replace("#", "\\#").replace("&", "\\&").replace("%", "\\%").replace("_", "\\_")
                    # then split the reply text into individual words. Because URLs will have very long reply
                    # texts, we replace slashes with slashes plus a whitespace, which will cause Python to
                    # split at slashes. This lets reply text be cut off at slashes
                    repliedMessageWords = repliedMessageWords.replace("/", "/ ")
                    repliedMessageWords = repliedMessageWords.split() 
                    
                    # Now, we generate the text in the reply box. First, we must keep track of the length, in
                    # characters, of our reply, including both the username length and the message itself.
                    # This way, the text won't exceed one line when displaying the quoted message
                    replyToLength = len(getUser(attachment["user_id"])[0])
                    for k in range(len(repliedMessageWords)):
                        
                        replyToLength += len(repliedMessageWords[k])
                        
                        # handle emojis
                        emojiContent = [c for c in repliedMessageWords[k] if c in emoji.UNICODE_EMOJI['en']] 
                        if emojiContent: # if the reply has emojis
                            for e in emojiContent:
                                if e not in ["™", "®️"]:
                                    TeXemoji = emoji.demojize(e)[1:-1]
                                    TeXemoji = TeXemoji.replace("_", ' ')
                                    TeXemoji = "\\raisebox{-0.1em}{\\normalsize\\texttwemoji{" + TeXemoji + "}}"
                                    repliedMessageWords[k] = repliedMessageWords[k].replace(e, TeXemoji)
                            repliedMessageWords[k] = re.sub(r"(}}.?\\raisebox{-0.1em}{\\normalsize\\texttwemoji{)((?:\w|-)+)( skin tone}})", r": \2 skin tone}}", repliedMessageWords[k])
                            repliedMessageWords[k] = re.sub(r"{\\Large\\texttwemoji{person ((?:\w|\s|:|-)+)}}.?\\raisebox{-0\.1em}{\\Large\\texttwemoji{female sign}}️", r"{\\normalsize\\texttwemoji{woman \1}}", repliedMessageWords[k])
                            repliedMessageWords[k] = re.sub(r"{\\Large\\texttwemoji{person ((?:\w|\s|:|-)+)}}.?\\raisebox{-0\.1em}{\\Large\\texttwemoji{male sign}}️", r"{\\normalsize\\texttwemoji{man \1}}", repliedMessageWords[k])
                            
                        if "/" in repliedMessageWords[k]:
                            output += repliedMessageWords[k]
                        else:
                            output += repliedMessageWords[k] + " "
                        
                        # once the reply is too long to fit on one line, cut it off
                        # we have semi-arbitrarily defined "too long" to be 60 characters
                        if replyToLength > 60 and k != len(repliedMessageWords) - 1: 
                            output += " $\\ldots$"
                            break

                            # TO DO - add non-Latin script support in replies
                    
                    output += "}\n"
                if attachment["type"] == "image":
                    imagePresent += "\\includegraphics[width=7cm]{GroupMe_img/" + m["id"] + "_" + str(attachmentIndex) + "}\n"
                if attachment["type"] == "file":
                    pass # no longer needed, but might need it in the future
                if attachment["type"] == "video":
                    videoPresent = m["id"] + "_" + str(attachmentIndex) # becomes file path to image of video preview
                
                attachmentIndex += 1
        
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
            
        messageContent = m["text"].replace("\\", "\\textbackslash{}").replace("\n", "\\\\")
        
        # Emojis --------------------------------------------
        emojiContent = [c for c in messageContent if c in emoji.UNICODE_EMOJI['en']] 
        if emojiContent: # if the message has emojis, then transform them into LaTeX-readable commands
            for e in emojiContent:
                if e not in ["™", "®️"]: # exceptions - keep trademark symbols as Unicode characters
                    TeXemoji = emoji.demojize(e)[1:-1] # demojize, then remove colons at front and end
                    TeXemoji = TeXemoji.replace("_", ' ') # replace underscores with spaces
                    TeXemoji = "\\raisebox{-0.2em}{\\Large\\texttwemoji{" + TeXemoji + "}}"
                    messageContent = messageContent.replace(e, TeXemoji)
                
                emojiList.append(e)
            
            # handle the weird way Python emoji breaks up emojis involving skin color
            messageContent = re.sub(
                    r"(}}.?\\raisebox{-0.2em}{\\Large\\texttwemoji{)((?:\w|-)+)( skin tone}})",
                    r": \2 skin tone}}", messageContent
                )
            
            # handle the weird way Python emoji breaks up emojis involving gender
            messageContent = re.sub(r"{\\Large\\texttwemoji{person ((?:\w|\s|:|-)+)}}.?\\raisebox{-0\.2em}{\\Large\\texttwemoji{female sign}}️", r"{\\Large\\texttwemoji{woman \1}}", messageContent)
            messageContent = re.sub(r"{\\Large\\texttwemoji{person ((?:\w|\s|:|-)+)}}.?\\raisebox{-0\.2em}{\\Large\\texttwemoji{male sign}}️", r"{\\Large\\texttwemoji{man \1}}", messageContent)
        
        # URLs ---------------------------------------------
        if "https://" in messageContent or "http://" in messageContent:
            messageContent = re.sub(r"(https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*))", r"\\url{\1}", messageContent)

        # Process remaining text ---------------------------
        messageContent = messageContent.replace("^", "\\textasciicircum{}")
        if "Created new poll" in messageContent[0:16]:
            messageContent = messageContent.replace("Created new poll", "{\\itshape Created new poll") + "}"
        messageContent = messageContent.replace("- Shared a document: ", "Shared a document: ") # delete extra hyphen
        messageContent = messageContent.replace("Shared a document: ", "\\par\\vspace{1ex}\\raisebox{-1em}{\\includegraphics[height = 3em]{GroupMe_img/file_icon}}\\ \\emph{Shared a document: }")
        
        # If there isn't a URL in the message, replace the hashtag, ampersand, and other characters
        # with their LaTeX equivalents. If there is a URL in the message, then only replace those 
        # either preceding or following a space (depending on the character). This way, we won't
        # wreck characters that are already inside the argument of \url
        # This is a bit of a workaround, and it's easy to think of examples where these two
        # heuristics fail, but realistically (and from experience), this works most of the time
        if "\\url" not in messageContent:
            messageContent = messageContent.replace("#", "\\#")
            messageContent = messageContent.replace("$", "\\$")
            messageContent = messageContent.replace("&", "\\&")
            messageContent = messageContent.replace("%", "\\%")
            messageContent = messageContent.replace("_", "\\_")
            messageContent = messageContent.replace("~", "\\~{}")
        else:
            messageContent = messageContent.replace(" #", " \\#")
            messageContent = messageContent.replace(" $", " \\$")
            messageContent = messageContent.replace(" &", " \\&")
            messageContent = messageContent.replace("% ", "\\% ")
            messageContent = messageContent.replace("_\\", "\\_\\")
            messageContent = messageContent.replace(" ~", " \\~{}")
            if videoPresent: # change GroupMe video URLs into video previews
                messageContent = re.sub("\\\\url{(https://v.groupme.com/\S+)}", r"\n\n\\video{" + videoPresent + r"}{\1}", messageContent)
        
        messageContent = messageContent.replace(">","{>}")
        messageContent = messageContent.replace("<","{<}")
        messageContent = messageContent.replace("⟨", "$\\langle$")
        messageContent = messageContent.replace("⟩", "$\\rangle$")

        # prevent LaTeX spaces from treating the period in Dr. as the end of a sentence
        messageContent = re.sub("(dr|mr|prof|ms)\.\s", r"\1.\\ ", messageContent, flags = re.IGNORECASE)

        # Process non-Latin scripts ------------------------
        # If your GroupMe chat doesn't have a lot of non-Latin characters, it's a little faster to run
        # if you just comment these lines out.
        # Japanese
        messageContent = re.sub(u"([\u3000-\u30ff\uff01-\uff9f\uffe0-\uffee]+)", r"{\\fontspec{" + lang_font["jp"] + r"}\1}", messageContent)
        # Chinese
        messageContent = re.sub(u"((?:[\u4e00-\u9fff\u3000-\u303f\uff01-\uff63])+)", r"{\\fontspec{" + lang_font["zh"] + r"}\1}", messageContent)
        # Korean
        messageContent = re.sub(u"((?:[\u3130-\u318f\uac00-\ud7af\uff01-\uff63\uffa0-\uffee]+,?\s?)+)", r"{\\fontspec{" + lang_font["ko"] + r"}\1}", messageContent)
        # Hindi
        messageContent = re.sub(u"((?:[\u0900-\u097f]+,?\s?)+)", r"{\\fontspec[Script=Devanagari]{" + lang_font["hi"] + r"}\\texthindi{\1}}", messageContent)
        # Tamil
        messageContent = re.sub(u"((?:[\u0b82-\u0bf2]+,?\s?)+)", r"{\\fontspec[Script=Tamil]{" + lang_font["ta"] + r"}\\texttamil{\1}}", messageContent)
        # Bengali
        messageContent = re.sub(u"((?:[\u0980-\u09fe]+,?\s?)+)", r"{\\fontspec[Script=Bengali]{" + lang_font["bn"] + r"}\\textbengali{\1}}", messageContent)
        # Languages in Arabic script
        messageContent = re.sub(u"((?:[\u0600-\u06ff]+\s*)+)", r"\\textarabic{\1}", messageContent)
        # Gothic
        messageContent = re.sub(u"((?:[\U00010330-\U0001034F]+\s?)+)", r"{\\fontspec{" + lang_font["got"] + r"}\1}", messageContent)
        # Runic
        messageContent = re.sub(u"((?:[\u16a0-\u16f8]+\s?)+)", r"{\\fontspec{" + lang_font["runic"] + r"}\1}", messageContent)
        # Old Italic (Etruscan)
        messageContent = re.sub(u"((?:[\U00010300-\U0001032F]+\s?)+)", r"{\\fontspec{" + lang_font["ett"] + r"}\1}", messageContent)
        # Now, I bet you're wondering what kinds of groupchats I get myself into...

        # Add message content ------------------------------
        output += "\n" + messageContent + "\n"
        
        # Attach images ------------------------------------
        if imagePresent:
            output += "\n" + imagePresent + "\n"

        
        if m["name"] != "GroupMe":
            if prev_m["name"] != m["name"]:
                output += "\\end{senderFirstMessage}\n"
        else:
            output += "}\n"
            
        if m["favorited_by"]:
            output += "\n\\heart{" + ", ".join([getUser(user)[0] for user in m["favorited_by"]]) + "}\n"
            if len(m["favorited_by"]) > len(mostLiked["favorited_by"]):
                mostLiked = m
                mostLiked_list = [m]
            elif len(m["favorited_by"]) > len(mostLiked["favorited_by"]):
                mostLiked_list.append(m)
        
    except:
        failureStr += m["id"] + ": " + str(m["text"]) + "\n"
        
        
#print(output)


if failureStr:
    print("UH OH! THIS DIDN'T WORK:\n===================================")
    print(failureStr) # this way, we know which messages trigger errors in the code
    print("===================================\n")


f = open("GroupMeInput.tex", "w", encoding="utf-8")
f.write(output)
f.close()

# Uncomment these just for fun :)
# =======================================================================
# mostWords       # what message has the most words?
# mostChars       # what message has the most characters?
# oneCharList     # what messages were exactly one character long?
# mostSubstr_list # what messages contained the substring `coolSubstr` the most times? Case is ignored
# mostChars_no_e  # what was the longest message that didn't contain the letter e?
# mostLiked_list  # what messages were tied for the most liked messages?
# emojiList       # what emojis appeared in the chat?
#
# print("In the message with the most words, there were {} words in total".format(len(mostWords["text"].split())))
# print("In the message with the most characters, there were {} characters in total".format(len(mostChars["text"])))
#
# oneCharList_chars = [m["text"] for m in oneCharList]
# oneCharList_freqs = []
# for c in oneCharList_chars:
#     oneCharList_freqs.append([ord(c), oneCharList_chars.count(c)])
# mostFreqOneCharMessage = oneCharList_freqs[np.argmax(np.array(oneCharList_freqs)[:,1])]
# print("There were {} messages with exactly one character, and the most frequent one-character message was \"{}\", which occurred {} times"\
#       .format(len(oneCharList), chr(mostFreqOneCharMessage[0]), mostFreqOneCharMessage[1]))
#
# emojiFreqs = []
# for e in emojiList:
#     emojiFreqs.append([ord(e), emojiList.count(e)])
# mostFreqEmoji = emojiFreqs[np.argmax(np.array(emojiFreqs)[:,1])]
# print("The most common emoji was {}, which appeared a total of {} times"\
#       .format(chr(mostFreqEmoji[0]), mostFreqEmoji[1]))