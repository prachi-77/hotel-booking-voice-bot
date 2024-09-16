**StaySeeker - Hotel Booking Voice Bot**

StaySeeker is a voice assistant designed to simplify the hotel booking process. Built using AWS Lex, Lambda, and Google Hotels API, it allows users to interact through natural language for a seamless booking experience. Users can provide location details, check-in/check-out dates, and the number of guests to receive real-time hotel options.

**Features**
1. **Voice Interaction:** A voice-enabled bot that allows hands-free hotel booking.
2. **Location-based Search:** Fetches user location using latitude and longitude to find nearby hotels.
3. **Hotel Search:** Integrated with Google Hotels API (via Serp API) to provide real-time hotel availability, pricing, and ratings.
4. **Validation:** Input validation for secure and accurate bookings.
5. **Secure Deployment:** Hosted on an HTTPS-enabled static website using AWS S3 and Cloudfront

**Components Overview**

**Lambda Functions:**
1. Fetch user location details via latitude and longitude provided by user using the geocoder library.
2. Search for hotels via the Google Hotels API (Serp API) based on user inputs like check-in date, duration, and guests.
   
**Lex Intents:**
1. **BookRoom:** Gathers location, check-in, check-out dates, and guest details.
2. **SearchNearbyHotels:** Provides top 5 hotel options based on user inputs.
3. **ProvideDetails:** Collects user details (name, phone, email) for booking confirmation.
4. **ConfirmBooking:** Confirms the booking details and finalizes the process.
5. **Fallback Intent:** Activated if the bot doesn't recognize user input or hits an error.

```graphql
.
├── 
│   ├── lambda_handler.py       # Main Lambda function handling hotel booking logic
│   ├── helpers/
│   │   ├── get_current_location.py # Logic to fetch location based on lat and long using Geocoder & Integration with Google Hotels API for hotel search
│   │   ├── lex_response.py         # Lex response functions (close, elicit slot, confirm intent)
│   └── hotel_details.txt       # Cached Google search response for hotel data to avoid API rate limits
├── static_website/
│   └── index.html              # Hosted on AWS S3 to capture user location details
└── README.md                   # Project documentation


