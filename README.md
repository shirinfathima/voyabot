# 🌍 Voyabot – Your Personalized AI Travel Guide
**Voyabot** is an intelligent, AI-powered travel assistant that helps users explore destinations, book flights, find accommodations and get custom travel recommendations based on their preferences. Built with **Flask (backend)** and **Streamlit (frontend)**, it leverages the **Gemini AI model** to provide dynamic responses and personalized suggestions.

# ✨ Features
* 🛂 **User Authentication** – Secure sign-up and login using JWT tokens
* 📋 **Questionnaire-Based Personalization** – Collects user preferences to generate custom travel plans
* 🤖 **AI Chat Interface** – WhatsApp-style chat powered by Gemini for real-time travel queries
* ✈️ **Flight Recommendations** – Integrated with the Amadeus API
* 🏨 **Hotel Search** – Fetches hotel data from MakCorps API
* 📍 **Place Suggestions via GenAI** – AI-generated tourist spot suggestions based on user input (no external place APIs)
* 💬 **User Review Section** – Share experiences with others
* 🎨 **Themed UI Pages** – Custom styled pages for chat, options, questionnaire and authentication

# ⚙️ Tech Stack
* **Backend**: Flask, MongoDB Atlas, JWT, Gemini API, Amadeus API, MakCorps API
* **Frontend**: Streamlit (with custom CSS), PIL, Requests
* **AI Model**: Gemini (Generative AI from Google)
* **Database**: MongoDB Atlas

# 🚀 Setup Instructions
1. Clone the repo
2. Install dependencies
3. Create a `.env` file with API keys and Mongo URI
4. Run the Flask server (`python app.py`)
5. Run the Streamlit frontend (`streamlit run frontend.py`)

# 💡 Future Enhancements
* Add global destination coverage
* Smart itinerary planning
* Multilingual support
* In-app maps and navigation
* 
