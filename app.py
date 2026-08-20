import sqlite3
import datetime
import hashlib
import io
import urllib.parse
import streamlit as st
import pandas as pd

# ---------------------------------------------------------
# PAGE SETUP
# ---------------------------------------------------------
st.set_page_config(
    page_title="Studio Management Suite",
    page_icon="✂️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Global Enter-Key Navigation & Auto-Submit Engine
st.components.v1.html("""
<script>
(function() {
    function setupEnterNavigation() {
        const doc = window.parent.document;
        if (!doc) return;
        
        doc.removeEventListener('keydown', handleGlobalKeyDown, true);
        doc.addEventListener('keydown', handleGlobalKeyDown, true);
    }

    function handleGlobalKeyDown(e) {
        if (e.key !== 'Enter') return;
        
        const doc = window.parent.document;
        const active = doc.activeElement;
        if (!active) return;

        const printBtn = doc.querySelector('iframe')?.contentDocument?.querySelector('.print-btn') || doc.querySelector('.print-btn');
        if (printBtn && active.tagName === 'BODY') {
            printBtn.click();
            return;
        }

        const isInput = active.tagName === 'INPUT' && !['submit', 'button', 'checkbox', 'radio'].includes(active.type);
        const isTextArea = active.tagName === 'TEXTAREA';
        
        if (isInput || isTextArea) {
            if (isTextArea && e.shiftKey) return;
            
            const currentForm = active.closest('form');
            if (currentForm) {
                const selector = 'input:not([type="hidden"]):not([disabled]):not([type="submit"]):not([type="button"]), textarea:not([disabled])';
                const formInputs = Array.from(currentForm.querySelectorAll(selector)).filter(el => {
                    const rect = el.getBoundingClientRect();
                    return rect.width > 0 && rect.height > 0 && window.getComputedStyle(el).visibility !== 'hidden';
                });
                
                const currentIndex = formInputs.indexOf(active);
                
                if (currentIndex > -1 && currentIndex < formInputs.length - 1) {
                    e.preventDefault();
                    e.stopPropagation();
                    const nextInput = formInputs[currentIndex + 1];
                    nextInput.focus();
                    if (nextInput.select) nextInput.select();
                } else if (currentIndex === formInputs.length - 1) {
                    e.preventDefault();
                    e.stopPropagation();
                    const submitBtn = currentForm.querySelector('button[kind="primaryFormSubmit"], button[type="submit"]');
                    if (submitBtn) submitBtn.click();
                }
            }
        }
    }

    setTimeout(setupEnterNavigation, 300);
    setInterval(setupEnterNavigation, 1200);
})();
</script>
""", height=0, width=0)

# ---------------------------------------------------------
# DATABASE ENGINE & DYNAMIC SETTINGS TABLE
# ---------------------------------------------------------
DB_FILE = "master_tailor.db"

def get_db():
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def hash_pw(password):
    return hashlib.sha256(password.encode()).hexdigest()

def init_db():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );
        """)
        # Initialize default studio and credential configurations if missing
        cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('brand_name', 'BAMNIYA STUDIO')")
        cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('brand_tagline', 'Bespoke Master Tailoring & Haute Couture')")
        cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('admin_master_key', 'ADMIN176920')")
        cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('tailor_master_key', '176920')")
        cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('admin_recovery_phone', '')")
        cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('tally_ledger', 'Tailoring Sales')")
        cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('tally_cash_ledger', 'Cash')")
        cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('tally_bank_ledger', 'Bank Account')")

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS clients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_code TEXT UNIQUE NOT NULL,
            full_name TEXT NOT NULL,
            phone TEXT NOT NULL,
            email TEXT,
            posture_notes TEXT,
            asymmetry_notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS measurements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER NOT NULL,
            revision_label TEXT DEFAULT 'Standard',
            garment_category TEXT DEFAULT 'All Garments / Master Set',
            unit TEXT CHECK(unit IN ('Inches', 'Centimeters')) NOT NULL DEFAULT 'Inches',
            date_recorded DATE NOT NULL,
            full_length_jacket REAL,
            neck REAL,
            cross_shoulder REAL,
            chest_full REAL,
            waist_stomach REAL,
            seat_hip REAL,
            armhole REAL,
            sleeve_length REAL,
            wrist REAL,
            trouser_waist REAL,
            front_rise REAL,
            crotch_depth REAL,
            thigh REAL,
            bottom_opening REAL,
            notes TEXT,
            FOREIGN KEY (client_id) REFERENCES clients (id) ON DELETE CASCADE
        );
        """)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_number TEXT UNIQUE NOT NULL,
            client_id INTEGER NOT NULL,
            measurement_id INTEGER NOT NULL,
            garment_type TEXT NOT NULL,
            fit_preference TEXT NOT NULL,
            fabric_details TEXT,
            total_amount REAL DEFAULT 0.0,
            amount_paid REAL DEFAULT 0.0,
            payment_mode TEXT DEFAULT 'Cash',
            payment_status TEXT DEFAULT 'Due',
            delivery_date DATE,
            workflow_status TEXT DEFAULT 'Drafted',
            fitting_remarks TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (client_id) REFERENCES clients (id) ON DELETE CASCADE,
            FOREIGN KEY (measurement_id) REFERENCES measurements (id) ON DELETE CASCADE
        );
        """)
        conn.commit()

init_db()

def get_setting(key, default=""):
    with get_db() as conn:
        row = conn.cursor().execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
        return row[0] if row else default

def set_setting(key, value):
    with get_db() as conn:
        conn.cursor().execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value))
        conn.commit()

BRAND_NAME = get_setting("brand_name", "BAMNIYA STUDIO")
BRAND_TAGLINE = get_setting("brand_tagline", "Bespoke Master Tailoring & Haute Couture")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@700;800&family=Plus+Jakarta+Sans:wght@500;600;700;800&display=swap');

    .stApp {
        background-color: #FAF7F2 !important;
        color: #111827 !important;
        font-family: 'Plus Jakarta Sans', sans-serif !important;
    }

    p, span, label, h1, h2, h3, h4, h5, h6, [data-testid="stMarkdownContainer"] p {
        color: #111827 !important;
        font-family: 'Plus Jakarta Sans', sans-serif !important;
    }

    label[data-testid="stWidgetLabel"] p {
        color: #111827 !important;
        font-weight: 800 !important;
        font-size: 1.05rem !important;
    }

    div[data-baseweb="select"], div[data-baseweb="input"], div[data-baseweb="base-input"] {
        background-color: #FFFFFF !important;
        border: 1.5px solid #C8B9A6 !important;
        border-radius: 10px !important;
    }
    div[data-baseweb="select"] *, div[data-baseweb="input"] * {
        background-color: transparent !important;
        color: #111827 !important;
        font-weight: 700 !important;
    }

    div[data-baseweb="popover"], div[data-baseweb="popover"] > div, ul[data-baseweb="menu"], div[data-baseweb="calendar"] {
        background-color: #FFFFFF !important;
        border: 1.5px solid #C8B9A6 !important;
    }
    ul[data-baseweb="menu"] li {
        background-color: #FFFFFF !important;
        color: #111827 !important;
    }
    ul[data-baseweb="menu"] li:hover {
        background-color: #EAE0D0 !important;
        color: #000000 !important;
    }

    .stTextInput input, .stNumberInput input, .stTextArea textarea, .stDateInput input {
        background-color: #FFFFFF !important;
        color: #111827 !important;
        font-weight: 700 !important;
        border-radius: 10px !important;
        border: 1.5px solid #C8B9A6 !important;
    }

    .stButton>button {
        background: #EAE0D0 !important;
        color: #111827 !important;
        border: 2px solid #C8B9A6 !important;
        border-radius: 14px !important;
        min-height: 3.5rem !important;
        font-size: 1.05rem !important;
        font-weight: 800 !important;
        margin-bottom: 0.3rem !important;
        transition: all 0.2s ease-in-out !important;
    }
    .stButton>button:hover {
        background: #DFD3C0 !important;
        border-color: #8C6D4F !important;
        color: #000000 !important;
        transform: translateY(-2px) !important;
    }

    .section-title-btn {
        background: #EAE0D0;
        color: #111827 !important;
        border: 2px solid #C8B9A6;
        padding: 0.5rem 1.2rem;
        border-radius: 10px;
        font-size: 1.15rem;
        font-weight: 800;
        display: inline-block;
        margin: 0.8rem 0;
    }

    div[data-testid="stMetric"] {
        background: #FFFFFF !important;
        border: 2px solid #E5DCCE !important;
        padding: 1rem !important;
        border-radius: 14px !important;
    }
    div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
        color: #111827 !important;
        font-weight: 800 !important;
    }

    section[data-testid="stSidebar"] {
        background-color: #24201D !important;
        border-right: 2px solid #D6C7B2 !important;
    }
    section[data-testid="stSidebar"] * {
        color: #FDFCFA !important;
    }
    section[data-testid="stSidebar"] .stButton>button {
        background: #3A3430 !important;
        color: #FDFCFA !important;
        border: 1.5px solid #5A524C !important;
        min-height: 3rem !important;
    }
    section[data-testid="stSidebar"] .stButton>button:hover {
        background: #524741 !important;
        border-color: #D6C7B2 !important;
        color: #FFFFFF !important;
    }

    .brand-title {
        font-family: 'Cinzel', serif !important;
        font-size: 2.8rem;
        font-weight: 800;
        color: #111827 !important;
        text-align: center;
        margin-bottom: 0.1rem;
    }
    .brand-tagline {
        text-align: center;
        color: #8C6D4F !important;
        font-size: 0.95rem;
        letter-spacing: 2px;
        text-transform: uppercase;
        margin-bottom: 1.2rem;
        font-weight: 700;
    }

    .order-card {
        background: #FFFFFF;
        border: 1.5px solid #D8CCBE;
        border-radius: 12px;
        padding: 1.2rem;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# STATE ROUTING
# ---------------------------------------------------------
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "is_admin" not in st.session_state:
    st.session_state.is_admin = False
if "username" not in st.session_state:
    st.session_state.username = ""
if "page" not in st.session_state:
    st.session_state.page = "Dashboard"
if "active_client_id" not in st.session_state:
    st.session_state.active_client_id = None
if "active_order_no" not in st.session_state:
    st.session_state.active_order_no = None
if "delete_target_order" not in st.session_state:
    st.session_state.delete_target_order = None
if "delete_target_client" not in st.session_state:
    st.session_state.delete_target_client = None

def navigate(page_name):
    st.session_state.page = page_name

# ---------------------------------------------------------
# AUTHENTICATION
# ---------------------------------------------------------
if not st.session_state.authenticated:
    st.markdown(f"<div class='brand-title'>{BRAND_NAME}</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='brand-tagline'>{BRAND_TAGLINE}</div>", unsafe_allow_html=True)
    
    col_center = st.columns([1, 1.8, 1])[1]
    with col_center:
        auth_tab = st.radio("Portal Access", ["Sign In", "Forgot Password / Reset", "Create Tailor Account"], horizontal=True)
        
        current_admin_key = get_setting("admin_master_key", "ADMIN176920")
        current_tailor_key = get_setting("tailor_master_key", "176920")
        saved_phone = get_setting("admin_recovery_phone", "")

        if auth_tab == "Sign In":
            with st.form("signin_form"):
                st.subheader("Studio Sign In")
                u_name = st.text_input("Username ", type="password")
                p_word = st.text_input("Password", type="password")
                btn_login = st.form_submit_button("Sign In to Studio Hub", use_container_width=True)
                if btn_login:
                    entered_code = u_name.strip() or p_word.strip()
                    
                    # 1. Admin Master Key Login
                    if entered_code == current_admin_key:
                        st.session_state.authenticated = True
                        st.session_state.is_admin = True
                        st.session_state.username = "Administrator"
                        st.session_state.page = "Dashboard"
                        st.rerun()
                    
                    # 2. Tailor Master Key Login
                    elif entered_code == current_tailor_key:
                        st.session_state.authenticated = True
                        st.session_state.is_admin = False
                        st.session_state.username = f"Master Tailor ({BRAND_NAME})"
                        st.session_state.page = "Dashboard"
                        st.rerun()
                    
                    # 3. Database user account login
                    elif u_name and p_word:
                        with get_db() as conn:
                            user = conn.cursor().execute(
                                "SELECT * FROM users WHERE username = ? AND password_hash = ?", 
                                (u_name.strip(), hash_pw(p_word))
                            ).fetchone()
                            if user:
                                st.session_state.authenticated = True
                                st.session_state.is_admin = False
                                st.session_state.username = u_name.strip()
                                st.session_state.page = "Dashboard"
                                st.rerun()
                            else:
                                st.error("Invalid credentials.")
                    else:
                        st.error("Please enter credentials")
                        
        elif auth_tab == "Forgot Password / Reset":
            st.subheader("Reset Admin Master Password")
            if not saved_phone:
                st.warning("⚠️ No recovery phone number has been configured yet in the Admin Panel.")
            else:
                with st.form("reset_password_form"):
                    verify_phone = st.text_input("Enter Registered Admin Phone Number")
                    new_admin_pwd = st.text_input("Enter New Admin Master Password", type="password")
                    confirm_pwd = st.text_input("Confirm New Admin Master Password", type="password")
                    btn_reset = st.form_submit_button("Reset Password", use_container_width=True)
                    
                    if btn_reset:
                        clean_input_phone = "".join(filter(str.isdigit, verify_phone))
                        clean_saved_phone = "".join(filter(str.isdigit, saved_phone))
                        
                        if clean_input_phone and clean_input_phone == clean_saved_phone:
                            if new_admin_pwd and new_admin_pwd == confirm_pwd:
                                set_setting("admin_master_key", new_admin_pwd.strip())
                                st.success("Admin Master Password has been successfully reset! You can now Sign In.")
                            else:
                                st.error("Passwords do not match or cannot be empty.")
                        else:
                            st.error("Phone number verification failed. Please enter the exact registered number.")
        else:
            with st.form("signup_form"):
                st.subheader("New Tailor Registration")
                new_user = st.text_input("Choose Username*")
                new_pass = st.text_input("Create Password*", type="password")
                btn_signup = st.form_submit_button("Register Account", use_container_width=True)
                if btn_signup and new_user and new_pass:
                    try:
                        with get_db() as conn:
                            conn.cursor().execute(
                                "INSERT INTO users (username, password_hash) VALUES (?, ?)",
                                (new_user.strip(), hash_pw(new_pass))
                            )
                            conn.commit()
                        st.success("Account created! You can now sign in.")
                    except sqlite3.IntegrityError:
                        st.error("Username already registered.")
    st.stop()

# ---------------------------------------------------------
# SIDEBAR NAVIGATION
# ---------------------------------------------------------
st.sidebar.markdown(f"## ✂️ **{BRAND_NAME}**")
st.sidebar.caption(f"Operator: **{st.session_state.username}**")
st.sidebar.markdown("---")
st.sidebar.markdown("### Studio Menu")

if st.sidebar.button("Main Hub (Home)", use_container_width=True):
    navigate("Dashboard")
    st.rerun()

if st.sidebar.button("1. Register Client", use_container_width=True):
    navigate("New Client")
    st.rerun()

if st.sidebar.button("2. New Order", use_container_width=True):
    navigate("New Order")
    st.rerun()

if st.sidebar.button("3. Record Measurements", use_container_width=True):
    navigate("New Measurement")
    st.rerun()

if st.sidebar.button("4. Print Receipt", use_container_width=True):
    navigate("Print Slip")
    st.rerun()

if st.sidebar.button("5. Order Tracking", use_container_width=True):
    navigate("Order Tracking")
    st.rerun()

if st.sidebar.button("6. Order Status & Sales", use_container_width=True):
    navigate("Order Status")
    st.rerun()

if st.sidebar.button("7. Database", use_container_width=True):
    navigate("Client Records")
    st.rerun()

# Only shown if logged in with Admin Master Key
if st.session_state.is_admin:
    if st.sidebar.button("Admin Control Panel", use_container_width=True):
        navigate("Admin Settings")
        st.rerun()

st.sidebar.markdown("---")
if st.sidebar.button("Logout", use_container_width=True):
    st.session_state.authenticated = False
    st.session_state.is_admin = False
    st.session_state.username = ""
    st.session_state.active_client_id = None
    st.session_state.active_order_no = None
    st.session_state.page = "Dashboard"
    st.rerun()


# ---------------------------------------------------------
# LANDING PAGE: MAIN HUB
# ---------------------------------------------------------
if st.session_state.page == "Dashboard":
    st.markdown(f"<div class='brand-title'>{BRAND_NAME}</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='brand-tagline'>{BRAND_TAGLINE}</div>", unsafe_allow_html=True)
    
    with get_db() as conn:
        total_clients = conn.cursor().execute("SELECT COUNT(*) FROM clients").fetchone()[0]
        active_orders = conn.cursor().execute("SELECT COUNT(*) FROM orders WHERE workflow_status != 'Delivered'").fetchone()[0]
        unpaid_count = conn.cursor().execute("SELECT COUNT(*) FROM orders WHERE payment_status IN ('Due', 'Advance Paid', 'Half Paid')").fetchone()[0]

    c1, c2, c3 = st.columns(3)
    c1.metric("Client Profiles", f"{total_clients}")
    c2.metric("In Production", f"{active_orders}")
    c3.metric("Payments Due", f"{unpaid_count}")
    
    st.markdown("<div class='section-title-btn'>Studio Action Centre</div>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Register New Client", key="btn_hub_client", use_container_width=True):
            navigate("New Client")
            st.rerun()
        if st.button("Record Client Measurements", key="btn_hub_measure", use_container_width=True):
            navigate("New Measurement")
            st.rerun()
        if st.button("Create New Garment Order", key="btn_hub_new_order", use_container_width=True):
            navigate("New Order")
            st.rerun()

    with col2:
        if st.button("Order Tracking (Workshop)", key="btn_hub_track_orders", use_container_width=True):
            navigate("Order Tracking")
            st.rerun()
        if st.button("Order Status & Financials", key="btn_hub_status_orders", use_container_width=True):
            navigate("Order Status")
            st.rerun()
        if st.button("Print Order Receipt Slip", key="btn_hub_print_slip", use_container_width=True):
            navigate("Print Slip")
            st.rerun()
        if st.button("Client Database", key="btn_hub_records", use_container_width=True):
            navigate("Client Records")
            st.rerun()


# ---------------------------------------------------------
# 1. REGISTER CLIENT
# ---------------------------------------------------------
elif st.session_state.page == "New Client":
    st.markdown("<div class='section-title-btn'>Step 1: Register Client Profile</div>", unsafe_allow_html=True)
    if st.button("← Back to Main Hub", key="btn_back_client"):
        navigate("Dashboard")
        st.rerun()
        
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT client_code FROM clients")
        rows = cur.fetchall()
        highest_num = 0
        for r in rows:
            code_str = str(r[0]).strip() if r[0] else ""
            if code_str.isdigit():
                val = int(code_str)
                if val > highest_num:
                    highest_num = val
        next_num = highest_num + 1
        default_client_code = f"{next_num:03d}"
        
    with st.form("new_client_form"):
        c1, c2 = st.columns(2)
        with c1:
            client_code = st.text_input("Client ID *", value=default_client_code)
            full_name = st.text_input("Full Name *")
            phone = st.text_input("Contact Number *")
            email = st.text_input("Email (Optional)")
        with c2:
            posture_notes = st.text_area("Posture Observations", placeholder="e.g., Erect stance, forward sloping shoulders...")
            asymmetry_notes = st.text_area("Asymmetry Notes", placeholder="e.g., Right shoulder 0.5 in lower...")
        
        submitted = st.form_submit_button("Save & Proceed to Measurements → (Press Enter)", use_container_width=True)
        if submitted and client_code and full_name and phone:
            try:
                with get_db() as conn:
                    cur = conn.cursor()
                    cur.execute("""
                    INSERT INTO clients (client_code, full_name, phone, email, posture_notes, asymmetry_notes)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """, (client_code.strip(), full_name.strip(), phone.strip(), email.strip(), posture_notes, asymmetry_notes))
                    new_id = cur.lastrowid
                    conn.commit()
                st.session_state.active_client_id = new_id
                st.success(f"Client '{full_name}' created with ID {client_code}! Redirecting to measurements...")
                navigate("New Measurement")
                st.rerun()
            except sqlite3.IntegrityError:
                st.error("Client ID or Phone already exists. Please choose a different ID.")


# ---------------------------------------------------------
# 2. RECORD MEASUREMENTS
# ---------------------------------------------------------
elif st.session_state.page == "New Measurement":
    st.markdown("<div class='section-title-btn'>Step 2: Record Client Measurements</div>", unsafe_allow_html=True)
    if st.button("← Back to Main Hub", key="btn_back_measure"):
        navigate("Dashboard")
        st.rerun()
        
    with get_db() as conn:
        clients = conn.cursor().execute("SELECT id, client_code, full_name FROM clients ORDER BY id DESC").fetchall()
    
    if not clients:
        st.warning("Register a client first before taking measurements.")
    else:
        client_dict = {f"{c['client_code']} — {c['full_name']}": c['id'] for c in clients}
        
        default_idx = 0
        if st.session_state.active_client_id:
            for idx, cid in enumerate(client_dict.values()):
                if cid == st.session_state.active_client_id:
                    default_idx = idx
                    break

        selected_client_label = st.selectbox("Client Selection", list(client_dict.keys()), index=default_idx)
        selected_client_id = client_dict[selected_client_label]
        st.session_state.active_client_id = selected_client_id
        
        with get_db() as conn:
            prev_m = conn.cursor().execute(
                "SELECT * FROM measurements WHERE client_id = ? ORDER BY id DESC LIMIT 1", 
                (selected_client_id,)
            ).fetchone()

        garment_options = [
            "Kurta saya", "Kurta saya with izar", "Pehran", "Only kurta",
            "Kurta Short)", "Pajama", "Shirt", "Trousers", "Sherwani",
            "Nehru Jacket", "Waistcoat", "Jodhpuri Suit", "Pathani Suit",
            "Two-Piece / Three-Piece Suit", "Blazer / Formal Coat",
            "Shirt & Trousers", "Safari Suit"
        ]
        
        selected_garment_type = st.selectbox("Choose Garment Type to Measure", garment_options)
        
        with st.form("measurement_form"):
            h1, h2 = st.columns(2)
            with h1:
                rec_date = st.date_input("Date Taken", datetime.date.today())
            with h2:
                unit = st.selectbox("Measurement Unit", ["Inches", "Centimeters"])
            
            st.markdown("<div class='section-title-btn'>Upper Body Dimensions</div>", unsafe_allow_html=True)
            full_length_jacket = st.number_input("Length", value=float(prev_m['full_length_jacket']) if prev_m and prev_m['full_length_jacket'] else None, min_value=0.0, step=0.25, placeholder="0.00")
            neck = st.number_input("Neck", value=float(prev_m['neck']) if prev_m and prev_m['neck'] else None, min_value=0.0, step=0.25, placeholder="0.00")
            cross_shoulder = st.number_input("Shoulder", value=float(prev_m['cross_shoulder']) if prev_m and prev_m['cross_shoulder'] else None, min_value=0.0, step=0.25, placeholder="0.00")
            chest_full = st.number_input("Chest", value=float(prev_m['chest_full']) if prev_m and prev_m['chest_full'] else None, min_value=0.0, step=0.25, placeholder="0.00")
            waist_stomach = st.number_input("Stomach", value=float(prev_m['waist_stomach']) if prev_m and prev_m['waist_stomach'] else None, min_value=0.0, step=0.25, placeholder="0.00")
            seat_hip = st.number_input("Hips", value=float(prev_m['seat_hip']) if prev_m and prev_m['seat_hip'] else None, min_value=0.0, step=0.25, placeholder="0.00")
            armhole = st.number_input("Armhole", value=float(prev_m['armhole']) if prev_m and prev_m['armhole'] else None, min_value=0.0, step=0.25, placeholder="0.00")
            sleeve_length = st.number_input("Sleeve", value=float(prev_m['sleeve_length']) if prev_m and prev_m['sleeve_length'] else None, min_value=0.0, step=0.25, placeholder="0.00")
            wrist = st.number_input("Wrist", value=float(prev_m['wrist']) if prev_m and prev_m['wrist'] else None, min_value=0.0, step=0.25, placeholder="0.00")

            st.markdown("<div class='section-title-btn'>Lower Side Dimensions</div>", unsafe_allow_html=True)
            trouser_waist = st.number_input("Waist", value=float(prev_m['trouser_waist']) if prev_m and prev_m['trouser_waist'] else None, min_value=0.0, step=0.25, placeholder="0.00")
            front_rise = st.number_input("Front Rise", value=float(prev_m['front_rise']) if prev_m and prev_m['front_rise'] else None, min_value=0.0, step=0.25, placeholder="0.00")
            crotch_depth = st.number_input("Crotch", value=float(prev_m['crotch_depth']) if prev_m and prev_m['crotch_depth'] else None, min_value=0.0, step=0.25, placeholder="0.00")
            thigh = st.number_input("Thigh", value=float(prev_m['thigh']) if prev_m and prev_m['thigh'] else None, min_value=0.0, step=0.25, placeholder="0.00")
            bottom_opening = st.number_input("Bottom Opening", value=float(prev_m['bottom_opening']) if prev_m and prev_m['bottom_opening'] else None, min_value=0.0, step=0.25, placeholder="0.00")

            m_notes = st.text_area("Measurement Session & Fit Notes", value=str(prev_m['notes'] or "") if prev_m else "", placeholder="e.g., Slim tapering requested...")
            save_m = st.form_submit_button("Save & Proceed to Order / Billing → (Press Enter)", use_container_width=True)
            if save_m:
                with get_db() as conn:
                    conn.cursor().execute("""
                    INSERT INTO measurements (
                        client_id, revision_label, garment_category, unit, date_recorded,
                        full_length_jacket, neck, cross_shoulder, chest_full, waist_stomach,
                        seat_hip, armhole, sleeve_length, wrist, trouser_waist,
                        front_rise, crotch_depth, thigh, bottom_opening, notes
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        selected_client_id, "Standard", selected_garment_type, unit, rec_date,
                        full_length_jacket, neck, cross_shoulder, chest_full, waist_stomach,
                        seat_hip, armhole, sleeve_length, wrist, trouser_waist,
                        front_rise, crotch_depth, thigh, bottom_opening, m_notes
                    ))
                    conn.commit()
                st.success("Measurements recorded! Proceeding to New Order / Billing...")
                navigate("New Order")
                st.rerun()


# ---------------------------------------------------------
# 3. CREATE NEW ORDER / BILLING
# ---------------------------------------------------------
elif st.session_state.page == "New Order":
    st.markdown("<div class='section-title-btn'>New Order Booking & Billing</div>", unsafe_allow_html=True)
    if st.button("← Back to Main Hub", key="btn_back_order"):
        navigate("Dashboard")
        st.rerun()
        
    with get_db() as conn:
        clients = conn.cursor().execute("SELECT id, client_code, full_name, phone FROM clients ORDER BY full_name ASC").fetchall()
        
    if not clients:
        st.warning("Please register a client before creating orders.")
    else:
        client_options = {f"{c['full_name']} (Phone: {c['phone']} | ID: {c['client_code']})": c['id'] for c in clients}
        
        default_idx = 0
        if st.session_state.active_client_id:
            for idx, cid in enumerate(client_options.values()):
                if cid == st.session_state.active_client_id:
                    default_idx = idx
                    break

        selected_client_label = st.selectbox("Search & Select Client (Type Name or Phone)", list(client_options.keys()), index=default_idx)
        selected_client_id = client_options[selected_client_label]
        st.session_state.active_client_id = selected_client_id
        
        with get_db() as conn:
            latest_m = conn.cursor().execute(
                "SELECT id, date_recorded FROM measurements WHERE client_id = ? ORDER BY id DESC LIMIT 1", 
                (selected_client_id,)
            ).fetchone()

        st.markdown("### Client Action Options")
        col_act_m, col_act_b = st.columns(2)
        with col_act_m:
            if st.button("Update / Adjust Measurements First", use_container_width=True):
                navigate("New Measurement")
                st.rerun()
        with col_act_b:
            st.info("Or fill billing details below to proceed directly")
            
        st.markdown("---")
            
        if not latest_m:
            st.error("No measurements found for this client. Please record measurements first before billing.")
            if st.button("Record Measurements Now →", use_container_width=True):
                navigate("New Measurement")
                st.rerun()
        else:
            measurement_id = latest_m['id']
            with st.form("new_order_form"):
                o1, o2 = st.columns(2)
                with o1:
                    order_no = st.text_input("Order Reference ID*", value=f"BS-{datetime.date.today().strftime('%Y%m%d')}-01")
                    garment_type = st.selectbox("Garment to Stitch", [
                        "Kurta saya", "Kurta saya with izar", "Pehran", "Only kurta",
                        "Kurta Short)", "Pajama", "Shirt", "Trousers", "Sherwani",
                        "Nehru Jacket", "Waistcoat", "Jodhpuri Suit", "Pathani Suit",
                        "Two-Piece / Three-Piece Suit", "Blazer / Formal Coat",
                        "Shirt & Trousers", "Safari Suit"
                    ])
                    fit_preference = st.selectbox("Fit Preference", ["Slim Fit", "Regular Fit", "Relaxed Fit", "Qasar fit", "Qali", "Barik Qali",])
                with o2:
                    total_amount = st.number_input("Total Garment Price (₹)", value=None, min_value=0.0, step=500.0, placeholder="Enter total price")
                    amount_paid = st.number_input("Initial Amount Received (₹)", value=None, min_value=0.0, step=500.0, placeholder="Enter advance paid")
                    payment_mode = st.selectbox("Payment Mode*", ["Cash", "UPI / QR", "Credit/Debit Card", "Bank Transfer"])
                    
                    calc_total = float(total_amount or 0.0)
                    calc_paid = float(amount_paid or 0.0)
                    
                    auto_status = "Due"
                    if calc_paid >= calc_total and calc_total > 0:
                        auto_status = "Fully Paid"
                    elif calc_paid == (calc_total / 2) and calc_total > 0:
                        auto_status = "Half Paid"
                    elif calc_paid > 0:
                        auto_status = "Advance Paid"
                        
                    payment_status = st.selectbox("Payment Status*", ["Due", "Advance Paid", "Half Paid", "Fully Paid"], index=["Due", "Advance Paid", "Half Paid", "Fully Paid"].index(auto_status))
                    delivery_date = st.date_input("Target Delivery Date (Completion)", datetime.date.today() + datetime.timedelta(days=12))

                fabric_details = st.text_area("Fabric Specifications & Mill Details", placeholder="e.g., Pure Silk, Worsted Wool...")
                remarks = st.text_area("Specific Cutting / Fitting Requirements")
                
                place_order = st.form_submit_button("Submit Order & Generate Receipt → (Press Enter)", use_container_width=True)
                if place_order:
                    with get_db() as conn:
                        conn.cursor().execute("""
                        INSERT INTO orders (
                            order_number, client_id, measurement_id, garment_type, fit_preference, 
                            fabric_details, total_amount, amount_paid, payment_mode, payment_status, delivery_date, fitting_remarks
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            order_no, selected_client_id, measurement_id, garment_type, fit_preference,
                            fabric_details, calc_total, calc_paid, payment_mode, payment_status, delivery_date, remarks
                        ))
                        conn.commit()
                    st.session_state.active_order_no = order_no
                    st.success(f"Order {order_no} generated! Redirecting to Receipt...")
                    navigate("Print Slip")
                    st.rerun()


# ---------------------------------------------------------
# 4. PRINT RECEIPT
# ---------------------------------------------------------
elif st.session_state.page == "Print Slip":
    st.markdown("<div class='section-title-btn'>Step 4: Print A5 Receipt Slip</div>", unsafe_allow_html=True)
    if st.button("← Back to Main Hub", key="btn_back_slip"):
        navigate("Dashboard")
        st.rerun()
        
    with get_db() as conn:
        orders = conn.cursor().execute("""
        SELECT o.order_number, c.full_name FROM orders o JOIN clients c ON o.client_id = c.id ORDER BY o.id DESC
        """).fetchall()
        
    if not orders:
        st.info("No orders found to generate slips.")
    else:
        order_opts = {f"{o['order_number']} — {o['full_name']}": o['order_number'] for o in orders}
        
        default_o_idx = 0
        if st.session_state.active_order_no:
            for idx, ono in enumerate(order_opts.values()):
                if ono == st.session_state.active_order_no:
                    default_o_idx = idx
                    break

        selected_slip_order = st.selectbox("Select Order Reference", list(order_opts.keys()), index=default_o_idx)
        ord_no = order_opts[selected_slip_order]
        st.session_state.active_order_no = ord_no
        
        with get_db() as conn:
            slip_data = conn.cursor().execute("""
            SELECT o.*, c.client_code, c.full_name as client_name, c.phone, c.email,
                   m.unit, m.neck, m.chest_full, m.waist_stomach, m.cross_shoulder,
                   m.armhole, m.wrist, m.sleeve_length,
                   m.full_length_jacket, m.trouser_waist, m.seat_hip, m.thigh,
                   m.bottom_opening, m.front_rise, m.crotch_depth
            FROM orders o
            JOIN clients c ON o.client_id = c.id
            JOIN measurements m ON o.measurement_id = m.id
            WHERE o.order_number = ?
            """, (ord_no,)).fetchone()
            
        if slip_data:
            total_amt = float(slip_data['total_amount'] or 0.0)
            paid_amt = float(slip_data['amount_paid'] or 0.0)
            bal_amt = total_amt - paid_amt
            
            c_name = str(slip_data['client_name'])
            c_id = str(slip_data['client_code'])
            c_phone = str(slip_data['phone'])
            ord_id = str(slip_data['order_number'])
            book_date = str(slip_data['created_at'])[:10]
            del_date = str(slip_data['delivery_date'])
            garment = str(slip_data['garment_type'])
            fit = str(slip_data['fit_preference'])
            pay_mode = str(slip_data['payment_mode'] or 'Cash')
            pay_stat = str(slip_data['payment_status'])
            unit = str(slip_data['unit'])

            up_len = str(slip_data['full_length_jacket'] or '-')
            up_neck = str(slip_data['neck'] or '-')
            up_shld = str(slip_data['cross_shoulder'] or '-')
            up_chest = str(slip_data['chest_full'] or '-')
            up_stom = str(slip_data['waist_stomach'] or '-')
            up_hip = str(slip_data['seat_hip'] or '-')
            up_armh = str(slip_data['armhole'] or '-')
            up_slv = str(slip_data['sleeve_length'] or '-')
            up_wrst = str(slip_data['wrist'] or '-')

            lw_waist = str(slip_data['trouser_waist'] or '-')
            lw_frise = str(slip_data['front_rise'] or '-')
            lw_crotch = str(slip_data['crotch_depth'] or '-')
            lw_seat = str(slip_data['seat_hip'] or '-')
            lw_thigh = str(slip_data['thigh'] or '-')
            lw_bot = str(slip_data['bottom_opening'] or '-')

            receipt_html_parts = [
                "<!DOCTYPE html><html><head><meta charset='utf-8'>",
                "<title>Receipt_" + ord_id + "</title>",
                "<style>",
                "@page { size: A5 portrait; margin: 5mm; }",
                "* { box-sizing: border-box; }",
                "@media print { .print-btn { display: none !important; } }",
                "</style>",
                "</head>",
                "<body style='margin:0; padding:6px; background:#FFFFFF; font-family:Courier New, Courier, monospace; color:#000000; font-size:12px; line-height:1.3;'>",
                "<button class='print-btn' onclick='window.print()' style='display:block; width:100%; max-width:138mm; margin:0 auto 10px auto; background:#111827; color:#FFFFFF; border:none; padding:10px; font-size:14px; font-weight:bold; cursor:pointer; border-radius:6px;'>🖨️ PRINT RECEIPT (A5) / PRESS ENTER</button>",
                "<div style='width:100%; max-width:138mm; margin:0 auto; border:1.5px solid #000000; padding:10px 12px;'>",
                "<div style='text-align:center;'>",
                "<div style='font-size:16px; font-weight:bold; letter-spacing:1px; margin:0;'>" + BRAND_NAME + "</div>",
                "<div style='font-size:10px; margin:2px 0; text-transform:uppercase;'>" + BRAND_TAGLINE + "</div>",
                "<div style='font-size:11px; font-weight:bold;'>SALES & MEASUREMENT RECEIPT</div>",
                "</div>",
                "<hr style='border:none; border-top:1px dashed #000; margin:6px 0;'>",
                "<table style='width:100%; border-collapse:collapse; font-size:11px;'>",
                "<tr><td><b>CLIENT:</b> " + c_name + "</td><td style='text-align:right;'><b>DATE:</b> " + book_date + "</td></tr>",
                "<tr><td><b>ID:</b> " + c_id + "</td><td style='text-align:right;'><b>ORDER #:</b> " + ord_id + "</td></tr>",
                "<tr><td colspan='2'><b>PHONE:</b> " + c_phone + "</td></tr>",
                "<tr><td colspan='2'><b>GARMENT:</b> " + garment + " (" + fit + ")</td></tr>",
                "<tr><td colspan='2'><b>DELIVERY:</b> " + del_date + "</td></tr>",
                "</table>",
                "<hr style='border:none; border-top:1px dashed #000; margin:6px 0;'>",
                
                "<div style='font-weight:bold; font-size:11px; text-align:center; margin-bottom:4px;'>[ BODY MEASUREMENTS (" + unit + ") ]</div>",
                "<table style='width:100%; border-collapse:collapse; font-size:10.5px;'>",
                "<tr style='background:#EEEEEE; text-align:center;'>",
                "<th colspan='2' style='border:1px solid #000; padding:3px;'>UPPER BODY</th>",
                "<th colspan='2' style='border:1px solid #000; padding:3px;'>LOWER SIDE</th>",
                "</tr>",
                "<tr>",
                "<td style='border:1px solid #000; padding:2px 4px;'>Length</td><td style='border:1px solid #000; padding:2px 4px; text-align:center;'><b>" + up_len + "</b></td>",
                "<td style='border:1px solid #000; padding:2px 4px;'>Waist</td><td style='border:1px solid #000; padding:2px 4px; text-align:center;'><b>" + lw_waist + "</b></td>",
                "</tr>",
                "<tr>",
                "<td style='border:1px solid #000; padding:2px 4px;'>Neck</td><td style='border:1px solid #000; padding:2px 4px; text-align:center;'><b>" + up_neck + "</b></td>",
                "<td style='border:1px solid #000; padding:2px 4px;'>Front Rise</td><td style='border:1px solid #000; padding:2px 4px; text-align:center;'><b>" + lw_frise + "</b></td>",
                "</tr>",
                "<tr>",
                "<td style='border:1px solid #000; padding:2px 4px;'>Shoulder</td><td style='border:1px solid #000; padding:2px 4px; text-align:center;'><b>" + up_shld + "</b></td>",
                "<td style='border:1px solid #000; padding:2px 4px;'>Crotch</td><td style='border:1px solid #000; padding:2px 4px; text-align:center;'><b>" + lw_crotch + "</b></td>",
                "</tr>",
                "<tr>",
                "<td style='border:1px solid #000; padding:2px 4px;'>Chest</td><td style='border:1px solid #000; padding:2px 4px; text-align:center;'><b>" + up_chest + "</b></td>",
                "<td style='border:1px solid #000; padding:2px 4px;'>Seat</td><td style='border:1px solid #000; padding:2px 4px; text-align:center;'><b>" + lw_seat + "</b></td>",
                "</tr>",
                "<tr>",
                "<td style='border:1px solid #000; padding:2px 4px;'>Stomach</td><td style='border:1px solid #000; padding:2px 4px; text-align:center;'><b>" + up_stom + "</b></td>",
                "<td style='border:1px solid #000; padding:2px 4px;'>Thigh</td><td style='border:1px solid #000; padding:2px 4px; text-align:center;'><b>" + lw_thigh + "</b></td>",
                "</tr>",
                "<tr>",
                "<td style='border:1px solid #000; padding:2px 4px;'>Hips</td><td style='border:1px solid #000; padding:2px 4px; text-align:center;'><b>" + up_hip + "</b></td>",
                "<td style='border:1px solid #000; padding:2px 4px;'>Bottom</td><td style='border:1px solid #000; padding:2px 4px; text-align:center;'><b>" + lw_bot + "</b></td>",
                "</tr>",
                "<tr>",
                "<td style='border:1px solid #000; padding:2px 4px;'>Armhole</td><td style='border:1px solid #000; padding:2px 4px; text-align:center;'><b>" + up_armh + "</b></td>",
                "<td style='border:1px solid #000; padding:2px 4px; background:#FAFAFA;'>-</td><td style='border:1px solid #000; padding:2px 4px; background:#FAFAFA; text-align:center;'>-</td>",
                "</tr>",
                "<tr>",
                "<td style='border:1px solid #000; padding:2px 4px;'>Sleeve</td><td style='border:1px solid #000; padding:2px 4px; text-align:center;'><b>" + up_slv + "</b></td>",
                "<td style='border:1px solid #000; padding:2px 4px; background:#FAFAFA;'>-</td><td style='border:1px solid #000; padding:2px 4px; background:#FAFAFA; text-align:center;'>-</td>",
                "</tr>",
                "<tr>",
                "<td style='border:1px solid #000; padding:2px 4px;'>Wrist</td><td style='border:1px solid #000; padding:2px 4px; text-align:center;'><b>" + up_wrst + "</b></td>",
                "<td style='border:1px solid #000; padding:2px 4px; background:#FAFAFA;'>-</td><td style='border:1px solid #000; padding:2px 4px; background:#FAFAFA; text-align:center;'>-</td>",
                "</tr>",
                "</table>",
                
                "<hr style='border:none; border-top:1px dashed #000; margin:6px 0;'>",
                "<table style='width:100%; border-collapse:collapse; font-size:11px;'>",
                "<tr><td><b>TOTAL AMOUNT:</b></td><td style='text-align:right; font-weight:bold;'>Rs. " + f"{total_amt:,.2f}" + "</td></tr>",
                "<tr><td><b>AMOUNT PAID:</b></td><td style='text-align:right;'>Rs. " + f"{paid_amt:,.2f}" + "</td></tr>",
                "<tr><td style='font-weight:bold;'>BALANCE DUE:</td><td style='text-align:right; font-weight:bold; font-size:13px;'>Rs. " + f"{bal_amt:,.2f}" + "</td></tr>",
                "<tr><td><b>PAYMENT MODE:</b></td><td style='text-align:right;'>" + pay_mode + "</td></tr>",
                "<tr><td><b>PAYMENT STAGE:</b></td><td style='text-align:right; font-weight:bold;'>" + pay_stat + "</td></tr>",
                "</table>",
                "<hr style='border:none; border-top:1px dashed #000; margin:6px 0;'>",
                "<div style='text-align:center; font-size:10px;'>THANK YOU FOR CHOOSING " + BRAND_NAME + "<br>Exact Fit & Master Craftsmanship Guaranteed</div>",
                "<br>",
                "<table style='width:100%; font-size:9.5px;'><tr><td>CLIENT SIGN: ____________</td><td style='text-align:right;'>MASTER TAILOR: ____________</td></tr></table>",
                "</div></body></html>"
            ]

            pure_receipt_html = "".join(receipt_html_parts)
            st.components.v1.html(pure_receipt_html, height=720, scrolling=True)


# ---------------------------------------------------------
# 5A. ORDER TRACKING
# ---------------------------------------------------------
elif st.session_state.page == "Order Tracking":
    st.markdown("<div class='section-title-btn'>Order Tracking (Workshop Production)</div>", unsafe_allow_html=True)
    if st.button("← Back to Main Hub", key="btn_back_track"):
        navigate("Dashboard")
        st.rerun()
        
    with get_db() as conn:
        orders_df = pd.read_sql_query("""
        SELECT o.id, o.order_number, c.full_name as client_name, c.phone, o.garment_type, 
               o.workflow_status, o.delivery_date, o.fabric_details, o.fitting_remarks
        FROM orders o
        JOIN clients c ON o.client_id = c.id
        ORDER BY o.delivery_date ASC
        """, conn)
        
    if orders_df.empty:
        st.info("No active garment orders in production.")
    else:
        filter_q = st.text_input("Search Order in Workshop by Client Name, Phone or Order #")
        filtered_orders = orders_df
        if filter_q:
            filtered_orders = orders_df[orders_df.apply(lambda r: filter_q.lower() in r.astype(str).str.lower().values, axis=1)]

        stages = ['Drafted', 'Fabric Cut', 'Basted Fitting', 'Alterations', 'Final Pressed', 'Delivered']
        
        for _, order in filtered_orders.iterrows():
            with st.container():
                st.markdown(f"""
                <div class='order-card'>
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <h3 style="margin:0; font-family:'Cinzel', serif;">{order['order_number']} — {order['garment_type']}</h3>
                        <span style="font-weight:800; font-size:1.1rem; color:#8C6D4F !important;">Target: {order['delivery_date']}</span>
                    </div>
                    <p style="margin: 0.3rem 0;"><b>Client:</b> {order['client_name']} ({order['phone']}) | <b>Current Stage:</b> {order['workflow_status']}</p>
                </div>
                """, unsafe_allow_html=True)
                
                c_stage, c_del = st.columns([3, 1])
                with c_stage:
                    cur_idx = stages.index(order['workflow_status']) if order['workflow_status'] in stages else 0
                    new_stage = st.selectbox("Update Stage", stages, index=cur_idx, key=f"track_stg_{order['order_number']}")
                    if new_stage != order['workflow_status']:
                        with get_db() as conn:
                            conn.cursor().execute("UPDATE orders SET workflow_status = ? WHERE order_number = ?", (new_stage, order['order_number']))
                            conn.commit()
                        st.rerun()

                with c_del:
                    st.write("")
                    if st.button(f"Delete Order", key=f"del_track_{order['order_number']}", use_container_width=True):
                        st.session_state.delete_target_order = order['order_number']
                
                if st.session_state.delete_target_order == order['order_number']:
                    st.warning(f"Confirm deleting {order['order_number']} permanently?")
                    y_col, n_col = st.columns(2)
                    with y_col:
                        if st.button("Yes, Delete", key=f"y_track_{order['order_number']}", use_container_width=True):
                            with get_db() as conn:
                                conn.cursor().execute("DELETE FROM orders WHERE order_number = ?", (order['order_number'],))
                                conn.commit()
                            st.session_state.delete_target_order = None
                            st.rerun()
                    with n_col:
                        if st.button("Cancel", key=f"n_track_{order['order_number']}", use_container_width=True):
                            st.session_state.delete_target_order = None
                            st.rerun()
                st.markdown("<hr style='margin:0.5rem 0 1rem 0; border:0.5px solid #E5DCCE;'>", unsafe_allow_html=True)


# ---------------------------------------------------------
# 5B. ORDER STATUS & FINANCIAL SALES REPORT
# ---------------------------------------------------------
elif st.session_state.page == "Order Status":
    st.markdown("<div class='section-title-btn'>Order Status & Financial Sales Report</div>", unsafe_allow_html=True)
    if st.button("← Back to Main Hub", key="btn_back_status"):
        navigate("Dashboard")
        st.rerun()
        
    with get_db() as conn:
        orders_df = pd.read_sql_query("""
        SELECT o.id, o.order_number, c.full_name as client_name, c.phone, o.garment_type, 
               o.payment_status, o.payment_mode, o.total_amount, o.amount_paid,
               (o.total_amount - o.amount_paid) as balance_due,
               o.delivery_date
        FROM orders o
        JOIN clients c ON o.client_id = c.id
        ORDER BY o.delivery_date ASC
        """, conn)
        
    if orders_df.empty:
        st.info("No sales or billing records found.")
    else:
        total_revenue = orders_df['total_amount'].sum()
        total_collected = orders_df['amount_paid'].sum()
        total_receivable = total_revenue - total_collected
        
        st.markdown("### Financial & Billing Summary")
        m1, m2, m3 = st.columns(3)
        m1.metric("Gross Sales Booked", f"₹{total_revenue:,.2f}")
        m2.metric("Payments Collected", f"₹{total_collected:,.2f}")
        m3.metric("Outstanding Balance Due", f"₹{total_receivable:,.2f}")
        
        st.markdown("---")
        st.markdown("### Order Financial List")
        st.dataframe(orders_df, use_container_width=True)
        
        st.markdown("### 💬 Outstanding Payment Reminders & Settlement")
        unpaid_orders = orders_df[orders_df['balance_due'] > 0]
        
        if unpaid_orders.empty:
            st.success("All client orders are fully settled! No outstanding balances.")
        else:
            for _, order in unpaid_orders.iterrows():
                with st.container():
                    c_details, c_msg, c_paid = st.columns([2.5, 1.5, 1.2])
                    with c_details:
                        st.markdown(f"**{order['client_name']}** (`{order['phone']}`)<br>"
                                    f"Order: `{order['order_number']}` ({order['garment_type']}) | "
                                    f"**Due: ₹{order['balance_due']:,.2f}**", unsafe_allow_html=True)
                    with c_msg:
                        clean_phone = "".join(filter(str.isdigit, str(order['phone'])))
                        if len(clean_phone) == 10:
                            clean_phone = "91" + clean_phone
                        
                        wa_text = (
                            f"Dear {order['client_name']},\n\n"
                            f"This is a payment reminder from *{BRAND_NAME}* regarding your order *{order['order_number']}* ({order['garment_type']}).\n\n"
                            f"• Total Order Price: ₹{order['total_amount']:,.2f}\n"
                            f"• Amount Received: ₹{order['amount_paid']:,.2f}\n"
                            f"• *Balance Due: ₹{order['balance_due']:,.2f}*\n\n"
                            f"Kindly clear the remaining balance at your earliest convenience.\n\n"
                            f"Thank you,\n*{BRAND_NAME}*"
                        )
                        encoded_msg = urllib.parse.quote(wa_text)
                        wa_link = f"https://wa.me/{clean_phone}?text={encoded_msg}"
                        
                        st.markdown(
                            f"""<a href="{wa_link}" target="_blank" style="text-decoration:none;">
                                <button style="width:100%; background:#25D366; color:#FFFFFF; border:none; 
                                border-radius:10px; padding:0.6rem; font-weight:800; font-size:0.95rem; cursor:pointer;">
                                💬 Send WhatsApp
                                </button>
                            </a>""", 
                            unsafe_allow_html=True
                        )
                    with c_paid:
                        if st.button(f"Mark Full Paid (₹{order['balance_due']:,.0f})", key=f"reconcile_{order['order_number']}", use_container_width=True):
                            with get_db() as conn:
                                conn.cursor().execute("UPDATE orders SET amount_paid = total_amount, payment_status = 'Fully Paid' WHERE order_number = ?", (order['order_number'],))
                                conn.commit()
                            st.success(f"Order {order['order_number']} marked Fully Paid!")
                            st.rerun()
                    st.markdown("<hr style='margin:0.4rem 0 0.8rem 0; border:0.5px solid #E5DCCE;'>", unsafe_allow_html=True)


# ---------------------------------------------------------
# 6. DATABASE
# ---------------------------------------------------------
elif st.session_state.page == "Client Records":
    st.markdown("<div class='section-title-btn'>Client Database</div>", unsafe_allow_html=True)
    if st.button("← Back to Main Hub", key="btn_back_db"):
        navigate("Dashboard")
        st.rerun()
        
    with get_db() as conn:
        clients_df = pd.read_sql_query("SELECT id, client_code, full_name, phone, posture_notes, asymmetry_notes FROM clients ORDER BY full_name", conn)
        
    if not clients_df.empty:
        search_query = st.text_input("Search Client by Name or Phone Number", placeholder="Type name or phone...")
        
        matched_clients = clients_df
        if search_query:
            matched_clients = clients_df[clients_df.apply(lambda r: search_query.lower() in r.astype(str).str.lower().values, axis=1)]
        
        st.markdown("### Matched Client Records")
        if matched_clients.empty:
            st.info("No client records matched your search.")
        else:
            for _, client in matched_clients.iterrows():
                with st.container():
                    c_info, c_action, c_del = st.columns([2.5, 2, 0.7])
                    with c_info:
                        st.markdown(f"**{client['full_name']}** (ID: `{client['client_code']}` | Phone: `{client['phone']}`)")
                    with c_action:
                        with st.popover(f"Actions for {client['full_name']}"):
                            st.write(f"Choose next step for **{client['full_name']}**:")
                            if st.button("Update Measurements", key=f"pop_m_{client['id']}", use_container_width=True):
                                st.session_state.active_client_id = client['id']
                                navigate("New Measurement")
                                st.rerun()
                            if st.button("Proceed to Direct Billing (New Order)", key=f"pop_o_{client['id']}", use_container_width=True):
                                st.session_state.active_client_id = client['id']
                                navigate("New Order")
                                st.rerun()
                    with c_del:
                        if st.button("Delete", key=f"db_del_{client['id']}", use_container_width=True):
                            st.session_state.delete_target_client = client['id']
                    
                    if st.session_state.delete_target_client == client['id']:
                        st.error(f"Confirm deleting {client['full_name']} & all history?")
                        cy, cn = st.columns(2)
                        with cy:
                            if st.button("Yes, Delete", key=f"cy_{client['id']}", use_container_width=True):
                                with get_db() as conn:
                                    cur = conn.cursor()
                                    cur.execute("DELETE FROM orders WHERE client_id = ?", (client['id'],))
                                    cur.execute("DELETE FROM measurements WHERE client_id = ?", (client['id'],))
                                    cur.execute("DELETE FROM clients WHERE id = ?", (client['id'],))
                                    conn.commit()
                                st.session_state.delete_target_client = None
                                st.success("Client and all history deleted successfully.")
                                st.rerun()
                        with cn:
                            if st.button("Cancel", key=f"cn_{client['id']}", use_container_width=True):
                                st.session_state.delete_target_client = None
                                st.rerun()
                    st.markdown("<hr style='margin:0.3rem 0 0.8rem 0; border:0.5px solid #E5DCCE;'>", unsafe_allow_html=True)
    else:
        st.info("No client records found in the database.")


# ---------------------------------------------------------
# 7. ADMIN PANEL (PASSWORD CHANGING, RECOVERY & EXPORTS)
# ---------------------------------------------------------
elif st.session_state.page == "Admin Settings":
    if not st.session_state.is_admin:
        st.error("Unauthorized. Please log in using the Admin Master Key.")
        st.stop()

    st.markdown("<div class='section-title-btn'>Admin Control Panel</div>", unsafe_allow_html=True)
    if st.button("← Back to Main Hub", key="btn_back_admin"):
        navigate("Dashboard")
        st.rerun()

    # --- 1. ADMIN SECURITY & PASSWORD MANAGEMENT ---
    st.markdown("### 🔐 Admin Security & Password Recovery Setup")
    with st.form("admin_security_form"):
        s1, s2 = st.columns(2)
        with s1:
            new_admin_key_val = st.text_input(
                "Admin Master Password", 
                value=get_setting("admin_master_key", "ADMIN176920"), 
                type="password"
            )
            new_tailor_key_val = st.text_input(
                "Staff / Tailor Master Password", 
                value=get_setting("tailor_master_key", "176920"), 
                type="password"
            )
        with s2:
            recovery_phone_val = st.text_input(
                "Admin Recovery Phone Number (Used for Password Reset)", 
                value=get_setting("admin_recovery_phone", ""),
                placeholder="e.g., +91 9876543210"
            )
            st.caption("If you forget your password, you will enter this phone number on the login screen to reset it.")

        save_security = st.form_submit_button("Save Security Credentials", use_container_width=True)
        if save_security:
            if new_admin_key_val.strip() and new_tailor_key_val.strip():
                set_setting("admin_master_key", new_admin_key_val.strip())
                set_setting("tailor_master_key", new_tailor_key_val.strip())
                set_setting("admin_recovery_phone", recovery_phone_val.strip())
                st.success("Security settings and passwords updated successfully!")
                st.rerun()
            else:
                st.error("Master passwords cannot be empty.")

    st.markdown("---")

    # --- 2. BRAND CUSTOMIZATION ---
    st.markdown("### Studio Branding & Identity Customizer")
    with st.form("brand_settings_form"):
        b1, b2 = st.columns(2)
        with b1:
            new_brand = st.text_input("Brand / Studio Name", value=BRAND_NAME)
        with b2:
            new_tagline = st.text_input("Tagline (Appears on Receipts & Headers)", value=BRAND_TAGLINE)
        
        save_brand = st.form_submit_button("Save Branding Settings", use_container_width=True)
        if save_brand:
            set_setting("brand_name", new_brand.strip())
            set_setting("brand_tagline", new_tagline.strip())
            st.success("Brand identity updated across the entire application and receipts!")
            st.rerun()

    st.markdown("---")

    # --- 3. MS EXCEL BACKUP ---
    st.markdown("### Microsoft Excel Backup & Data Export")
    st.write("Export your entire studio database (Clients, Measurements, Billing Ledgers) into an Excel workbook for local storage and reporting.")

    with get_db() as conn:
        df_clients = pd.read_sql_query("SELECT * FROM clients", conn)
        df_measurements = pd.read_sql_query("SELECT * FROM measurements", conn)
        df_orders = pd.read_sql_query("""
            SELECT o.*, c.client_code, c.full_name as client_name, c.phone 
            FROM orders o JOIN clients c ON o.client_id = c.id
        """, conn)

    excel_buffer = io.BytesIO()
    with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
        df_clients.to_excel(writer, sheet_name='Clients', index=False)
        df_measurements.to_excel(writer, sheet_name='Measurements', index=False)
        df_orders.to_excel(writer, sheet_name='Orders_and_Billing', index=False)
    
    excel_data = excel_buffer.getvalue()
    today_str = datetime.date.today().strftime('%Y-%m-%d')
    st.download_button(
        label="Download Full Database as Excel (.xlsx)",
        data=excel_data,
        file_name=f"{BRAND_NAME.replace(' ', '_')}_Backup_{today_str}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True
    )

    st.markdown("---")

    # --- 4. TALLY PRIME SALES XML EXPORT ---
    st.markdown("### Tally Prime XML Integration (Direct Accounting Import)")
    st.write("Generate a Tally-compliant XML sales voucher file. You can import this file directly into **Tally Prime** via **Import > Transactions > XML**.")
    
    with st.form("tally_config_form"):
        t1, t2, t3 = st.columns(3)
        with t1:
            sales_ledger = st.text_input("Tally Sales Ledger Name", value=get_setting("tally_ledger", "Tailoring Sales"))
        with t2:
            cash_ledger = st.text_input("Tally Cash Ledger Name", value=get_setting("tally_cash_ledger", "Cash"))
        with t3:
            bank_ledger = st.text_input("Tally Bank Ledger Name", value=get_setting("tally_bank_ledger", "Bank Account"))
        
        save_tally = st.form_submit_button("Update Tally Ledger Names", use_container_width=True)
        if save_tally:
            set_setting("tally_ledger", sales_ledger.strip())
            set_setting("tally_cash_ledger", cash_ledger.strip())
            set_setting("tally_bank_ledger", bank_ledger.strip())
            st.success("Tally ledger configurations saved!")
            st.rerun()

    def build_tally_xml(orders_dataframe, sales_acc, cash_acc, bank_acc):
        xml = [
            '<ENVELOPE>',
            '  <HEADER>',
            '    <TALLYREQUEST>Import Data</TALLYREQUEST>',
            '  </HEADER>',
            '  <BODY>',
            '    <IMPORTDATA>',
            '      <REQUESTDESC>',
            '        <REPORTNAME>Vouchers</REPORTNAME>',
            '      </REQUESTDESC>',
            '      <REQUESTDATA>'
        ]
        
        for _, ord_row in orders_dataframe.iterrows():
            v_date = datetime.date.today().strftime('%Y%m%d')
            if ord_row['created_at']:
                try:
                    v_date = str(ord_row['created_at'])[:10].replace('-', '')
                except:
                    pass
                    
            total_val = float(ord_row['total_amount'] or 0.0)
            paid_val = float(ord_row['amount_paid'] or 0.0)
            client_party = str(ord_row['client_name']).replace('&', '&amp;').replace('<', '&lt;')
            ord_ref = str(ord_row['order_number'])
            pay_mode = str(ord_row['payment_mode'] or 'Cash')
            
            debit_ledger = cash_acc if 'Cash' in pay_mode else bank_acc

            xml.append('        <TALLYMESSAGE xmlns:UDF="TallyUDF">')
            xml.append(f'          <VOUCHER VCHTYPE="Sales" ACTION="Create">')
            xml.append(f'            <DATE>{v_date}</DATE>')
            xml.append(f'            <VOUCHERTYPENAME>Sales</VOUCHERTYPENAME>')
            xml.append(f'            <VOUCHERNUMBER>{ord_ref}</VOUCHERNUMBER>')
            xml.append(f'            <PARTYLEDGERNAME>{client_party}</PARTYLEDGERNAME>')
            xml.append(f'            <NARRATION>Bespoke order {ord_ref} ({ord_row["garment_type"]}) for {client_party}</NARRATION>')
            
            xml.append('            <ALLLEDGERENTRIES.LIST>')
            xml.append(f'              <LEDGERNAME>{client_party}</LEDGERNAME>')
            xml.append('              <ISDEEMEDPOSITIVE>Yes</ISDEEMEDPOSITIVE>')
            xml.append(f'              <AMOUNT>-{total_val:.2f}</AMOUNT>')
            xml.append('            </ALLLEDGERENTRIES.LIST>')
            
            xml.append('            <ALLLEDGERENTRIES.LIST>')
            xml.append(f'              <LEDGERNAME>{sales_acc}</LEDGERNAME>')
            xml.append('              <ISDEEMEDPOSITIVE>No</ISDEEMEDPOSITIVE>')
            xml.append(f'              <AMOUNT>{total_val:.2f}</AMOUNT>')
            xml.append('            </ALLLEDGERENTRIES.LIST>')
            xml.append('          </VOUCHER>')
            xml.append('        </TALLYMESSAGE>')

            if paid_val > 0:
                xml.append('        <TALLYMESSAGE xmlns:UDF="TallyUDF">')
                xml.append(f'          <VOUCHER VCHTYPE="Receipt" ACTION="Create">')
                xml.append(f'            <DATE>{v_date}</DATE>')
                xml.append(f'            <VOUCHERTYPENAME>Receipt</VOUCHERTYPENAME>')
                xml.append(f'            <VOUCHERNUMBER>RCT-{ord_ref}</VOUCHERNUMBER>')
                xml.append(f'            <PARTYLEDGERNAME>{client_party}</PARTYLEDGERNAME>')
                xml.append(f'            <NARRATION>Payment received via {pay_mode} for order {ord_ref}</NARRATION>')
                
                xml.append('            <ALLLEDGERENTRIES.LIST>')
                xml.append(f'              <LEDGERNAME>{debit_ledger}</LEDGERNAME>')
                xml.append('              <ISDEEMEDPOSITIVE>Yes</ISDEEMEDPOSITIVE>')
                xml.append(f'              <AMOUNT>-{paid_val:.2f}</AMOUNT>')
                xml.append('            </ALLLEDGERENTRIES.LIST>')
                
                xml.append('            <ALLLEDGERENTRIES.LIST>')
                xml.append(f'              <LEDGERNAME>{client_party}</LEDGERNAME>')
                xml.append('              <ISDEEMEDPOSITIVE>No</ISDEEMEDPOSITIVE>')
                xml.append(f'              <AMOUNT>{paid_val:.2f}</AMOUNT>')
                xml.append('            </ALLLEDGERENTRIES.LIST>')
                xml.append('          </VOUCHER>')
                xml.append('        </TALLYMESSAGE>')

        xml.append('      </REQUESTDATA>')
        xml.append('    </IMPORTDATA>')
        xml.append('  </BODY>')
        xml.append('</ENVELOPE>')
        return "\n".join(xml)

    if not df_orders.empty:
        tally_xml_string = build_tally_xml(
            df_orders, 
            get_setting("tally_ledger", "Tailoring Sales"),
            get_setting("tally_cash_ledger", "Cash"),
            get_setting("tally_bank_ledger", "Bank Account")
        )
        st.download_button(
            label="Export Sales & Receipts for Tally Prime (.xml)",
            data=tally_xml_string,
            file_name=f"Tally_Import_Vouchers_{today_str}.xml",
            mime="application/xml",
            use_container_width=True
        )
    else:
        st.info("No order transactions available to export to Tally.")
