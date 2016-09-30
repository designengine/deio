from __future__ import print_function

import sys
sys.path.append('./libs')

import boto3
import json
import requests
import urllib2
import urllib
import re
import base64


dynamo = boto3.client('dynamodb')

print('Loading function')


DEIO_AI_URL = 'http://deio-ai-api-loadbalancer-136587519.us-east-1.elb.amazonaws.com/visual.addStyle'
style_models = ['starrynight', 'seurat', 'composition', 'cubist', 'edtaonisl', 'hundertwasser', 'hokusai', 'kandinsky', 'elefant_0', 'dee', 'slack']


def slack_api(params, method='chat.postMessage'):
    """
    Super simple Slack API call
    """
    SLACK_API = 'https://slack.com/api/' + method

    # url = SLACK_API + urllib.urlencode(params)
    #
    # print("URL:", url)
    # content = urllib2.urlopen(url)

    r = requests.get(SLACK_API, params=params)

    return r.text

def get_slack_file(url, token):

    headers = {
        'Authorization': 'Bearer ' + token
    }

    request = urllib2.Request(url, headers=headers)
    img = urllib2.urlopen(request).read()
    img_base64 = base64.b64encode(img)

    return img_base64

def deio_stylize(img_base64, style='cubist'):

    print("Calling DEIO server")

    payload = {
        "image": img_base64,
        "style": style
    }

    content = requests.post(DEIO_AI_URL, json=payload)

    print("DEIO server responded with", content.text)
    return content.json()


def lambda_handler(event, context):
    # print("Received event: " + json.dumps(event, indent=2))
    sns_message = json.loads(event['Records'][0]['Sns']['Message'])
    print("From SNS: " + str(sns_message))

    team = dynamo.get_item(TableName='Team',
        Key={
            'id': {'S': sns_message['team_id']}
        }
    )
    team_token = team['Item']['bot']['M']['token']['S']

    # Check general call is ok.
    if 'event' not in sns_message:
        pass

    # If event is type message, and subtype file_comment or file_shared
    # Have to accept both subtypes because Slack might only send 1 message for new file with 1 comment.
    elif sns_message['event']['type'] == 'message' and (sns_message['event']['subtype'] == 'file_comment'  or sns_message['event']['subtype'] == 'file_share'):

        user_comment = sns_message['event']['comment']['comment']
        user_comment = user_comment.lower()

        # Look for keyword
        style_match = re.match("stylize (\w+)", user_comment)

        # Verify that style name exists
        if style_match and style_match.group(1) in style_models:

            style = style_match.group(1)

            params = {
                'token': team_token,
                'channel': sns_message['event']['channel'],
                'text': "Sure, I will start working on it."
            }
            response = slack_api(params)

            # Get Slack file
            slack_file = sns_message['event']['file']

            # Default image to use is thumb_480
            # if not available, then image is smaller. So use original image.
            # TODO. When plans active, make sure to use original for paying plans.
            if 'thumb_480' not in slack_file:
                url_slack_img = slack_file['url_private']
            else:
                url_slack_img = slack_file['thumb_480']

            img_base64 = get_slack_file(url_slack_img, team_token)

            deio_response = deio_stylize(img_base64, style=style)
            print('DEIO reponse', deio_response)

            if deio_response['ok']:
                params = {
                    'token': team_token,
                    'channel': sns_message['event']['channel'],
                    'text': deio_response['visual']['url']
                }

                response = slack_api(params)

                print("Slack API response:", response)
            return

        # Don't know style, so send informative message.
        else:

            params = {
                'token': team_token,
                'channel': sns_message['event']['channel'],
                'text': 'Sorry, I don\'t know that style. The styles I know are: ' + '_' + '_, _'.join(style_models) + '_'
            }

            response = slack_api(params)
            print(response)

    # Event is message but not comment in file
    elif sns_message['event']['type'] == 'message':
        user_message = sns_message['event']['text']

        if user_message == 'styles':
            params = {
                'token': team_token,
                'channel': sns_message['event']['channel'],
                'text': 'I can paint the following styles: ' + '_' + '_, _'.join(style_models) + '_'
            }
            response = slack_api(params)


    return
