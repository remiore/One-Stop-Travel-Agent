
# Travel Agent with MCP

A Streamlit-based AI travel planning application that generates detailed, personalized itineraries using MCP servers and Google Maps. The app integrates Airbnb MCP for real accommodation data and a custom Google Maps MCP for accurate distances, travel times, and location services.

## Agent Architecture
The system follows an end-to-end agent workflow that plans, validates, and assembles a complete travel itinerary in a single execution.

Gemini 2.5 Flash-Lite acts as the central reasoning engine, interpreting user inputs (destination, dates, budget, preferences) and decomposing the trip into structured planning steps such as lodging, daily activities, transportation, and timing.

Airbnb MCP is queried to retrieve real accommodation listings with live pricing, availability, amenities, and location data. These results are evaluated against the user’s budget and proximity requirements.

Google Maps MCP is used to calculate precise distances, travel times, and route feasibility between accommodations, attractions, and restaurants, ensuring the itinerary is geographically realistic and time-aware.

Google Search tools provide up-to-date external context, including weather forecasts, attraction details, operating hours, reviews, and local insights, which are incorporated into daily planning decisions.

End-to-end generation means the agent autonomously gathers all required data, reasons across multiple tools, resolves conflicts (time, distance, budget), and outputs a complete, actionable itinerary without asking follow-up questions.
## Features

**AI-Powered Travel Planning**

- Detailed Itineraries: Day-by-day schedules with timing, addresses, and estimated costs

- Accurate Distance & Travel Time: Powered by Google Maps MCP

- Real Accommodation Data: Live pricing and availability via Airbnb MCP

- Personalized Plans: Tailored to user preferences and budget

**Airbnb MCP Integration**

- Real Airbnb listings with current pricing

- Property details including amenities and reviews

- Budget-filtered recommendations

- Real-time booking information

**Google Maps MCP Integration**

- Precise distance calculations

- Reliable travel time estimates

- Location and address verification

- Optimized transportation routing

**Google Search Integration**

- Current weather forecasts

- Restaurant and attraction details

- Local insights and cultural tips

- Practical travel information

**Additional Features**

- Calendar Export (.ics for Google, Apple, Outlook)\
- Email Export
- Cost Breakdown for all trip components
- Reviews from other travelers via Google maps api
- Built-in Buffer Time for delays
- Multiple Lodging Options per destination


## Local Setup
**Requirements**

**1. API Keys:**

- Gemini API Key https://aistudio.google.com/

- Google Maps API Key https://mapsplatform.google.com/

**2. Python 3.8+**

- MCP Servers:

- Airbnb MCP Server

- Custom Google Maps MCP

## Installation
```bash
  git clone https://github.com/remiore/One-Stop-Travel-Agent.git
  pip install -r requirements.txt
```

## Running the App
```bash
  streamlit run app.py
```
- Enter your API keys in the interface

- Set destination, dates, budget, and preferences

- Click Generate Itinerary

## Troubleshooting

- Verify API keys if errors occur

- Allow time for responses (up to 60 seconds)

- Network restrictions may block MCP connections

##Acknowledgements
greatful for the learning from 
https://github.com/Shubhamsaboo