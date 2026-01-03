import re
import asyncio

# Ensure an event loop exists before importing agno which requires it
try:
    asyncio.get_running_loop()
except RuntimeError:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

from textwrap import dedent
from agno.agent import Agent
from agno.run.agent import RunOutput
from agno.tools.mcp import MultiMCPTools
from agno.tools.serpapi import SerpApiTools
from agno.models.google import Gemini
from icalendar import Calendar, Event
from datetime import datetime, timedelta
import streamlit as st
from datetime import date
import os

def generate_ics_content(plan_text: str, start_date: datetime = None) -> bytes:
    """
    Generate an ICS calendar file from a travel itinerary text.

    Args:
        plan_text: The travel itinerary text
        start_date: Optional start date for the itinerary (defaults to today)

    Returns:
        bytes: The ICS file content as bytes
    """
    cal = Calendar()
    cal.add('prodid','-//AI Travel Planner//github.com//')
    cal.add('version', '2.0')

    if start_date is None:
        start_date = datetime.today()

    # Split the plan into days
    day_pattern = re.compile(r'Day (\d+)[:\s]+(.*?)(?=Day \d+|$)', re.DOTALL)
    days = day_pattern.findall(plan_text)

    if not days:  # If no day pattern found, create a single all-day event with the entire content
        event = Event()
        event.add('summary', "Travel Itinerary")
        event.add('description', plan_text)
        event.add('dtstart', start_date.date())
        event.add('dtend', start_date.date())
        event.add("dtstamp", datetime.now())
        cal.add_component(event)
    else:
        # Process each day
        for day_num, day_content in days:
            day_num = int(day_num)
            current_date = start_date + timedelta(days=day_num - 1)

            # Create a single event for the entire day
            event = Event()
            event.add('summary', f"Day {day_num} Itinerary")
            event.add('description', day_content.strip())

            # Make it an all-day event
            event.add('dtstart', current_date.date())
            event.add('dtend', current_date.date())
            event.add("dtstamp", datetime.now())
            cal.add_component(event)

    return cal.to_ical()

async def run_mcp_travel_planner(destination: str, num_days: int, preferences: str, budget: int, gemini_key: str, google_maps_key: str):
    """Run the MCP-based travel planner agent with real-time data access."""

    try:
        # Set Google Maps API key environment variable
        os.environ["GOOGLE_MAPS_API_KEY"] = google_maps_key

        # Initialize MCPTools with Airbnb MCP
        mcp_tools = MultiMCPTools(
            [
            "npx -y @openbnb/mcp-server-airbnb --ignore-robots-txt",
            "npx @gongrzhe/server-travelplanner-mcp",
            ],      
            env={
                "GOOGLE_MAPS_API_KEY": google_maps_key,
            },
            timeout_seconds=60,
        )   

        # Connect to Airbnb MCP server
        await mcp_tools.connect()


        travel_planner = Agent(
            name="Travel Planner",
            role="Creates travel itineraries using Airbnb, Google Maps, and Google Search",
            model=Gemini(
                id="gemini-2.0-flash-exp",
                api_key=gemini_key,
                retries=10,
                exponential_backoff=True,
                delay_between_retries=10
            ),
            description=dedent(
                """\
                You are a professional travel consultant AI that creates highly detailed travel itineraries directly without asking questions.

                You have access to:
                🏨 Airbnb listings with real availability and current pricing
                🗺️ Google Maps MCP for location services, directions, distance calculations, and local navigation
                🔍 Web search capabilities for current information, reviews, and travel updates

                ALWAYS create a complete, detailed itinerary immediately without asking for clarification or additional information.
                Use Google Maps MCP extensively to calculate distances between all locations and provide precise travel times.
                If information is missing, use your best judgment and available tools to fill in the gaps.
                """
            ),
            instructions=[
                "IMPORTANT: Never ask questions or request clarification - always generate a complete itinerary",
                "Research the destination thoroughly using all available tools to gather comprehensive current information",
                "Find suitable accommodation options within the budget using Airbnb MCP with real prices and availability",
                "Create an extremely detailed day-by-day itinerary with specific activities, locations, exact timing, and distances",
                "Use Google Maps MCP extensively to calculate distances between ALL locations and provide travel times",
                "Include detailed transportation options and turn-by-turn navigation tips using Google Maps MCP",
                "Research dining options with specific restaurant names, addresses, price ranges, and distance from accommodation",
                "Check current weather conditions, seasonal factors, and provide detailed packing recommendations",
                "Calculate precise estimated costs for EVERY aspect of the trip and ensure recommendations fit within budget",
                "Include detailed information about each attraction: opening hours, ticket prices, best visiting times, and distance from accommodation",
                "Add practical information including local transportation costs, currency exchange, safety tips, and cultural norms",
                "Structure the itinerary with clear sections, detailed timing for each activity, and include buffer time between activities",
                "Use all available tools proactively without asking for permission",
                "Generate the complete, detailed itinerary in one response without follow-up questions"
            ],
            tools=[mcp_tools, SerpApiTools()],
            add_datetime_to_context=True,
            markdown=True,
            debug_mode=False,
        )

        # Create the planning prompt
        prompt = f"""
        IMMEDIATELY create an extremely detailed and comprehensive travel itinerary for:

        **Destination:** {destination}
        **Duration:** {num_days} days
        **Budget:** ${budget} USD total
        **Preferences:** {preferences}

        DO NOT ask any questions. Generate a complete, highly detailed itinerary now using all available tools.

        **CRITICAL REQUIREMENTS:**
        - Use Google Maps MCP to calculate distances and travel times between ALL locations
        - Include specific addresses for every location, restaurant, and attraction
        - Provide detailed timing for each activity with buffer time between locations
        - Calculate precise costs for transportation between each location
        - Include opening hours, ticket prices, and best visiting times for all attractions
        - Provide detailed weather information and specific packing recommendations

        **REQUIRED OUTPUT FORMAT:**
        1. **Trip Overview** - Summary, total estimated cost breakdown, detailed weather forecast
        2. **Accommodation** - 3 specific Airbnb options with real prices, addresses, amenities, and distance from city center
        3. **Transportation Overview** - Detailed transportation options, costs, and recommendations
        4. **Day-by-Day Itinerary** - Extremely detailed schedule with:
           - Specific start/end times for each activity
           - Exact distances and travel times between locations (use Google Maps MCP)
           - Detailed descriptions of each location with addresses
           - Opening hours, ticket prices, and best visiting times
           - Estimated costs for each activity and transportation
           - Buffer time between activities for unexpected delays
        5. **Dining Plan** - Specific restaurants with addresses, price ranges, cuisine types, and distance from accommodation
        6. **Detailed Practical Information**:
           - Weather forecast with clothing recommendations
           - Currency exchange rates and costs
           - Local transportation options and costs
           - Safety information and emergency contacts
           - Cultural norms and etiquette tips
           - Communication options (SIM cards, WiFi, etc.)
           - Health and medical considerations
           - Shopping and souvenir recommendations

        Use Airbnb MCP for real accommodation data, Google Maps MCP for ALL distance calculations and location services, and web search for current information.
        Make reasonable assumptions and fill in any gaps with your knowledge.
        Generate the complete, highly detailed itinerary in one response without asking for clarification.
        """

        response: RunOutput = await travel_planner.arun(prompt)
        return response.content

    finally:
        await mcp_tools.close()

def run_travel_planner(destination: str, num_days: int, preferences: str, budget: int, gemini_key: str, google_maps_key: str):
    """Synchronous wrapper for the async MCP travel planner."""
    return asyncio.run(run_mcp_travel_planner(destination, num_days, preferences, budget, gemini_key, google_maps_key))
    
# -------------------- Streamlit App --------------------
    
# Configure the page
st.set_page_config(
    page_title="MCP AI Travel Planner",
    page_icon="✈️",
    layout="wide"
)

# Initialize session state for theme
if 'theme' not in st.session_state:
    st.session_state.theme = 'light'

def set_theme(key_name):
    # Update theme based on the toggle state - Ensure it is a string!
    # We use the key provided to check the specific widget state
    is_dark = st.session_state.get(key_name, False)
    st.session_state.theme = 'dark' if is_dark else 'light'

# Dynamic CSS generation based on theme
def get_theme_css(theme):
    if theme == 'dark':
        # Dark Mode Variables
        primary_color = "#ffffff"
        background_color = "#000000"
        secondary_background_color = "#111111"
        sidebar_background_color = "#111111"
        text_color = "#ffffff"
        border_color = "#ffffff"
        input_bg = "#000000"
        button_bg = "#ffffff"
        button_text = "#000000"
        button_hover_bg = "#000000"
        button_hover_text = "#ffffff"
        shadow_color = "#ffffff"
    else:
        # Light Mode Variables (Default)
        primary_color = "#000000"
        background_color = "#ffffff"
        secondary_background_color = "#FFA500" # Orange for toggle visibility
        sidebar_background_color = "#fafafa"
        text_color = "#000000"
        border_color = "#000000"
        input_bg = "#ffffff"
        button_bg = "#ffffff"
        button_text = "#000000"
        button_hover_bg = "#000000"
        button_hover_text = "#ffffff"
        shadow_color = "#000000"

    return f"""
    <style>
        /* Modern Minimalist Font Stack */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
        
        :root {{
            --primary-color: {primary_color};
            --background-color: {background_color};
            --secondary-background-color: {secondary_background_color};
            --text-color: {text_color};
            --font: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
        }}

        html, body {{
            font-family: var(--font);
            color: {text_color};
            background-color: {background_color};
        }}
        
        /* Main background */
        .stApp {{
            background-color: {background_color};
            color: {text_color};
        }}
        
        /* Sidebar Polish */
        section[data-testid="stSidebar"] {{
            background-color: {sidebar_background_color};
            border-right: 2px solid {border_color};
        }}
        div[data-testid="stSidebarNav"] {{
            border-bottom: 2px solid {border_color};
            margin-bottom: 1rem;
            padding-bottom: 1rem;
        }}
        
        /* Typography Hierarchy */
        h1, h2, h3 {{
            font-weight: 700 !important;
            letter-spacing: -0.02em !important;
            text-transform: uppercase;
            color: {text_color} !important;
        }}
        h1 {{ font-size: 2.5rem !important; margin-bottom: 1.5rem !important; }}
        h2 {{ font-size: 1.8rem !important; margin-top: 2rem !important; border-bottom: 2px solid {border_color}; padding-bottom: 0.5rem; }}
        h3 {{ font-size: 1.4rem !important; }}
        
        /* Inputs - Solid & Professional */
        .stTextInput input, 
        .stNumberInput input, 
        .stDateInput input, 
        .stTextArea textarea, 
        .stSelectbox div[data-baseweb="select"] {{
            background-color: {input_bg} !important;
            color: {text_color} !important;
            border: 2px solid {border_color} !important;
            border-radius: 0px !important;
            box-shadow: none !important;
            padding: 0.5rem 0.75rem !important;
            font-size: 1rem !important;
            font-weight: 500;
        }}
        
        /* Input Labels */
        .stTextInput label, .stNumberInput label, .stDateInput label, .stTextArea label, .stSelectbox label {{
            color: {text_color} !important;
        }}

        /* Focus state - Sharp & Clean */
        .stTextInput input:focus, 
        .stNumberInput input:focus, 
        .stDateInput input:focus, 
        .stTextArea textarea:focus,
        .stSelectbox div[data-baseweb="select"]:focus-within {{
            border-color: {border_color} !important;
            background-color: {secondary_background_color} !important; 
        }}
        
        /* Buttons - High Impact & Contrast */
        div.stButton > button {{
            background-color: {button_bg} !important;
            color: {button_text} !important;
            border: 2px solid {border_color} !important;
            border-radius: 0px !important;
            padding: 0.75rem 2rem !important;
            font-weight: 700 !important;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            transition: all 0.2s ease;
        }}
        /* Ensure text inside button inherits color */
        div.stButton > button p {{
            color: {button_text} !important;
        }}
        
        div.stButton > button:hover {{
            background-color: {button_hover_bg} !important;
            color: {button_hover_text} !important;
            transform: translateY(-2px);
            box-shadow: 4px 4px 0px 0px {shadow_color} !important;
            border: 2px solid {border_color} !important;
        }}
        div.stButton > button:hover p {{
            color: {button_hover_text} !important;
        }}
        
        div.stButton > button:active {{
            transform: translateY(0px);
            box-shadow: 0px 0px 0px 0px {shadow_color} !important;
        }}
        
        /* Download Button consistent with primary */
        a[download] {{
            display: inline-flex;
            justify-content: center;
            align-items: center;
            background-color: {button_bg} !important;
            color: {button_text} !important;
            border: 2px solid {border_color} !important;
            border-radius: 0px !important;
            padding: 0.75rem 2rem !important;
            font-weight: 700 !important;
            text-transform: uppercase;
            text-decoration: none;
            transition: all 0.2s ease;
        }}
        a[download]:hover {{
            background-color: {button_hover_bg} !important;
            color: {button_hover_text} !important;
            box-shadow: 4px 4px 0px 0px {shadow_color} !important;
        }}
        
        /* Multiselect refinement */
        .stMultiSelect span[data-baseweb="tag"] {{
            background-color: {secondary_background_color} !important;
            color: {text_color} !important;
            border: 1px solid {border_color} !important;
            border-radius: 0px;
            font-weight: 600;
        }}
        
        /* Alerts/Info boxes - Minimalist */
        .stAlert {{
            background-color: {background_color} !important;
            color: {text_color} !important;
            border: 2px solid {border_color} !important;
            border-radius: 0px !important;
        }}
        
        /* Labels */
        label, .stText, p {{
            color: {text_color} !important;
            font-weight: 600 !important;
            font-size: 0.95rem !important;
        }}
        
        /* Expander/Accordion */
        .streamlit-expanderHeader {{
            border: 2px solid {border_color} !important;
            border-radius: 0px !important;
            background-color: {background_color} !important;
            color: {text_color} !important;
        }}
        
        /* Checkbox/Radio */
        .stCheckbox label, .stRadio label, .stToggle label {{
            color: {text_color} !important;
        }}

        /* Toggle Track - Force Color */
        .stToggle div[data-baseweb="checkbox"] div {{
            background-color: {secondary_background_color} !important;
        }}
    </style>
    """

# Inject Dynamic CSS
st.markdown(get_theme_css(st.session_state.theme), unsafe_allow_html=True)

# Initialize session state
if 'itinerary' not in st.session_state:
    st.session_state.itinerary = None

# Initialize session state
if 'itinerary' not in st.session_state:
    st.session_state.itinerary = None
if 'setup_complete' not in st.session_state:
    st.session_state.setup_complete = False
if 'gemini_api_key' not in st.session_state:
    st.session_state.gemini_api_key = ''
if 'google_maps_key' not in st.session_state:
    st.session_state.google_maps_key = ''

# Helper function to reset the app
def reset_app():
    st.session_state.setup_complete = False
    st.session_state.itinerary = None
    # We keep the keys pre-filled for convenience, or clear them if strict security is needed.
    # For user friendliness, let's keep them in session state but require clicking "Start" again.

# --- SIGN IN PAGE (Configuration) ---
if not st.session_state.setup_complete:
    # Centered Container for "Sign In"
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("""
        <h1 style='text-align: center; margin-bottom: -35px; line-height: 1.0;'>TripSynth</h1>
        <p style='text-align: center; margin-top: 0px; font-size: 1.1rem;'>Your next adventure begin here...</p>
        <div style='height: 30px;'></div>
        """, unsafe_allow_html=True)

        with st.container(border=True):
            st.markdown("<h3 style='text-align: center; margin-bottom: 20px;'>We need a few things to get started</h3>", unsafe_allow_html=True)
            
            # Theme Toggle centered
            st.toggle(
                "Dark Mode", 
                value=(st.session_state.theme == 'dark'), 
                key='theme_toggle', 
                on_change=set_theme,
                kwargs={'key_name': 'theme_toggle'}
            )
            
            st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
            
            # API Keys Inputs
            gemini_key_input = st.text_input(
                "Gemini API Key", 
                type="password", 
                help="Required for AI planning",
                value=st.session_state.gemini_api_key
            )
            
            google_maps_key_input = st.text_input(
                "Google Maps API Key", 
                type="password", 
                help="Required for location services",
                value=st.session_state.google_maps_key
            )
            
            st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
            
            # Start Button
            if st.button("Start Planning ✈️", use_container_width=True):
                if gemini_key_input and google_maps_key_input:
                    st.session_state.gemini_api_key = gemini_key_input
                    st.session_state.google_maps_key = google_maps_key_input
                    st.session_state.setup_complete = True
                    st.rerun()
                else:
                    st.error("Please enter both API keys to continue.")
                    st.info("""
                    **Required API Keys:**
                    - **Gemini API Key**: https://aistudio.google.com/app/apikey
                    - **Google Maps API Key**: https://console.cloud.google.com/apis/credentials
                    """)

# --- MAIN APP INTERFACE ---
else:
    # Sidebar only shows Reset/Configuration button when logged in
    with st.sidebar:
        st.header("⚙️ Settings")
        
        # Theme Toggle in Sidebar (also available here)
        st.toggle(
            "Dark Mode", 
            value=(st.session_state.theme == 'dark'), 
            key='theme_toggle_sidebar', 
            on_change=set_theme,
            kwargs={'key_name': 'theme_toggle_sidebar'}
        )
        
        st.divider()
        if st.button("🔄 Reset Configuration", use_container_width=True):
            reset_app()
            st.rerun()

    # Title and description (Minimal version for main app)
    st.markdown("""
    <h1 style='text-align: center; margin-bottom: -35px; line-height: 1.0;'>Bestie Travel Agent</h1>
    <p style='text-align: center; margin-top: 0px; font-size: 1.1rem;'>Your next adventure begin here...</p>
    """, unsafe_allow_html=True)

    # Main input section
    st.header("Trip Details")

    col1, col2 = st.columns(2)

    with col1:
        destination = st.text_input("Destination", placeholder="e.g., Paris, Tokyo, New York")
        num_days = st.number_input("Number of Days", min_value=1, max_value=30, value=7)

    with col2:
        budget = st.number_input("Budget (USD)", min_value=100, max_value=10000, step=100, value=2000)
        start_date = st.date_input("Start Date", min_value=date.today(), value=date.today())

    # Preferences section
    st.subheader("Travel Preferences")
    preferences_input = st.text_area(
        "Describe your travel preferences",
        placeholder="e.g., adventure activities, cultural sites, food, relaxation, nightlife...",
        height=100
    )

    # Quick preference buttons
    quick_prefs = st.multiselect(
        "Quick Preferences (optional)",
        ["Adventure", "Relaxation", "Sightseeing", "Cultural Experiences",
         "Beach", "Mountain", "Luxury", "Budget-Friendly", "Food & Dining",
         "Shopping", "Nightlife", "Family-Friendly"],
        help="Select multiple preferences or describe in detail above"
    )

    # Combine preferences
    all_preferences = []
    if preferences_input:
        all_preferences.append(preferences_input)
    if quick_prefs:
        all_preferences.extend(quick_prefs)

    preferences = ", ".join(all_preferences) if all_preferences else "General sightseeing"

    # Generate button
    col1, col2 = st.columns([1, 1])

    with col1:
        if st.button("🎯 Generate Itinerary", type="primary"):
            if not destination:
                st.error("Please enter a destination.")
            elif not preferences:
                st.warning("Please describe your preferences or select quick preferences.")
            else:
                tools_message = "🏨 Connecting to Airbnb MCP"
                # Use stored keys
                gemini_key = st.session_state.gemini_api_key
                maps_key = st.session_state.google_maps_key
                
                if maps_key:
                    tools_message += " and Google Maps MCP"
                tools_message += ", creating itinerary..."

                with st.spinner(tools_message):
                    try:
                        # Calculate number of days from start date
                        response = run_travel_planner(
                            destination=destination,
                            num_days=num_days,
                            preferences=preferences,
                            budget=budget,
                            gemini_key=gemini_key,
                            google_maps_key=maps_key
                        )

                        # Store the response in session state
                        st.session_state.itinerary = response

                        # Show MCP connection status
                        if "Airbnb" in response and ("listing" in response.lower() or "accommodation" in response.lower()):
                            st.success("✅ Your travel itinerary is ready with Airbnb data!")
                            st.info("🏨 Used real Airbnb listings for accommodation recommendations")
                        else:
                            st.success("✅ Your travel itinerary is ready!")
                            st.info("📝 Used general knowledge for accommodation suggestions (Airbnb MCP may have failed to connect)")

                    except Exception as e:
                        st.error(f"Error: {str(e)}")
                        st.info("Please try again or check your internet connection.")

    with col2:
        if st.session_state.itinerary:
            # Generate the ICS file
            ics_content = generate_ics_content(st.session_state.itinerary, datetime.combine(start_date, datetime.min.time()))

            # Provide the file for download
            st.download_button(
                label="📅 Download as Calendar",
                data=ics_content,
                file_name="travel_itinerary.ics",
                mime="text/calendar"
            )

    # Display itinerary
    if st.session_state.itinerary:
        st.header("📋 Your Travel Itinerary")
        st.markdown(st.session_state.itinerary)