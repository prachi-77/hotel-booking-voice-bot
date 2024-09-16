

def close(session_attributes, active_contexts, fulfillment_state, intent, message):
    print("close intent triggered--")
    response = {
        'sessionState': {
            'activeContexts':[{
                'name': 'intentContext',
                'contextAttributes': active_contexts,
                'timeToLive': {
                    'timeToLiveInSeconds': 600,
                    'turnsToLive': 1
                }
            }],
            'sessionAttributes': session_attributes,
            'dialogAction': {
                'type': 'Close',
            },
            'intent': intent,
        },
        'messages': [{'contentType': 'PlainText', 'content': message}]
    }

    return response

def confirm_intent(session_attributes,intentName,slot):
   
    return {
    "sessionState":{
        "sessionAttributes": session_attributes,
        "dialogAction":{
            "slotToElicit":slot,
            "type":"ElicitSlot"
        },
        "intent":{
            "confirmationState":"None",
            "name":intentName,
            "state":"InProgress"
        }
    }
    }


def elicit_slot(session_attributes, active_contexts, intent, slot_to_elicit, message):
  
    return {
        "sessionState": {
            "activeContexts": [
                {
                    "name": "intentContext",
                    "contextAttributes": active_contexts,
                    "timeToLive": {"timeToLiveInSeconds": 600, "turnsToLive": 1},
                }
            ],
            "sessionAttributes": session_attributes,
            "dialogAction": {"type": "ElicitSlot", "slotToElicit": slot_to_elicit},
            "intent": intent,
        },
        "messages": message,
    }
