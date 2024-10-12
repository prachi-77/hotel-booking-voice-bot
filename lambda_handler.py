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

def handle_change_details_intent(session_attributes,event):
    user_input = event['inputTranscript'].lower() 
    active_contexts= {}
    print("user input",user_input)
    slots = event['sessionState']['intent']['slots']
    if 'name' in user_input:
        session_attributes['Name'] = None  # Reset the Name slot
        slot_to_elicit = 'UpdatedName'
        prompt_message = "Please enter your new name."

    elif 'phone' in user_input:
        session_attributes['Phone'] = None  # Reset the Phone slot
        slot_to_elicit = 'UpdatedPhone'
        prompt_message = "Please enter your new phone number."

    elif 'email' in user_input:
        session_attributes['Email'] = None  # Reset the Email slot
        slot_to_elicit = 'UpdatedEmail'
        prompt_message = "Please enter your new email address."
    else:
        # switch to other intent
        return close(session_attributes, active_contexts, 'Fulfilled', event['sessionState']['intent'], "Updated the name")
    return elicit_slot(
            session_attributes,
            active_contexts,
            event['sessionState']['intent'],
            slot_to_elicit,
            get_plain_text_msg(prompt_message)
            )   

def handle_book_room_intent(session_attributes,event):
    active_contexts= {}
    slots = event['sessionState']['intent']['slots']
    user_choice = event['inputTranscript'].lower()
    lat_value_slot = slots.get('latitude')
    long_value_slot = slots.get('longitude')
    lat_value = ''
    long_value = ''
    lat_msg = ''
    long_msg = ''
    if user_choice == "user declined location":
        event['sessionState']['intent']['slots']['longitude'] = None
        event['sessionState']['intent']['slots']['latitude'] = None
        lat_value_slot = None
        lat_msg = 'Please enter new latitude coordinates.'
        long_msg = 'Please enter new longitude coordinates.'
    else:
        lat_msg = 'Please enter the latitude coordinates displayed on your webpage.'
        long_msg = 'Please enter the longitude coordinates displayed on your webpage.'

    if (lat_value_slot is not None):
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
            get_plain_text_msg(lat_msg)
            )   
    
    if (long_value_slot is not None) :
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
            get_plain_text_msg(long_msg)
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
                {"text": "No", "value": "user declined location"}]

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
    # calling google hotels api & it will save result to a .txt file
    search_hotels(hotel_info)
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
        link = hotel['link'][:49]
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
                        return confirm_intent(session_attributes, "RateExperience", "Rating")
                        # return close(session_attributes, {}, 'Fulfilled', event['sessionState']['intent'], prompt)

                return handle_confirm_booking_intent(session_attributes,event)
            case 'ChangeDetails':
                print("Change details intent")
                
                return handle_change_details_intent(session_attributes,event)
                

        
    except Exception as e:
        prompt = "Unable to generate prompt at the moment. Please try again later."
        active_contexts = {}
        logger.error(f"Found error -- {e}")
        traceback.print_exc()
        return close(session_attributes, active_contexts, 'Fulfilled', event['sessionState']['intent'], prompt)

