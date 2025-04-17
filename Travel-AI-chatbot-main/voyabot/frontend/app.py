#Frontend-current
import sys
import os
import streamlit as st
import requests
from datetime import datetime
from PIL import Image
from io import BytesIO
import urllib.parse

# Streamlit app configuration
st.set_page_config(page_title="Voyabot", page_icon="🌍", layout="centered")

def load_css(file_name):
    with open(file_name, "r") as f:
        css = f.read()
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)

load_css("assets/style.css")  # Ensure "styles.css" is in the same directory as your script

# ✅ Ensure session state is initialized
if "current_page" not in st.session_state:
    st.session_state["current_page"] = "Authentication"  # Default page

# ✅ Function to apply different background images and styles for each page
def apply_page_style():
    styles = {
        "Authentication": {
            "bg": "https://img.freepik.com/premium-photo/top-view-helpful-methods-travel_1257223-1145.jpg",
            "color": "white",
            "title_color": "#000000",
            "class": "auth-page"
        },
        "Options": {
            "bg": "https://wallpaperaccess.com/full/14753797.jpg",
            "color": "#000",
            "title_color": "#FFFFFF",
            "class": "option-page"
        },
        "Chat Area": {
            "bg": "https://wallpaperaccess.com/full/4930665.jpg",
            "color": "#333",
            "title_color": "#2196F3",
            "class": "chat-page"
        },
        "Questionnaire": {
            "bg": "https://wallpapercave.com/wp/wp8918814.jpg",
            "color": "black",
            "title_color": "green",
            "class": "questionnaire-page"
        },
        "Underrated Places": {
            "bg": "http://getwallpapers.com/wallpaper/full/3/d/f/108167.jpg",
            "color": "white",
            "title_color": "orange",
            "class": "underrated-page"
        },
        "User Reviews": {  # ✅ Added Review Page
            "bg": "https://www.vertical-leap.uk/wp-content/uploads/2016/10/Travel-background1.jpg",
            "color": "white",
            "title_color": "black", 
            "class": "review-page"
        }
    }

    page = st.session_state["current_page"]
    bg_url = styles[page]["bg"]
    text_color = styles[page]["color"]
    title_color = styles[page]["title_color"]
    page_class = styles[page]["class"]

    custom_css = f"""
    <style>
        .stApp {{
            background-image: url("{bg_url}");
            background-size: cover;
            background-position: center;
            background-attachment: fixed;
        }}
        .main-content {{
            margin-left: 280px;
            transition: margin-left 0.3s ease;
            padding: 20px;
        }}
        @media (max-width: 991.98px) {{
            .main-content {{
                margin-left: 0;
            }}
        }}
        .centered-container {{
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
        }}
        .title-text {{
            color: {title_color};
            font-family: 'Cinzel',serif;
            font-size: 48px;
            font-weight: bold;
            text-align: center;
            padding: 20px;
        }}
        .text {{
            color: {text_color};
            font-size: 20px;
            text-align: center;
            padding: 10px;
        }}
        .stButton > button {{
            background-color: #2089a1;
            color: white;
            border-radius: 10px;
            padding: 10px 20px;
        }}
        .option-page button {{
            background-color: #2089a1 !important;
            color: #f7f5f5 !important;
            font-size: 18px !important;
            padding: 12px 24px !important;
            border-radius: 8px !important;
            font-weight: bold !important;
            border: none !important;
            margin: 10px;
        }}
        .stImage img {{
            width: 100px;
            height: 100px;
            border-radius: 50%;
            display: flex;
            justify-content: center;
            border: 3px solid white;
            object-fit: cover;
            margin: 10px;
        }}
        .assistance-box {{
            background-color: rgba(255, 255, 255, 0.7); /* White with 70% opacity */
            backdrop-filter: blur(5px);
            border-radius: 10px;
            padding: 15px;
            margin: 15px 0;
            border: 1px solid rgba(255, 255, 255, 0.3);
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
        }}
        .option-image-container {{
            display: flex;
            justify-content: center;
            margin: 10px;
        }}
        .option-image {{
            width: 150px;
            height: 150px;
            border-radius: 50%;
            object-fit: cover;
            border: 3px solid white;
            transition: all 0.3s ease;
            box-shadow: 0 4px 8px rgba(0,0,0,0.2);
        }}

        .option-image:hover {{
            transform: scale(1.1);
            border-color: #2089a1;
        }}
        .button-container {{
            display: flex;
            justify-content: center;
            gap: 20px;
            margin-top: 20px;
        }}
        .underrated-card {{
            background-color: rgba(255, 165, 0, 0.7) !important;
            backdrop-filter: blur(5px);
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 25px;
            border: 1px solid rgba(255, 255, 255, 0.3);
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
        }}
        .white-bg {{
            background-color: rgba(255, 255, 255, 0.7) !important;
        }}
        .underrated-page .stImage img {{
            border-radius: 8px !important;
            height: 250px !important;
            object-fit: cover !important;
            margin-bottom: 15px !important;
            border: 2px solid rgba(255, 255, 255, 0.8) !important;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1) !important;
        }}
        .underrated-page .stImage img:hover {{
            transform: scale(1.02) !important;
            box-shadow: 0 6px 12px rgba(0,0,0,0.15) !important;
            border-color: white !important;
        }}
    </style>
    """
    st.markdown(custom_css, unsafe_allow_html=True)

# ✅ Apply the custom style based on the current page
apply_page_style()

# Add the backend directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

# Flask backend URL
BASE_URL = "http://127.0.0.1:5001"

# Image URLs for circular bubbles
image_urls = [
    "https://img.veenaworld.com/wp-content/uploads/2018/06/1-cover-shutterstock_782705764-Camel-ride-on-the-sand-dunes-of-Thar-desert-Jaisalmer.jpg",
    "https://cdn.urlaubsguru.at/wp-content/uploads/2019/03/Taj-Mahal-in-Indien-iStock-155096944.jpg",
    "http://www.techandfacts.com/wp-content/uploads/2014/02/Lotus-Temple.jpg",
    "https://static2.tripoto.com/media/filter/nl/img/503298/TripDocument/1515665810_img_2540.jpg",
    "https://www.oyorooms.com/travel-guide/wp-content/uploads/2019/05/Revel-in-the-sheer-beauty-of-gorgeous-Indian-Lakes-Hero-Image.jpg",
    "http://4.bp.blogspot.com/-CQwnLJ4zN5w/UQfK4p0rVhI/AAAAAAAAf4g/J4ypEVYi2VQ/s1600/clark5himalaya.jpg",
    "http://3.bp.blogspot.com/-tWJq5BhEn_w/T7o388Yt9GI/AAAAAAAAAY8/H3F_wzD_2PQ/s1600/Kovalam-Beach-Kerala.jpg"
]

def display_images():
    """Display circular travel images in the options page."""
    cols = st.columns(len(image_urls))
    for idx, url in enumerate(image_urls):
        # Wrap the image in a div with a custom class for styling
        cols[idx].markdown(
            f'<div class="option-image-container">'
            f'<img src="{url}" class="option-image">'
            f'</div>',
            unsafe_allow_html=True
        )

def show_navbar():
    # Only show sidebar on these pages
    if st.session_state["current_page"] in ["Chat Area", "Underrated Places", "Questionnaire", "User Reviews"]:
        with st.sidebar:
            st.markdown("""
            <style>
                /* Dark theme styles */
                .sidebar-nav {
                    display: flex;
                    flex-direction: column;
                    gap: 6px;
                    padding: 12px;
                }
                .nav-item {
                    padding: 14px 18px;
                    border-radius: 8px;
                    border: none;
                    background: transparent;
                    color: #e0e0e0;
                    font-weight: 500;
                    cursor: pointer;
                    text-align: left;
                    transition: all 0.2s ease;
                    display: flex;
                    align-items: center;
                    gap: 12px;
                    font-size: 15px;
                    margin-bottom: 4px;
                }
                .nav-item:hover {
                    background: rgba(32, 137, 161, 0.3);
                    color: #ffffff;
                }
                .nav-item.active {
                    background: #2089a1;
                    color: white;
                    box-shadow: 0 4px 8px rgba(0,0,0,0.2);
                }
                .sidebar-title {
                    font-size: 24px;
                    font-weight: 700;
                    color: #ffffff;
                    margin-bottom: 24px;
                    padding-bottom: 12px;
                    border-bottom: 1px solid #444;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                }
                .sidebar-footer {
                    margin-top: 30px;
                    padding-top: 15px;
                    border-top: 1px solid #444;
                }
                /* Close button styling */
                .stSidebarCloseButton button {
                    color: #bbb !important;
                    font-size: 20px !important;
                    opacity: 0.8;
                }
                .stSidebarCloseButton button:hover {
                    color: #fff !important;
                    opacity: 1;
                }
                /* Sidebar container */
                [data-testid="stSidebar"] {
                    background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%);
                    border-right: 1px solid #333;
                }
                /* Sidebar width */
                section[data-testid="stSidebar"] {
                    min-width: 260px !important;
                    max-width: 260px !important;
                }
                /* Button styling */
                .stButton>button {
                    border: 1px solid #444;
                    background-color: #333;
                    color: white;
                }
                .stButton>button:hover {
                    border-color: #555;
                    background-color: #444;
                }
            </style>
            """, unsafe_allow_html=True)
            
            current_page = st.session_state["current_page"]
            
            # Sidebar header with title
            st.markdown(
                '<div class="sidebar-title">'
                '<span>🌍 Voyabot</span>'
                '</div>', 
                unsafe_allow_html=True
            )
            
            st.markdown('<div class="sidebar-nav">', unsafe_allow_html=True)
            
            # Navigation items with icons
            nav_items = [
                {"icon": "💬", "label": "Chat with Bot", "page": "Chat Area"},
                {"icon": "🌄", "label": "Hidden Gems", "page": "Underrated Places"},
                {"icon": "📝", "label": "Questionnaire", "page": "Questionnaire"},
                {"icon": "🌟", "label": "User Reviews", "page": "User Reviews"}
            ]
            
            for item in nav_items:
                if st.button(
                    f"{item['icon']} {item['label']}",
                    key=f"nav_{item['page'].lower().replace(' ', '_')}",
                    disabled=current_page == item["page"]
                ):
                    st.session_state["current_page"] = item["page"]
                    st.rerun()
            
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Footer with back button
            st.markdown('<div class="sidebar-footer">', unsafe_allow_html=True)
            if st.button(
                "← Back to Main Menu",
                key="back_to_main",
                use_container_width=True,
                type="secondary"
            ):
                st.session_state["current_page"] = "Options"
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

# ✅ Initialize session state variables (only once)
if "messages" not in st.session_state:
    st.session_state["messages"] = []  # Stores chat history

if "waiting_for_reply" not in st.session_state:
    st.session_state["waiting_for_reply"] = False  # Prevent multiple API calls

if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False
    st.session_state["username"] = ""
    st.session_state["token"] = ""
    st.session_state["messages"] = []
    st.session_state["last_message"] = None
    st.session_state["selected_option"] = None  # Track if user chooses chat or questionnaire

# ✅ Authentication Page
if st.session_state["current_page"] == "Authentication":
    st.markdown('<div class="title-text">Voyabot Login</div>', unsafe_allow_html=True)
    
    login_tab, signup_tab = st.tabs(["Login", "Sign Up"])

    with login_tab:
        st.subheader("Login")
        username = st.text_input("Username", key="login_username")
        password = st.text_input("Password", type="password", key="login_password")

        if st.button("Login"):
            response = requests.post(f"{BASE_URL}/login", json={"username": username, "password": password})
            if response.status_code == 200:
                data = response.json()
                st.session_state["authenticated"] = True
                st.session_state["username"] = username
                st.session_state["token"] = data.get("token")
                st.session_state["current_page"] = "Options"
                st.rerun()
            else:
                st.error(response.json().get("message"))
    
    with signup_tab:
        st.subheader("Sign Up")
        new_username = st.text_input("Create Username", key="signup_username")
        new_password = st.text_input("Create Password", type="password", key="signup_password")

        if st.button("Sign Up"):
            response = requests.post(f"{BASE_URL}/signup", json={"username": new_username, "password": new_password})
            if response.status_code == 201:
                st.success(response.json().get("message"))
            else:
                st.error(response.json().get("message"))

# ✅ Options Page
elif st.session_state["current_page"] == "Options":
    st.markdown(f'<div class="title-text">Welcome, {st.session_state["username"]}! 🌍</div>', unsafe_allow_html=True)

    # ✅ Add circular image display here
    display_images()

    # ✅ Button container for alignment
    st.markdown('<div class="button-container">', unsafe_allow_html=True)
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("Chat with Voyabot 🤖"):
            st.session_state["current_page"] = "Chat Area"
            st.rerun()

    with col2:
        if st.button("Fill Travel Questionnaire ✈️"):
            st.session_state["current_page"] = "Questionnaire"
            st.rerun()

    col3, col4 = st.columns([1, 1])
    with col3:
        if st.button("User Reviews 📝"):
            st.session_state["current_page"] = "User Reviews"
            st.rerun()
    with col4:
        if st.button("Discover Hidden Gems 🌄"):
            st.session_state["current_page"] = "Underrated Places"
            st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)  # Close button-container div

#Chat-Area
elif st.session_state["current_page"] == "Chat Area":
    show_navbar() 
    st.markdown('<div class="main-content"><div class="centered-container">', unsafe_allow_html=True)
    st.markdown('<div class="title-text">Namaste! Your Personalized Travel Guide to India</div>', unsafe_allow_html=True)

    # ✅ WhatsApp-like chat UI
    chat_container = st.container()
    with chat_container:
        st.markdown('<div class="chat-container">', unsafe_allow_html=True)  # Wrapper for messages

        for message in st.session_state["messages"]:
            role = message["role"]
            content = message["content"]
            timestamp = message.get("timestamp", "")

            if role == "user":
                st.markdown(
                    f"""
                    <div class="user-message">
                        <span class="message-text">{content}</span>
                        <span class="timestamp">{timestamp}</span>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.markdown(
                    f"""
                    <div class="bot-message">
                        <span class="message-text">{content}</span>
                        <span class="timestamp">{timestamp}</span>
                    </div>
                    """, unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)  # Close chat-container div

    # **WhatsApp-like input field inside a form**
    with st.form(key="chat_form", clear_on_submit=True):  # Added clear_on_submit=True
        chat_input = st.text_input(
            "Type your message here...",
            value="",  # Always start with empty value
            key="chat_input_widget",  # Changed key to avoid session state conflict
            placeholder="Ask your travel questions here"
        )
        submit_button = st.form_submit_button("Send")

    # **Process Input Only If Not Waiting for Reply**
    if submit_button and chat_input.strip() and not st.session_state.get("waiting_for_reply", False):
        try:
            st.session_state["waiting_for_reply"] = True  # ✅ Prevent duplicate requests
            headers = {"Authorization": f"Bearer {st.session_state['token']}"}
            response = requests.post(f"{BASE_URL}/chat", json={"message": chat_input}, headers=headers)

            if response.status_code == 200:
                data = response.json()  
                if "error" in data:
                    bot_response = f"⚠️ {data['error']}"  # Show error message if API fails
                else:
                    bot_response = data.get("reply", "No response available.")
            else:
                bot_response = "⚠️ Server error. Try again."

            # ✅ Store chat in session state
            timestamp = datetime.now().strftime("%H:%M")
            st.session_state["messages"].append({"role": "user", "content": chat_input, "timestamp": timestamp})
            st.session_state["messages"].append({"role": "bot", "content": bot_response, "timestamp": timestamp})

        except requests.exceptions.ConnectionError:
            st.error("Could not connect to the backend. Is the Flask server running?")
        
        finally:
            # ✅ Reset input and rerun to refresh UI
            st.session_state["waiting_for_reply"] = False
            st.rerun()

    st.markdown('</div></div>', unsafe_allow_html=True)  # Close containers

    # ✅ Improved "Back to Options" button behavior
    if st.button("← Back to Options", key="back_to_options"):
        st.session_state["current_page"] = "Options"
        st.rerun()

# ✅ Questionnaire Page
elif st.session_state["current_page"] == "Questionnaire":
    show_navbar() 
    st.markdown('<div class="main-content"><div class="centered-container">', unsafe_allow_html=True)
    st.markdown('<div class="title-text">Travel Preferences Questionnaire</div>', unsafe_allow_html=True)

    try:
        headers = {"Authorization": f"Bearer {st.session_state['token']}"}
        response = requests.get(f"{BASE_URL}/get_questions", headers=headers)

        if response.status_code == 200:
            questions_data = response.json()
            
            # Initialize form submission state
            if "questionnaire_submitted" not in st.session_state:
                st.session_state.questionnaire_submitted = False
            
            # Main form container
            form_container = st.empty()
            
            if not st.session_state.questionnaire_submitted:
                with form_container.form(key="questionnaire_form"):
                    answers = {}
                    
                    # Render questions
                    for question in questions_data:
                        q_text = question["question"]
                        options = question["options"]
                        answers[q_text] = st.radio(
                            q_text, 
                            options, 
                            key=f"radio_{hash(q_text)}",
                            index=None
                        )

                    # Special needs text area
                    additional_assistance = st.text_area(
                        "Do you have any special travel needs?",
                        key="special_needs_input"
                    )
                    answers["special_requirements"] = additional_assistance

                    # Submit button
                    if st.form_submit_button("Submit Questionnaire"):
                        if None in answers.values() or "" in answers.values():
                            st.error("⚠️ Please answer all questions before submitting.")
                        else:
                            try:
                                response = requests.post(
                                    f"{BASE_URL}/submit_questionnaire", 
                                    json=answers, 
                                    headers=headers
                                )
                                if response.status_code == 201:
                                    st.session_state.questionnaire_submitted = True
                                    st.session_state.questionnaire_data = response.json()
                                    form_container.empty()  # Clear the form
                            except requests.exceptions.RequestException as e:
                                st.error(f"⚠️ Could not connect to the backend. Error: {str(e)}")

            # Show results after submission
            if st.session_state.questionnaire_submitted:
                data = st.session_state.questionnaire_data
                st.success(data["message"])

                # Display recommendations
                st.markdown(f"""
                    <div class="recommendation-box">
                        <h3>🌍 Personalized Travel Recommendation</h3>
                        <p>{data['recommendation']}</p>
                    </div>
                """, unsafe_allow_html=True)

                if "assistance" in data and data["assistance"]:
                    st.subheader("\U0001F6E0 Additional Assistance:")
                    st.markdown(
                        f"""<div class="assistance-box">
                            <div>{data['assistance']}</div>
                        </div>""", 
                        unsafe_allow_html=True
                    )

                # New questionnaire button
                if st.button("Start New Questionnaire"):
                    st.session_state.questionnaire_submitted = False
                    st.rerun()

        else:
            st.error("Failed to fetch questionnaire questions.")
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")

    st.markdown('</div></div>', unsafe_allow_html=True)

    # Back to Options Button
    if st.button("← Back to Options"):
        st.session_state["current_page"] = "Options"
        st.rerun()
        
# ✅ Underrated Places Page
elif st.session_state.get("current_page") == "Underrated Places":
    show_navbar() 
    st.markdown('<div class="main-content"><div class="centered-container">', unsafe_allow_html=True)
    st.markdown('<div class="title-text">Discover Hidden Gems 🌟</div>', unsafe_allow_html=True)

    if "underrated_places_data" not in st.session_state:
        st.session_state.underrated_places_data = None
        st.session_state.underrated_places_loaded = False

    # Only fetch if we haven't loaded data yet
    if not st.session_state.underrated_places_loaded:
        with st.spinner("Fetching travel recommendations..."):
            try:
                response = requests.get(f"{BASE_URL}/underrated_places")
                if response.status_code == 200:
                    st.session_state.underrated_places_data = response.json()
                    st.session_state.underrated_places_loaded = True
                else:
                    st.error(f"⚠️ Failed to fetch underrated places. Status Code: {response.status_code}")
            except requests.exceptions.RequestException as e:
                st.error(f"⚠️ An error occurred while fetching data: {str(e)}")

    # Display the data if we have it
    if st.session_state.underrated_places_loaded and st.session_state.underrated_places_data:
        places = st.session_state.underrated_places_data.get("places", [])

        for place in places:
            # Alternate between orange and white background
            bg_class = "underrated-card" if places.index(place) % 2 == 0 else "underrated-card white-bg"

            with st.container():
                st.markdown(f'<div class="{bg_class}">', unsafe_allow_html=True)

                # Create two columns for image and details
                col1, col2 = st.columns([1, 2])

                # Column 1: Image
                with col1:
                    st.image(
                        place.get("image_url", "https://via.placeholder.com/400x300"),
                        use_column_width=True,
                        caption=place['Phase Name']
                    )

                # Column 2: Details
                with col2:
                    st.subheader(f"📍 {place['Phase Name']}")
                    st.write(f"**Location:** {place['Location']}")
                    st.write(f"**Category:** {place['Category']}")

                    # Know More expander
                    with st.expander("ℹ️ Know More About This Place"):
                        st.markdown(place.get("ai_details", "No description available"))

                    # Additional details
                    st.write(f"**Budget:** {place.get('Travel Budget', 'Not available')}")
                    st.write(f"**Best Transportation:** {', '.join(place.get('Best Transportation', ['Not available']))}")
                    st.write(f"**Recommended Hotels:** {', '.join(place.get('Recommended Hotels', ['Not available']))}")

                st.markdown('</div>', unsafe_allow_html=True)
                st.markdown("---")

    else:
        st.error("No places found in the response.")

    st.markdown('</div></div>', unsafe_allow_html=True)  # Close containers

    if st.button("← Back to Options"):
        st.session_state["current_page"] = "Options"
        st.rerun()

# Review page
elif st.session_state["current_page"] == "User Reviews":
    show_navbar() 
    st.markdown('<div class="main-content"><div class="centered-container">', unsafe_allow_html=True)
    st.markdown('<div class="title-text">🌟 User Reviews</div>', unsafe_allow_html=True)
    headers = {"Authorization": f"Bearer {st.session_state['token']}"}

    # Initialize session state for form management
    if "review_form_key" not in st.session_state:
        st.session_state.review_form_key = 0
    if "reply_form_keys" not in st.session_state:
        st.session_state.reply_form_keys = {}

    try:
        # Fetch reviews with loading state
        with st.spinner("Loading reviews..."):
            response = requests.get(f"{BASE_URL}/get_reviews", headers=headers)
            response.raise_for_status()
            reviews = response.json()

        if not reviews:
            st.info("No reviews yet. Be the first to share your experience!")
        else:
            for review in reviews:
                review_id = review['_id']
                
                with st.container():
                    # Header with username and timestamp
                    try:
                        timestamp = datetime.strptime(review["timestamp"], "%a, %d %b %Y %H:%M:%S GMT").strftime("%b %d, %Y at %I:%M %p")
                    except ValueError:
                        timestamp = "Unknown time"

                    col_head, col_actions = st.columns([4, 1])
                    
                    with col_head:
                        st.markdown(f"""
                            **👤 {review['username']}**  
                            <small>📅 {timestamp}</small>
                        """, unsafe_allow_html=True)
                    
                    with col_actions:
                        # Like/Dislike buttons with immediate feedback
                        like_col, dislike_col = st.columns(2)
                        with like_col:
                            if st.button(f"👍 {review.get('likes', 0)}", 
                                        key=f"like_{review_id}",
                                        help="Like this review"):
                                with st.spinner("Sending like..."):
                                    requests.post(
                                        f"{BASE_URL}/like_dislike_review",
                                        json={"review_id": review_id, "action": "like"},
                                        headers=headers
                                    )
                                st.rerun()
                        
                        with dislike_col:
                            if st.button(f"👎 {review.get('dislikes', 0)}", 
                                        key=f"dislike_{review_id}",
                                        help="Dislike this review"):
                                with st.spinner("Sending dislike..."):
                                    requests.post(
                                        f"{BASE_URL}/like_dislike_review",
                                        json={"review_id": review_id, "action": "dislike"},
                                        headers=headers
                                    )
                                st.rerun()

                    # Review text
                    st.markdown(f"""
                        <div style="background-color: rgba(255,255,255,0.7); padding: 15px; border-radius: 10px; margin: 10px 0;">
                            {review['review_text']}
                        </div>
                    """, unsafe_allow_html=True)
                    st.write("---")

                    # Replies section
                    if review.get("replies"):
                        with st.expander(f"💬 {len(review['replies'])} Replies", expanded=False):
                            for i, reply in enumerate(review["replies"]):
                                try:
                                    # Handle both string and datetime timestamp formats
                                    if isinstance(reply["timestamp"], str):
                                        reply_time = datetime.strptime(reply["timestamp"], "%a, %d %b %Y %H:%M:%S GMT")
                                    else:
                                        reply_time = reply["timestamp"]
                                    formatted_time = reply_time.strftime("%b %d, %Y at %I:%M %p")
                                except (ValueError, KeyError) as e:
                                    formatted_time = "Unknown time"
                                
                                # Create columns for reply content and delete button
                                reply_col, del_col = st.columns([5, 1])
                                
                                with reply_col:
                                    st.markdown(f"""
                                        <div style="background-color: rgba(255,255,255,0.7); 
                                                    padding: 12px; 
                                                    border-radius: 8px; 
                                                    margin: 8px 0;
                                                    box-shadow: 0 2px 4px rgba(0,0,0,0.1)">
                                            <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                                                <strong>↪️ {reply.get('username', 'Unknown')}</strong>
                                                <small style="color: #666;">{formatted_time}</small>
                                            </div>
                                            <div style="padding-left: 10px; border-left: 3px solid #2089a1;">
                                                {reply.get('reply_text', '')}
                                            </div>
                                        </div>
                                    """, unsafe_allow_html=True)
                                
                                # Add delete button if reply belongs to current user
                                with del_col:
                                    if reply.get('username') == st.session_state["username"]:
                                        if st.button("🗑️", key=f"del_reply_{review_id}_{i}"):
                                            with st.spinner("Deleting reply..."):
                                                response = requests.delete(
                                                    f"{BASE_URL}/delete_reply",
                                                    json={
                                                        "review_id": review_id,
                                                        "reply_index": i
                                                    },
                                                    headers=headers
                                                )
                                            if response.status_code == 200:
                                                st.rerun()
                                            else:
                                                st.error("Failed to delete reply")

                    # Reply form with clearing functionality
                    reply_form_key = st.session_state.reply_form_keys.get(review_id, 0)
                    with st.form(key=f"reply_form_{review_id}_{reply_form_key}"):
                        reply_text = st.text_area(
                            "Your reply...", 
                            key=f"reply_{review_id}",
                            placeholder="Write your response here...",
                            height=100
                        )
                        
                        submit_col, _ = st.columns([2, 5])
                        with submit_col:
                            if st.form_submit_button("Post Reply", use_container_width=True):
                                if reply_text.strip():
                                    with st.spinner("Posting reply..."):
                                        try:
                                            response = requests.post(
                                                f"{BASE_URL}/reply_review",
                                                json={
                                                    "review_id": review_id,
                                                    "reply_text": reply_text
                                                },
                                                headers=headers
                                            )
                                            if response.status_code == 200:
                                                st.session_state.reply_form_keys[review_id] = reply_form_key + 1
                                                st.success("Reply posted successfully!")
                                                st.rerun()
                                            else:
                                                error_msg = response.json().get('error', 'Failed to post reply')
                                                st.error(f"Error: {error_msg}")
                                        except requests.exceptions.RequestException as e:
                                            st.error(f"Connection error: {str(e)}")
                                else:
                                    st.warning("Please write something before submitting")

                    st.markdown("---")

    except requests.exceptions.RequestException as e:
        st.error(f"Failed to load reviews: {str(e)}")

    # New review form with clearing functionality
    with st.form(key=f"new_review_form_{st.session_state.review_form_key}"):
        st.subheader("✍️ Share Your Experience")
        new_review = st.text_area("Your review...", height=100, key="new_review_input")
        if st.form_submit_button("Submit Review"):
            if new_review.strip():
                with st.spinner("Submitting review..."):
                    try:
                        response = requests.post(
                            f"{BASE_URL}/submit_review",
                            json={"review_text": new_review},
                            headers=headers
                        )
                        if response.status_code == 201:
                            st.session_state.review_form_key += 1
                            st.success("Review submitted successfully!")
                            st.rerun()
                        else:
                            st.error(f"Error: {response.json().get('error', 'Unknown error')}")
                    except requests.exceptions.RequestException:
                        st.error("Failed to connect to server")
            else:
                st.warning("Please write something in your review")

    st.markdown('</div></div>', unsafe_allow_html=True)  # Close containers

    if st.button("← Back to Options"):
        st.session_state["current_page"] = "Options"
        st.rerun()
