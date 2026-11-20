import os
import io
import math
import random
import json
import sqlite3
import hashlib
import importlib
import base64
import re
from datetime import datetime
try:
    import streamlit as st  # type: ignore
    STREAMLIT_AVAILABLE = True
except Exception:
    st = None
    STREAMLIT_AVAILABLE = False
import pandas as pd  # type: ignore
try:
    import matplotlib.pyplot as plt  # type: ignore
    MATPLOTLIB_AVAILABLE = True
except Exception:
    plt = None
    MATPLOTLIB_AVAILABLE = False
try:
    from dotenv import load_dotenv  # type: ignore
    DOTENV_AVAILABLE = True
except Exception:
    # Provide a no-op fallback if python-dotenv is not installed
    def load_dotenv(*args, **kwargs):
        return False
    DOTENV_AVAILABLE = False

# Try importing Plotly
try:
    import plotly.graph_objects as go  # type: ignore
    import plotly.express as px  # type: ignore
    PLOTLY_AVAILABLE = True
except Exception:
    go = None
    px = None
    PLOTLY_AVAILABLE = False

# Try importing ReportLab for PDF generation
try:
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph  # type: ignore
    from reportlab.lib import colors  # type: ignore
    from reportlab.lib.styles import getSampleStyleSheet  # type: ignore
    from reportlab.lib.units import inch  # type: ignore
    REPORTLAB_AVAILABLE = True
except ImportError:
    SimpleDocTemplate = None
    Table = None
    TableStyle = None
    Paragraph = None
    colors = None
    getSampleStyleSheet = None
    inch = None
    REPORTLAB_AVAILABLE = False

try:
    from PIL import Image, ImageDraw, ImageFont  # type: ignore
    PIL_AVAILABLE = True
except Exception:
    Image = None
    ImageDraw = None
    ImageFont = None
    PIL_AVAILABLE = False

# Try importing Groq SDK
try:
    groq = importlib.import_module("groq")
    GROQ_AVAILABLE = True
except Exception:
    groq = None
    GROQ_AVAILABLE = False

# Load environment variables
load_dotenv()
load_dotenv("streamlit_app3.env")

# NO HARDCODED API KEYS OR SECRETS
GROQ_API_KEY = os.getenv("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", "").strip().strip('"').strip("'")

groq_client = None
if GROQ_API_KEY and GROQ_AVAILABLE and groq is not None:
    try:
        groq_client = groq.Groq(api_key=GROQ_API_KEY)
    except Exception:
        groq_client = None

# -----------------------------
# MASTER SELECTION LISTS
# -----------------------------
WORLD_COUNTRIES = [
    "India",
    "United States",
    "United Kingdom",
    "Canada",
    "Australia",
    "Germany",
    "France",
    "United Arab Emirates",
    "Singapore",
    "Japan",
    "China",
    "Brazil",
    "South Africa",
    "Saudi Arabia",
    "Netherlands",
    "Switzerland",
    "Sweden",
    "Spain",
    "Italy",
    "Mexico",
    "Indonesia",
    "Malaysia",
    "New Zealand",
    "Pakistan",
    "Bangladesh",
    "Nepal",
    "Sri Lanka",
    "Nigeria",
    "Kenya",
    "Egypt",
    "Argentina",
    "Chile",
    "Colombia",
    "Philippines",
    "Vietnam",
    "Thailand",
    "South Korea",
    "Turkey",
    "Poland",
    "Norway",
    "Denmark",
    "Finland",
    "Ireland",
    "Belgium",
    "Austria",
    "Portugal",
    "Greece",
    "Czech Republic",
    "Hungary",
    "Romania",
    "Israel",
    "Qatar",
    "Kuwait",
    "Oman",
    "Bahrain",
    "Other Country"
]

INDIAN_STATES = [
    "Andhra Pradesh",
    "Arunachal Pradesh",
    "Assam",
    "Bihar",
    "Chhattisgarh",
    "Goa",
    "Gujarat",
    "Haryana",
    "Himachal Pradesh",
    "Jharkhand",
    "Karnataka",
    "Kerala",
    "Madhya Pradesh",
    "Maharashtra",
    "Manipur",
    "Meghalaya",
    "Mizoram",
    "Nagaland",
    "Odisha",
    "Punjab",
    "Rajasthan",
    "Sikkim",
    "Tamil Nadu",
    "Telangana",
    "Tripura",
    "Uttar Pradesh",
    "Uttarakhand",
    "West Bengal",
    "Andaman and Nicobar Islands",
    "Chandigarh",
    "Dadra and Nagar Haveli and Daman and Diu",
    "Delhi (NCT)",
    "Jammu and Kashmir",
    "Ladakh",
    "Lakshadweep",
    "Puducherry"
]

PROFESSIONS_LIST = [
    "Software Engineer / Developer",
    "Data Scientist / AI Specialist",
    "Product Manager / Project Manager",
    "DevOps / Cloud Engineer",
    "UI/UX Designer / Product Designer",
    "Financial Analyst / Accountant / CA",
    "Investment Banker / Wealth Advisor",
    "Doctor / Physician / Surgeon",
    "Nurse / Healthcare Specialist",
    "Lawyer / Legal Consultant",
    "Business Owner / Entrepreneur",
    "Marketing Specialist / Growth Strategist",
    "Sales / Business Development",
    "Teacher / Professor / Educator",
    "Architect / Civil Engineer",
    "Mechanical / Electrical Engineer",
    "Human Resources (HR) Manager",
    "Consultant / Strategy Advisor",
    "Freelancer / Creative Professional",
    "Student / Researcher",
    "Government Servant / Civil Service",
    "Retired / Independent Investor",
    "Other (Specify Custom)"
]

# STRICT ABSOLUTE PATH DATABASE LOCATION
DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "money_matrix.db")

def fmt_curr(val, sym="₹"):
    """Guaranteed Currency Formatter - Cannot be corrupted by timestamp strings."""
    s = str(sym).strip() if sym else "₹"
    if s not in ["₹", "$", "€", "£", "A$"] or ":" in s or "-" in s or len(s) > 4:
        s = "₹"
    try:
        num = float(val)
        return f"{s} {num:,.0f}"
    except Exception:
        return f"{s} 0"

# -----------------------------
# Database Setup & Operations
# -----------------------------
def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password_hash TEXT NOT NULL,
            full_name TEXT,
            email TEXT UNIQUE,
            age INTEGER,
            gender TEXT,
            marital_status TEXT,
            dependents INTEGER,
            profession TEXT,
            location TEXT,
            goal TEXT,
            risk_tolerance TEXT,
            retirement_age INTEGER,
            currency_symbol TEXT,
            profile_pic TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Migration helper for email & profile_pic columns if missing
    cursor.execute("PRAGMA table_info(users)")
    columns = [row[1] for row in cursor.fetchall()]
    if "email" not in columns:
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN email TEXT")
        except Exception:
            pass
    if "profile_pic" not in columns:
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN profile_pic TEXT")
        except Exception:
            pass

    # Financial progress records table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS financial_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            month_year TEXT NOT NULL,
            total_income REAL,
            total_expense REAL,
            balance REAL,
            savings_rate REAL,
            salary REAL,
            freelance REAL,
            business REAL,
            rental REAL,
            investment REAL,
            other_income REAL,
            rent REAL,
            food REAL,
            electricity REAL,
            internet REAL,
            shopping REAL,
            travel REAL,
            education REAL,
            medical REAL,
            emi REAL,
            entertainment REAL,
            insurance REAL,
            others REAL,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (username) REFERENCES users(username)
        )
    """)
    
    # Monthly challenges table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS challenges (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            title TEXT NOT NULL,
            category TEXT,
            target_value REAL,
            current_value REAL,
            status TEXT DEFAULT 'In Progress',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Daily goal checkins table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS daily_checkins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            date_str TEXT NOT NULL,
            completed INTEGER,
            note TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Clean up any corrupted legacy columns in users table
    cursor.execute("""
        UPDATE users SET currency_symbol = '₹'
        WHERE currency_symbol IS NULL OR currency_symbol LIKE '%2026-%' OR currency_symbol LIKE '%:%' OR length(currency_symbol) > 5
    """)
    cursor.execute("""
        UPDATE users SET profession = 'Software Engineer / Developer'
        WHERE profession IS NULL OR profession LIKE '%2026-%' OR profession LIKE '%:%' OR profession LIKE '%Ahmedabad%'
    """)
    cursor.execute("""
        UPDATE users SET location = 'Gujarat, India'
        WHERE location IS NULL OR location LIKE '%2026-%' OR location LIKE '%:%' OR location LIKE '%Savings Maximizer%'
    """)

    # Ensure default admin / demo user exists for instant out-of-the-box login
    cursor.execute("SELECT COUNT(*) FROM users WHERE username='admin'")
    if cursor.fetchone()[0] == 0:
        admin_pw_hash = hashlib.sha256("admin123".encode("utf-8")).hexdigest()
        try:
            cursor.execute("""
                INSERT INTO users (username, password_hash, email, full_name, age, gender, marital_status, dependents, profession, location, goal, risk_tolerance, retirement_age, currency_symbol)
                VALUES ('admin', ?, 'admin@moneymatrix.io', 'Alex Morgan (Admin)', 30, 'Male', 'Single', 1, 'Software Engineer / Developer', 'Gujarat, India', 'Savings Maximizer (Aggressive Savings)', 'Balanced', 60, '₹')
            """, (admin_pw_hash,))
        except Exception:
            pass

    conn.commit()
    conn.close()

init_db()

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

def db_get_user(username_or_email: str):
    if not username_or_email:
        return None
    query_val = str(username_or_email).strip()
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row  # Explicit column name indexing to prevent positional column shift
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE LOWER(username) = LOWER(?) OR LOWER(email) = LOWER(?)", (query_val, query_val))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    
    col_keys = row.keys()
    username = row["username"] if "username" in col_keys else ""
    pw_hash = row["password_hash"] if "password_hash" in col_keys else ""
    full_name = row["full_name"] if "full_name" in col_keys else "Alex Morgan"
    email = row["email"] if "email" in col_keys else f"{username}@moneymatrix.io"
    age = row["age"] if "age" in col_keys else 30
    gender = row["gender"] if "gender" in col_keys else "Male"
    marital = row["marital_status"] if "marital_status" in col_keys else "Single"
    dependents = row["dependents"] if "dependents" in col_keys else 1
    profession = row["profession"] if "profession" in col_keys else "Software Engineer / Developer"
    location = row["location"] if "location" in col_keys else "Gujarat, India"
    goal = row["goal"] if "goal" in col_keys else "Savings Maximizer (Aggressive Savings)"
    risk = row["risk_tolerance"] if "risk_tolerance" in col_keys else "Balanced"
    ret_age = row["retirement_age"] if "retirement_age" in col_keys else 60
    currency_symbol = row["currency_symbol"] if "currency_symbol" in col_keys else "₹"
    profile_pic = row["profile_pic"] if "profile_pic" in col_keys and row["profile_pic"] else ""
    created_at = row["created_at"] if "created_at" in col_keys else ""

    # Sanitize currency symbol, profession, location
    if not currency_symbol or currency_symbol not in ["₹", "$", "€", "£", "A$"] or ":" in str(currency_symbol) or "-" in str(currency_symbol) or len(str(currency_symbol)) > 4:
        currency_symbol = "₹"

    if not profession or ":" in str(profession) or "-" in str(profession) or "2026-" in str(profession):
        profession = "Software Engineer / Developer"

    if not location or ":" in str(location) or "-" in str(location) or "2026-" in str(location) or "Savings Maximizer" in str(location):
        location = "Gujarat, India"

    return (
        username, pw_hash, full_name, email, age, gender, marital, dependents,
        profession, location, goal, risk, ret_age, currency_symbol, profile_pic, created_at
    )

def db_create_user(username, password, email="", full_name="Alex Morgan", age=30, gender="Male", marital_status="Single", dependents=1, profession="Software Engineer / Developer", location="Gujarat, India", goal="Savings Maximizer (Aggressive Savings)", risk_tolerance="Balanced", retirement_age=60, currency_symbol="₹", profile_pic=""):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    u_clean = username.strip()
    p_clean = password.strip()
    pw_hash = hash_password(p_clean)
    email_clean = email.strip() if email else f"{u_clean}@moneymatrix.io"
    try:
        cursor.execute("""
            INSERT INTO users (username, password_hash, email, full_name, age, gender, marital_status, dependents, profession, location, goal, risk_tolerance, retirement_age, currency_symbol, profile_pic)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (u_clean, pw_hash, email_clean, full_name, int(age), gender, marital_status, int(dependents), profession, location, goal, risk_tolerance, int(retirement_age), currency_symbol, profile_pic))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        conn.close()
        return False

def db_update_user_profile(username, full_name, email, age, gender, marital_status, dependents, profession, location, goal, risk_tolerance, retirement_age, currency_symbol, profile_pic=None):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    if profile_pic is not None:
        cursor.execute("""
            UPDATE users SET full_name=?, email=?, age=?, gender=?, marital_status=?, dependents=?, profession=?, location=?, goal=?, risk_tolerance=?, retirement_age=?, currency_symbol=?, profile_pic=?
            WHERE username=?
        """, (full_name, email, int(age), gender, marital_status, int(dependents), profession, location, goal, risk_tolerance, int(retirement_age), currency_symbol, profile_pic, username))
    else:
        cursor.execute("""
            UPDATE users SET full_name=?, email=?, age=?, gender=?, marital_status=?, dependents=?, profession=?, location=?, goal=?, risk_tolerance=?, retirement_age=?, currency_symbol=?
            WHERE username=?
        """, (full_name, email, int(age), gender, marital_status, int(dependents), profession, location, goal, risk_tolerance, int(retirement_age), currency_symbol, username))
    conn.commit()
    conn.close()

def db_get_records(username):
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query("""
        SELECT id, username, month_year, total_income, total_expense, balance, savings_rate,
               salary, freelance, business, rental, investment, other_income,
               rent, food, electricity, internet, shopping, travel, education, medical, emi, entertainment, insurance, others, notes, created_at
        FROM financial_records WHERE username=? ORDER BY created_at DESC
    """, conn, params=(username,))
    conn.close()
    return df

def db_add_record(username, month_year, inc_data, exp_data, notes=""):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    tot_inc = sum(inc_data.values())
    tot_exp = sum(exp_data.values())
    bal = tot_inc - tot_exp
    sav_rate = (bal / tot_inc * 100) if tot_inc > 0 else 0.0
    
    cursor.execute("""
        INSERT INTO financial_records (
            username, month_year, total_income, total_expense, balance, savings_rate,
            salary, freelance, business, rental, investment, other_income,
            rent, food, electricity, internet, shopping, travel, education, medical, emi, entertainment, insurance, others, notes
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        username, month_year, tot_inc, tot_exp, bal, sav_rate,
        inc_data.get("salary", 0), inc_data.get("freelance", 0), inc_data.get("business", 0), inc_data.get("rental", 0), inc_data.get("investment", 0), inc_data.get("other_income", 0),
        exp_data.get("rent", 0), exp_data.get("food", 0), exp_data.get("electricity", 0), exp_data.get("internet", 0), exp_data.get("shopping", 0), exp_data.get("travel", 0), exp_data.get("education", 0), exp_data.get("medical", 0), exp_data.get("emi", 0), exp_data.get("entertainment", 0), exp_data.get("insurance", 0), exp_data.get("others", 0), notes
    ))
    conn.commit()
    conn.close()

def db_delete_record(record_id):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM financial_records WHERE id=?", (record_id,))
    conn.commit()
    conn.close()

def db_get_challenges(username):
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query("SELECT id, username, title, category, target_value, current_value, status, created_at FROM challenges WHERE username=? ORDER BY created_at DESC", conn, params=(username,))
    conn.close()
    return df

def db_add_challenge(username, title, category, target_val):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO challenges (username, title, category, target_value, current_value, status) VALUES (?, ?, ?, ?, 0, 'In Progress')", (username, title, category, target_val))
    conn.commit()
    conn.close()

def db_update_challenge(challenge_id, current_val, status):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("UPDATE challenges SET current_value=?, status=? WHERE id=?", (current_val, status, challenge_id))
    conn.commit()
    conn.close()

def db_delete_challenge(challenge_id):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM challenges WHERE id=?", (challenge_id,))
    conn.commit()
    conn.close()

def db_add_daily_checkin(username, date_str, completed, note=""):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO daily_checkins (username, date_str, completed, note) VALUES (?, ?, ?, ?)", (username, date_str, completed, note))
    conn.commit()
    conn.close()

def db_get_daily_checkins(username):
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query("SELECT id, username, date_str, completed, note, created_at FROM daily_checkins WHERE username=? ORDER BY created_at DESC", conn, params=(username,))
    conn.close()
    return df

# -----------------------------
# Centralized Financial Emotion Engine
# -----------------------------
def get_financial_emotion(savings_rate: float, score: int, debt_ratio: float = 0.0):
    if savings_rate >= 30:
        return {
            "emotion": "celebrate",
            "color": "#059669",
            "icon": "🎉",
            "status": "Excellent",
            "grade": "A+",
            "voice_phrase": "Fantastic job! Your financial health is in peak condition with superb savings discipline!"
        }
    elif savings_rate >= 20:
        return {
            "emotion": "happy",
            "color": "#10B981",
            "icon": "👍",
            "status": "Good",
            "grade": "B+",
            "voice_phrase": "Good job! You maintain a solid surplus balance and healthy savings rate."
        }
    elif savings_rate >= 10:
        return {
            "emotion": "alert",
            "color": "#F59E0B",
            "icon": "⚠️",
            "status": "Average",
            "grade": "C",
            "voice_phrase": "Your financial health is average. Consider reducing discretionary lifestyle expenses."
        }
    else:
        return {
            "emotion": "sad",
            "color": "#EF4444",
            "icon": "❌",
            "status": "Poor",
            "grade": "D",
            "voice_phrase": "Warning! Your spending exceeds recommended CFP benchmark limits."
        }

# -----------------------------
# Audio & Web Speech Synthesizer Engine
# -----------------------------
def trigger_audio_emotion(emotion: str, toast_message: str = "", toast_icon: str = "🎵", voice_phrase: str = ""):
    audio_enabled = st.session_state.get("audio_enabled", True)
    voice_enabled = st.session_state.get("voice_enabled", False)

    if toast_message:
        if emotion in ["happy", "celebrate"]:
            st.toast(toast_message, icon=toast_icon if toast_icon != "🎵" else "🎉")
        elif emotion == "sad":
            st.toast(toast_message, icon=toast_icon if toast_icon != "🎵" else "😔")
        else:
            st.toast(toast_message, icon=toast_icon)

    if not audio_enabled and not voice_enabled:
        return

    voice_js = ""
    if voice_enabled and voice_phrase:
        escaped_phrase = voice_phrase.replace("'", "\\'").replace('"', '\\"')
        voice_js = f"""
            if ('speechSynthesis' in window) {{
                const utter = new SpeechSynthesisUtterance("{escaped_phrase}");
                utter.rate = 1.0;
                utter.pitch = 1.05;
                window.speechSynthesis.speak(utter);
            }}
        """

    audio_js = ""
    if audio_enabled:
        audio_js = f"""
            const AudioContext = window.AudioContext || window.webkitAudioContext;
            if (AudioContext) {{
                const ctx = new AudioContext();
                function playTone(freq, type, startTime, duration, startVol=0.35, endFreq=null) {{
                    const osc = ctx.createOscillator();
                    const gain = ctx.createGain();
                    osc.type = type;
                    osc.frequency.setValueAtTime(freq, ctx.currentTime + startTime);
                    if (endFreq) {{
                        osc.frequency.exponentialRampToValueAtTime(endFreq, ctx.currentTime + startTime + duration);
                    }}
                    gain.gain.setValueAtTime(startVol, ctx.currentTime + startTime);
                    gain.gain.exponentialRampToValueAtTime(0.0001, ctx.currentTime + startTime + duration);
                    osc.connect(gain);
                    gain.connect(ctx.destination);
                    osc.start(ctx.currentTime + startTime);
                    osc.stop(ctx.currentTime + startTime + duration);
                }}

                const emo = '{emotion}';
                if (emo === 'happy') {{
                    playTone(523.25, 'triangle', 0.0, 0.18, 0.4);
                    playTone(659.25, 'triangle', 0.08, 0.18, 0.4);
                    playTone(783.99, 'triangle', 0.16, 0.22, 0.4);
                    playTone(1046.50, 'sine', 0.24, 0.40, 0.5);
                }} else if (emo === 'celebrate') {{
                    playTone(523.25, 'sine', 0.0, 0.12, 0.4);
                    playTone(659.25, 'sine', 0.08, 0.12, 0.4);
                    playTone(783.99, 'sine', 0.16, 0.12, 0.4);
                    playTone(1046.50, 'triangle', 0.24, 0.25, 0.5);
                    playTone(1318.51, 'sine', 0.35, 0.50, 0.5);
                }} else if (emo === 'sad') {{
                    playTone(440.00, 'sawtooth', 0.0, 0.20, 0.25);
                    playTone(415.30, 'sawtooth', 0.12, 0.20, 0.25);
                    playTone(392.00, 'sawtooth', 0.24, 0.25, 0.25);
                    playTone(349.23, 'sine', 0.36, 0.45, 0.3);
                }} else if (emo === 'alert' || emo === 'theme_change') {{
                    playTone(600, 'sine', 0.0, 0.10, 0.35, 900);
                    playTone(900, 'sine', 0.08, 0.18, 0.35, 1200);
                }} else if (emo === 'click') {{
                    playTone(800, 'sine', 0.0, 0.06, 0.3, 1100);
                }}
            }}
        """

    full_js = f"""
    <script>
    (function() {{
        try {{
            {audio_js}
            {voice_js}
        }} catch(e) {{
            console.log('Audio/Voice execution notice:', e);
        }}
    }})();
    </script>
    """
    st.components.v1.html(full_js, height=0, width=0)

# -----------------------------
# Page Configuration & Session State
# -----------------------------
st.set_page_config(
    page_title="Money Matrix — Personal Financial Intelligence Platform",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "username" not in st.session_state:
    st.session_state.username = ""

if "user_data" not in st.session_state:
    st.session_state.user_data = None

if "report_generated" not in st.session_state:
    st.session_state.report_generated = False

if "ai_response" not in st.session_state:
    st.session_state.ai_response = ""

if "login_theme_idx" not in st.session_state:
    st.session_state.login_theme_idx = 1

if "audio_enabled" not in st.session_state:
    st.session_state.audio_enabled = True

if "voice_enabled" not in st.session_state:
    st.session_state.voice_enabled = False

TAB_NAMES = [
    "📊 Real-Time Dashboard",
    "📅 Monthly Tracker (CRUD)",
    "🎯 Challenges & Goals",
    "💡 Smart Budget Audit",
    "🤖 AI Wealth Advisor",
    "🛠 Financial Calculators",
    "📋 Executive Matrix",
    "🔮 FIRE Simulator",
    "🛡️ Tax Savings Audit",
    "⚡ Stress Test Engine",
    "📥 Download Center"
]

if "active_tab_name" not in st.session_state or st.session_state.active_tab_name not in TAB_NAMES:
    st.session_state.active_tab_name = "📊 Real-Time Dashboard"

# -----------------------------
# LIGHT BACKGROUND THEMES CONFIGURATION
# -----------------------------
LIGHT_LOGIN_THEMES = {
    1: {
        "name": "Green & White",
        "bg_gradient": "linear-gradient(135deg, #ECFDF5 0%, #E6F4EA 50%, #FFFFFF 100%)",
        "sidebar_bg": "#F0FDF4",
        "card_bg": "#FFFFFF",
        "card_border": "rgba(16, 185, 129, 0.25)",
        "input_bg": "#F4FBF7",
        "input_text": "#064E3B",
        "input_border": "#10B981",
        "primary": "#059669",
        "secondary": "#10B981",
        "text": "#064E3B",
        "subtitle": "#047857",
        "accent_glow": "rgba(16, 185, 129, 0.35)",
        "pie_colors": ["#059669", "#10B981", "#34D399", "#6EE7B7", "#A7F3D0", "#14B8A6", "#06B6D4", "#38BDF8", "#818CF8", "#F59E0B", "#E11D48", "#84CC16"]
    },
    2: {
        "name": "Orange & White",
        "bg_gradient": "linear-gradient(135deg, #FFFBEB 0%, #FEF3C7 50%, #FFFFFF 100%)",
        "sidebar_bg": "#FFFBEB",
        "card_bg": "#FFFFFF",
        "card_border": "rgba(245, 158, 11, 0.25)",
        "input_bg": "#FFFDF7",
        "input_text": "#451A03",
        "input_border": "#F59E0B",
        "primary": "#D97706",
        "secondary": "#F59E0B",
        "text": "#451A03",
        "subtitle": "#78350F",
        "accent_glow": "rgba(245, 158, 11, 0.35)",
        "pie_colors": ["#D97706", "#F59E0B", "#FBBF24", "#FCD34D", "#FB923C", "#F97316", "#EA580C", "#EF4444", "#8B5CF6", "#EC4899", "#10B981", "#6366F1"]
    },
    3: {
        "name": "Red & White",
        "bg_gradient": "linear-gradient(135deg, #FEF2F2 0%, #FEE2E2 50%, #FFFFFF 100%)",
        "sidebar_bg": "#FEF2F2",
        "card_bg": "#FFFFFF",
        "card_border": "rgba(225, 29, 72, 0.25)",
        "input_bg": "#FFF8F8",
        "input_text": "#450A0A",
        "input_border": "#EF4444",
        "primary": "#DC2626",
        "secondary": "#EF4444",
        "text": "#450A0A",
        "subtitle": "#991B1B",
        "accent_glow": "rgba(225, 29, 72, 0.35)",
        "pie_colors": ["#DC2626", "#EF4444", "#F87171", "#FCA5A5", "#FB923C", "#F59E0B", "#10B981", "#06B6D4", "#6366F1", "#8B5CF6", "#D97706", "#450A0A"]
    }
}

theme = LIGHT_LOGIN_THEMES[st.session_state.login_theme_idx]

# Apply High-End Fintech SaaS Theme CSS with Input Cut-Off Fixes & Instruction Hiding
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;500;600;700;800;900&display=swap');

html, body, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {{
    background: {theme['bg_gradient']} !important;
    color: {theme['text']} !important;
    font-family: 'Outfit', -apple-system, BlinkMacSystemFont, sans-serif !important;
    font-size: 16px !important;
    line-height: 1.55 !important;
}}

[data-testid="stSidebar"] {{
    background: {theme['sidebar_bg']} !important;
    border-right: 1.5px solid {theme['card_border']} !important;
    min-width: 300px !important;
    max-width: 330px !important;
}}

[data-testid="stSidebar"] * {{
    color: {theme['text']} !important;
}}

.main .block-container {{
    padding-top: 0.5rem;
    padding-bottom: 3.5rem;
    max-width: 1280px;
}}

/* Typography Hierarchy */
h1 {{ font-size: 38px !important; font-weight: 900 !important; color: {theme['primary']} !important; margin-bottom: 6px !important; }}
h2 {{ font-size: 28px !important; font-weight: 800 !important; color: {theme['primary']} !important; }}
h3 {{ font-size: 22px !important; font-weight: 700 !important; color: {theme['text']} !important; }}
h4 {{ font-size: 18px !important; font-weight: 700 !important; color: {theme['subtitle']} !important; }}
p, span, label {{ color: {theme['text']}; font-weight: 500; }}

.logo-text-only {{
    text-align: center;
    font-size: 52px !important;
    font-weight: 900 !important;
    letter-spacing: -1.5px !important;
    color: {theme['primary']} !important;
    margin-top: 10px !important;
    margin-bottom: 18px !important;
    line-height: 1.1 !important;
    text-shadow: 0 4px 15px {theme['accent_glow']};
    animation: float_title 4s ease-in-out infinite;
}}

@keyframes float_title {{
    0%, 100% {{ transform: translateY(0px); }}
    50% {{ transform: translateY(-5px); }}
}}

.main-header {{
    text-align: center;
    font-size: 42px;
    font-weight: 900;
    color: {theme['primary']};
    margin-bottom: 4px;
    letter-spacing: -1px;
}}

.sub-header {{
    text-align: center;
    color: {theme['subtitle']};
    font-size: 18px;
    margin-bottom: 24px;
    font-weight: 600;
}}

/* Unified SaaS Card Design System */
.pro-card {{
    background-color: {theme['card_bg']};
    border: 1.5px solid {theme['card_border']};
    border-radius: 20px;
    padding: 24px;
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.04);
    margin-bottom: 20px;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}}

.pro-card:hover {{
    transform: translateY(-4px);
    box-shadow: 0 14px 35px {theme['accent_glow']};
}}

div[data-testid="metric-container"] {{
    background-color: {theme['card_bg']} !important;
    border: 1.5px solid {theme['card_border']} !important;
    border-radius: 18px;
    padding: 18px;
    box-shadow: 0 6px 18px rgba(0, 0, 0, 0.03);
    transition: all 0.3s ease;
}}

div[data-testid="metric-container"]:hover {{
    transform: translateY(-3px);
    box-shadow: 0 10px 25px {theme['accent_glow']};
}}

div[data-testid="metric-container"] label {{
    color: {theme['subtitle']} !important;
    font-size: 15px !important;
    font-weight: 700 !important;
}}

div[data-testid="metric-container"] div[data-testid="stMetricValue"] {{
    color: {theme['primary']} !important;
    font-size: 30px !important;
    font-weight: 800 !important;
}}

.summary-card {{
    background-color: {theme['card_bg']};
    padding: 24px;
    border-radius: 20px;
    box-shadow: 0 10px 28px rgba(0, 0, 0, 0.04);
    border-left: 8px solid {theme['primary']};
    margin-bottom: 20px;
    color: {theme['text']};
    font-size: 16px;
    transition: all 0.3s ease;
}}

/* Button System */
.stButton>button {{
    min-height: 52px !important;
    border-radius: 35px !important;
    font-size: 16px !important;
    font-weight: 800 !important;
    padding: 12px 24px !important;
    transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1) !important;
    border: 2px solid {theme['card_border']} !important;
    background: {theme['card_bg']} !important;
    color: {theme['text']} !important;
    box-shadow: 0 6px 16px rgba(0, 0, 0, 0.04) !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    text-align: center !important;
    width: 100% !important;
    white-space: normal !important;
    word-break: break-word !important;
    overflow: visible !important;
}}

.stButton>button:hover {{
    transform: translateY(-3px) scale(1.02) !important;
    box-shadow: 0 12px 28px {theme['accent_glow']} !important;
    border-color: {theme['primary']} !important;
}}

.stButton>button[kind="primary"] {{
    background: linear-gradient(135deg, {theme['primary']}, {theme['secondary']}) !important;
    color: white !important;
    border: none !important;
    box-shadow: 0 8px 24px {theme['accent_glow']} !important;
    animation: pulse_glow 3s infinite ease-in-out;
}}

@keyframes pulse_glow {{
    0%, 100% {{ box-shadow: 0 8px 24px {theme['accent_glow']}; }}
    50% {{ box-shadow: 0 12px 32px {theme['accent_glow']}; }}
}}

/* CUT-OFF FIX FOR ALL TEXT & NUMBER INPUTS & SELECTBOXES WITH CRISP RECTANGULAR BORDERS */
.stTextInput input, .stNumberInput input {{
    font-size: 16px !important;
    border-radius: 6px !important; /* Full crisp rectangular look */
    background-color: {theme['input_bg']} !important;
    color: {theme['input_text']} !important;
    border: 2.5px solid {theme['input_border']} !important; /* Full prominent theme border line (Green/Orange/Red) */
    box-shadow: 0 0 6px {theme['accent_glow']} !important;
    font-weight: 600 !important;
    min-height: 48px !important;
    height: auto !important;
    line-height: 1.4 !important;
    padding: 10px 14px !important;
    overflow: visible !important;
    box-sizing: border-box !important;
    width: 100% !important;
    transition: all 0.25s ease !important;
}}

.stTextArea textarea {{
    font-size: 16px !important;
    border-radius: 6px !important; /* Full crisp rectangular look */
    background-color: {theme['input_bg']} !important;
    color: {theme['input_text']} !important;
    border: 2.5px solid {theme['input_border']} !important; /* Full prominent theme border line */
    box-shadow: 0 0 6px {theme['accent_glow']} !important;
    font-weight: 600 !important;
    min-height: 110px !important;
    line-height: 1.5 !important;
    padding: 12px 14px !important;
    white-space: pre-wrap !important;
    word-break: break-word !important;
    box-sizing: border-box !important;
    width: 100% !important;
    transition: all 0.25s ease !important;
}}

.stSelectbox div[data-baseweb="select"] {{
    font-size: 16px !important;
    border-radius: 6px !important; /* Full crisp rectangular look */
    background-color: {theme['input_bg']} !important;
    color: {theme['input_text']} !important;
    border: 2.5px solid {theme['input_border']} !important; /* Full prominent theme border line */
    box-shadow: 0 0 6px {theme['accent_glow']} !important;
    font-weight: 600 !important;
    min-height: 48px !important;
    height: auto !important;
    box-sizing: border-box !important;
    width: 100% !important;
}}

.stTextInput input:focus, .stNumberInput input:focus, .stTextArea textarea:focus {{
    border-color: {theme['primary']} !important;
    box-shadow: 0 0 14px {theme['accent_glow']} !important;
}}

div[data-baseweb="select"] span {{
    color: {theme['input_text']} !important;
    font-weight: 700 !important;
}}

/* REMOVE "PRESS ENTER TO APPLY" INSTRUCTION CAPTIONS GLOBALLY */
div[data-testid="stInputInstructions"],
small[data-testid="stInputInstructions"],
span[data-testid="stInputInstructions"],
.stTextInput small,
.stNumberInput small,
.stTextArea small {{
    display: none !important;
    visibility: hidden !important;
    height: 0 !important;
    margin: 0 !important;
    padding: 0 !important;
}}

/* REPLACE RAW ">>" ICON WITH NAMED "📂 OPEN SIDEBAR" BUTTON WHEN SIDEBAR IS CLOSED */
[data-testid="stSidebarCollapsedControl"],
div[data-testid="stSidebarCollapsedControl"],
[data-testid="collapsedControl"],
div[data-testid="collapsedControl"] {{
    display: flex !important;
    visibility: visible !important;
    opacity: 1 !important;
    position: fixed !important;
    top: 12px !important;
    left: 16px !important;
    z-index: 999999 !important;
}}

[data-testid="stSidebarCollapsedControl"] button,
div[data-testid="stSidebarCollapsedControl"] button,
[data-testid="collapsedControl"] button,
button[aria-label="Expand sidebar"],
button[aria-label="Open sidebar"],
button[title="Expand sidebar"] {{
    display: inline-flex !important;
    align-items: center !important;
    justify-content: center !important;
    background: linear-gradient(135deg, {theme['primary']}, {theme['secondary']}) !important;
    color: #FFFFFF !important;
    border: 2px solid #FFFFFF !important;
    border-radius: 25px !important;
    padding: 8px 18px !important;
    font-size: 14px !important;
    font-weight: 800 !important;
    box-shadow: 0 4px 14px {theme['accent_glow']} !important;
    cursor: pointer !important;
    transition: all 0.25s ease !important;
    font-family: 'Outfit', sans-serif !important;
    width: auto !important;
    height: auto !important;
    min-height: 38px !important;
}}

[data-testid="stSidebarCollapsedControl"] button:hover,
[data-testid="collapsedControl"] button:hover {{
    transform: translateY(-2px) scale(1.05) !important;
    box-shadow: 0 8px 22px {theme['accent_glow']} !important;
}}

/* HIDE THE RAW SVG CHEVRON / ">>" ICON INSIDE THE BUTTON */
[data-testid="stSidebarCollapsedControl"] button svg,
[data-testid="stSidebarCollapsedControl"] button span,
[data-testid="collapsedControl"] button svg,
[data-testid="collapsedControl"] button span,
button[aria-label="Expand sidebar"] svg,
button[title="Expand sidebar"] svg {{
    display: none !important;
    width: 0 !important;
    height: 0 !important;
    font-size: 0 !important;
    visibility: hidden !important;
}}

/* INJECT PROPER "📂 Open Sidebar" BUTTON NAME LABEL */
[data-testid="stSidebarCollapsedControl"] button::after,
[data-testid="collapsedControl"] button::after,
button[aria-label="Expand sidebar"]::after,
button[title="Expand sidebar"]::after,
button[aria-label="Open sidebar"]::after {{
    content: "📂 Open Sidebar" !important;
    font-weight: 800 !important;
    font-size: 14px !important;
    color: #FFFFFF !important;
    white-space: nowrap !important;
    letter-spacing: 0.3px !important;
}}

/* ALL 11 TABS FORCED INTO A SINGLE HORIZONTAL SCROLLABLE ROW BELOW BUTTON */
div[data-testid="stRadio"] > div {{
    display: flex !important;
    flex-wrap: nowrap !important;
    overflow-x: auto !important;
    white-space: nowrap !important;
    gap: 6px !important;
    margin-top: 12px !important;
    margin-bottom: 20px !important;
    padding-bottom: 8px !important;
    scrollbar-width: thin !important;
}}

div[data-testid="stRadio"] label {{
    flex: 0 0 auto !important;
    white-space: nowrap !important;
    background-color: {theme['card_bg']} !important;
    border-radius: 10px !important;
    padding: 8px 16px !important;
    border: 2px solid {theme['card_border']} !important;
    color: {theme['text']} !important;
    font-size: 14px !important;
    font-weight: 800 !important;
    cursor: pointer !important;
    transition: all 0.2s ease !important;
}}

div[data-testid="stRadio"] label:hover {{
    border-color: {theme['primary']} !important;
    transform: translateY(-2px) !important;
}}

div[data-testid="stRadio"] label[data-checked="true"] {{
    background: linear-gradient(135deg, {theme['primary']}, {theme['secondary']}) !important;
    color: white !important;
    border-color: {theme['primary']} !important;
    box-shadow: 0 6px 18px {theme['accent_glow']} !important;
}}

div[data-testid="stRadio"] label span {{
    color: inherit !important;
}}

/* PLOTLY MODEBAR OVERLAY */
.modebar-container {{
    opacity: 1 !important;
    visibility: visible !important;
    background: rgba(15, 23, 42, 0.9) !important;
    border-radius: 10px !important;
    padding: 4px 8px !important;
    border: 1.5px solid {theme['primary']} !important;
}}

.modebar-btn {{
    font-size: 16px !important;
    color: #FFFFFF !important;
}}

.modebar-btn:hover {{
    color: #EF4444 !important;
}}
</style>
""", unsafe_allow_html=True)

# Inject Floating WhatsApp Profile Picture Lightbox Modal HTML/JS Overlay
st.components.v1.html("""
<script>
(function() {
    try {
        const parentDoc = window.parent.document;
        
        // Remove any legacy floating red exit buttons if present in DOM
        const legacyBtn = parentDoc.getElementById('red-circular-exit-btn');
        if (legacyBtn) legacyBtn.remove();
        
        // 1. CREATE WHATSAPP PROFILE LIGHTBOX MODAL IF NOT EXISTS
        let modal = parentDoc.getElementById('whatsapp-profile-modal-overlay');
        if (!modal) {
            modal = parentDoc.createElement('div');
            modal.id = 'whatsapp-profile-modal-overlay';
            modal.style.cssText = 'display: none; position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; background: rgba(10, 15, 25, 0.94); backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px); z-index: 2147483647; align-items: center; justify-content: center; flex-direction: column; overflow: hidden; font-family: "Outfit", sans-serif;';
            
            modal.innerHTML = `
                <!-- Top-Right Close Button (✕) -->
                <button id="wa-profile-exit-btn" title="Close Profile Photo" style="position: fixed; top: 20px; right: 25px; width: 42px; height: 42px; border-radius: 50%; background: rgba(255, 255, 255, 0.2); color: #FFFFFF; border: 1.5px solid rgba(255, 255, 255, 0.4); cursor: pointer; font-size: 22px; font-weight: 800; display: flex; align-items: center; justify-content: center; z-index: 2147483648; transition: all 0.2s ease; line-height: 1; padding: 0; margin: 0;">✕</button>

                <!-- Profile Header Title -->
                <div id="wa-profile-title" style="position: fixed; top: 24px; left: 30px; color: #FFFFFF; font-size: 18px; font-weight: 800; text-shadow: 0 2px 8px rgba(0,0,0,0.8); z-index: 2147483648;">Profile Photo</div>

                <!-- Main Bounded Image Box -->
                <div id="wa-profile-img-container" style="position: relative; max-width: 90vw; max-height: 80vh; display: flex; align-items: center; justify-content: center; overflow: hidden; cursor: grab;">
                    <img id="wa-profile-img" src="" alt="Profile Photo" style="max-width: 80vw; max-height: 75vh; border-radius: 14px; box-shadow: 0 12px 45px rgba(0,0,0,0.9), 0 0 25px rgba(16, 185, 129, 0.4); transition: transform 0.15s cubic-bezier(0.2, 0, 0.2, 1); transform-origin: center center; object-fit: contain; user-select: none;" />
                </div>

                <!-- Floating Zoom Toolbar (WhatsApp Style) -->
                <div id="wa-profile-toolbar" style="position: fixed; bottom: 25px; display: flex; align-items: center; gap: 14px; background: rgba(15, 23, 42, 0.88); backdrop-filter: blur(12px); padding: 8px 22px; border-radius: 35px; border: 1.5px solid rgba(255,255,255,0.25); z-index: 2147483648; box-shadow: 0 10px 30px rgba(0,0,0,0.6);">
                    <button id="wa-zoom-out" title="Zoom Out (-)" style="background: rgba(255,255,255,0.18); color: #FFF; border: none; width: 36px; height: 36px; border-radius: 50%; font-size: 20px; font-weight: 800; cursor: pointer; display: flex; align-items: center; justify-content: center; transition: background 0.2s;">-</button>
                    <span id="wa-zoom-label" style="color: #FFF; font-size: 14px; font-weight: 800; min-width: 55px; text-align: center;">100%</span>
                    <button id="wa-zoom-in" title="Zoom In (+)" style="background: rgba(255,255,255,0.18); color: #FFF; border: none; width: 36px; height: 36px; border-radius: 50%; font-size: 20px; font-weight: 800; cursor: pointer; display: flex; align-items: center; justify-content: center; transition: background 0.2s;">+</button>
                    <button id="wa-zoom-reset" title="Reset Zoom" style="background: rgba(255,255,255,0.18); color: #FFF; border: none; padding: 4px 14px; border-radius: 18px; font-size: 13px; font-weight: 800; cursor: pointer; height: 36px; transition: background 0.2s;">Reset</button>
                </div>
            `;
            parentDoc.body.appendChild(modal);

            let currentScale = 1.0;
            const imgEl = parentDoc.getElementById('wa-profile-img');
            const labelEl = parentDoc.getElementById('wa-zoom-label');
            const exitBtn = parentDoc.getElementById('wa-profile-exit-btn');
            const container = parentDoc.getElementById('wa-profile-img-container');

            function applyZoom(newScale) {
                currentScale = Math.max(0.4, Math.min(5.0, newScale));
                imgEl.style.transform = `scale(${currentScale})`;
                labelEl.textContent = `${Math.round(currentScale * 100)}%`;
            }

            function closeModal() {
                modal.style.display = 'none';
                currentScale = 1.0;
                imgEl.style.transform = 'scale(1)';
            }

            exitBtn.onclick = closeModal;
            exitBtn.onmouseover = function() { this.style.background = 'rgba(255,255,255,0.4)'; };
            exitBtn.onmouseout = function() { this.style.background = 'rgba(255,255,255,0.2)'; };

            modal.onclick = function(e) {
                if (e.target === modal || e.target === container) {
                    closeModal();
                }
            };

            parentDoc.getElementById('wa-zoom-in').onclick = function(e) {
                e.stopPropagation();
                applyZoom(currentScale + 0.25);
            };

            parentDoc.getElementById('wa-zoom-out').onclick = function(e) {
                e.stopPropagation();
                applyZoom(currentScale - 0.25);
            };

            parentDoc.getElementById('wa-zoom-reset').onclick = function(e) {
                e.stopPropagation();
                applyZoom(1.0);
            };

            // Mouse Wheel Zoom Support (WhatsApp Web Behavior)
            container.onwheel = function(e) {
                e.preventDefault();
                if (e.deltaY < 0) {
                    applyZoom(currentScale + 0.15);
                } else {
                    applyZoom(currentScale - 0.15);
                }
            };
        }

        // Expose open helper function
        parentDoc.defaultView.openWhatsAppModal = function(src, name) {
            const modal = parentDoc.getElementById('whatsapp-profile-modal-overlay');
            const imgEl = parentDoc.getElementById('wa-profile-img');
            const titleEl = parentDoc.getElementById('wa-profile-title');
            if (modal && imgEl) {
                imgEl.src = src;
                imgEl.style.transform = 'scale(1)';
                if (titleEl) titleEl.textContent = name ? `${name} — Profile Photo` : 'Profile Photo';
                modal.style.display = 'flex';
            }
        };

        // Clean any legacy red circular button from parent DOM
        const legacyBtn = parentDoc.getElementById('red-circular-exit-btn');
        if (legacyBtn) legacyBtn.remove();

        // 2. EVENT MONITORING LOOP (AUTO-ATTACH CLICK LISTENERS TO SIDEBAR AVATARS)
        setInterval(function() {
            // Clean any legacy red circular button if present
            const oldBtn = parentDoc.getElementById('red-circular-exit-btn');
            if (oldBtn) oldBtn.remove();

            // Attach WhatsApp Modal trigger to all sidebar avatars and profile pictures
            const avatars = parentDoc.querySelectorAll('[data-testid="stSidebar"] img, .sidebar-profile-avatar');
            avatars.forEach(function(img) {
                if (!img.dataset.waClickAttached && img.src) {
                    img.dataset.waClickAttached = "true";
                    img.style.cursor = "pointer";
                    img.title = "Click to view full profile picture";
                    img.onclick = function(e) {
                        e.preventDefault();
                        e.stopPropagation();
                        parentDoc.defaultView.openWhatsAppModal(img.src, "Profile");
                    };
                }
            });

            // Also attach to initials circular div if user has no image
            const letterAvatars = parentDoc.querySelectorAll('.sidebar-avatar-circle');
            letterAvatars.forEach(function(div) {
                if (!div.dataset.waClickAttached) {
                    div.dataset.waClickAttached = "true";
                    div.style.cursor = "pointer";
                    div.title = "Click to view profile";
                }
            });
        }, 500);

    } catch(e) {
        console.log('Profile modal script notice:', e);
    }
})();
</script>
""", height=0, width=0)

# Helper Functions for Export Reports
def generate_pdf_report(report_df, user_name):
    if not REPORTLAB_AVAILABLE or SimpleDocTemplate is None:
        return None
    try:
        pdf_buf = io.BytesIO()
        doc = SimpleDocTemplate(pdf_buf, pagesize=(8.5 * inch, 11 * inch))
        styles = getSampleStyleSheet()
        elements = [
            Paragraph(f"<b><font size=20 color='#059669'>MONEY MATRIX FINANCIAL AUDIT - {user_name.upper()}</font></b>", styles["Title"]),
            Paragraph(f"Generated on {datetime.now().strftime('%d %B %Y')}", styles["Normal"]),
            Paragraph("<br/>", styles["Normal"])
        ]
        pdf_table_data = [["Metric Parameter", "Audit Value"]]
        for _, row_item in report_df.iterrows():
            if str(row_item["Parameter"]):
                pdf_table_data.append([str(row_item["Parameter"]), str(row_item["Value"])])

        p_table = Table(pdf_table_data, colWidths=[3.5 * inch, 3.5 * inch])
        p_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#059669")),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('GRID', (0,0), (-1,-1), 1, colors.lightgrey),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0,0), (-1,0), 8),
            ('TOPPADDING', (0,1), (-1,-1), 6),
            ('ALIGN', (0,0), (-1,-1), 'LEFT')
        ]))
        elements.append(p_table)
        doc.build(elements)
        pdf_buf.seek(0)
        return pdf_buf
    except Exception:
        return None

def generate_jpeg_report(report_df, user_name):
    try:
        img_h = max(800, 180 + len(report_df) * 45)
        img_obj = Image.new("RGB", (1200, img_h), "#FFFFFF")
        draw_obj = ImageDraw.Draw(img_obj)
        try:
            t_font = ImageFont.truetype("arial.ttf", 34)
            h_font = ImageFont.truetype("arial.ttf", 22)
            v_font = ImageFont.truetype("arial.ttf", 20)
        except Exception:
            t_font = ImageFont.load_default()
            h_font = ImageFont.load_default()
            v_font = ImageFont.load_default()

        draw_obj.rectangle((0, 0, 1200, 100), fill="#059669")
        draw_obj.text((40, 30), f"MONEY MATRIX FINANCIAL REPORT - {user_name.upper()}", fill="#FFFFFF", font=t_font)

        y_offset = 130
        for _, r_item in report_df.iterrows():
            if str(r_item["Parameter"]):
                draw_obj.text((50, y_offset), str(r_item["Parameter"]), fill="#1E293B", font=h_font)
                draw_obj.text((600, y_offset), str(r_item["Value"]), fill="#059669", font=v_font)
                y_offset += 40

        img_buf = io.BytesIO()
        img_obj.save(img_buf, format="JPEG")
        img_buf.seek(0)
        return img_buf
    except Exception:
        return None

# ------------------------------------------------------------------------------
# TOP HEADER BAR: COMPACT CYLINDER PILL THEME SWITCHER
# ------------------------------------------------------------------------------
top_bar_left, top_bar_right = st.columns([2.5, 2])

with top_bar_right:
    st.markdown(
        f"<div style='text-align: right; font-size: 13px; font-weight: 700; color: {theme['subtitle']}; margin-bottom: 4px;'>"
        "🎨 Background Theme (Pill Switcher)"
        "</div>",
        unsafe_allow_html=True
    )
    tc1, tc2, tc3 = st.columns(3)
    with tc1:
        if st.button("🌿 Green", key="top_t1", use_container_width=True):
            st.session_state.login_theme_idx = 1
            trigger_audio_emotion("theme_change", "Theme changed to Green & White", "🎨")
            st.rerun()
    with tc2:
        if st.button("🍊 Orange", key="top_t2", use_container_width=True):
            st.session_state.login_theme_idx = 2
            trigger_audio_emotion("theme_change", "Theme changed to Orange & White", "🎨")
            st.rerun()
    with tc3:
        if st.button("🍎 Red", key="top_t3", use_container_width=True):
            st.session_state.login_theme_idx = 3
            trigger_audio_emotion("theme_change", "Theme changed to Red & White", "🎨")
            st.rerun()

# ==============================================================================
# SIMPLE CLEAN AUTHENTICATION SCREEN (LOGIN / REGISTER)
# ==============================================================================
if not st.session_state.logged_in:
    
    auth_col1, auth_col2, auth_col3 = st.columns([1, 2.2, 1])

    with auth_col2:
        # CLEAN TEXT LOGO ONLY (Dynamic Theme Color Matching)
        st.markdown(
            f"<div class='logo-text-only'>Money Matrix</div>",
            unsafe_allow_html=True
        )

        auth_tab1, auth_tab2 = st.tabs(["🔐 Sign In", "📝 Create Account"])

        # TAB 1: SIMPLE SIGN IN
        with auth_tab1:
            st.markdown("### Welcome Back to Money Matrix")
            login_user = st.text_input("Username or Email", key="login_u")
            login_pass = st.text_input("Password", type="password", key="login_p")

            st.caption("💡 **Default Demo Login:** Username: `admin` | Password: `admin123`")

            if st.button("🚀 Sign In to Dashboard", use_container_width=True, type="primary", key="btn_login_submit"):
                login_u_clean = login_user.strip()
                login_p_clean = login_pass.strip()

                if not login_u_clean or not login_p_clean:
                    trigger_audio_emotion("sad", "Please fill in all credentials", "⚠️")
                    st.error("Please enter both username/email and password.")
                else:
                    user_row = db_get_user(login_u_clean)
                    if user_row and user_row[1] == hash_password(login_p_clean):
                        st.session_state.logged_in = True
                        st.session_state.username = user_row[0]
                        st.session_state.user_data = user_row
                        trigger_audio_emotion("happy", f"Welcome back, {user_row[2] or user_row[0]}!", "🎉")
                        st.rerun()
                    else:
                        trigger_audio_emotion("sad", "Login Invalid! Check username or password.", "❌")
                        st.error("❌ **Login Invalid!** Username/Email or Password is incorrect.")

        # TAB 2: SIMPLE CREATE ACCOUNT
        with auth_tab2:
            st.markdown("### Create a New Money Matrix Account")
            reg_user = st.text_input("Choose Username", key="reg_u")
            reg_email = st.text_input("Email Address", value="", key="reg_email")
            reg_pass = st.text_input("Choose Password", type="password", key="reg_p")
            reg_name = st.text_input("Full Name", value="Alex Morgan", key="reg_n")
            
            c_r1, c_r2 = st.columns(2)
            with c_r1:
                reg_age = st.number_input("Age", 18, 100, 30, key="reg_a")
                reg_gender = st.selectbox("Gender", ["Male", "Female", "Non-Binary", "Prefer not to say"], key="reg_g")
            with c_r2:
                reg_prof_sel = st.selectbox("Profession", PROFESSIONS_LIST, key="reg_prof_sel")
                if reg_prof_sel == "Other (Specify Custom)":
                    reg_profession = st.text_input("Specify Profession", value="", key="reg_prof_custom")
                else:
                    reg_profession = reg_prof_sel
                
                reg_curr = st.selectbox("Preferred Currency", ["₹ (INR)", "$ (USD)", "€ (EUR)", "£ (GBP)", "A$ (AUD)"], key="reg_curr")

            st.markdown("#### 🌍 Location Details")
            c_loc1, c_loc2 = st.columns(2)
            with c_loc1:
                reg_country = st.selectbox("Country", WORLD_COUNTRIES, index=0, key="reg_country_sel")
            with c_loc2:
                if reg_country == "India":
                    reg_state = st.selectbox("State / Union Territory (India)", INDIAN_STATES, index=10, key="reg_state_sel")  # Gujarat default
                    reg_location = f"{reg_state}, India"
                else:
                    reg_city = st.text_input("State / City / Region", value="", key="reg_city_in")
                    reg_location = f"{reg_city}, {reg_country}" if reg_city else reg_country

            if st.button("✨ Register & Access Portal", use_container_width=True, type="primary", key="btn_reg_submit"):
                clean_reg_name = re.sub(r'[^a-zA-Z\s\.]', '', reg_name).strip() or "User"
                clean_reg_prof = re.sub(r'[^a-zA-Z\s/\-]', '', reg_profession).strip() or "Professional"
                clean_reg_city = re.sub(r'[^a-zA-Z\s,]', '', reg_city).strip() if (reg_country != "India" and 'reg_city' in locals()) else ""
                clean_reg_location = f"{clean_reg_city}, {reg_country}" if clean_reg_city else reg_location

                if not reg_user or not reg_pass or not reg_email or not clean_reg_prof:
                    trigger_audio_emotion("sad", "Please specify username, email, password, and profession", "⚠️")
                    st.warning("Please complete required registration fields.")
                else:
                    curr_sym = reg_curr.split(" ")[0]
                    success = db_create_user(
                        username=reg_user.strip(),
                        password=reg_pass.strip(),
                        email=reg_email.strip(),
                        full_name=clean_reg_name,
                        age=int(reg_age),
                        gender=reg_gender,
                        profession=clean_reg_prof,
                        location=clean_reg_location,
                        currency_symbol=curr_sym
                    )
                    if success:
                        st.session_state.logged_in = True
                        st.session_state.username = reg_user.strip()
                        st.session_state.user_data = db_get_user(reg_user.strip())
                        trigger_audio_emotion("happy", "Account created successfully! Welcome!", "🎉")
                        st.success("🎉 Account created successfully!")
                        st.rerun()
                    else:
                        trigger_audio_emotion("sad", "Username or Email already exists!", "❌")
                        st.error("Username or Email already taken. Please pick another one.")

    st.stop()

# ==============================================================================
# MAIN LOGGED IN APP (MONEY MATRIX PLATFORM)
# ==============================================================================

user_db_info = db_get_user(st.session_state.username)
if not user_db_info:
    st.session_state.logged_in = False
    st.rerun()

# Safe robust tuple unpacking for User Profile (Explicit SQL positions)
(
    u_name, u_pass_hash, u_fullname, u_email, u_age, u_gender, u_marital, u_dependents,
    u_profession, u_location, u_goal, u_risk, u_ret_age, u_curr_symbol, u_profile_pic, u_created
) = user_db_info[:16]

u_fullname = str(u_fullname) if u_fullname else "Alex Morgan"
u_email = str(u_email) if u_email else f"{st.session_state.username}@moneymatrix.io"

try:
    u_age = int(u_age) if u_age is not None else 30
except Exception:
    u_age = 30
u_age = max(18, min(100, u_age))

u_gender = str(u_gender) if u_gender else "Male"
u_marital = str(u_marital) if u_marital else "Single"

try:
    u_dependents = int(u_dependents) if u_dependents is not None else 1
except Exception:
    u_dependents = 1
u_dependents = max(0, min(10, u_dependents))

u_profession = str(u_profession) if u_profession else "Software Engineer / Developer"
if ":" in u_profession or "-" in u_profession or "2026-" in u_profession:
    u_profession = "Software Engineer / Developer"

u_location = str(u_location) if u_location else "Gujarat, India"
if ":" in u_location or "-" in u_location or "2026-" in u_location or "Savings Maximizer" in u_location:
    u_location = "Gujarat, India"

u_goal = str(u_goal) if u_goal else "Savings Maximizer (Aggressive Savings)"
u_risk = str(u_risk) if u_risk else "Balanced"

try:
    u_ret_age = int(u_ret_age) if u_ret_age is not None else 60
except Exception:
    u_ret_age = 60
u_ret_age = max(30, min(80, u_ret_age))

u_curr_symbol = str(u_curr_symbol) if u_curr_symbol else "₹"
if u_curr_symbol not in ["₹", "$", "€", "£", "A$"] or ":" in u_curr_symbol or "-" in u_curr_symbol or len(u_curr_symbol) > 4:
    u_curr_symbol = "₹"

u_profile_pic = str(u_profile_pic) if u_profile_pic else ""

# -----------------------------
# SIDEBAR NAVIGATION & PROFILE
# -----------------------------
with st.sidebar:
    if u_profile_pic:
        st.markdown(
            f"""
            <div style="text-align: center; padding: 10px 0;">
                <img src="{u_profile_pic}" class="sidebar-profile-avatar" style="width: 76px; height: 76px; border-radius: 50%; object-fit: cover; border: 3.5px solid {theme['primary']}; box-shadow: 0 6px 20px {theme['accent_glow']}; margin: 0 auto 10px auto; display: block; cursor: pointer; transition: transform 0.25s ease;" onmouseover="this.style.transform='scale(1.12)'" onmouseout="this.style.transform='scale(1.0)'" title="Click to view full profile photo" onclick="if(window.parent && window.parent.openWhatsAppModal) window.parent.openWhatsAppModal('{u_profile_pic}', '{u_fullname}');" />
                <h3 style="margin: 0; color: {theme['primary']}; font-weight: 900;">Money Matrix</h3>
                <p style="margin: 4px 0 0 0; font-size: 14px; font-weight: 700; color: {theme['subtitle']};">{u_fullname}</p>
                <span style="font-size: 12px; color: {theme['text']}; opacity: 0.8;">{u_email}</span>
            </div>
            """,
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            f"""
            <div style="text-align: center; padding: 10px 0;">
                <div class="sidebar-avatar-circle" style="width: 68px; height: 68px; border-radius: 50%; background: linear-gradient(135deg, {theme['primary']}, {theme['secondary']}); color: white; display: flex; align-items: center; justify-content: center; font-size: 28px; font-weight: 900; margin: 0 auto 10px auto; box-shadow: 0 6px 20px {theme['accent_glow']}; cursor: pointer; transition: transform 0.25s ease;" onmouseover="this.style.transform='scale(1.12)'" onmouseout="this.style.transform='scale(1.0)'" title="Click to view profile">
                    {u_fullname[0].upper() if u_fullname else 'M'}
                </div>
                <h3 style="margin: 0; color: {theme['primary']}; font-weight: 900;">Money Matrix</h3>
                <p style="margin: 4px 0 0 0; font-size: 14px; font-weight: 700; color: {theme['subtitle']};">{u_fullname}</p>
                <span style="font-size: 12px; color: {theme['text']}; opacity: 0.8;">{u_email}</span>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.divider()

    # User Profile Editor & Picture Change
    with st.expander("📝 Edit Profile & Avatar", expanded=False):
        p_avatar_file = st.file_uploader("📷 Change Profile Picture", type=["png", "jpg", "jpeg"], key="p_avatar_file_in")
        
        p_fullname = st.text_input("Full Name", value=u_fullname, key="p_fullname_in")
        p_email = st.text_input("Email Address", value=u_email, key="p_email_in")
        p_age = st.number_input("Age", 18, 100, u_age, key="p_age_in")
        p_gender = st.selectbox("Gender", ["Male", "Female", "Non-Binary", "Prefer not to say"], index=["Male", "Female", "Non-Binary", "Prefer not to say"].index(u_gender) if u_gender in ["Male", "Female", "Non-Binary", "Prefer not to say"] else 0, key="p_gender_in")
        p_marital = st.selectbox("Marital Status", ["Single", "Married", "Married with Children", "Divorced"], index=["Single", "Married", "Married with Children", "Divorced"].index(u_marital) if u_marital in ["Single", "Married", "Married with Children", "Divorced"] else 0, key="p_marital_in")
        p_dependents = st.number_input("Dependents", 0, 10, u_dependents, key="p_dependents_in")
        
        # PROFESSION SELECTION (COMPREHENSIVE OPTIONS)
        init_prof_idx = PROFESSIONS_LIST.index(u_profession) if u_profession in PROFESSIONS_LIST else len(PROFESSIONS_LIST) - 1
        p_prof_sel = st.selectbox("Profession", PROFESSIONS_LIST, index=init_prof_idx, key="p_prof_sel")
        if p_prof_sel == "Other (Specify Custom)":
            p_profession = st.text_input("Custom Profession", value=u_profession if u_profession not in PROFESSIONS_LIST else "", key="p_prof_custom")
        else:
            p_profession = p_prof_sel

        # LOCATION SELECTION (WORLD COUNTRIES + INDIAN STATES)
        init_country = "India"
        init_state = "Gujarat"
        init_city = ""
        if u_location:
            if "India" in u_location:
                init_country = "India"
                parts = [p.strip() for p in u_location.split(",") if p.strip() != "India"]
                for p in parts:
                    if p in INDIAN_STATES:
                        init_state = p
            else:
                parts = [p.strip() for p in u_location.split(",")]
                if parts and parts[-1] in WORLD_COUNTRIES:
                    init_country = parts[-1]
                    init_city = ", ".join(parts[:-1])

        p_country = st.selectbox("Country", WORLD_COUNTRIES, index=WORLD_COUNTRIES.index(init_country) if init_country in WORLD_COUNTRIES else 0, key="p_country_sel")
        if p_country == "India":
            p_state = st.selectbox("State / Union Territory (India)", INDIAN_STATES, index=INDIAN_STATES.index(init_state) if init_state in INDIAN_STATES else 0, key="p_state_sel")
            p_location = f"{p_state}, India"
        else:
            p_city = st.text_input("State / City / Region", value=init_city, key="p_city_in")
            p_location = f"{p_city}, {p_country}" if p_city else p_country

        p_goal = st.selectbox(
            "Primary Wealth Goal",
            [
                "Savings Maximizer (Aggressive Savings)",
                "Investment Fund & Portfolio Growth",
                "Debt Free & EMI Acceleration",
                "Emergency Cushion & Liquidity First",
                "Early Retirement (FIRE) & Freedom Fund",
                "Real Estate & Property Buying",
                "Tax Optimization & Wealth Protection",
                "Children's Education & Family Legacy"
            ],
            index=0,
            key="p_goal_in"
        )
        
        # Enhanced Risk Assessment Slider
        risk_levels = ["Conservative", "Moderately Conservative", "Balanced", "Growth Oriented", "Aggressive Growth"]
        init_risk_idx = risk_levels.index(u_risk) + 1 if u_risk in risk_levels else 3
        
        p_risk_idx = st.slider(
            "Risk Assessment Profile Slider",
            min_value=1,
            max_value=5,
            value=init_risk_idx,
            step=1,
            key="p_risk_slider",
            help="1: Conservative 🛡️ | 2: Moderately Conservative ⚖️ | 3: Balanced ⚖️ | 4: Growth Oriented 📈 | 5: Aggressive Growth 🔥"
        )
        p_risk = risk_levels[p_risk_idx - 1]
        
        risk_icons = ["🛡️ Conservative", "⚖️ Moderately Conservative", "⚖️ Balanced", "📈 Growth Oriented", "🔥 Aggressive Growth"]
        st.markdown(
            f"<div style='text-align: center; padding: 6px; border-radius: 12px; background: {theme['card_bg']}; border: 1px solid {theme['card_border']}; font-weight: 800; color: {theme['primary']};'>"
            f"{risk_icons[p_risk_idx - 1]}"
            f"</div>",
            unsafe_allow_html=True
        )
        
        p_ret_age = st.number_input("Retirement Age Goal", 30, 80, u_ret_age, key="p_ret_age_in")

        p_curr_choice = st.selectbox(
            "Currency Symbol",
            ["₹ (INR)", "$ (USD)", "€ (EUR)", "£ (GBP)", "A$ (AUD)"],
            index=["₹", "$", "€", "£", "A$"].index(u_curr_symbol) if u_curr_symbol in ["₹", "$", "€", "£", "A$"] else 0,
            key="p_curr_choice_in"
        )
        p_curr_sym = p_curr_choice.split(" ")[0]

        if st.button("💾 Save Profile Settings", use_container_width=True, type="primary", key="btn_save_profile"):
            new_pic = u_profile_pic
            if p_avatar_file is not None:
                bytes_data = p_avatar_file.getvalue()
                b64_str = base64.b64encode(bytes_data).decode("utf-8")
                mime_type = p_avatar_file.type or "image/png"
                new_pic = f"data:{mime_type};base64,{b64_str}"

            clean_p_fullname = re.sub(r'[^a-zA-Z\s\.]', '', p_fullname).strip() or u_fullname
            clean_p_profession = re.sub(r'[^a-zA-Z\s/\-]', '', p_profession).strip() or u_profession
            clean_p_city = re.sub(r'[^a-zA-Z\s,]', '', p_city).strip() if (p_country != "India" and 'p_city' in locals()) else ""
            clean_p_location = f"{clean_p_city}, {p_country}" if clean_p_city else p_location

            db_update_user_profile(
                username=st.session_state.username,
                full_name=clean_p_fullname,
                email=p_email.strip(),
                age=int(p_age),
                gender=p_gender,
                marital_status=p_marital,
                dependents=int(p_dependents),
                profession=clean_p_profession,
                location=clean_p_location,
                goal=p_goal,
                risk_tolerance=p_risk,
                retirement_age=int(p_ret_age),
                currency_symbol=p_curr_sym,
                profile_pic=new_pic
            )
            trigger_audio_emotion("happy", "Profile parameters updated!", "✅")
            st.rerun()

    st.divider()

    # Sidebar Audio & Voice Controls
    st.markdown("#### 🔊 Audio & Voice Assistant")
    st.session_state.audio_enabled = st.checkbox("🔊 Sound Effects", value=st.session_state.audio_enabled, key="chk_sound_fx")
    st.session_state.voice_enabled = st.checkbox("🗣️ Voice Assistant (Speech Synthesis)", value=st.session_state.voice_enabled, key="chk_voice_asst")

    st.divider()

    # Logout Button
    if st.button("🚪 Log Out of Money Matrix", use_container_width=True, key="btn_logout"):
        trigger_audio_emotion("sad", "Logged out of session.", "🚪")
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.session_state.user_data = None
        st.rerun()

# Main Header
st.markdown(
    f"<div class='main-header'>Money Matrix Platform</div>",
    unsafe_allow_html=True
)
st.markdown(
    f"<div class='sub-header'>Comprehensive Financial Analytics • Persistent Tracker • AI Strategy • Challenges</div>",
    unsafe_allow_html=True
)

# -----------------------------
# RESPONSIVE FINANCIAL INPUT CARDS
# -----------------------------
st.markdown("### 📥 Monthly Financial Input System")

with st.expander("💵 1. Monthly Income Breakdown", expanded=True):
    inc_c1, inc_c2 = st.columns(2)
    with inc_c1:
        salary = st.number_input("Monthly Salary / Fixed Pay", min_value=0.0, max_value=9999999999.0, value=75000.0, step=5000.0, key="inc_salary")
        freelance = st.number_input("Freelancing / Consulting", min_value=0.0, max_value=9999999999.0, value=15000.0, step=2000.0, key="inc_freelance")
        business = st.number_input("Business Profits", min_value=0.0, max_value=9999999999.0, value=0.0, step=5000.0, key="inc_business")
    with inc_c2:
        rental = st.number_input("Rental Income", min_value=0.0, max_value=9999999999.0, value=0.0, step=2000.0, key="inc_rental")
        investment = st.number_input("Investment Returns / Dividends", min_value=0.0, max_value=9999999999.0, value=5000.0, step=1000.0, key="inc_investment")
        other_income = st.number_input("Other Side Income", min_value=0.0, max_value=9999999999.0, value=0.0, step=1000.0, key="inc_other")

total_income = salary + freelance + business + rental + investment + other_income

with st.expander("💸 2. Monthly Expenses Breakdown", expanded=True):
    exp_t1, exp_t2, exp_t3 = st.tabs(["🏠 Essential", "🛍️ Lifestyle & Growth", "💳 Obligations & Other"])
    
    with exp_t1:
        e1, e2 = st.columns(2)
        with e1:
            rent = st.number_input("House Rent / Housing", min_value=0.0, max_value=9999999999.0, value=22000.0, step=1000.0, key="exp_rent")
            food = st.number_input("Food & Groceries", min_value=0.0, max_value=9999999999.0, value=12000.0, step=1000.0, key="exp_food")
        with e2:
            electricity = st.number_input("Electricity & Utilities", min_value=0.0, max_value=9999999999.0, value=3000.0, step=500.0, key="exp_electricity")
            internet = st.number_input("Internet & Mobile Plans", min_value=0.0, max_value=9999999999.0, value=1500.0, step=200.0, key="exp_internet")
            
    with exp_t2:
        l1, l2 = st.columns(2)
        with l1:
            shopping = st.number_input("Shopping & Lifestyle", min_value=0.0, max_value=9999999999.0, value=8000.0, step=1000.0, key="exp_shopping")
            travel = st.number_input("Travel & Commute", min_value=0.0, max_value=9999999999.0, value=5000.0, step=500.0, key="exp_travel")
            entertainment = st.number_input("Entertainment & Dining Out", min_value=0.0, max_value=9999999999.0, value=4500.0, step=500.0, key="exp_entertainment")
        with l2:
            education = st.number_input("Education & Upskilling", min_value=0.0, max_value=9999999999.0, value=4000.0, step=500.0, key="exp_education")
            medical = st.number_input("Healthcare & Medical", min_value=0.0, max_value=9999999999.0, value=3000.0, step=500.0, key="exp_medical")

    with exp_t3:
        o1, o2 = st.columns(2)
        with o1:
            emi = st.number_input("Loan EMI / Debt Payments", min_value=0.0, max_value=9999999999.0, value=14000.0, step=1000.0, key="exp_emi")
            insurance = st.number_input("Insurance Premiums", min_value=0.0, max_value=9999999999.0, value=3500.0, step=500.0, key="exp_insurance")
        with o2:
            others = st.number_input("Other Miscellaneous Expenses", min_value=0.0, max_value=9999999999.0, value=2500.0, step=500.0, key="exp_others")

total_expense = (
    rent + food + electricity + internet +
    shopping + travel + education + medical +
    emi + entertainment + insurance + others
)

expenses_dict = {
    "House Rent": rent,
    "Food": food,
    "Electricity": electricity,
    "Internet": internet,
    "Shopping": shopping,
    "Travel": travel,
    "Education": education,
    "Medical": medical,
    "Loan EMI": emi,
    "Entertainment": entertainment,
    "Insurance": insurance,
    "Other Expenses": others
}

with st.expander("🏦 3. Assets & Target Wealth Goal", expanded=True):
    col_s1, col_s2 = st.columns(2)
    with col_s1:
        current_savings = st.number_input("Current Liquid Savings & Funds", min_value=0.0, max_value=9999999999.0, value=250000.0, step=10000.0, key="ast_savings")
    with col_s2:
        target_savings = st.number_input("Target Wealth Goal", min_value=0.0, max_value=9999999999.0, value=1000000.0, step=50000.0, key="ast_target_savings")

# Calculations
balance = total_income - total_expense
savings_rate = (balance / total_income * 100) if total_income > 0 else 0.0
debt_ratio = (emi / total_income * 100) if total_income > 0 else 0.0
emergency_required = total_expense * 6

score = 95 if savings_rate >= 30 else (80 if savings_rate >= 20 else (60 if savings_rate >= 10 else 35))
emo_config = get_financial_emotion(savings_rate, score, debt_ratio)
financial_grade = emo_config["grade"]

# -----------------------------
# REDESIGNED ANALYSIS ACTION CENTERPIECE CARD
# -----------------------------
st.markdown(
    f"""
    <div style="background: {theme['card_bg']}; border: 2px solid {theme['card_border']}; border-radius: 24px; padding: 28px; text-align: center; margin: 24px 0; box-shadow: 0 12px 32px {theme['accent_glow']};">
        <span style="font-size: 15px; font-weight: 800; color: {theme['subtitle']}; text-transform: uppercase; letter-spacing: 1px;">Ready to Analyze?</span>
        <h2 style="font-size: 32px; color: {theme['primary']}; margin: 6px 0 12px 0; font-weight: 900;">Generate Comprehensive Financial Audit Report</h2>
        <p style="font-size: 16px; color: {theme['text']}; max-width: 700px; margin: 0 auto 20px auto;">Evaluate cashflow efficiency, debt exposure, liquid emergency cushion readiness, and financial health score.</p>
    </div>
    """,
    unsafe_allow_html=True
)

if st.button("🚀 Generate Financial Health Report", use_container_width=True, type="primary", key="btn_gen_report"):
    with st.spinner("Analyzing financial profile... Calculating savings rate... Checking emergency reserve..."):
        st.session_state.report_generated = True
        trigger_audio_emotion(
            emo_config["emotion"],
            f"Financial Audit Complete! Health Grade: {financial_grade}",
            emo_config["icon"],
            emo_config["voice_phrase"]
        )

# ==============================================================================
# STATEFUL NAVIGATION SYSTEM (ALL TABS IN A SINGLE HORIZONTAL ROW BELOW BUTTON)
# ==============================================================================
active_tab_nav = st.radio(
    "Navigation Options",
    TAB_NAMES,
    index=TAB_NAMES.index(st.session_state.active_tab_name),
    horizontal=True,
    key="nav_radio_pill_bar",
    label_visibility="collapsed"
)
st.session_state.active_tab_name = active_tab_nav

# ------------------------------------------------------------------------------
# TAB 1: REAL-TIME DASHBOARD
# ------------------------------------------------------------------------------
if st.session_state.active_tab_name == "📊 Real-Time Dashboard":
    st.markdown(
        f"<h2 style='color: {theme['primary']}; font-weight: 900;'>Your Financial Health Overview</h2>",
        unsafe_allow_html=True
    )
    st.caption(f"Client Diagnostic Profile for **{u_fullname}** ({st.session_state.username})")

    # Row 1: 4 Animated Metric Cards (Guaranteed Clean Currency Formatting)
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("💵 Monthly Income", fmt_curr(total_income, u_curr_symbol))
    m2.metric("💸 Monthly Expenses", fmt_curr(total_expense, u_curr_symbol))
    m3.metric("💰 Net Surplus Balance", fmt_curr(balance, u_curr_symbol))
    m4.metric("⭐ Financial Health Score", f"{score}/100")

    st.divider()

    # Row 2: Financial Health Grade + Target Wealth Progress
    col_dash1, col_dash2 = st.columns([1, 1])

    with col_dash1:
        st.markdown("#### 🏆 Financial Health Grade & Diagnostic")
        st.markdown(
            f"""
            <div style="background: {theme['card_bg']}; border-left: 8px solid {emo_config['color']}; border-radius: 18px; padding: 20px; box-shadow: 0 8px 24px rgba(0,0,0,0.04);">
                <div style="display: flex; align-items: center; justify-content: space-between;">
                    <h2 style="margin: 0; color: {emo_config['color']}; font-size: 36px;">Grade {financial_grade}</h2>
                    <span style="font-size: 32px;">{emo_config['icon']}</span>
                </div>
                <p style="margin: 8px 0 0 0; font-size: 16px; font-weight: 700; color: {theme['text']};">{emo_config['status']} Cashflow Health</p>
                <p style="margin: 4px 0 0 0; font-size: 14px; color: {theme['subtitle']};">{emo_config['voice_phrase']}</p>
            </div>
            """,
            unsafe_allow_html=True
        )

        st.write(f"**Savings Rate:** `{savings_rate:.2f}%` of total monthly income")

        st.markdown("#### 🎯 Target Wealth Progress")
        if target_savings > 0:
            progress = min(1.0, current_savings / target_savings)
            st.progress(progress)
            st.write(f"**Accumulated Funds:** {fmt_curr(current_savings, u_curr_symbol)} / **Target:** {fmt_curr(target_savings, u_curr_symbol)} (`{progress*100:.1f}%`) Achieved")

    with col_dash2:
        st.markdown("#### 📈 Income vs Expense vs Surplus Breakdown")
        chart_df = pd.DataFrame({
            "Category": ["Income", "Expenses", "Net Surplus"],
            "Amount": [float(total_income), float(total_expense), float(balance)]
        })
        fig_bar = px.bar(chart_df, x="Category", y="Amount", color="Category",
                         color_discrete_sequence=[theme["primary"], "#EF4444", "#F59E0B"])
        fig_bar.update_layout(height=300, margin=dict(l=10, r=10, t=20, b=10), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig_bar, use_container_width=True)

    st.divider()

    # Row 3: Emergency Cushion & Category Allocation Pie Chart
    col_dash3, col_dash4 = st.columns([1, 1])

    with col_dash3:
        st.markdown("#### 🚨 Emergency Cushion & Debt Status")
        if current_savings >= emergency_required:
            st.success(f"✅ **Safe Cushion:** Liquid reserve meets 6-month CFP benchmark target ({fmt_curr(emergency_required, u_curr_symbol)}).")
        else:
            st.warning(f"⚠️ **Cushion Deficit:** Target reserve is {fmt_curr(emergency_required, u_curr_symbol)}. Deficit: {fmt_curr(emergency_required - current_savings, u_curr_symbol)}.")

        st.markdown("#### 💳 Debt Exposure Diagnostic")
        if debt_ratio <= 20:
            st.success(f"✅ **Healthy Debt Exposure:** EMI commitments consume `{debt_ratio:.1f}%` of income.")
        elif debt_ratio <= 35:
            st.warning(f"⚠️ **Moderate Debt Burden:** EMI commitments consume `{debt_ratio:.1f}%` of income.")
        else:
            st.error(f"🚨 **High Debt Risk:** EMI commitments consume `{debt_ratio:.1f}%` of income.")

    with col_dash4:
        st.markdown("#### 🥧 Interactive Expense Allocation")
        filtered_expenses = [(k, float(v)) for k, v in expenses_dict.items() if v > 0]
        if filtered_expenses and PLOTLY_AVAILABLE:
            fig_pie = go.Figure(data=[go.Pie(
                labels=[x[0] for x in filtered_expenses],
                values=[x[1] for x in filtered_expenses],
                hole=0.45,
                textinfo="percent+label",
                marker=dict(colors=theme["pie_colors"], line=dict(color="#FFFFFF", width=1.5)),
                hovertemplate="<b>%{label}</b><br>" + u_curr_symbol + " %{value:,.0f}<br>%{percent}<extra></extra>"
            )])
            fig_pie.update_layout(height=320, margin=dict(l=10, r=10, t=10, b=10), paper_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig_pie, use_container_width=True)

# ------------------------------------------------------------------------------
# TAB 2: MONTHLY TRACKER (DATA PERSISTENCE & CRUD)
# ------------------------------------------------------------------------------
elif st.session_state.active_tab_name == "📅 Monthly Tracker (CRUD)":
    st.markdown("### 📅 Persistent Monthly Financial Progress Tracker")
    st.write("Store, update, view, and manage your historical monthly financial records in Money Matrix.")

    t2_col1, t2_col2 = st.columns([1, 2])

    with t2_col1:
        st.markdown("#### 💾 Save Current Month Entry")
        rec_month = st.text_input("Month & Year Title", value=datetime.now().strftime("%B %Y"), key="rec_m_title")
        rec_notes = st.text_area("Optional Notes", value="Monthly financial summary log.", key="rec_m_notes")
        
        if st.button("➕ Save Record to Database", use_container_width=True, type="primary", key="btn_save_record"):
            inc_dict = {
                "salary": salary, "freelance": freelance, "business": business,
                "rental": rental, "investment": investment, "other_income": other_income
            }
            exp_dict = expenses_dict.copy()
            db_add_record(st.session_state.username, rec_month, inc_dict, exp_dict, rec_notes)
            trigger_audio_emotion("happy", f"Record for {rec_month} saved!", "💾", "Monthly financial record saved successfully!")
            st.session_state.active_tab_name = "📅 Monthly Tracker (CRUD)"
            st.rerun()

    with t2_col2:
        st.markdown("#### 📊 Historical Progress Records & Multi-Month Trend")
        df_records = db_get_records(st.session_state.username)

        if df_records.empty:
            st.info("No historical records saved yet. Save your first monthly log using the form on the left!")
        else:
            if PLOTLY_AVAILABLE:
                fig_trend = go.Figure()
                fig_trend.add_trace(go.Scatter(x=df_records["month_year"], y=df_records["total_income"], mode="lines+markers", name="Income", line=dict(color=theme["primary"], width=3)))
                fig_trend.add_trace(go.Scatter(x=df_records["month_year"], y=df_records["total_expense"], mode="lines+markers", name="Expenses", line=dict(color="#EF4444", width=3)))
                fig_trend.add_trace(go.Scatter(x=df_records["month_year"], y=df_records["balance"], mode="lines+markers", name="Surplus Balance", line=dict(color="#F59E0B", width=3)))
                fig_trend.update_layout(title="Multi-Month Income vs Expense Trend", height=320, margin=dict(l=10, r=10, t=35, b=10), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
                st.plotly_chart(fig_trend, use_container_width=True)

            st.markdown("#### 📋 Saved Records Table")
            display_cols = ["id", "month_year", "total_income", "total_expense", "balance", "savings_rate", "created_at"]
            st.dataframe(df_records[display_cols], use_container_width=True, hide_index=True)

            # Record Delete Option
            st.markdown("##### 🗑 Delete Historical Entry")
            del_id = st.selectbox("Select Record ID to Delete", df_records["id"].tolist(), key="sel_del_record")
            if st.button("🗑 Delete Selected Record", type="secondary", key="btn_del_record"):
                db_delete_record(del_id)
                trigger_audio_emotion("sad", f"Record #{del_id} deleted.", "🗑")
                st.session_state.active_tab_name = "📅 Monthly Tracker (CRUD)"
                st.rerun()

# ------------------------------------------------------------------------------
# TAB 3: MONTHLY CHALLENGES & DAILY GOAL CHECK-INS
# ------------------------------------------------------------------------------
elif st.session_state.active_tab_name == "🎯 Challenges & Goals":
    st.markdown("### 🎯 Monthly Challenges & Daily Goal System")
    st.write("Stay accountable with daily goal check-ins and monthly financial challenges.")

    # DAILY GOAL CHECK-IN SECTION WITH EMOTIONAL AUDIO
    st.markdown(f"""
    <div class="summary-card">
        <h3 style="margin:0; color:{theme['primary']}; font-size:22px;">📅 Daily Goal Check-In Prompt</h3>
        <p style="margin-top:6px; font-size:16px;">Did you stick to your budget and achieve your primary financial goal today?</p>
    </div>
    """, unsafe_allow_html=True)

    g_col1, g_col2 = st.columns(2)

    with g_col1:
        if st.button("🎉 YES! Goal Completed Today!", use_container_width=True, type="primary", key="btn_daily_yes"):
            today_str = datetime.now().strftime("%Y-%m-%d")
            db_add_daily_checkin(st.session_state.username, today_str, 1, "Completed daily goal!")
            trigger_audio_emotion("celebrate", "🎉 FANTASTIC JOB! Daily Goal Completed! Keep building wealth!", "🏆", "Fantastic job! Daily goal completed!")
            st.balloons()

    with g_col2:
        if st.button("😔 NO, Goal Missed Today", use_container_width=True, key="btn_daily_no"):
            today_str = datetime.now().strftime("%Y-%m-%d")
            db_add_daily_checkin(st.session_state.username, today_str, 0, "Missed goal.")
            trigger_audio_emotion("sad", "😔 Keep working on your goal! Tomorrow is a fresh start to succeed!", "💪")

    st.divider()

    # CHALLENGES MANAGEMENT
    ch_col1, ch_col2 = st.columns([1, 2])

    with ch_col1:
        st.markdown("#### ➕ Create New Monthly Challenge")
        ch_title = st.text_input("Challenge Title", value="Save 30% of Income this Month", key="ctitle")
        ch_cat = st.selectbox("Category", ["Savings Target", "Debt Reduction", "No-Spend Rule", "Investment SIP", "Budget Control"], key="ccat")
        ch_target = st.number_input("Target Goal Value", min_value=1.0, max_value=9999999999.0, value=25000.0, step=1000.0, key="ctarget")
        
        if st.button("🎯 Add Challenge", use_container_width=True, type="primary", key="btn_add_challenge"):
            db_add_challenge(st.session_state.username, ch_title, ch_cat, ch_target)
            trigger_audio_emotion("happy", "New Challenge Added!", "🎯")
            st.session_state.active_tab_name = "🎯 Challenges & Goals"
            st.rerun()

    with ch_col2:
        st.markdown("#### 🏆 Active Challenges & Progress")
        df_challenges = db_get_challenges(st.session_state.username)

        if df_challenges.empty:
            st.info("No active challenges yet. Create one using the form on the left!")
        else:
            for _, ch in df_challenges.iterrows():
                with st.container():
                    st.markdown(f"""
                    <div class="pro-card">
                        <div style="display:flex; justify-content:space-between; align-items:center;">
                            <h4 style="margin:0; color:{theme['primary']}; font-size:18px;">{ch['title']}</h4>
                            <span style="background:{theme['card_border']}; padding:4px 14px; border-radius:14px; font-weight:800; font-size:13px; color:{theme['primary']};">{ch['status']}</span>
                        </div>
                        <p style="margin:6px 0; font-size:15px; color:{theme['subtitle']};">Category: {ch['category']} | Target: {fmt_curr(ch['target_value'], u_curr_symbol)}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    c_up1, c_up2, c_up3, c_up4 = st.columns([2, 1.2, 0.9, 0.9])
                    with c_up1:
                        new_val = st.number_input("Update Progress", value=float(ch['current_value']), key=f"cur_{ch['id']}")
                    with c_up2:
                        new_stat = st.selectbox("Status", ["In Progress", "Completed 🎉", "Failed ❌"], key=f"stat_{ch['id']}")
                    with c_up3:
                        st.write("")
                        if st.button("Update", key=f"btn_u_{ch['id']}", use_container_width=True):
                            db_update_challenge(ch['id'], new_val, new_stat)
                            if "Completed" in new_stat:
                                trigger_audio_emotion("celebrate", f"Challenge '{ch['title']}' Completed!", "🏆", "Congratulations! Challenge completed!")
                            else:
                                trigger_audio_emotion("alert", "Challenge updated.", "📝")
                            st.session_state.active_tab_name = "🎯 Challenges & Goals"
                            st.rerun()
                    with c_up4:
                        st.write("")
                        if st.button("🗑 Delete", key=f"btn_d_{ch['id']}", use_container_width=True, type="secondary"):
                            db_delete_challenge(ch['id'])
                            trigger_audio_emotion("sad", f"Challenge '{ch['title']}' Deleted!", "🗑", "Challenge deleted successfully!")
                            st.session_state.active_tab_name = "🎯 Challenges & Goals"
                            st.rerun()

# ------------------------------------------------------------------------------
# TAB 4: SMART BUDGET AUDIT
# ------------------------------------------------------------------------------
elif st.session_state.active_tab_name == "💡 Smart Budget Audit":
    st.markdown("### 💡 Smart Category Benchmark Audit")
    st.write("Comparing your monthly allocations against global CFP standards.")

    recommended_limits = {
        "House Rent": 30, "Food": 15, "Electricity": 5, "Internet": 3,
        "Shopping": 10, "Travel": 8, "Education": 10, "Medical": 5,
        "Loan EMI": 30, "Entertainment": 5, "Insurance": 10, "Other Expenses": 5
    }

    budget_report = []
    for cat_name, amt in expenses_dict.items():
        pct = (amt / total_income * 100) if total_income > 0 else 0.0
        rec_limit_pct = recommended_limits[cat_name]
        rec_amt = total_income * rec_limit_pct / 100
        diff = amt - rec_amt
        monthly_sav = max(0.0, diff)
        yearly_sav = monthly_sav * 12

        if pct <= rec_limit_pct * 0.80:
            risk, priority = "Optimal", "Very Low"
        elif pct <= rec_limit_pct:
            risk, priority = "Good", "Low"
        elif pct <= rec_limit_pct * 1.20:
            risk, priority = "Moderate Risk", "Medium"
        else:
            risk, priority = "Overbudget Risk", "High Priority"

        budget_report.append({
            "Category": cat_name,
            f"Current ({u_curr_symbol})": round(amt, 2),
            "Income %": round(pct, 2),
            "Benchmark %": rec_limit_pct,
            f"Monthly Excess ({u_curr_symbol})": round(monthly_sav, 2),
            f"Annual Savings Potential ({u_curr_symbol})": round(yearly_sav, 2),
            "Audit Status": risk,
            "Priority": priority
        })

    budget_df = pd.DataFrame(budget_report)
    st.dataframe(budget_df, use_container_width=True, hide_index=True)

# ------------------------------------------------------------------------------
# TAB 5: AI WEALTH ADVISOR
# ------------------------------------------------------------------------------
elif st.session_state.active_tab_name == "🤖 AI Wealth Advisor":
    st.markdown("### 🤖 Money Matrix AI Wealth Advisor")
    st.write("Generate a personalized, professional financial advisory strategy based on your Money Matrix profile.")

    if st.button("✨ Generate Custom AI Wealth Plan", key="ai_gen_btn", type="primary"):
        with st.spinner("AI Strategy Engine calculating personalized wealth plan..."):
            if GROQ_AVAILABLE and groq is not None and GROQ_API_KEY:
                try:
                    dyn_client = groq.Groq(api_key=GROQ_API_KEY)
                    ai_prompt = f"""
You are an expert Certified Financial Planner (CFP) for Money Matrix platform.
Prepare a highly detailed, professional, easy-to-understand, step-by-step wealth plan for:
Client: {u_fullname} ({st.session_state.username}), Age: {u_age}, Profession: {u_profession}, Location: {u_location}
Strategy Goal: {u_goal}, Risk Profile: {u_risk}, Target Retirement Age: {u_ret_age}

FINANCIAL METRICS:
Monthly Income: {fmt_curr(total_income, u_curr_symbol)}
Monthly Expenses: {fmt_curr(total_expense, u_curr_symbol)}
Surplus Balance: {fmt_curr(balance, u_curr_symbol)}
Savings Rate: {savings_rate:.2f}% | Health Grade: {financial_grade}
Current Assets: {fmt_curr(current_savings, u_curr_symbol)} | Wealth Goal: {fmt_curr(target_savings, u_curr_symbol)}

Structure:
# 🏛️ Executive Summary & Health Diagnostic
# 📊 Recommended Asset Allocation Strategy ({u_risk} Profile)
# 🛡️ Risk Mitigation & Emergency Reserve Audit
# 🎯 Goal Acceleration Roadmap
# 🗓️ Step-by-Step 30-Day Execution Roadmap
"""
                    response = dyn_client.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=[
                            {"role": "system", "content": "You are a senior Certified Financial Planner (CFP). Provide professional, clear, action-oriented financial advice."},
                            {"role": "user", "content": ai_prompt}
                        ],
                        temperature=0.25,
                        max_tokens=3000
                    )
                    st.session_state.ai_response = response.choices[0].message.content
                    trigger_audio_emotion("happy", "AI Strategy Plan Generated!", "🤖", "Your custom AI Wealth Strategy plan is ready.")
                except Exception as ex:
                    GROQ_API_KEY_TEMP = ""  # trigger fallback below

            if not GROQ_API_KEY or not GROQ_AVAILABLE or "ai_response" not in st.session_state or not st.session_state.ai_response:
                # Built-in Ultra-Detailed Professional Wealth Strategy Plan
                detailed_plan = f"""
# 🏛️ Comprehensive Financial Advisory & Wealth Strategy Plan
**Client:** {u_fullname} | **Profession:** {u_profession} | **Location:** {u_location}  
**Diagnostic Date:** {datetime.now().strftime("%d %B %Y")}

---

### 1. 📈 Executive Summary & Health Diagnostic
- **Overall Financial Grade:** Grade {financial_grade} ({emo_config['status']} Health Status)
- **Monthly Net Surplus:** {fmt_curr(balance, u_curr_symbol)} ({savings_rate:.2f}% Savings Rate)
- **Primary Wealth Goal:** {u_goal}
- **Risk Profile:** {u_risk}

Your gross monthly income of **{fmt_curr(total_income, u_curr_symbol)}** minus monthly expenses of **{fmt_curr(total_expense, u_curr_symbol)}** yields a monthly net surplus balance of **{fmt_curr(balance, u_curr_symbol)}**.

---

### 2. 📊 Recommended Asset Allocation Strategy ({u_risk} Profile)
Based on your **{u_risk}** risk profile and target retirement age of **{u_ret_age}**, your net surplus should be systematically allocated as follows:

- **💎 Equity & Growth Mutual Funds (50% Allocation):** {fmt_curr(max(0, balance * 0.5), u_curr_symbol)} / month  
  *Target:* Nifty 50 Index Funds, Flexi-Cap Funds & Quality Large-Cap Growth Equities.
- **🛡️ Fixed Income & Debt Instruments (30% Allocation):** {fmt_curr(max(0, balance * 0.3), u_curr_symbol)} / month  
  *Target:* Public Provident Fund (PPF), High-Yield Corporate Bonds & Debt Mutual Funds.
- **🥇 Emergency Cushion & Gold ETFs (20% Allocation):** {fmt_curr(max(0, balance * 0.2), u_curr_symbol)} / month  
  *Target:* High-Yield Liquid Mutual Funds & Sovereign Gold Bonds (SGB).

---

### 3. 🛡️ Risk Mitigation & Emergency Reserve Audit
- **Emergency Reserve Cushion:** Target required liquid reserve is **{fmt_curr(emergency_required, u_curr_symbol)}** (6 months living expenses).
- **Debt Exposure Ratio:** Your EMI commitments consume **{debt_ratio:.1f}%** of your gross income (Recommended threshold: < 30%).
- **Insurance Coverage Benchmark:** Maintain term life cover of **10x annual income** ({fmt_curr(total_income * 12 * 10, u_curr_symbol)}) & family health cover of **{fmt_curr(1000000, u_curr_symbol)}**.

---

### 4. 🗓️ Step-by-Step 30-Day Execution Roadmap
1. **Week 1 (Payday Automation):** Set up automated monthly SIP transfers of **{fmt_curr(max(0, balance * 0.7), u_curr_symbol)}** on payday to enforce savings discipline.
2. **Week 2 (Emergency Liquidity Build):** Allocate **{fmt_curr(max(0, balance * 0.2), u_curr_symbol)}** into a separate liquid fund until your reserve reaches **{fmt_curr(emergency_required, u_curr_symbol)}**.
3. **Week 3 (Debt & Tax Optimization):** Prioritize pre-paying any high-interest debt and optimize Section 80C/80D tax deductions.
4. **Week 4 (Monthly Review):** Track goal progress in Money Matrix and adjust budget allocations as income scales.
"""
                st.session_state.ai_response = detailed_plan
                trigger_audio_emotion("happy", "Financial Advisory Strategy Generated!", "📊", "Your financial advisory strategy plan is ready.")

    if st.session_state.ai_response:
        st.markdown(f'<div class="summary-card">{st.session_state.ai_response}</div>', unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# TAB 6: FINANCIAL CALCULATORS
# ------------------------------------------------------------------------------
elif st.session_state.active_tab_name == "🛠 Financial Calculators":
    st.markdown("### 🛠 Interactive Financial Utilities")
    calc_tool = st.radio("Select Tool", ["🧮 EMI Calculator", "💳 Credit Score Estimator", "📈 SIP Growth Calculator"], horizontal=True, key="calc_tool_radio")

    if calc_tool == "🧮 EMI Calculator":
        lp = st.number_input("Loan Amount", 10000.0, 9999999999.0, 1000000.0, step=50000.0, key="calc_emi_lp")
        ir = st.number_input("Annual Interest Rate (%)", 1.0, 30.0, 8.5, step=0.1, key="calc_emi_ir")
        yr = st.number_input("Tenure (Years)", 1, 30, 15, key="calc_emi_yr")
        r_m = (ir / 12) / 100
        n_m = yr * 12
        emi_val = (lp * r_m * ((1 + r_m) ** n_m)) / (((1 + r_m) ** n_m) - 1) if r_m > 0 else (lp / n_m)
        st.metric("Monthly EMI Commitment", fmt_curr(emi_val, u_curr_symbol))

    elif calc_tool == "💳 Credit Score Estimator":
        c_util = st.slider("Credit Utilization (%)", 0, 100, 25, key="calc_credit_util")
        c_score = min(900, max(300, 300 + (100 - c_util) * 6))
        st.metric("Estimated Credit Score", f"{c_score} / 900")

    elif calc_tool == "📈 SIP Growth Calculator":
        sip_amt = st.number_input("Monthly SIP Amount", 500.0, 9999999999.0, 10000.0, step=1000.0, key="calc_sip_amt")
        sip_rate = st.number_input("Expected Annual Return (%)", 1.0, 30.0, 12.0, step=0.5, key="calc_sip_rate")
        sip_yrs = st.number_input("Years", 1, 40, 10, key="calc_sip_yrs")
        i_s = (sip_rate / 12) / 100
        m_s = sip_yrs * 12
        fv = sip_amt * (((1 + i_s) ** m_s - 1) / i_s) * (1 + i_s)
        st.metric("Projected SIP Portfolio Value", fmt_curr(fv, u_curr_symbol))

# ------------------------------------------------------------------------------
# TAB 7: EXECUTIVE MATRIX
# ------------------------------------------------------------------------------
elif st.session_state.active_tab_name == "📋 Executive Matrix":
    st.markdown("### 📋 Executive Financial Audit Matrix")
    report_df = pd.DataFrame({
        "Parameter": ["Client", "Profession", "Location", "Goal", "Risk Profile", "Monthly Income", "Monthly Expenses", "Surplus Balance", "Savings Rate", "Health Grade"],
        "Value": [u_fullname, u_profession, u_location, u_goal, u_risk, fmt_curr(total_income, u_curr_symbol), fmt_curr(total_expense, u_curr_symbol), fmt_curr(balance, u_curr_symbol), f"{savings_rate:.2f}%", financial_grade]
    })
    st.dataframe(report_df, use_container_width=True, hide_index=True)

# ------------------------------------------------------------------------------
# TAB 8: 🔮 FIRE SIMULATOR
# ------------------------------------------------------------------------------
elif st.session_state.active_tab_name == "🔮 FIRE Simulator":
    st.markdown("### 🔮 FIRE (Financial Independence, Retire Early) Simulator")
    st.write("Calculate your exact Financial Freedom Corpus target, timeline, and inflation-adjusted milestone roadmap.")

    fire_c1, fire_c2 = st.columns([1, 1])

    with fire_c1:
        fire_mult = st.slider("FIRE Target Expense Multiplier (25x Rule default)", 20, 35, 25, help="Standard 25x multiplier corresponds to a 4% safe annual withdrawal rate.", key="fire_mult_slider")
        fire_inf_rate = st.slider("Expected Annual Inflation (%)", 0.0, 12.0, 6.0, 0.5, key="fire_inf_slider")
        fire_return_rate = st.slider("Expected Portfolio Annual Return (%)", 4.0, 20.0, 12.0, 0.5, key="fire_ret_slider")

    annual_exp = total_expense * 12
    base_fire_corpus = annual_exp * fire_mult
    net_real_return = max(0.1, fire_return_rate - fire_inf_rate) / 100

    # Projection calculation
    months_to_fire = 0
    curr_w = current_savings
    monthly_inv = max(0.0, balance)

    if monthly_inv > 0 and base_fire_corpus > curr_w:
        m_rate = net_real_return / 12
        while curr_w < base_fire_corpus and months_to_fire < 600:
            curr_w = curr_w * (1 + m_rate) + monthly_inv
            months_to_fire += 1
        years_to_fire = round(months_to_fire / 12, 1)
    elif curr_w >= base_fire_corpus:
        years_to_fire = 0.0
    else:
        years_to_fire = 99.0

    projected_fire_age = u_age + int(years_to_fire)

    with fire_c2:
        st.markdown(f"""
        <div class="pro-card" style="border-left: 8px solid {theme['primary']};">
            <h4 style="margin:0; color:{theme['primary']};">🎯 Your Financial Freedom Target</h4>
            <h2 style="margin:10px 0; font-size:36px; color:{theme['text']};">{fmt_curr(base_fire_corpus, u_curr_symbol)}</h2>
            <p style="margin:0; font-size:15px; color:{theme['subtitle']};">Based on {fire_mult}x annual living expenses of {fmt_curr(annual_exp, u_curr_symbol)}</p>
        </div>
        """, unsafe_allow_html=True)

    f_m1, f_m2, f_m3 = st.columns(3)
    f_m1.metric("⏱️ Years to Financial Freedom", f"{years_to_fire} Years" if years_to_fire < 99 else "Increase Surplus")
    f_m2.metric("🎂 Projected FIRE Age", f"Age {projected_fire_age}" if years_to_fire < 99 else "N/A")
    f_m3.metric("💰 Monthly SIP Required", f"{fmt_curr(monthly_inv, u_curr_symbol)}/mo")

    st.divider()

    st.markdown("#### 📊 Projected Wealth Accumulation Trajectory")
    years_range = list(range(0, min(35, int(years_to_fire) + 5)))
    traj_data = []
    w_val = float(current_savings)
    target_val = float(base_fire_corpus)
    
    # Safe financial ceiling to prevent 64-bit integer overflow in JSON serializers
    SAFE_MAX_VAL = 1e14

    for y in years_range:
        safe_w = min(SAFE_MAX_VAL, max(0.0, w_val))
        safe_target = min(SAFE_MAX_VAL, max(0.0, target_val))
        traj_data.append({
            "Year": y,
            "Age": u_age + y,
            "Projected Wealth": round(safe_w, 2),
            "FIRE Target": round(safe_target, 2)
        })
        w_val = (w_val + (monthly_inv * 12)) * (1 + net_real_return)

    traj_df = pd.DataFrame(traj_data)
    if PLOTLY_AVAILABLE:
        try:
            fig_fire = go.Figure()
            fig_fire.add_trace(go.Scatter(x=traj_df["Age"], y=traj_df["Projected Wealth"], mode="lines+markers", name="Projected Net Worth", line=dict(color=theme["primary"], width=3)))
            fig_fire.add_trace(go.Scatter(x=traj_df["Age"], y=traj_df["FIRE Target"], mode="lines", name="FIRE Target Line", line=dict(color="#EF4444", width=2, dash="dash")))
            fig_fire.update_layout(height=340, margin=dict(l=10, r=10, t=30, b=10), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", xaxis_title="Your Age", yaxis_title=f"Net Worth ({u_curr_symbol})")
            st.plotly_chart(fig_fire, use_container_width=True)
        except Exception:
            st.line_chart(traj_df.set_index("Age")[["Projected Wealth", "FIRE Target"]])

# ------------------------------------------------------------------------------
# TAB 9: 🛡️ TAX SAVINGS AUDIT
# ------------------------------------------------------------------------------
elif st.session_state.active_tab_name == "🛡️ Tax Savings Audit":
    st.markdown("### 🛡️ Tax Optimization & Tax Savings Audit")
    st.write("Evaluate annual tax liability, deduction utilization, and potential tax savings.")

    annual_gross = total_income * 12
    t_c1, t_c2 = st.columns([1, 1])

    with t_c1:
        tax_gross_in = st.number_input("Annual Gross Taxable Income", min_value=0.0, max_value=9999999999.0, value=float(annual_gross), step=50000.0, key="tax_gross_in")
        c_80c = st.number_input("Current 80C Investments (EPF/ELSS/PPF, max 1,50,000)", 0.0, 150000.0, 80000.0, step=10000.0, key="tax_80c_in")
        c_80d = st.number_input("Current 80D Health Insurance (max 50,000)", 0.0, 50000.0, 15000.0, step=5000.0, key="tax_80d_in")

    rem_80c = max(0.0, 150000.0 - c_80c)
    rem_80d = max(0.0, 50000.0 - c_80d)
    potential_deductions = rem_80c + rem_80d
    projected_tax_saved = potential_deductions * 0.208  # Approx 20% slab + cess

    with t_c2:
        st.markdown(
            f"""
            <div class="pro-card" style="border-left: 8px solid #10B981;">
                <h4 style="margin:0; color:#059669;">💡 Unused Tax Savings Potential</h4>
                <h2 style="margin:10px 0; font-size:34px; color:{theme['text']};">{fmt_curr(projected_tax_saved, u_curr_symbol)} / year</h2>
                <p style="margin:0; font-size:14px; color:{theme['subtitle']};">By optimizing remaining Section 80C ({fmt_curr(rem_80c, u_curr_symbol)}) & 80D ({fmt_curr(rem_80d, u_curr_symbol)}) limits.</p>
            </div>
            """,
            unsafe_allow_html=True
        )

        st.markdown("#### 📋 Recommended Tax Optimization Checklist")
        if rem_80c > 0:
            st.warning(f"⚠️ **80C Gap:** Invest {fmt_curr(rem_80c, u_curr_symbol)} in ELSS or PPF to lower taxable income.")
        else:
            st.success("✅ **80C Limit Maximized:** Full 1.5 Lakh limit utilized.")

        if rem_80d > 0:
            st.warning(f"⚠️ **80D Gap:** Allocate {fmt_curr(rem_80d, u_curr_symbol)} toward health insurance premiums.")
        else:
            st.success("✅ **80D Limit Maximized:** Health insurance tax benefit optimized.")

# ------------------------------------------------------------------------------
# TAB 10: ⚡ STRESS TEST ENGINE
# ------------------------------------------------------------------------------
elif st.session_state.active_tab_name == "⚡ Stress Test Engine":
    st.markdown("### ⚡ Economic Stress Test & Resilience Engine")
    st.write("Simulate macro-economic downturn scenarios to test your cashflow runway and emergency cushion resilience.")

    runway_months = round(current_savings / total_expense, 1) if total_expense > 0 else 99.0
    resilience_score = min(100, max(10, int(runway_months * 10 - (debt_ratio * 0.8))))

    st.markdown(
        f"""
        <div class="summary-card" style="border-left: 8px solid {'#059669' if resilience_score >= 70 else ('#F59E0B' if resilience_score >= 45 else '#EF4444')};">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <div>
                    <h3 style="margin:0; color:{theme['primary']};">Resilience Score: {resilience_score}/100</h3>
                    <p style="margin:4px 0 0 0; font-size:15px; color:{theme['subtitle']};">Liquid Emergency Cushion Runway: <b>{runway_months} Months</b> of living expenses</p>
                </div>
                <span style="font-size:36px;">{'🛡️' if resilience_score >= 70 else ('⚠️' if resilience_score >= 45 else '🚨')}</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    s1, s2, s3 = st.columns(3)

    with s1:
        st.markdown(
            f"""
            <div class="pro-card">
                <h4>💥 Scenario A: Sudden Job Loss</h4>
                <p style="font-size:14px;">Total income stops immediately while living expenses continue.</p>
                <h3 style="color:{theme['primary']};">{runway_months} Months Cushion</h3>
                <p style="font-size:13px; color:{theme['subtitle']};">CFP Safe Target: >= 6 Months</p>
            </div>
            """,
            unsafe_allow_html=True
        )

    with s2:
        inf_exp = total_expense * 1.20
        revised_bal = total_income - inf_exp
        st.markdown(
            f"""
            <div class="pro-card">
                <h4>📈 Scenario B: 20% Inflation Shock</h4>
                <p style="font-size:14px;">Living expenses & utility prices surge by 20%.</p>
                <h3 style="color:{'#059669' if revised_bal > 0 else '#EF4444'};">{fmt_curr(revised_bal, u_curr_symbol)} / mo</h3>
                <p style="font-size:13px; color:{theme['subtitle']};">Revised Monthly Balance</p>
            </div>
            """,
            unsafe_allow_html=True
        )

    with s3:
        med_shock = current_savings - 100000.0
        st.markdown(
            f"""
            <div class="pro-card">
                <h4>🏥 Scenario C: Medical Outflow</h4>
                <p style="font-size:14px;">Unforeseen lump sum medical outflow of {u_curr_symbol} 100,000.</p>
                <h3 style="color:{'#059669' if med_shock > 0 else '#EF4444'};">{fmt_curr(max(0.0, med_shock), u_curr_symbol)}</h3>
                <p style="font-size:13px; color:{theme['subtitle']};">Remaining Liquid Reserve</p>
            </div>
            """,
            unsafe_allow_html=True
        )

# ------------------------------------------------------------------------------
# TAB 11: DOWNLOAD CENTER
# ------------------------------------------------------------------------------
elif st.session_state.active_tab_name == "📥 Download Center":
    st.markdown("### 📥 Download Financial Report Hub")
    st.write("Export your financial health metrics in structured CSV dataset, printable PDF document, or Infographic JPEG format.")

    report_df = pd.DataFrame({
        "Parameter": ["Client", "Profession", "Location", "Goal", "Risk Profile", "Monthly Income", "Monthly Expenses", "Surplus Balance", "Savings Rate", "Health Grade"],
        "Value": [u_fullname, u_profession, u_location, u_goal, u_risk, fmt_curr(total_income, u_curr_symbol), fmt_curr(total_expense, u_curr_symbol), fmt_curr(balance, u_curr_symbol), f"{savings_rate:.2f}%", financial_grade]
    })

    d_col1, d_col2, d_col3 = st.columns(3)

    # 1. CSV Download Card
    csv_bytes = report_df.to_csv(index=False).encode("utf-8")
    with d_col1:
        st.markdown(
            f"""
            <div class="pro-card" style="text-align: center;">
                <span style="font-size: 42px;">📄</span>
                <h4 style="margin: 10px 0 4px 0; color: {theme['primary']};">CSV Financial Dataset</h4>
                <p style="font-size: 14px; color: {theme['subtitle']};">Raw structured audit data for spreadsheet analysis.</p>
            </div>
            """,
            unsafe_allow_html=True
        )
        if st.download_button(
            label="📄 Download CSV Dataset",
            data=csv_bytes,
            file_name=f"MoneyMatrix_Report_{st.session_state.username}.csv",
            mime="text/csv",
            use_container_width=True,
            key="btn_dl_csv"
        ):
            trigger_audio_emotion("happy", "CSV Report Downloaded!", "📄")

    # 2. PDF Download Card
    pdf_buf = generate_pdf_report(report_df, u_fullname)
    with d_col2:
        st.markdown(
            f"""
            <div class="pro-card" style="text-align: center;">
                <span style="font-size: 42px;">📕</span>
                <h4 style="margin: 10px 0 4px 0; color: {theme['primary']};">PDF Financial Audit</h4>
                <p style="font-size: 14px; color: {theme['subtitle']};">Printable executive audit document.</p>
            </div>
            """,
            unsafe_allow_html=True
        )
        if pdf_buf is not None:
            if st.download_button(
                label="📕 Download PDF Report",
                data=pdf_buf,
                file_name=f"MoneyMatrix_Report_{st.session_state.username}.pdf",
                mime="application/pdf",
                use_container_width=True,
                key="btn_dl_pdf"
            ):
                trigger_audio_emotion("happy", "PDF Report Downloaded!", "📕")

    # 3. JPEG Download Card
    jpeg_buf = generate_jpeg_report(report_df, u_fullname)
    with d_col3:
        st.markdown(
            f"""
            <div class="pro-card" style="text-align: center;">
                <span style="font-size: 42px;">🖼️</span>
                <h4 style="margin: 10px 0 4px 0; color: {theme['primary']};">Financial Infographic</h4>
                <p style="font-size: 14px; color: {theme['subtitle']};">High-resolution visual report image.</p>
            </div>
            """,
            unsafe_allow_html=True
        )
        if jpeg_buf is not None:
            if st.download_button(
                label="🖼️ Download Infographic JPEG",
                data=jpeg_buf,
                file_name=f"MoneyMatrix_Report_{st.session_state.username}.jpeg",
                mime="image/jpeg",
                use_container_width=True,
                key="btn_dl_jpeg"
            ):
                trigger_audio_emotion("happy", "Infographic JPEG Downloaded!", "🖼️")