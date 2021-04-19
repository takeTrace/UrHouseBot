# Notify Tools

import requests
import json
import private

def slackMe(content):
    slack_data = {
        'text': content,
        'type': 'mrkdwn',
    }
    response = requests.post(private.slackBotOpenInfoShare,
                             data=json.dumps(slack_data),
                             headers={'Content-Type': 'application/json'})
    if response.status_code != 200:
        raise ValueError(
            'Request to slack returned an error %s, the response is:\n%s' %
            (response.status_code, response.text))


def colorTitle(title):
    return f"{bcolors.OKGREEN}{title}{bcolors.ENDC}"


class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
