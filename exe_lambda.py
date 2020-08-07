import boto3
import json
import datetime
import os
import sys

# Python 2.7
client = boto3.client('lambda')
time_now = datetime.datetime.now().isoformat()

def load_config(file_path):
    '''
    Expects a JSON file path as input
    Returns configuration as a dictionary
    This **WILL** ignore any new line in the config file
    '''
    t = None
    d_data = None
    try:
        f = open(file_path, "r")
        t = f.read()
    except Exception as e1:
        print "ERROR in loading configuration file. Please check that the path is correct."
        return None
    try:
        d_data = json.loads(t.replace('\n', ''))
    except Exception as e2:
        print "Error in parsing JSON"
        return None
    return d_data
        
def alert_admin(server, aws_region):
    '''
    Expects server name and AWS region
    Executes lambda 
    '''
    j_data = {
        "Records":  [
                        {
                            "Sns": {
                                    "AlarmName": "awsec2-" + server + "-Low-Free-Disk-Space",
                                    "Message": "{\"AlarmName\": \"awsec2-" + server + "-Low-Free-Disk-Space\",\"Trigger\": {\"Namespace\": \"AWS/EC2\"},\"StateChangeTime\": \"" + time_now + "\", \"Region\":\"" + aws_region + "\"}"
                                   }
                        }
                    ]
    }

    try:
            response = client.invoke(
            FunctionName='di-early-warning-mgr',
            InvocationType='RequestResponse',
            LogType='None',
            Payload=json.dumps(j_data)
        )
            if response['StatusCode'] != 200:
                    if 'FunctionError' in response.keys():
                            print response['FunctionError']
    except Exception as e:
        print e

def get_fs_usage(part_name):
    '''
    Expects device name (disk)
    Returns the usage in percentage 
    '''
    os.system("df -BG | grep '" + part_name + "' | cut -d'G' -f 4 | cut -d'%' -f 1 > fs_check.log")
    usage = None
    try:
        f = open("fs_check.log", "r")
        w = f.readline()
        f.close()
        usage = int(w)
    except Exception as e:
        print e
        return None
    return usage
        
def drive():
    if len(sys.argv) != 2:
        print "usage: " + sys.argv[0] + " /path/to/config.json"
        return EXIT_WARN
    else:
        cfg = load_config(sys.argv[1])
        if cfg == None:
            print "Failed to load configuration. Exiting."
            return EXIT_ERR
            
    fs_used = get_fs_usage(cfg["part_name"])
    if fs_used:
        if fs_used > cfg["threshold"]:
            alert_admin(cfg["server"], cfg["aws_region"])
    else:
        print "Unable to fetch disk uage"
        return EXIT_ERR
        
    return EXIT_OK

# MAIN
# ----
EXIT_OK = 0
EXIT_ERR = -1
EXIT_WARN = 1
drive()
