# GroupMe-2-PDF

GroupMe-2-PDF is a utility that converts a GroupMe chat into a PDF. GroupMe is a popular messaging app that has spread thanks to its ability to create group chats and instantly add new members, even those without GroupMe accounts. Although available through both a mobile app and a web app, GroupMe for web lacks a significant amount of the functionality of the mobile app, such as search features, which hinders its use in important communications. On the other hand, the GroupMe mobile app has all the inconveniences of mobile devices:  small screen size, limited ability to use a keyboard or mouse, and limited ability to work with other apps. For those who need to search chats for old but critically important messages, neither of these two choices is particularly desirable.

The generation of a PDF from a GroupMe chat facilitates searching through old messages, and it archives chats so that future can benefit from reading a conversation without having to join the group chat. GroupMe-2-PDF relies on a modern distribution of these programs to:
- XeLaTeX or LuaLaTeX
- Python

## Creating a GroupMe API token

A GroupMe API token grants you access to the chats your account is a part of. To create a token for your account, you can visit the [GroupMe developer authentication tutorial](https://dev.groupme.com/tutorials/oauth), and click on "Create Application." This page will also show you how to obtain the IDs of the group chats you are part of, which you'll need for GroupMe-2-PDF to know which chat to convert to PDF.

You can set your Callback Host to `localhost` if you don't have a callback URL that you have access. 

## Generating a PDF

To get started, you'll need to download the contents of this repository. The Python and LaTeX files run with the assumption that you are using the directory structure of this repository.

Once you have the group ID of the chat you want to convert, you should open `GroupMe webscraper.py`, and set the `groupID` value. Set the `token` value to your GroupMe token. You can then run the Python script from the beginning. This will create several new files: a JSON of all the messages, a file called `GroupMeInput.tex`, and images from your chat (which will be saved to `GroupMe_img`). 

Before you proceed to the next step, you'll need to install the [`twemojis`](https://ctan.org/pkg/twemojis) package for LaTeX in order for the PDF to successfully include emojis. It is possible to manually edit the Python code to include Unicode emojis, rather than turning them into LaTeX-readable commands, but I hope to have an alternative way to add emojis for those who don't wish to install the `twemojis` package.

To generate the actual PDF, run XeLaTeX or LuaLaTeX on the file `GroupMe webscraper output.tex`. If TeX throws an error, you can input `R` into the terminal to attempt to get TeX to fix the error on its own, or you can edit the other .tex file, `GroupMeInput`, to remove the error. Congratulations! You've now archived your GroupMe in the form of a PDF.

## Customization

Most of the commands to generate structure in the PDF can be found in the .tex file. If you want to increase or decrease the amount of whitespace, or change the font, you can edit the .tex file directly. 

To set the time zone of the timestamps in the PDF, you can change the `to_zone` variable in the Python script.
