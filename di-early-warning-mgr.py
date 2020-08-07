import json
import os
from botocore.vendored import requests
from datetime import datetime
import dateutil.parser

def read_sns_event(_event):
    '''
    Reads SNS alarms and returns subject line
    Input a JSON in any of the following format 
    // JSON type-1 
    {
        "Records": [
            "Sns": {
                "AlarmName": "..."
                "Message": "{
                    "AlarmName": "...",
                    "Trigger": {
                        "Namespace": "..."
                    }
                }", 
                ...
            }
        ]
    }


    '''
    # Read SNS alarm 
    msg_txt = ""
    meta_info = ""
    try:
        # validate json
        c_data = _event

        if 'Records' not in c_data.keys():
            return "ERROR: Records not found"
        else:
            c_data = c_data["Records"]
        
        if type(c_data) != type([1,2]):
            return "ERROR: List in Records not found"
        else: 
            c_data = c_data[0]
        
        if 'Sns' not in c_data.keys():
            return "ERROR: Sns not found in Records"
        else:
            c_data = c_data["Sns"]
        
        if 'Message' not in c_data.keys():
            return "ERROR: Message not found in Records"
        else:
            c_data = c_data["Message"]
        
        try:
            a_data = json.loads(c_data)
        except Exception:
            return "ERROR: Message can not be parsed as JSON"

        c_data = a_data
        if 'AlarmName' not in c_data.keys():
            return "ERROR: AlarmName not found in Message"
        else:
            a_name = c_data["AlarmName"]
            a_name_bow = a_name.split("-")
            a_resource = a_name_bow[1]
            a_indication = a_name_bow[2]

        if 'Region' not in c_data.keys():
            return "ERROR: region not found in Message"
        else:
            # Additional information
            d_region = c_data["Region"]

        if 'StateChangeTime' not in c_data.keys():
            return "ERROR: StateChangeTime not found in Message"
        else:
            d_date = dateutil.parser.parse(c_data["StateChangeTime"])

        if 'Trigger' not in c_data.keys():
            return "ERROR: Trigger not found in Message"
        elif 'Namespace' not in c_data["Trigger"].keys():
            return "ERROR: Namespace not found in Message"
        else:
            a_namespace = c_data["Trigger"]["Namespace"]
        
        # Date format: YYYY-MM-DD HH24:MI:SS
        meta_info = "\nRegion: {} \n{}-{}-{} {}:{}:{}".format(d_region, d_date.year, d_date.month, d_date.day, d_date.hour, d_date.minute, d_date.second) 

        # Result
        # "{Namespace} {AlarmName[1]} is {AlarmName[2]} on {AlarmName[3:]]}"
        msg_template = "{} {} is {} on {}"
        msg_txt = msg_template.format(a_namespace, a_resource, a_indication, " ".join(a_name_bow[3:]))
    
    except Exception as v:
        print ("ERROR: event can not be parsed as JSON \nOR\nsome other error as ", v)


    
    return msg_txt + meta_info

def lambda_handler(event, context):
    if event:
        slack_channel = os.environ['slack_channel']
        #slack_channel = "https://hooks.slack.com/services/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"
        
        # Alarm data
        msg_txt = read_sns_event(event)
        
        if msg_txt.startswith("ERROR"):
            print (msg_txt)
            return {"statusCode": 403, "body": msg_txt}

        # Slack JSON data
        _data = {"text": msg_txt }
        
        # Send notification to Slack channel
        try:
            response = requests.post(url=slack_channel, data=json.dumps(_data))
        except Exception as e:
            raise e
    
        return {"statusCode": response.status_code, "body": msg_txt}
