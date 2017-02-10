import os
import time
from slackclient import SlackClient
from random import randint
from Crypto.Cipher import AES

# ## Bot Setup ##

BOT_NAME = 'guesser'
SLACK_BOT_TOKEN = '' #slackbot token (unique)

#slack_client = SlackClient(os.environ.get('SLACK_BOT_TOKEN'))

slack_client = SlackClient(SLACK_BOT_TOKEN)
api_call = slack_client.api_call("users.list")
if api_call.get('ok'):
    # retrieve all users so we can find our bot\n",
    users = api_call.get('members')
    for user in users:
        if 'name' in user and user.get('name') == BOT_NAME:
            print("Bot ID for '" + user['name'] + "' is " + user.get('id'))
            BOT_ID = user.get('id')
    print('loop completed')
else:
    print("could not find bot user with the name " + BOT_NAME)


# starterbot's ID as an environment variable
#BOT_ID = os.environ.get("BOT_ID")

# constants
AT_BOT = "<@" + BOT_ID + ">"
EXAMPLE_COMMAND = "do"

# instantiate Slack & Twilio clients
slack_client = SlackClient(SLACK_BOT_TOKEN)


# ## Parsing output  ##

def parse_slack_output(slack_rtm_output):
    """
        The Slack Real Time Messaging API is an events firehose.
        this parsing function returns None unless a message is
        directed at the Bot, based on its ID.
    """
    output_list = slack_rtm_output
    if output_list and len(output_list) > 0:
        for output in output_list:
            if output and 'text' in output and AT_BOT in output['text']:
                # return text after the @ mention, whitespace removed
                return output['text'].split(AT_BOT)[1].strip(),                        output['channel']
    return None, None

def encryptMessage(key, iv, message):
    obj = AES.new(key, AES.MODE_CBC, iv)
    msg16 = messageBlock16(message)
    cipherText = obj.encrypt(message)
    return cipherText

def decryptMessage(key, iv, cipherText):
    obj = AES.new(key, AES.MODE_CBC, iv)
    message = obj.decrypt(cipherText)
    return message.rstrip()

def messageBlock16(message):
    if(len(message) % 16 != 0):
        nblocks = len(message)// 16
        appendSize = 16 - ((nblocks * 16 - len(message))% 16)
        for i in range(appendSize):
            message += " "
    return message


# ## State Machine Definitions ##

class State:
    def handle_command(self, command, channel):
        assert 0, "handle command not implemented"

class InitialState(State):

    def __init__(self):
        print("creating InitialState")


    def handle_command(self, command, channel):
        print("InitialState receiving " + command)
    
        
        if(command == "/help"):
            response = "Current accepted commands: /guess /text /endbot " + command
            slack_client.api_call("chat.postMessage", channel=channel, text=response, as_user=True)
            return InitialState()
        
        if(command == "/guess"):
            response = "Guessing Number Game Started \n Start guessing or '/quitgame' to quit"
            slack_client.api_call("chat.postMessage", channel=channel, text=response, as_user=True)
            global target_number
            target_number = randint(1,100)
            self.current_state = GameState()
            self.READ_WEBSOCKET_DELAY = 1 #1 second delay
            while True:
                command, channel = parse_slack_output(slack_client.rtm_read())
                if command and channel:
                    print('com:' + str(command))
                    print('chan:' +str(channel))
                    #self.guess_history.append(command)
                    self.current_state = self.current_state.handle_command(command,channel)
                    if( self.current_state == None):
                        print('Quitting Game')
                        #print('number is',target_number)
                        break
                    #handle_command(command, channel)
                    time.sleep(self.READ_WEBSOCKET_DELAY)
            return InitialState()
        if(command == "/text"):
            print ("hello world")
            response = "To Be continued.... " + command
            slack_client.api_call("chat.postMessage", channel=channel, text=response, as_user=True)
            return InitialState()
        if(command == "/endbot"):
            response = "Bye"
            slack_client.api_call("chat.postMessage", channel=channel, text=response, as_user=True)
            return None
        else:
            response = "I don't recognize this command " + command
            slack_client.api_call("chat.postMessage", channel=channel, text=response, as_user=True)
            return InitialState()
               


# ## Guessing Game Related States ##

class GameState(State):
    def __init__(self):
        print("Number Guessing Game Loop")
    def handle_command(self, command, channel):
        print("GameState receiving " + command)
        try:
            value = int(command)
        except:
            word_list = command.split()
            if(command == "/quitgame" ):
                response = "Thanks for playing"
                slack_client.api_call("chat.postMessage", channel=channel, text=response, as_user=True)
                return None
            if ('sucks' in word_list or 'hate' in word_list):
                response = "Sorry you feel that way."
                slack_client.api_call("chat.postMessage", channel=channel, text=response, as_user=True)
            else:
                response = "I don't recognize this as a number: " + command
                slack_client.api_call("chat.postMessage", channel=channel, text=response, as_user=True)
            return GameState()
        if(value < target_number):
            response= "too low"
            slack_client.api_call("chat.postMessage", channel=channel, text=response, as_user=True)
            return GameState()
        if(value > target_number):
            response= "too high"
            slack_client.api_call("chat.postMessage", channel=channel, text=response, as_user=True)
            return GameState()
        if(value == target_number):
            response= "correct! \n\'/guess\' to play again"
            slack_client.api_call("chat.postMessage", channel=channel, text=response, as_user=True)
            return None



class stateMachine:
    def __init__(self):
        self.guess_history = []
        self.current_state = InitialState()
        self.READ_WEBSOCKET_DELAY = 1 #1 second delay

    def run(self):
        if slack_client.rtm_connect():
            print("StarterBot connected and running!")
            while True:
                command, channel = parse_slack_output(slack_client.rtm_read())
                if command and channel:
                    print('com:' + str(command))
                    print('chan:' +str(channel))
                    self.guess_history.append(command)
                    self.current_state = self.current_state.handle_command(command,channel)
                    if( self.current_state == None):
                        print('Quitting Bot')
                        #print('number is',target_number)
                        break
                    #handle_command(command, channel)
                    time.sleep(self.READ_WEBSOCKET_DELAY)
        else:
            print("Connection failed. Invalid Slack token or bot ID?")


if __name__ == "__main__":
    values = {'Robert': randint(1,20),
             'John': randint(1,20),
             'Anna': randint(1,20)}
    print(values)
    target_number = randint(1,100)
    bot = stateMachine()
    bot.run()

print("thats all folks")




