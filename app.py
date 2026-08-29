import os
import asyncio
import streamlit as st
from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

# ---------- Cell 2: API Key ----------
os.environ["GOOGLE_API_KEY"] = st.secrets["GEMINI_API_KEY"]

# ---------- Cell 3: Knowledge Base ----------
faq_data = {
    "What do you offer?": "Hello po! Thank you po for your interest! We offer po a long-term partnership with you to help grow your personal brand. Paid advertising to help you reach a bigger audience. Your own community events like if you want to run a contest, we can sponsor the prizes. Financial support for events and other activities you may need for your personal Brand growth. For creatives po, we could supply you po with content for your community and such. We can also sponsor paid ads across social media platforms for your community. Like kung gusto mo po mas dumami yung members ng community nyo across different platforms, we can pay for the ads to help grow it. Even if yung sole purpose po is positioning the community as free for all who wants to learn about trading, we can support and promote that as well. This is only in exchange for being an affiliate po ng IQ Option. For everything that you need financially or for the growth of your community, kami po bahala. What do you think po kaya with this offer? We'd really love to work with you and support your growth, especially if we can build a long-term partnership together.",
    "Would love to be partner with you but how much you offer for an upfront fee/Paid Content Like I will create a promotional video for you and put it in my Channel/Communties?": "We do offer paid content po, but we're more interested in building a long-term partnership rather than doing just a one-time payment or per content. With us you can earn up to 80% commission from the trading activities of the traders you refer. on the top of that you can expect 100% of my support as your personal affiliate manager for your online and offline activities in the trading industry, such as sponsoring your events, covering your paid advertisements. to make sure that your community and personal social media pages are going to reach more people for the sole purpose of providing Knowledge and insights about the trading industry through the content you create. For paid promotional content, may I ask po how much you have in mind for your rate? We'd be happy to discuss and see how we can create a long-term partnership that works well for both sides.",
    "Can I get a bunos upfront?": "We do offer Upfront but that should come with a guaranteed number of FTD, but actually we're more interested in building a long-term partnership rather than doing just a one-time payment or per content. With us you can earn up to 80% commission from the trading activities of the traders you refer. on the top of that you can expect 100% of my support as your personal affiliate manager for your online and offline activities in the trading industry, such as sponsoring your events, covering your paid advertisements. to make sure that your community and personal social media pages are going to reach more people for the sole purpose of providing Knowledge and insights about the trading industry through the content you create."
}

commission_data = {
    "standard_commission": "Up to 80% commission from trading activities of referred traders",
    "upfront_bonus": "Available only with a guaranteed number of FTD (First Time Deposits)",
    "support": "100% support for online/offline activities, sponsoring events, paid ads"
}

tone_rules = """
1. Language: Taglish (70% English, 20% Tagalog).
2. Tone: Natural, human, polite ("po"). Avoid robotic or overly formal phrasing.
3. Restrictions: NO EMOJIS. NO HYPHENS. 
4. Objective: Emphasize long-term partnership over one-time payments.
"""

# ---------- Cell 4: Agent ----------
agent_persona = f"""
You are a dedicated Affiliate Manager for IQ Option. Your goal is to recruit partners and build long-term relationships in the trading industry.

TONE RULES:
{tone_rules}

COMMISSION & OFFER DATA:
{commission_data}

FAQ REFERENCE:
{faq_data}

YOUR DIRECTIVE:
1. Read the affiliate's message.
2. Answer their specific question using the FAQ REFERENCE and COMMISSION DATA.
3. If they ask about upfront payments, always pivot to the long-term partnership value.
4. Provide ONLY the reply text. No introductory filler, ready to copy-paste.
5. STRICTLY adhere to the TONE RULES (Taglish, polite 'po', no emojis, no hyphens).
"""

root_agent = Agent(
    name="affiliate_reply_agent",
    model="gemini-3.6-flash",
    description="Drafts replies to potential IQ Option affiliates.",
    instruction=agent_persona
)

# ---------- Cell 5: Runner + Session setup (cached so it only runs once) ----------
APP_NAME = "iqoption_affiliate_agent"
USER_ID = "manager_01"

@st.cache_resource
def get_runner_and_session_service():
    session_service = InMemorySessionService()
    runner = Runner(agent=root_agent, app_name=APP_NAME, session_service=session_service)
    return runner, session_service

runner, session_service = get_runner_and_session_service()

async def generate_reply(session_id, affiliate_message):
    content = types.Content(role="user", parts=[types.Part(text=affiliate_message)])
    final_reply = ""
    async for event in runner.run_async(user_id=USER_ID, session_id=session_id, new_message=content):
        if event.is_final_response() and event.content and event.content.parts:
            final_reply = event.content.parts[0].text
    return final_reply.strip() if final_reply else ""

async def ensure_session(session_id):
    await session_service.create_session(app_name=APP_NAME, user_id=USER_ID, session_id=session_id)

# ---------- Cell 8: UI (replaces input()/while loop) ----------
st.title("IQ Option Affiliate Reply Assistant")

if "active_sessions" not in st.session_state:
    st.session_state.active_sessions = set()

affiliate_name = st.text_input("Affiliate name")
message = st.text_area("Paste affiliate's message")

if st.button("Generate Reply"):
    if not affiliate_name.strip() or not message.strip():
        st.warning("Please enter both a name and a message.")
    else:
        session_id = affiliate_name.lower().replace(" ", "_")

        async def run_flow():
            if session_id not in st.session_state.active_sessions:
                await ensure_session(session_id)
                st.session_state.active_sessions.add(session_id)
            return await generate_reply(session_id, message)

        try:
            reply = asyncio.run(run_flow())
        except Exception as e:
            st.error(f"⚠️ Request failed: {e}")
            st.info("This is usually a temporary Gemini server issue — try again in a moment.")
            reply = ""

        if reply:
            st.subheader(f"Reply to {affiliate_name}")
            st.text_area("Ready to copy & paste", value=reply, height=250)
        else:
            st.warning("⚠️ No reply generated (model may have been overloaded). Try again.")
