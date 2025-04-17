# Backend
from flask import Flask, request, jsonify
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from flask_cors import CORS
from pymongo import MongoClient,DESCENDING
import requests
import os
from dotenv import load_dotenv
import google.generativeai as genai
import random
import time
import re
from datetime import datetime,timezone
from dateutil import parser

load_dotenv()  # Load environment variables from .env file

app = Flask(__name__)
CORS(app)
bcrypt = Bcrypt(app)
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
app.config["JWT_SECRET_KEY"] = JWT_SECRET_KEY
jwt = JWTManager(app)

# MongoDB Connection
MONGO_URI = os.getenv("MONGO_URI")
client = MongoClient(MONGO_URI)
db = client.travel_bot

# Collections
city_codes_collection = db.city_codes
underrated_collections = db.underrated
questions_collection = db.questions
users_collection = db.users
responses_collection = db.responses
reviews_collection = db.reviews

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
# Configure Gemini API
genai.configure(api_key=GEMINI_API_KEY)
best_model = "models/gemini-1.5-pro-latest"
backup_model = "models/gemini-1.5-flash-latest"

# Amadeus API Credentials
AMADEUS_API_KEY = os.getenv("AMADEUS_API_KEY")
AMADEUS_API_SECRET = os.getenv("AMADEUS_API_SECRET")
AMADEUS_TOKEN_URL = os.getenv("AMADEUS_TOKEN_URL")
AMADEUS_FLIGHT_SEARCH_URL = os.getenv("AMADEUS_FLIGHT_SEARCH_URL")
AMADEUS_HOTEL_SEARCH_URL = os.getenv("AMADEUS_HOTEL_SEARCH_URL")
LOCATIONIQ_API_KEY = os.getenv("LOCATIONIQ_API_KEY")

# Store the token and expiry time
access_token = None
token_expiry = 0  # Stores UNIX timestamp

# Amadeus API functions
def get_access_token():
    """Fetch and cache Amadeus API access token."""
    global access_token, token_expiry
    if access_token and time.time() < token_expiry:
        return access_token
    try:
        response = requests.post(AMADEUS_TOKEN_URL, data={
            "grant_type": "client_credentials",
            "client_id": AMADEUS_API_KEY,
            "client_secret": AMADEUS_API_SECRET
        })
        response.raise_for_status()
        json_response = response.json()
        access_token = json_response["access_token"]
        token_expiry = time.time() + json_response["expires_in"]
        return access_token
    except requests.exceptions.RequestException as e:
        return None

# ✅ Flight Search
def search_flights(origin, destination, departure_date):
    token = get_access_token()
    if not token:
        return None
    try:
        response = requests.get(AMADEUS_FLIGHT_SEARCH_URL, headers={
            "Authorization": f"Bearer {token}"
        }, params={
            "originLocationCode": origin,
            "destinationLocationCode": destination,
            "departureDate": departure_date,
            "adults": 1,
            "currencyCode": "INR",
            "max": 5
        })
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return None
    
def extract_flight_details(user_message):
    words = user_message.lower().split()
    
    city_codes = {doc["city"].lower(): doc["iata_code"] for doc in city_codes_collection.find({})}

    origin, destination = None, None

    for city in city_codes.keys():
        if city in words:
            if not origin:
                origin = city_codes[city]
            else:
                destination = city_codes[city]
                break

    if not origin or not destination:
        return None

    # ✅ Use dateutil to parse date directly
    try:
        parsed_date = parser.parse(user_message, fuzzy=True, default=datetime(datetime.now().year, 1, 1))
        formatted_date = parsed_date.strftime("%Y-%m-%d")
    except Exception as e:
        print(f"❗ Date parsing error: {e}")
        return None

    return {"origin": origin, "destination": destination, "date": formatted_date}


def get_hotels_by_city(city_code):
    """Step 1: Fetch hotel IDs in a city using Amadeus API."""
    token = get_access_token()
    if not token:
        return None
    try:
        response = requests.get(
            AMADEUS_HOTEL_SEARCH_URL,
            headers={"Authorization": f"Bearer {token}"},
            params={
                "cityCode": city_code,
                "radius": 5,
                "radiusUnit": "KM",               
            }
        )
        response.raise_for_status()
        return response.json().get("data", [])
    except requests.exceptions.RequestException as e:
        print(f"❗ Hotel list API error: {e}")
        return None

def get_hotel_availability(hotel_ids, check_in, check_out, adults=2):
    """Step 2: Check availability for specific hotels."""
    token = get_access_token()
    if not token:
        return None
    try:
        response = requests.get(
            "https://test.api.amadeus.com/v3/shopping/hotel-offers",
            headers={"Authorization": f"Bearer {token}"},
            params={
                "hotelIds": ",".join(hotel_ids),
                #"checkInDate": check_in,
                #"checkOutDate": check_out,
                #"adults": adults,
                "bestRateOnly": True  # Get best price per hotel
            }
        )
        response.raise_for_status()
        return response.json().get("data", [])
    except requests.exceptions.RequestException as e:
        print(f"❗ Hotel availability API error: {e}")
        return None

def search_hotels_combined(city_code, check_in, check_out, adults=2):
    """Combined workflow: Get hotels in city -> Check availability."""
    # Step 1: Get hotel IDs in the city
    hotels = get_hotels_by_city(city_code)
    if not hotels:
        return None
    
    # Extract hotel IDs (first 5 for demo)
    hotel_ids = [hotel["hotelId"] for hotel in hotels[:5]]
    
    # Step 2: Check availability
    return get_hotel_availability(hotel_ids, check_in, check_out, adults)

# Updated extractor to handle city-based queries
def extract_hotel_details(user_message):
    words = user_message.lower().split()
    
    city_codes = {doc["city"].lower(): doc["iata_code"] for doc in city_codes_collection.find({})}
    city_code = None

    # Find city code
    for city in city_codes.keys():
        if city in words:
            city_code = city_codes[city]
            break

    if not city_code:
        return None

    # Extract dates
    dates_found = extract_dates(user_message)
    check_in = dates_found[0] if len(dates_found) > 0 else None
    check_out = dates_found[1] if len(dates_found) > 1 else None

    # Default adults if not found
    adults = extract_number(user_message, "guests") or 2

    if not check_in or not check_out:
        print("❗ Check-in/check-out date not found")
        return None

    return {
        "city_code": city_code,
        "check_in": check_in,
        "check_out": check_out,
        "adults": adults
    }

def extract_dates(user_message):
    """Extracts all dates (check-in and check-out) from user message."""
    date_pattern = r"(\d{1,2})(?:st|nd|rd|th)?\s*(?:of\s*)?([A-Za-z]+)(?:\s*(\d{4}))?"
    matches = re.findall(date_pattern, user_message, re.IGNORECASE)
    
    dates = []
    for match in matches:
        day, month, year = match[0], match[1], match[2] if match[2] else str(datetime.now().year)
        full_date = f"{day} {month} {year}"

        try:
            parsed_date = datetime.strptime(full_date, "%d %B %Y")
            dates.append(parsed_date.strftime("%Y-%m-%d"))
        except ValueError:
            print(f"Invalid date format: {full_date}")
            continue

    return dates  # This will return a list of all valid dates


def extract_number(user_message, field):
    """Extracts a number (like guests) from user input."""
    match = re.search(r"(\d+)\s*" + field, user_message, re.IGNORECASE)
    if match:
        try:
            return int(match.group(1))
        except ValueError:
            print(f"Invalid number format in: {user_message}")
            return None
    print(f"No valid number found for {field} in: {user_message}")
    return None

def get_location_coordinates(place):
    url = f"https://us1.locationiq.com/v1/search.php"
    params = {
        "key": LOCATIONIQ_API_KEY,
        "q": place,
        "format": "json"
    }
    response = requests.get(url, params=params)
    return response.json()[0]  # First result
    
def extract_location(user_message):
    """Extracts location from user input using LocationIQ API if not found in predefined city list."""
    words = user_message.lower().split()
    
    # 🔹 Fetch all city names from MongoDB
    city_names = [doc["city"].lower() for doc in city_codes_collection.find({}, {"city": 1, "_id": 0})]

    for city in city_names:
        if city in words:
            return city.capitalize()  # Return formatted city name

    # 🔹 If not found in database, use LocationIQ API for geocoding
    url = f"https://us1.locationiq.com/v1/search.php"
    params = {
        "key": LOCATIONIQ_API_KEY,
        "q": user_message,
        "format": "json",
        "limit": 1
    }
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        location_data = response.json()
        if location_data:
            return location_data[0]["display_name"].split(",")[0]  # Extract city name
    except requests.exceptions.RequestException as e:
        print(f"Error fetching location from LocationIQ: {e}")

    return None  # No valid location found

# Home route
@app.route('/')
def home():
    return jsonify({"message": "Voyabot backend is running!"})

# To enhance underrated using AI
def get_ai_description(place):
    """Enhance place details using the Gemini API."""
    prompt = f"Provide detailed travel information about {place['Phase Name']} located in {place['Location']}. Include its cultural importance, best travel time, local experiences, and food options."

    for model in [best_model, backup_model]:
        try:
            response = genai.GenerativeModel(model_name=model).generate_content(prompt)
            if response and response.text:
                return response.text
        except Exception as e:
            if "model_not_found" in str(e) or "quota_exceeded" in str(e):
                continue  # Try the next model
            else:
                return "AI data unavailable."

    return "AI model failed to provide details."

# ✅ AI-Powered Summary for Flights, Hotels, and Places
def generate_ai_summary(title, data):
    try:
        prompt = f"{title}:\n{data}"
        for model in [best_model, backup_model]:
            try:
                response = genai.GenerativeModel(model_name=model).generate_content(prompt)
                if response and response.text:
                    return response.text
            except Exception as e:
                if "model_not_found" in str(e) or "quota_exceeded" in str(e):
                    continue
                return "AI error: Unable to generate a summary."
        return "AI processing failed."
    except Exception as e:
        return "Error in AI processing."

# Fetch questions from MongoDB
@app.route('/get_questions', methods=['GET'])
def get_questions():
    try:
        questions = list(questions_collection.find({}, {"_id": 0}))
        return jsonify(questions), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Signup Route
@app.route('/signup', methods=['POST'])
def signup():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    if users_collection.find_one({'username': username}):
        return jsonify({"message": "Username already exists"}), 400

    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
    users_collection.insert_one({'username': username, 'password': hashed_password})
    return jsonify({"message": "User registered successfully"}), 201

# Login Route
@app.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    user = users_collection.find_one({'username': username})
    if user and bcrypt.check_password_hash(user['password'], password):
        access_token = create_access_token(identity=username)
        return jsonify({"message": "Login successful", "token": access_token}), 200
    return jsonify({"message": "Invalid credentials"}), 401

def gemini_fallback(user_message):
    """Helper function to handle Gemini fallback logic."""
    for model in [best_model, backup_model]:
        try:
            response = genai.GenerativeModel(model_name=model).generate_content(user_message)
            print(f"Gemini model response ({model}): {response}")
            if response and response.text:
                return jsonify({"reply": response.text})  # Return the response and exit
        except Exception as e:
            print(f"Error from Gemini model {model}: {e}")
            if "model_not_found" in str(e) or "quota_exceeded" in str(e):
                continue  # Try the next model
            else:
                return jsonify({"error": f"Gemini API error: {str(e)}"}), 500  # Return error and exit
    return jsonify({"error": "All AI models failed. Please try again later."}), 500  # Final fallback

@app.route("/chat", methods=["POST"])
@jwt_required()
def chat():
    user_message = request.json.get("message")
    print(f"Received message: {user_message}")

    if not user_message:
        return jsonify({"error": "Message is required"}), 400

    try:
        # Flight search
        if any(word in user_message.lower() for word in ["flight", "book ticket", "airfare"]):
            print("Detected flight query")
            data = extract_flight_details(user_message)
            print(f"Extracted flight details: {data}")
            if not data:
                raise Exception("Failed to extract flight details")
            
            flight_data = search_flights(data["origin"], data["destination"], data["date"])
            print(f"Flight API response: {flight_data}")
            if not flight_data or "data" not in flight_data:
                raise Exception("No flights found")
            
            summary = generate_ai_summary(f"Flight options from {data['origin']} to {data['destination']}", flight_data)
            return jsonify({"flights": flight_data["data"], "reply": summary})  # Return and exit

        
        # Hotel search
        if any(word in user_message.lower() for word in ["hotel", "stay", "accommodation"]):
            print("Detected hotel query")
            hotel_data_input = extract_hotel_details(user_message)
            print(f"Extracted hotel details: {hotel_data_input}")
            if not hotel_data_input:
                raise Exception("Failed to extract hotel details")

            # Use combined API workflow
            hotel_data = search_hotels_combined(
                hotel_data_input["city_code"],
                hotel_data_input["check_in"],
                hotel_data_input["check_out"],
                adults=hotel_data_input["adults"]
            )
            print(f"Combined hotel API response: {hotel_data}")
            if not hotel_data:
                raise Exception("No hotels found")

            summary = generate_ai_summary(
                f"Hotel options in {hotel_data_input['city_code']}",
                {"hotels": hotel_data}
            )
            return jsonify({
                "hotels": hotel_data,
                "reply": summary
            })

        
        # General Gemini fallback for queries that don't match flight, hotel, or place search
        print("Trying Gemini fallback for general query...")
        return gemini_fallback(user_message)  # Return and exit

    except Exception as e:
        print(f"Error occurred: {e}. Falling back to Gemini...")
        # General fallback to Gemini for any error
        return gemini_fallback(user_message)  # Return and exit


# Questionnaire submission & generate travel recommendations
@app.route('/submit_questionnaire', methods=['POST'])
@jwt_required()
def submit_questionnaire():
    try:
        data = request.json
        username = get_jwt_identity()

        # 🔹 Ensure no question is left unanswered
        if not all(data.values()):
            return jsonify({"error": "Please answer all questions before submitting."}), 400

        # Store user responses in MongoDB
        responses_collection.update_one(
            {"username": username}, 
            {"$set": {"responses": data}}, 
            upsert=True
        )

        # Generate travel recommendation using AI
        prompt = f"Based on the following user preferences: {data}, generate a personalized travel recommendation. Suggest at least three travel destinations in India that match the user's interests, preferred activities, and travel style. Provide a brief description of each place, highlighting why it would be a great choice. Also, include any relevant travel tips or must-visit attractions for each destination."
        recommendation = None

        for model in [best_model, backup_model]:
            try:
                response = genai.GenerativeModel(model_name=model).generate_content(prompt)
                if response and hasattr(response, 'text'):
                    recommendation = response.text
                    break  # Exit loop if recommendation is found
            except Exception as e:
                if any(err in str(e) for err in ["model_not_found", "quota_exceeded"]):
                    continue  # Try the next model
                return jsonify({"error": f"Gemini API error: {str(e)}"}), 500

        if not recommendation:
            return jsonify({"error": "AI model failed. Please try again later."}), 500

        # Check for additional assistance needs
        assistance_text = None
        special_requirements = data.get("special_requirements", [])
        if any(req in special_requirements for req in ["pet assistance", "medical conditions", "child care"]):
            assistance_prompt = f"User needs assistance for: {special_requirements}\nProvide suitable travel solutions."

            for model in [best_model, backup_model]:
                try:
                    assistance_response = genai.GenerativeModel(model_name=model).generate_content(assistance_prompt)
                    if assistance_response and hasattr(assistance_response, 'text'):
                        assistance_text = assistance_response.text
                        break
                except Exception as e:
                    if any(err in str(e) for err in ["model_not_found", "quota_exceeded"]):
                        continue  # Try next model
                    return jsonify({"error": f"Gemini API error: {str(e)}"}), 500

        # Prepare response payload
        response_payload = {
            "message": "Questionnaire submitted successfully!",
            "recommendation": recommendation
        }
        
        if assistance_text:
            response_payload["assistance"] = assistance_text

        return jsonify(response_payload), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Underrated Places
@app.route("/underrated_places", methods=["GET"])
def get_underrated_places():
    try:
        # Fetch all places from MongoDB (excluding _id)
        places = list(underrated_collections.find({}, {"_id": 0}))
        
        if not places:
            return jsonify({"error": "No places found in the database"}), 404
        
        # Shuffle and select 3 random places
        random.shuffle(places)
        selected_places = places[:3]

        # Enhance details with AI
        for place in selected_places:
            if "ai_details" not in place:
                place["ai_details"] = get_ai_description(place)
                
            place.setdefault("image_url", "https://via.placeholder.com/400x300?text=No+Image")

        return jsonify({"places": selected_places}), 200
    except Exception as e:
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500

@app.route('/get_reviews', methods=['GET'])
@jwt_required()
def get_reviews():
    try:
        # Include _id in the response by removing {"_id": 0} and converting ObjectId to string
        reviews = list(reviews_collection.find({}).sort("timestamp", DESCENDING))
        
        # Convert ObjectId to string for each review
        for review in reviews:
            review['_id'] = str(review['_id'])
        
        return jsonify(reviews), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
      
@app.route('/submit_review', methods=['POST'])
@jwt_required()
def submit_review():
    try:
        data = request.json
        username = get_jwt_identity()
        review_text = data.get("review_text")

        if not review_text:
            return jsonify({"error": "Review cannot be empty."}), 400

        review = {
            "username": username,
            "review_text": review_text,
            "timestamp": datetime.now(timezone.utc),
            "likes": 0,
            "dislikes": 0,
            "replies": []
        }

        reviews_collection.insert_one(review)
        return jsonify({"message": "Review submitted successfully!"}), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/like_dislike_review', methods=['POST'])
@jwt_required()
def like_dislike_review():
    try:
        # Validate request data
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400

        review_id = data.get("review_id")
        action = data.get("action")  # 'like' or 'dislike'

        # Validate required fields
        if not review_id:
            return jsonify({"error": "Review ID is required"}), 400
        if action not in ["like", "dislike"]:
            return jsonify({"error": "Invalid action. Must be 'like' or 'dislike'"}), 400

        # Convert string ID to ObjectId if needed
        try:
            from bson import ObjectId
            review_obj_id = ObjectId(review_id) if not isinstance(review_id, ObjectId) else review_id
        except:
            return jsonify({"error": "Invalid review ID format"}), 400

        # Determine which field to update
        update_field = "likes" if action == "like" else "dislikes"

        # Update and return the modified document
        result = reviews_collection.find_one_and_update(
            {"_id": review_obj_id},
            {"$inc": {update_field: 1}},
            return_document=True
        )

        if not result:
            return jsonify({"error": "Review not found"}), 404

        # Return success response with updated counts
        return jsonify({
            "message": f"Review {action}d successfully",
            "review_id": str(result["_id"]),
            "likes": result.get("likes", 0),
            "dislikes": result.get("dislikes", 0)
        }), 200

    except Exception as e:
        return jsonify({
            "error": "An error occurred",
            "details": str(e)
        }), 500

@app.route('/reply_review', methods=['POST'])
@jwt_required()
def reply_review():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400

        username = get_jwt_identity()
        review_id = data.get("review_id")
        reply_text = data.get("reply_text")

        # Validate required fields
        if not review_id:
            return jsonify({"error": "Review ID is required"}), 400
        if not reply_text or not reply_text.strip():
            return jsonify({"error": "Reply text cannot be empty"}), 400

        # Convert string ID to ObjectId if needed
        try:
            from bson import ObjectId
            review_obj_id = ObjectId(review_id) if not isinstance(review_id, ObjectId) else review_id
        except:
            return jsonify({"error": "Invalid review ID format"}), 400

        # Create reply object with proper timestamp
        reply = {
            "username": username,
            "reply_text": reply_text.strip(),
            "timestamp": datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S GMT")
        }

        # Update the review with the new reply
        result = reviews_collection.update_one(
            {"_id": review_obj_id},
            {"$push": {"replies": reply}}
        )

        if result.modified_count == 1:
            # Return the complete reply object
            return jsonify({
                "message": "Reply added successfully",
                "reply": reply
            }), 200
        else:
            return jsonify({"error": "Review not found or not updated"}), 404

    except Exception as e:
        return jsonify({
            "error": "An error occurred",
            "details": str(e)
        }), 500
    
@app.route('/delete_reply', methods=['DELETE'])
@jwt_required()
def delete_reply():
    try:
        data = request.json
        review_id = data.get("review_id")
        reply_index = data.get("reply_index")
        
        # Convert string ID to ObjectId if needed
        from bson import ObjectId
        review_obj_id = ObjectId(review_id) if not isinstance(review_id, ObjectId) else review_id
        
        # Update operation to remove the specific reply
        result = reviews_collection.update_one(
            {"_id": review_obj_id},
            {"$unset": {f"replies.{reply_index}": 1}}
        )
        
        # Then pull to remove null values
        reviews_collection.update_one(
            {"_id": review_obj_id},
            {"$pull": {"replies": None}}
        )
        
        if result.modified_count == 1:
            return jsonify({"message": "Reply deleted successfully"}), 200
        else:
            return jsonify({"error": "Reply not found or not deleted"}), 404
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500   

    
if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=5001)
