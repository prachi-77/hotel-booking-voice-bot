import geocoder
import pycountry
from serpapi import GoogleSearch
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
from countryinfo import CountryInfo
import json
import requests
# from serpapi.serp_api_client import SerpApiClientException, SerpApiQuotaExceeded

def get_country_name(country_code):
    try:
        country = pycountry.countries.get(alpha_2=country_code)
        return country.name
    except KeyError:
        return "Unknown"

def get_currency(name):
    country = CountryInfo(str(name))
    return country.currencies()

def get_current_coord():
    g = geocoder.ip('me')
    print("test--",g)
    if g.latlng is not None:
        return g
    else:
        return None


    
def reverse_geocode(lat, lon):
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
    try:
        country = pycountry.countries.lookup(country_name)
        return country.alpha_2
    except LookupError:
        return None

def fetch_hotels(params):
    try:
        search = GoogleSearch(params)
        results = search.get_dict()
        return results
    # except SerpApiQuotaExceeded:
    #     return {"error": "quota_exceeded", "message": "You have reached the maximum number of API calls for today."}
    # except SerpApiClientException as e:
    #     return {"error": "api_error", "message": str(e)}
    except Exception as e:
        print("Serp Api error----",e)
        return {"error": "unknown_error", "message": "An unexpected error occurred."}

    
def search_hotels(hotel_info):
    # print("searching for details:-",hotel_info)
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
    if "error" in search_result:
        return search_result
    else:
        # results = search_result.get_dict()
        results = search_result
        with open("hotel_details.txt", "w") as fp:
           json.dump(results, fp) 
        properties = results['properties']
        selected_property = properties
        options = [create_hotel_option(hotel) for hotel in selected_property[:5]]  # Show first 5 hotels
        return options
 

def format_hotel_info(hotel):
    name = hotel.get('name')
    description = hotel.get('description')
    rate = hotel.get('rate_per_night', {}).get('lowest', 'N/A')
    before_taxes = hotel.get('rate_per_night', {}).get('before_taxes_fees', 'N/A')
    total_rate = hotel.get('total_rate', {}).get('lowest', 'N/A')
    check_in = hotel.get('check_in_time', 'N/A')
    check_out = hotel.get('check_out_time', 'N/A')
    nearby = ', '.join([place['name'] for place in hotel.get('nearby_places', [])])
    hotel_class = f"{hotel.get('extracted_hotel_class', 'N/A')}-star hotel"
    link = hotel.get('link', '#')

def selected_hotel_details(hotel_name):
    with open("hotel_details.txt") as f:
        data = f.read()
    js = json.loads(data)
    properties = js['properties']
    for hotel in properties:
        if hotel["name"] == hotel_name:
            return hotel
        

def create_hotel_option(hotel):
    hotel_class = f"{hotel['hotel_class']}" if hotel.get('hotel_class') else ""
    # rating = f"Rating: {hotel.get('ratings', 'N/A')}"
    text = f"{hotel['name'][:15]} - {hotel['rate_per_night']['lowest']} per night- {hotel_class}"
    return {
        "text": text,
        "value": hotel['name']
    }

def read_txt():
    with open("hotel_details.txt") as f:
        data = f.read()
    js = json.loads(data)
    properties = js['properties']
    selected_property = properties
    options = [create_hotel_option(hotel) for hotel in selected_property[:5]]  # Show first 5 hotels
    return options


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


