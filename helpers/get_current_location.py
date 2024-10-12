import pycountry
from serpapi import GoogleSearch
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
from countryinfo import CountryInfo
import json
import requests
# from serpapi.serp_api_client import SerpApiClientException, SerpApiQuotaExceeded


def get_currency(name):
    """Fetches the currency information for a given country.
    Args:
        name (str): The name of the country (in English).

    Returns:
        list: A list of currency codes used in the specified country.
    """
    country = CountryInfo(str(name))
    return country.currencies()

    
def reverse_geocode(lat, lon):
    """
    Fetches reverse geocoding information (city, country, postcode, and address) 
    for a given latitude and longitude using the Nominatim API.

    Args:
        lat (float): Latitude of the location.
        lon (float): Longitude of the location.

    Returns:
        dict: A dictionary containing the following keys:
            - "city" (str): The city name (or 'N/A' if not available).
            - "country" (str): The country name (or 'N/A' if not available).
            - "postcode" (str): The postcode (or 'N/A' if not available).
            - "address" (str): The full display name of the location.
            - "lat" (str): The latitude of the location.
            - "long" (str): The longitude of the location.

    Raises:
        KeyError: If an error occurs in the API response, the function returns `None` 
        and prints the error message.
    """
    url = "https://nominatim.openstreetmap.org/reverse"
    params = {
        'format': 'json',
        'lat': lat,
        'lon': lon,
        'zoom': 18,
        'addressdetails': 1,
        'accept-language': 'en' 
    }
    
    headers = {
        'User-Agent': 'YourAppName/1.0 (your.email@example.com)'
    }
    
    response = requests.get(url, headers=headers, params=params)
    data = response.json()
    
    if 'error' in data:
        print("Error:", data['error'])
        return None
    else:
        # Return the information
        return {
            "city": data.get('address', {}).get('city', 'N/A'),
            "country": data.get('address', {}).get('country', 'N/A'),
            "postcode": data.get('address', {}).get('postcode', 'N/A'),
            "address": data['display_name'],
            "lat":data['lat'],
            "long": data['lon']
        }
  

def get_country_code(country_name):
    """
    Retrieves the ISO country code for a given country name required for SerpApi parameter.

    Args:
        country_name (str): The name of the country (in English).

    Returns:
        str: Country code if the country is found; 
             otherwise, returns None.

    Raises:
        LookupError: If the country name is not found in the country list.
    """
    try:
        country = pycountry.countries.lookup(country_name)
        return country.alpha_2
    except LookupError:
        return None

def fetch_hotels(params):
    """
    Fetches hotel search results from the Google Search API using the provided parameters.

    Args:
        params (dict): A dictionary of parameters to configure the hotel search query.

    Returns:
        dict: A dictionary containing the search results, which may include hotel 
              information or an error message.

    Raises:
        Exception: If an error occurs during the API call, prints the error message 
                   and returns an error dictionary.
    """
    try:
        search = GoogleSearch(params)
        results = search.get_dict()
        return results
    except Exception as e:
        print("Serp Api error----",e)
        return {"error": "unknown_error", "message": "An unexpected error occurred."}

    
def search_hotels(hotel_info):
    """
    Searches for hotels based on the provided hotel information and fetches the results 
    from the Google Hotels API.The results are cached in a text file to optimize API usage, 
    as the Serp API allows only 30 free searches.

    Args:
        hotel_info (dict): A dictionary containing hotel search parameters, including:
            - 'city' (str): The city where hotels are to be searched.
            - 'country' (str): The country where the city is located.
            - 'currency' (str): The currency to be used for pricing.
            - 'checkInDate' (str): The check-in date for the hotel stay (format: YYYY-MM-DD).
            - 'checkOutDate' (str): The check-out date for the hotel stay (format: YYYY-MM-DD).
            - 'adults' (int): The number of adults for the hotel booking.

    Returns:
        list: A list of hotel options (dictionaries) for the first five hotels found. 
              If an error occurs during the search, returns an error dictionary.

    Raises:
        Exception: If there is an issue with fetching the hotel data or writing to the file,
                    an error message is printed, and the error is handled.
    """
    params = {
        "engine": "google_hotels",
        "q": "hotels in {city}".format(city = hotel_info['city']),
        "gl":get_country_code(hotel_info['country']),
        "hl":"en",
        "currency":hotel_info['currency'],
        "check_in_date": hotel_info['checkInDate'],
        "check_out_date":hotel_info['checkOutDate'],
        "adults": hotel_info['adults'],
        "api_key": "api-key"
    }
    search_result = fetch_hotels(params)
    print("search result",search_result)
    
    if "error" in search_result:
        return search_result
    else:
        # results = search_result.get_dict()
        results = search_result
        # AWS Lambda functions run in a restricted environment where the local filesystem is read-only, 
        # with the exception of the /tmp directory. Lambda allows us to write temporary files only 
        # in the /tmp directory
        with open("/tmp/hotel_details.txt", "w") as fp:
           json.dump(results, fp) 
        properties = results['properties']
        selected_property = properties
        options = [create_hotel_option(hotel) for hotel in selected_property[:5]]  # Show first 5 hotels
        return options
 

def selected_hotel_details(hotel_name):
    """
    Retrieves the details of a selected hotel from the cached hotel data stored in a text file.

    Args:
        hotel_name (str): The name of the hotel to search for. The name will be trimmed to
                          the first 49 characters to comply with the limitations of the 
                          lex button.

    Returns:
        dict: A dictionary containing the details of the selected hotel if found. 
              If the hotel is not found, returns None.

    """
    with open("/tmp/hotel_details.txt") as f:
        data = f.read()
    js = json.loads(data)
    properties = js['properties']
    for hotel in properties:
        # lex button has 50 character limit
        trimmed_name = hotel["name"][:49]
        if trimmed_name == hotel_name:
            return hotel
        

def create_hotel_option(hotel):
    hotel_class = f"{hotel['hotel_class']}" if hotel.get('hotel_class') else ""
    # rating = f"Rating: {hotel.get('ratings', 'N/A')}"
    text = f"{hotel['name'][:15]} - {hotel['rate_per_night']['lowest']} per night- {hotel_class}"
    return {
        "text": text,
        "value": hotel['name']
    }
    
def trim_text(hotels_list):
    for hotel in hotels_list:
        # Trim the 'text' & value field to a maximum of 49 characters
        # lex button has 50 character limit
        hotel['text'] = hotel['text'][:49]
        hotel['value'] = hotel['value'][:49]
    return hotels_list

def read_txt():
    with open("/tmp/hotel_details.txt") as f:
        data = f.read()
    js = json.loads(data)
    properties = js['properties']
    selected_property = properties
    options = [create_hotel_option(hotel) for hotel in selected_property[:5]]  # Show first 5 hotels
    trimmed_list = trim_text(options)
    return trimmed_list


def get_user_location_details(lat,long):
    location_info = {}
    location_results = reverse_geocode(lat,long)
    print("location results are",location_results)
    if location_results is not None:
        location_info['location'] = location_results
        currency = get_currency(location_info['location']['country'])[0]
        location_info['currency'] = currency
        return location_info

    else:
        print("Unable to retrieve your GPS coordinates.")


