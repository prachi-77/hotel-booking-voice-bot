from helpers.get_current_location import *
from helpers.lex_response import *
import logging
import traceback
import json
import dateutil.parser
import datetime
import time

logging.basicConfig(level = logging.INFO)

logger = logging.getLogger()

def is_valid_date(date):
    try:
        dateutil.parser.parse(date)
        return True
    except ValueError:
        return False

def get_plain_text_msg(msg):
    if isinstance(msg,list):
        msg_list = []
        for i in msg:
            msgContent = {'contentType': 'PlainText', 'content':  i}
            msg_list.append(msgContent)
        return msg_list
    else:
        return [{'contentType': 'PlainText', 'content':  msg}]

def build_validation_result(isvalid, violated_slot, message_content):
    return {
        'isValid': isvalid,
        'violatedSlot': violated_slot,
        'message': message_content
        #'message': {'contentType': 'PlainText', 'content': message_content}
    }
def add_days(date, number_of_days):
    # new_date = dateutil.parser.parse(date).date()
    new_date = date
    new_date += datetime.timedelta(days=number_of_days)
    return new_date.strftime('%Y-%m-%d')

def safe_int(n):
    """
    Safely convert n value to int.
    """
    if n is not None:
        return int(n)
    return n

def get_json_data(x):
    json_data = {'shape': 'Scalar', 'value': {'originalValue': x, 'resolvedValues': [x], 'interpretedValue': x}}
    return json_data

def response_card(messageContent,title,subTitle,buttons):
    
    msg =  [
            {'contentType': 'PlainText', 'content': messageContent},
            {
            "contentType": "ImageResponseCard",
            "content": 'xyz',
            "imageResponseCard": 
                {
                    "title": title,
                    "subtitle": subTitle,
                    "buttons": buttons
                }
    }
    ]
    
    return msg

def handle_book_room_intent(session_attributes,event):
    active_contexts= {}
    slots = event['sessionState']['intent']['slots']
    lat_value_slot = slots.get('latitude')
    long_value_slot = slots.get('longitude')
    lat_value = ''
    long_value = ''
    if lat_value_slot is not None:
        if 'interpretedValue' in lat_value_slot["value"]:
            lat_value = lat_value_slot["value"]["interpretedValue"]
        else:
            lat_value = lat_value_slot["value"]["originalValue"]
       
        
    else:
        return elicit_slot(
            session_attributes,
            active_contexts,
            event['sessionState']['intent'],
            "latitude",
            get_plain_text_msg("Please enter the latitude coordinates displayed on your webpage.")
            )   
    
    if long_value_slot is not None:
        if 'interpretedValue' in long_value_slot["value"]:
            long_value = long_value_slot["value"]["interpretedValue"]
        else:
            long_value = long_value_slot["value"]["originalValue"]
       
        
    else:
        return elicit_slot(
            session_attributes,
            active_contexts,
            event['sessionState']['intent'],
            "longitude",
            get_plain_text_msg("Please enter the longitude coordinates displayed on your webpage.")
            ) 
    print("lat---",lat_value, long_value)
    # lat = 19.0152704
    # long = 19.0152704,73.0988544
    #disabling this for now as it allows only 1000 calls a day
    location_info = get_user_location_details(lat_value,long_value)
    # location_info = {'location': {'city': 'Panvel', 'country': 'India',
    # 'postcode': '410218',
    # 'address': 'Panvel, Panvel Taluka, Raigad, Maharashtra, 410218, India',
    # 'lat': '19.015328705343283', 'long': '73.09885188830808'},
    # 'currency': 'INR'}
   
    lat_float = float(location_info['location']['lat'])
    long_float = float(location_info['location']['long'])

    #setting slot value
    
    # event['sessionState']['intent']['slots']['Location'] = json.dumps(location_info['location']['address'])
    session_attributes['LocationValue'] = (location_info['location']['address'])
    session_attributes['CityValue'] = (location_info['location']['city'])
    session_attributes['CountryValue'] = (location_info['location']['country'])
    session_attributes['CurrencyValue'] = (location_info['currency'])
    
    event['sessionState']['intent']['slots']['Location'] = get_json_data(location_info['location']['address'])
    event['sessionState']['intent']['slots']['City'] = get_json_data(location_info['location']['city'])
    event['sessionState']['intent']['slots']['Country'] = get_json_data(location_info['location']['country'])
    event['sessionState']['intent']['slots']['Currency'] = get_json_data(location_info['currency'])
    
    message = (
        f"Your detected location is {location_info['location']['address']}. "
        f"The local currency here is {location_info['currency']}. "
        f"Your coordinates are approximately {lat_float:.6f}° latitude and "
        f"{long_float:.6f}° longitude."
        )
    buttons = [{"text": "Yes", "value": "search hotel api"},
                {"text": "No", "value": "Bye"}]

    return elicit_slot(
        session_attributes,
        active_contexts,
        event['sessionState']['intent'],
        "ConfirmLocation",
        response_card(message,
                      "Do you want to search for hotels here?",
                      "Do you want to search for hotels here?",
                      buttons
        )
    )

def handle_hotel_selection(session_attributes, event):
    slots = event['sessionState']['intent']['slots']
    selected_hotel = slots.get('SelectedHotel')

    if selected_hotel:
        hotel_name = selected_hotel['value']['interpretedValue'] if 'interpretedValue' in selected_hotel['value'] else selected_hotel['value']['originalValue']
        print("hotel is set---",hotel_name)
        # Save the selected hotel in session attributes
        session_attributes['SelectedHotel'] = hotel_name
        
        # Prepare a message to confirm the booking
        message1 = f"I see you have selected {hotel_name}. I will need few details in order to do your booking. Let's start with your name."
        message2 = "Please enter your name."
        return confirm_intent(session_attributes, "ProvideDetails", "Name")
      
    else:
        # If the user hasn't selected anything or something went wrong, re-prompt
        return elicit_slot(
            session_attributes,
            {},
            event['sessionState']['intent'],
            "SelectedHotel",
            get_plain_text_msg("Please select a hotel from the options provided.")
        )


def handle_search_room_intent(session_attributes,event):
    active_contexts= {}
    slots = event['sessionState']['intent']['slots']
    check_in_date_slot = slots["CheckInDate"]
    nights_slot = slots["StayDuration"]
    total_adults_slot = slots['NumberOfAdults']
    check_in_date = 0
    if check_in_date_slot is not None:
        if 'interpretedValue' in check_in_date_slot["value"]:
            check_in_date = check_in_date_slot["value"]["interpretedValue"]
        else:
            check_in_date = check_in_date_slot["value"]["originalValue"]
       
        if not is_valid_date(check_in_date):
            return elicit_slot(
            session_attributes,
            active_contexts,
            event['sessionState']['intent'],
            "CheckInDate",
            get_plain_text_msg("I did not understand your check in date. Ensure your date is in correct format yyyy-mm-dd")
        
            )
        check_in_date = dateutil.parser.parse(check_in_date) 
        
        
        if check_in_date.date() <= datetime.date.today():
            
            return elicit_slot(
            session_attributes,
            active_contexts,
            event['sessionState']['intent'],
            "CheckInDate",
            get_plain_text_msg("Reservations must be scheduled at least one day in advance.  Can you try a different date?")
        
            )
            
    else:
        return elicit_slot(
        session_attributes,
        active_contexts,
        event['sessionState']['intent'],
        "CheckInDate",
        get_plain_text_msg("Please enter your check-in date in yyyy-mm-dd format.")
        )
    if nights_slot is not None:
        if 'interpretedValue' in nights_slot["value"]:
            nights = safe_int(nights_slot["value"]["interpretedValue"])
        else:
            nights = safe_int(nights_slot["value"]["originalValue"])

        if (nights < 1 or nights > 30):
            return elicit_slot(
            session_attributes,
            active_contexts,
            event['sessionState']['intent'],
            "StayDuration",
            get_plain_text_msg("You can make a reservations from one to thirty nights.  How many nights would you like to stay for?")
            )
            
    else:
        return elicit_slot(
        session_attributes,
        active_contexts,
        event['sessionState']['intent'],
        "StayDuration",
        get_plain_text_msg("Please enter the number of days that you would like to stay")
       
        )
    
    if total_adults_slot is not None:
        if 'interpretedValue' in total_adults_slot["value"]:
            adults_count = safe_int(total_adults_slot["value"]["interpretedValue"])
        else:
            adults_count = safe_int(total_adults_slot["value"]["originalValue"])

        if (adults_count<1):
            return elicit_slot(
            session_attributes,
            active_contexts,
            event['sessionState']['intent'],
            "NumberOfAdults",
            get_plain_text_msg("Atleast 1 adult is required.")
            )
            
    else:
        return elicit_slot(
        session_attributes,
        active_contexts,
        event['sessionState']['intent'],
        "NumberOfAdults",
        get_plain_text_msg("How many adults will be staying?")
       
        )
    checkout_date  = add_days(check_in_date, safe_int(nights))

    hotel_info = {}
    hotel_info['city'] = session_attributes['CityValue']
    hotel_info['country'] = session_attributes['CountryValue']
    hotel_info['checkInDate'] = str(check_in_date.date())
    hotel_info['checkOutDate'] = checkout_date
    hotel_info['currency'] = session_attributes['CurrencyValue']
    hotel_info['adults'] = adults_count
    session_attributes['CheckOutDate'] = checkout_date
    session_attributes['CheckInDate'] = str(check_in_date.date())
    session_attributes['StayDuration'] = nights
    session_attributes['NumberOfAdults'] = adults_count
    event['sessionState']['intent']['slots']['CheckOutDate'] = get_json_data(checkout_date)

    # all_hotel_result = search_hotels(hotel_info)
    # session_attributes['SearchedHotelsInfo']= all_hotel_result
 
    # properties = all_hotel_result['properties']
    # selected_property = properties
    # options = [create_hotel_option(hotel) for hotel in selected_property[:5]]  # Show first 5 hotels
    # search_hotel_result = options

    search_hotel_result = read_txt()  # Show first 5 hotels
    print("search hotel result",search_hotel_result)
    if "error" in search_hotel_result:
        error_message = "Unexpected error occured while searching hotels via api"
        return close(session_attributes, active_contexts, 'Failed', event['sessionState']['intent'], error_message)

    else: 
        return elicit_slot(
            session_attributes,
            active_contexts,
            event['sessionState']['intent'],
            "SelectedHotel",
            response_card("Please select a hotel from the options below:",
                            "Available Hotels",
                            "Available Hotels",
                            search_hotel_result)
        )

    return close(session_attributes, active_contexts, 'Fulfilled', event['sessionState']['intent'], msg)

def handle_confirm_booking_intent(session_attributes,event):
    # hotel = selected_hotel_details(session_attributes['SearchedHotelsInfo'],session_attributes['SelectedHotel'])
    hotel = selected_hotel_details(session_attributes['SelectedHotel'])
    hotel_name = hotel["name"]
    total_price = hotel["total_rate"]["lowest"]
    check_in_time = hotel["check_in_time"]
    check_out_time = hotel["check_out_time"]
    amenities = ", ".join(hotel["amenities"])
    if 'link' in hotel:
        link = hotel["link"]
    else:
        link = "Not Available"

    message = '''Okay, I have you down for a {} night stay in {} starting 
            {}. Your Booking Details are: Hotel Name: {}, Total Price: {}, Check In time : {}
            Check Out time :{}, Hotel Link: {}'''.format(session_attributes['StayDuration'], session_attributes['CityValue'],session_attributes['CheckInDate'],hotel_name,total_price,check_in_time,
                                                         check_out_time,link)
    
    buttons = [{"text": "Yes", "value": "Yes"}, {"text": "No", "value": "Bye"}]                                                   
    return elicit_slot(
            session_attributes,
            {},
            event['sessionState']['intent'],
            "ConfirmHotelBooking",
            response_card(message,
                            "Shall I book the reservation?",
                            "Shall I book the reservation?",
                            buttons)
        )

def lambda_handler(event, context):
    try:
        print("event--",event)
        intent_name = event['interpretations'][0]['intent']['name']
        session_attributes = event['sessionState']['sessionAttributes']
        slots = event['sessionState']['intent']['slots']
        match intent_name:
            case 'BookHotelRoom':
                print("Book Room Intent")
                session_attributes['sessionId'] = event['sessionId']
                return handle_book_room_intent(session_attributes,event)
            case 'SearchNearbyHotels':
                print("Search Nearby Hotel Intent")
                session_attributes['sessionId'] = event['sessionId']
                
                selected_hotel_slot = slots['SelectedHotel']
                
                if selected_hotel_slot is not None:
                    session_attributes['SelectedHotel'] = selected_hotel_slot["value"]["interpretedValue"]
                    # once hotel is selected, trigger next intent
                    return handle_hotel_selection(session_attributes, event)
                return handle_search_room_intent(session_attributes,event)
            case 'ConfirmBooking':
                confirm_booking_slot = slots['ConfirmHotelBooking']
                print("Confirm Booking Intent Triggered")
                if confirm_booking_slot is not None:
                    response = confirm_booking_slot['value']['interpretedValue'] if 'interpretedValue' in confirm_booking_slot['value'] else confirm_booking_slot['value']['originalValue']
                    if response=="Yes":
                        prompt = "Thanks, I have placed your reservation. Have a Good Day. Bye :)"
                        return close(session_attributes, {}, 'Fulfilled', event['sessionState']['intent'], prompt)

                return handle_confirm_booking_intent(session_attributes,event)
                

        
    except Exception as e:
        prompt = "Unable to generate prompt at the moment. Please try again later."
        active_contexts = {}
        logger.error(f"Found error -- {e}")
        traceback.print_exc()
        return close(session_attributes, active_contexts, 'Fulfilled', event['sessionState']['intent'], prompt)



event =  {'sessionId': 'us-east-1:886280b7-aed3-c56b-5112-9222f4cb608e', 'inputTranscript': 'pc@mail.com', 'interpretations': [{'intent': {'confirmationState': 'None', 'name': 'ConfirmBooking', 'slots': {'ConfirmHotelBooking': None}, 'state': 'InProgress'}}, {'nluConfidence': 0.53, 'intent': {'confirmationState': 'None', 'name': 'Greeting', 'slots': {}, 'state': 'InProgress'}, 'interpretationSource': 'Lex'}, {'nluConfidence': 0.48, 'intent': {'confirmationState': 'None', 'name': 'Goodbye', 'slots': {}, 'state': 'InProgress'}, 'interpretationSource': 'Lex'}, {'nluConfidence': 0.48, 'intent': {'confirmationState': 'None', 'name': 'SearchNearbyHotels', 'slots': {'SelectedHotel': None, 'CheckInDate': None, 'StayDuration': None, 'NumberOfAdults': None, 'CheckOutDate': None}, 'state': 'InProgress'}, 'interpretationSource': 'Lex'}, {'nluConfidence': 0.46, 'intent': {'confirmationState': 'None', 'name': 'BotIdentity', 'slots': {}, 'state': 'InProgress'}, 'interpretationSource': 'Lex'}], 'bot': {'aliasId': 'TSTALIASID', 'aliasName': 'TestBotAlias', 'name': 'StaySeeker-hotel-bot', 'version': 'DRAFT', 'localeId': 'en_US', 'id': 'J8YREEFNXO'}, 'responseContentType': 'text/plain; charset=utf-8', 'proposedNextState': {'prompt': {'attempt': 'Initial'}, 'intent': {'confirmationState': 'None', 'name': 'ConfirmBooking', 'slots': {'ConfirmHotelBooking': None}, 'state': 'InProgress'}, 'dialogAction': {'slotToElicit': 'ConfirmHotelBooking', 'type': 'ElicitSlot'}}, 'sessionState': {'sessionAttributes': {'Email': 'pc@mail.com', 'CheckInDate': '2024-10-10', 'CountryValue': 'United Kingdom', 'StayDuration': '3', 'NumberOfAdults': '2', 'userAgent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36', 'sessionId': 'us-east-1:886280b7-aed3-c56b-5112-9222f4cb608e', 'Name': 'Prachi Chaudhary', 'SelectedHotel': 'Treehouse Cabin', 'CurrencyValue': 'GBP', 'userPc': 'hi', 'PhoneNumber': '9820066059', 'CityValue': 'N/A', 'LocationValue': 'Frinton-on-Sea, Tendring, Essex, England, CO13 9AZ, United Kingdom', 'CheckOutDate': '2024-10-13'}, 'activeContexts': [], 'intent': {'confirmationState': 'None', 'name': 'ConfirmBooking', 'slots': {'ConfirmHotelBooking': None}, 'state': 'InProgress'}, 'originatingRequestId': 'ffa3deeb-d69a-4ea2-8fd5-7600ba6c9f0f'}, 'messageVersion': '1.0', 'invocationSource': 'DialogCodeHook', 'transcriptions': [{'resolvedContext': {'intent': 'ProvideDetails'}, 'resolvedSlots': {'Email': {'shape': 'Scalar', 'value': {'originalValue': 'pc@mail.com', 'resolvedValues': ['pc@mail.com']}}}, 'transcriptionConfidence': 1.0, 'transcription': 'pc@mail.com'}], 'inputMode': 'Text'}

lambda_handler(event,'gh')

