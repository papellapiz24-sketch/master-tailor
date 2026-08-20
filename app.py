import sqlite3
import datetime
import hashlib
import streamlit as st
import pandas as pd

# ---------------------------------------------------------
# PAGE SETUP & HARMONIZED 5-COLOR SARTORIAL PALETTE
# ---------------------------------------------------------
st.set_page_config(
    page_title="Mohammad Hussain Atelier",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 5-Color Palette:
# 1. Canvas: #FAF7F2 (Warm Parchment)
# 2. Card/Surface: #FFFFFF (Crisp White)
# 3. Interactive/Buttons: #EAE0D0 (Sartorial Beige)
# 4. Text/Contrast: #111827 (Deep Ink Charcoal / Black)
# 5. Accent/Borders: #8C6D4F (Cognac Gold) & #C8B9A6 (Tailor Oat Border)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@700;800&family=Plus+Jakarta+Sans:wght@500;600;700;800&display=swap');

    /* 1. Global Canvas Background */
    .stApp {
        background-color: #FAF7F2 !important;
        background-image: radial-gradient(#D6C7B2 0.75px, transparent 0.75px), radial-gradient(#D6C7B2 0.75px, #FAF7F2 0.75px) !important;
        background-size: 20px 20px !important;
        background-position: 0 0, 10px 10px !important;
        color: #111827 !important;
        font-family: 'Plus Jakarta Sans', sans-serif !important;
    }

    /* 2. Global Universal Typography Color (Prevents Transparent / White-out Text) */
    p, span, label, h1, h2, h3, h4, h5, h6, [data-testid="stMarkdownContainer"] p {
        color: #111827 !important;
        font-family: 'Plus Jakarta Sans', sans-serif !important;
    }

    /* 3. Form Input Field Labels */
    label[data-testid="stWidgetLabel"] p {
        color: #111827 !important;
        font-weight: 800 !important;
        font-size: 1.05rem !important;
        margin-bottom: 4px !important;
    }

    /* 4. Complete Fix for Dropdowns, Selectboxes & Menus */
    div[data-baseweb="select"] {
        background-color: #FFFFFF !important;
        border: 1.5px solid #C8B9A6 !important;
        border-radius: 10px !important;
    }
    div[data-baseweb="select"] * {
        background-color: transparent !important;
        color: #111827 !important;
        font-weight: 700 !important;
    }
    /* Dropdown popover list items */
    ul[data-baseweb="menu"] {
        background-color: #FFFFFF !important;
        border: 1.5px solid #C8B9A6 !important;
    }
    ul[data-baseweb="menu"] li {
        background-color: #FFFFFF !important;
        color: #111827 !important;
        font-weight: 600 !important;
    }
    ul[data-baseweb="menu"] li:hover {
        background-color: #EAE0D0 !important;
        color: #111827 !important;
    }

    /* 5. Inputs, Number pickers & Textareas */
    .stTextInput input, .stNumberInput input, .stTextArea textarea, .stDateInput input {
        background-color: #FFFFFF !important;
        color: #111827 !important;
        font-weight: 700 !important;
        font-size: 1.05rem !important;
        border-radius: 10px !important;
        border: 1.5px solid #C8B9A6 !important;
    }
    .stTextInput input:focus, .stNumberInput input:focus, .stTextArea textarea:focus {
        border-color: #8C6D4F !important;
        box-shadow: 0 0 0 2px rgba(140, 109, 79, 0.2) !important;
    }

    /* 6. Form Surface Cards */
    div[data-testid="stForm"] {
        background: #FFFFFF !important;
        border: 2px solid #E5DCce !important;
        border-radius: 16px !important;
        padding: 2rem !important;
        box-shadow: 0 4px 16px rgba(0,0,0,0.03) !important;
    }

    /* 7. Extra-Large Sartorial Beige Action Buttons */
    .stButton>button {
        background: #EAE0D0 !important;
        color: #111827 !important;
        border: 2px solid #C8B9A6 !important;
        border-radius: 14px !important;
        min-height: 4.8rem !important;
        font-size: 1.15rem !important;
        font-weight: 800 !important;
        letter-spacing: 0.5px !important;
        box-shadow: 0 4px 10px rgba(0,0,0,0.04) !important;
        transition: all 0.2s ease-in-out !important;
        margin-bottom: 0.6rem !important;
    }
    .stButton>button:hover {
        background: #DFD3C0 !important;
        border-color: #8C6D4F !important;
        color: #000000 !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 18px rgba(0,0,0,0.08) !important;
    }

    /* 8. Title Badges & Metrics */
    .section-title-btn {
        background: #EAE0D0;
        color: #111827 !important;
        border: 2px solid #C8B9A6;
        padding: 0.7rem 1.6rem;
        border-radius: 12px;
        font-size: 1.25rem;
        font-weight: 800;
        letter-spacing: 1px;
        display: inline-block;
        margin: 1.2rem 0 1rem 0;
        box-shadow: 0 3px 8px rgba(0,0,0,0.04);
    }

    div[data-testid="stMetric"] {
        background: #FFFFFF !important;
        border: 2px solid #E5DCCE !important;
        padding: 1.4rem !important;
        border-radius: 14px !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.03) !important;
    }
    div[data-testid="stMetric"] label {
        color: #6B5E51 !important;
        font-weight: 700 !important;
        font-size: 1rem !important;
    }
    div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
        color: #111827 !important;
        font-weight: 800 !important;
        font-size: 2.2rem !important;
    }

    /* 9. Sidebar */
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
        min-height: 3.2rem !important;
    }
    section[data-testid="stSidebar"] .stButton>button:hover {
        background: #4A423D !important;
        border-color: #D6C7B2 !important;
    }

    /* 10. Brand Headers */
    .brand-title {
        font-family: 'Cinzel', serif !important;
        font-size: 3.2rem;
        font-weight: 800;
        color: #111827 !important;
        text-align: center;
        letter-spacing: 2px;
        margin-bottom: 0.1rem;
    }
    .brand-tagline {
        text-align: center;
        color: #8C6D4F !important;
        font-size: 1.05rem;
        letter-spacing: 3px;
        text-transform: uppercase;
        margin-bottom: 2rem;
        font-weight: 700;
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# DATABASE ENGINE
# ---------------------------------------------------------
DB_FILE = "master_tailor.db"

def get_db():
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def hash_pw(password):
    return hashlib.sha256(password.encode()).hexdigest()

def init_db():
    with get_db() as conn:
        cursor = conn.cursor()
        
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
            revision_label TEXT NOT NULL,
            unit TEXT CHECK(unit IN ('Inches', 'Centimeters')) NOT NULL DEFAULT 'Inches',
            date_recorded DATE NOT NULL,
            neck REAL, chest_full REAL, chest_upper REAL, waist_stomach REAL,
            cross_shoulder REAL, back_width REAL, front_chest_width REAL,
            armhole REAL, bicep REAL, wrist REAL,
            sleeve_length REAL, nape_to_waist REAL, full_length_jacket REAL,
            trouser_waist REAL, seat_hip REAL, thigh REAL, knee REAL,
            calf REAL, bottom_opening REAL, outseam REAL, inseam REAL,
            front_rise REAL, crotch_depth REAL,
            kurta_length REAL, sherwani_length REAL, churidar_length REAL,
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
            payment_status TEXT DEFAULT 'Due',
            delivery_date DATE,
            workflow_status TEXT DEFAULT 'Drafted',
            fitting_remarks TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (client_id) REFERENCES clients (id),
            FOREIGN KEY (measurement_id) REFERENCES measurements (id)
        );
        """)
        
        # Self-healing migration
        cursor.execute("PRAGMA table_info(orders);")
        existing_cols = [row[1] for row in cursor.fetchall()]
        
        col_patches = {
            "total_amount": "ALTER TABLE orders ADD COLUMN total_amount REAL DEFAULT 0.0;",
            "amount_paid": "ALTER TABLE orders ADD COLUMN amount_paid REAL DEFAULT 0.0;",
            "payment_status": "ALTER TABLE orders ADD COLUMN payment_status TEXT DEFAULT 'Due';",
            "workflow_status": "ALTER TABLE orders ADD COLUMN workflow_status TEXT DEFAULT 'Drafted';"
        }
        for col_name, sql_stmt in col_patches.items():
            if col_name not in existing_cols:
                try:
                    cursor.execute(sql_stmt)
                except Exception:
                    pass

        conn.commit()

init_db()

# ---------------------------------------------------------
# AUTHENTICATION STATE
# ---------------------------------------------------------
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "username" not in st.session_state:
    st.session_state.username = ""
if "current_page" not in st.session_state:
    st.session_state.current_page = "Dashboard"

def set_page(page_name):
    st.session_state.current_page = page_name

# ---------------------------------------------------------
# SIGN IN & SIGN UP (MOHAMMAD HUSSAIN)
# ---------------------------------------------------------
if not st.session_state.authenticated:
    st.markdown("<div class='brand-title'>MOHAMMAD HUSSAIN</div>", unsafe_allow_html=True)
    st.markdown("<div class='brand-tagline'>Bespoke Master Tailoring Atelier</div>", unsafe_allow_html=True)
    
    col_center = st.columns([1, 1.8, 1])[1]
    with col_center:
        auth_tab = st.radio("Atelier Portal Access", ["Sign In", "Create Tailor Account"], horizontal=True)
        
        if auth_tab == "Sign In":
            with st.form("signin_form"):
                st.subheader("Master Tailor Sign In")
                u_name = st.text_input("Username")
                p_word = st.text_input("Password", type="password")
                btn_login = st.form_submit_button("Sign In to Workshop", use_container_width=True)
                
                if btn_login:
                    if not u_name or not p_word:
                        st.error("Please enter both username and password.")
                    else:
                        with get_db() as conn:
                            user = conn.cursor().execute(
                                "SELECT * FROM users WHERE username = ? AND password_hash = ?", 
                                (u_name.strip(), hash_pw(p_word))
                            ).fetchone()
                            
                            if user:
                                st.session_state.authenticated = True
                                st.session_state.username = u_name
                                st.rerun()
                            else:
                                st.error("Invalid credentials.")
        else:
            with st.form("signup_form"):
                st.subheader("New Tailor Registration")
                new_user = st.text_input("Choose Username*")
                new_pass = st.text_input("Create Password*", type="password")
                btn_signup = st.form_submit_button("Register Account", use_container_width=True)
                
                if btn_signup:
                    if not new_user or not new_pass:
                        st.error("Fields cannot be empty.")
                    else:
                        try:
                            with get_db() as conn:
                                conn.cursor().execute(
                                    "INSERT INTO users (username, password_hash) VALUES (?, ?)",
                                    (new_user.strip(), hash_pw(new_pass))
                                )
                                conn.commit()
                            st.success("Account created! Switch to 'Sign In' above to login.")
                        except sqlite3.IntegrityError:
                            st.error("Username already registered.")
    st.stop()

# ---------------------------------------------------------
# SIDEBAR NAVIGATION
# ---------------------------------------------------------
st.sidebar.markdown("## ✂️ **Mohammad Hussain**")
st.sidebar.caption(f"Master Tailor: **{st.session_state.username}**")
st.sidebar.markdown("---")

nav_options = [
    "🏠 Main Hub",
    "👤 Register Client",
    "📏 Record Measurements",
    "🗂️ View Client Records",
    "➕ Create New Order",
    "🔄 Update Orders & Fitting"
]

selected_sidebar = st.sidebar.radio("Atelier Menu", nav_options)

page_map = {
    "🏠 Main Hub": "Dashboard",
    "👤 Register Client": "New Client",
    "📏 Record Measurements": "New Measurement",
    "🗂️ View Client Records": "Client Records",
    "➕ Create New Order": "New Order",
    "🔄 Update Orders & Fitting": "Update Orders"
}
st.session_state.current_page = page_map[selected_sidebar]

st.sidebar.markdown("---")
if st.sidebar.button("🚪 Logout", use_container_width=True):
    st.session_state.authenticated = False
    st.session_state.username = ""
    st.rerun()

# ---------------------------------------------------------
# 1. MAIN HUB (DEDICATED ACTION PANELS)
# ---------------------------------------------------------
if st.session_state.current_page == "Dashboard":
    st.markdown("<div class='brand-title'>MOHAMMAD HUSSAIN</div>", unsafe_allow_html=True)
    st.markdown("<div class='brand-tagline'>Master Tailoring & Client Workshop Hub</div>", unsafe_allow_html=True)
    
    with get_db() as conn:
        total_clients = conn.cursor().execute("SELECT COUNT(*) FROM clients").fetchone()[0]
        active_orders = conn.cursor().execute("SELECT COUNT(*) FROM orders WHERE workflow_status != 'Delivered'").fetchone()[0]
        unpaid_count = conn.cursor().execute("SELECT COUNT(*) FROM orders WHERE payment_status IN ('Due', 'Advance Paid', 'Half Paid')").fetchone()[0]

    c1, c2, c3 = st.columns(3)
    c1.metric("👥 Client Profiles", f"{total_clients}")
    c2.metric("🧵 In Production", f"{active_orders}")
    c3.metric("💳 Payments Due", f"{unpaid_count}")
    
    st.markdown("<div class='section-title-btn'>⚡ Atelier Action Centre</div>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("👤  REGISTER NEW CLIENT\n\nAdd client profile, posture observations & shoulder asymmetries", use_container_width=True):
            set_page("New Client")
            st.rerun()
            
        if st.button("📏  RECORD CLIENT MEASUREMENTS\n\nTake complete body dimensions across Western & Indian garments", use_container_width=True):
            set_page("New Measurement")
            st.rerun()
            
        if st.button("🗂️  VIEW CLIENT DATABASE & HISTORY\n\nInspect client measurements, past orders & revision history", use_container_width=True):
            set_page("Client Records")
            st.rerun()

    with col2:
        if st.button("➕  CREATE NEW GARMENT ORDER\n\nSet garment, fabrics, price, advance & payment stage", use_container_width=True):
            set_page("New Order")
            st.rerun()
            
        if st.button("🔄  ORDER STATUS & PAYMENT UPDATER\n\nTrack Due/Half/Full payments, fittings & delivery stage", use_container_width=True):
            set_page("Update Orders")
            st.rerun()

# ---------------------------------------------------------
# 2. REGISTER NEW CLIENT
# ---------------------------------------------------------
elif st.session_state.current_page == "New Client":
    st.markdown("<div class='section-title-btn'>👤 Register New Client Profile</div>", unsafe_allow_html=True)
    if st.button("← Back to Hub", use_container_width=False):
        set_page("Dashboard")
        st.rerun()
        
    with st.form("new_client_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            client_code = st.text_input("Client ID / Phone Number*", placeholder="e.g., MH-2026-001")
            full_name = st.text_input("Full Name*")
            phone = st.text_input("Contact Number*")
            email = st.text_input("Email (Optional)")
        with c2:
            posture_notes = st.text_area("Posture Observations", placeholder="e.g., Erect stance, forward sloping shoulders, swayback...")
            asymmetry_notes = st.text_area("Asymmetry Notes", placeholder="e.g., Right shoulder 0.5 in lower, right arm 0.25 in longer...")
        
        submitted = st.form_submit_button("Save Client Profile", use_container_width=True)
        if submitted:
            if not client_code or not full_name or not phone:
                st.error("Please fill in Client ID, Full Name, and Contact Number.")
            else:
                try:
                    with get_db() as conn:
                        conn.cursor().execute("""
                        INSERT INTO clients (client_code, full_name, phone, email, posture_notes, asymmetry_notes)
                        VALUES (?, ?, ?, ?, ?, ?)
                        """, (client_code.strip(), full_name.strip(), phone.strip(), email.strip(), posture_notes, asymmetry_notes))
                        conn.commit()
                    st.success(f"Client '{full_name}' recorded successfully!")
                except sqlite3.IntegrityError:
                    st.error("Client ID already exists. Please use a unique identifier.")

# ---------------------------------------------------------
# 3. RECORD MEASUREMENTS
# ---------------------------------------------------------
elif st.session_state.current_page == "New Measurement":
    st.markdown("<div class='section-title-btn'>📏 Record Dated Client Measurements</div>", unsafe_allow_html=True)
    if st.button("← Back to Hub", use_container_width=False):
        set_page("Dashboard")
        st.rerun()
        
    with get_db() as conn:
        clients = conn.cursor().execute("SELECT id, client_code, full_name FROM clients ORDER BY full_name").fetchall()
    
    if not clients:
        st.warning("Register a client first before taking measurements.")
    else:
        client_dict = {f"{c['client_code']} — {c['full_name']}": c['id'] for c in clients}
        selected_client_label = st.selectbox("Select Client", list(client_dict.keys()))
        selected_client_id = client_dict[selected_client_label]
        
        with st.form("measurement_form"):
            h1, h2, h3 = st.columns(3)
            with h1:
                rev_label = st.text_input("Session / Revision Tag*", value="Revision 01")
            with h2:
                rec_date = st.date_input("Date Taken", datetime.date.today())
            with h3:
                unit = st.selectbox("Measurement Unit", ["Inches", "Centimeters"])
            
            st.markdown("<div class='section-title-btn'>1. Upper Body Dimensions</div>", unsafe_allow_html=True)
            u1, u2, u3, u4 = st.columns(4)
            with u1:
                neck = st.number_input("Neck", min_value=0.0, step=0.25)
                chest_full = st.number_input("Chest (Full)", min_value=0.0, step=0.25)
                chest_upper = st.number_input("Upper Chest", min_value=0.0, step=0.25)
            with u2:
                waist_stomach = st.number_input("Stomach / Waist", min_value=0.0, step=0.25)
                cross_shoulder = st.number_input("Shoulder Width", min_value=0.0, step=0.25)
                back_width = st.number_input("Back Width", min_value=0.0, step=0.25)
            with u3:
                front_chest_width = st.number_input("Front Chest Width", min_value=0.0, step=0.25)
                armhole = st.number_input("Armhole", min_value=0.0, step=0.25)
                bicep = st.number_input("Bicep", min_value=0.0, step=0.25)
            with u4:
                wrist = st.number_input("Wrist", min_value=0.0, step=0.25)
                sleeve_length = st.number_input("Sleeve Length", min_value=0.0, step=0.25)
                full_length_jacket = st.number_input("Jacket Length", min_value=0.0, step=0.25)
                nape_to_waist = st.number_input("Nape to Waist", min_value=0.0, step=0.25)

            st.markdown("<div class='section-title-btn'>2. Lower Body Dimensions</div>", unsafe_allow_html=True)
            l1, l2, l3, l4 = st.columns(4)
            with l1:
                trouser_waist = st.number_input("Trouser Waist", min_value=0.0, step=0.25)
                seat_hip = st.number_input("Seat / Hip", min_value=0.0, step=0.25)
            with l2:
                thigh = st.number_input("Thigh", min_value=0.0, step=0.25)
                knee = st.number_input("Knee", min_value=0.0, step=0.25)
            with l3:
                calf = st.number_input("Calf", min_value=0.0, step=0.25)
                bottom_opening = st.number_input("Bottom Opening", min_value=0.0, step=0.25)
            with l4:
                outseam = st.number_input("Outseam", min_value=0.0, step=0.25)
                inseam = st.number_input("Inseam", min_value=0.0, step=0.25)
                front_rise = st.number_input("Front Rise", min_value=0.0, step=0.25)
                crotch_depth = st.number_input("Crotch Depth", min_value=0.0, step=0.25)

            st.markdown("<div class='section-title-btn'>3. Indian Traditional Specifics</div>", unsafe_allow_html=True)
            t1, t2, t3 = st.columns(3)
            with t1:
                kurta_length = st.number_input("Kurta Length", min_value=0.0, step=0.25)
            with t2:
                sherwani_length = st.number_input("Sherwani Length", min_value=0.0, step=0.25)
            with t3:
                churidar_length = st.number_input("Churidar Total Length", min_value=0.0, step=0.25)

            m_notes = st.text_area("Measurement Session Notes")

            save_m = st.form_submit_button("Save Measurements", use_container_width=True)
            if save_m:
                with get_db() as conn:
                    conn.cursor().execute("""
                    INSERT INTO measurements (
                        client_id, revision_label, unit, date_recorded,
                        neck, chest_full, chest_upper, waist_stomach, cross_shoulder, back_width,
                        front_chest_width, armhole, bicep, wrist, sleeve_length, nape_to_waist,
                        full_length_jacket, trouser_waist, seat_hip, thigh, knee, calf,
                        bottom_opening, outseam, inseam, front_rise, crotch_depth,
                        kurta_length, sherwani_length, churidar_length, notes
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        selected_client_id, rev_label, unit, rec_date,
                        neck, chest_full, chest_upper, waist_stomach, cross_shoulder, back_width,
                        front_chest_width, armhole, bicep, wrist, sleeve_length, nape_to_waist,
                        full_length_jacket, trouser_waist, seat_hip, thigh, knee, calf,
                        bottom_opening, outseam, inseam, front_rise, crotch_depth,
                        kurta_length, sherwani_length, churidar_length, m_notes
                    ))
                    conn.commit()
                st.success(f"Measurements saved for {selected_client_label} on {rec_date}!")

# ---------------------------------------------------------
# 4. VIEW CLIENT RECORDS
# ---------------------------------------------------------
elif st.session_state.current_page == "Client Records":
    st.markdown("<div class='section-title-btn'>🗂️ Client Database & Historical Records</div>", unsafe_allow_html=True)
    if st.button("← Back to Hub", use_container_width=False):
        set_page("Dashboard")
        st.rerun()
        
    with get_db() as conn:
        clients_df = pd.read_sql_query("SELECT id, client_code, full_name, phone, posture_notes, asymmetry_notes FROM clients ORDER BY full_name", conn)
        
    if not clients_df.empty:
        search = st.text_input("🔍 Search Client by Name or Phone Number")
        if search:
            clients_df = clients_df[clients_df.apply(lambda row: search.lower() in row.astype(str).str.lower().values, axis=1)]
            
        st.dataframe(clients_df, use_container_width=True)
        
        st.markdown("<div class='section-title-btn'>Historical Measurement Log</div>", unsafe_allow_html=True)
        client_options = {f"{r['client_code']} — {r['full_name']}": r['id'] for _, r in clients_df.iterrows()}
        if client_options:
            inspect_id = st.selectbox("Select Client", list(client_options.keys()))
            cid = client_options[inspect_id]
            
            with get_db() as conn:
                history_df = pd.read_sql_query("SELECT * FROM measurements WHERE client_id = ? ORDER BY date_recorded DESC", conn, params=(cid,))
            
            if not history_df.empty:
                st.dataframe(history_df, use_container_width=True)
            else:
                st.info("No measurements recorded yet for this client.")
    else:
        st.info("No client records found.")

# ---------------------------------------------------------
# 5. CREATE NEW GARMENT ORDER
# ---------------------------------------------------------
elif st.session_state.current_page == "New Order":
    st.markdown("<div class='section-title-btn'>➕ Create New Garment Order</div>", unsafe_allow_html=True)
    if st.button("← Back to Hub", use_container_width=False):
        set_page("Dashboard")
        st.rerun()
        
    with get_db() as conn:
        clients = conn.cursor().execute("SELECT id, client_code, full_name FROM clients ORDER BY full_name").fetchall()
        
    if not clients:
        st.warning("Please register a client before creating orders.")
    else:
        client_dict = {f"{c['client_code']} — {c['full_name']}": c['id'] for c in clients}
        selected_client_label = st.selectbox("Client", list(client_dict.keys()))
        selected_client_id = client_dict[selected_client_label]
        
        with get_db() as conn:
            revisions = conn.cursor().execute(
                "SELECT id, revision_label, date_recorded FROM measurements WHERE client_id = ? ORDER BY id DESC", 
                (selected_client_id,)
            ).fetchall()
            
        if not revisions:
            st.error("No measurement sets found for this client. Please take measurements first.")
        else:
            rev_dict = {f"{r['revision_label']} ({r['date_recorded']})": r['id'] for r in revisions}
            
            with st.form("new_order_form"):
                o1, o2 = st.columns(2)
                with o1:
                    order_no = st.text_input("Order Reference ID*", value=f"MH-{datetime.date.today().strftime('%Y%m%d')}-01")
                    selected_rev = st.selectbox("Cutting Measurement Revision*", list(rev_dict.keys()))
                    garment_type = st.selectbox("Garment", [
                        "Two-Piece Suit", "Three-Piece Suit", "Blazer", "Dress Trousers",
                        "Dress Shirt", "Kurta Pajama", "Nehru Jacket", "Bandhgala Suit",
                        "Sherwani / Achkan", "Pathani Suit"
                    ])
                    fit_preference = st.selectbox("Fit Preference", ["Slim Fit", "Regular Fit", "Relaxed Fit", "Traditional Loose"])
                with o2:
                    total_amount = st.number_input("Total Garment Price (₹)", min_value=0.0, step=500.0)
                    amount_paid = st.number_input("Initial Amount Received (₹)", min_value=0.0, step=500.0)
                    
                    auto_status = "Due"
                    if amount_paid >= total_amount and total_amount > 0:
                        auto_status = "Fully Paid"
                    elif amount_paid == (total_amount / 2) and total_amount > 0:
                        auto_status = "Half Paid"
                    elif amount_paid > 0:
                        auto_status = "Advance Paid"
                        
                    payment_status = st.selectbox("Payment Status*", ["Due", "Advance Paid", "Half Paid", "Fully Paid"], index=["Due", "Advance Paid", "Half Paid", "Fully Paid"].index(auto_status))
                    delivery_date = st.date_input("Target Delivery Date", datetime.date.today() + datetime.timedelta(days=12))

                fabric_details = st.text_area("Fabric Specifications & Mill Details", placeholder="e.g., Loro Piana 260 GSM Worsted Navy Wool...")
                remarks = st.text_area("Specific Cutting / Fitting Requirements")
                
                place_order = st.form_submit_button("Submit Garment Order", use_container_width=True)
                if place_order:
                    with get_db() as conn:
                        conn.cursor().execute("""
                        INSERT INTO orders (
                            order_number, client_id, measurement_id, garment_type, fit_preference, 
                            fabric_details, total_amount, amount_paid, payment_status, delivery_date, fitting_remarks
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            order_no, selected_client_id, rev_dict[selected_rev], garment_type, fit_preference,
                            fabric_details, total_amount, amount_paid, payment_status, delivery_date, remarks
                        ))
                        conn.commit()
                    st.success(f"Order {order_no} created successfully under Mohammad Hussain Atelier!")

# ---------------------------------------------------------
# 6. DEDICATED ORDER & PAYMENT WORKFLOW UPDATER
# ---------------------------------------------------------
elif st.session_state.current_page == "Update Orders":
    st.markdown("<div class='section-title-btn'>🔄 Order Status & Payment Workflow Updater</div>", unsafe_allow_html=True)
    if st.button("← Back to Hub", use_container_width=False):
        set_page("Dashboard")
        st.rerun()
        
    with get_db() as conn:
        orders_df = pd.read_sql_query("""
        SELECT o.id, o.order_number, c.full_name as client_name, c.phone, o.garment_type, 
               o.workflow_status, o.payment_status, o.total_amount, o.amount_paid,
               (o.total_amount - o.amount_paid) as balance_due,
               o.delivery_date, o.fabric_details, o.fitting_remarks
        FROM orders o
        JOIN clients c ON o.client_id = c.id
        ORDER BY o.delivery_date ASC
        """, conn)
        
    if orders_df.empty:
        st.info("No active garment orders found.")
    else:
        st.dataframe(orders_df, use_container_width=True)
        
        st.markdown("<div class='section-title-btn'>Update Order, Payment & Fitting Remarks</div>", unsafe_allow_html=True)
        
        order_list = orders_df["order_number"].tolist()
        selected_order_no = st.selectbox("Select Order Reference", order_list)
        
        current_order = orders_df[orders_df["order_number"] == selected_order_no].iloc[0]
        
        total_p = current_order['total_amount'] or 0.0
        paid_p = current_order['amount_paid'] or 0.0
        balance_p = total_p - paid_p
        
        st.info(f"💰 **Total Price:** ₹{total_p:,.2f} | **Paid so far:** ₹{paid_p:,.2f} | **Balance Due:** ₹{balance_p:,.2f}")
        
        with st.form("update_order_workflow_form"):
            u1, u2, u3 = st.columns(3)
            
            with u1:
                stages = ['Drafted', 'Fabric Cut', 'Basted Fitting', 'Alterations', 'Final Pressed', 'Delivered']
                cur_stage_idx = stages.index(current_order['workflow_status']) if current_order['workflow_status'] in stages else 0
                new_stage = st.selectbox("Garment Workflow Stage", stages, index=cur_stage_idx)
                
            with u2:
                payment_statuses = ["Due", "Advance Paid", "Half Paid", "Fully Paid"]
                cur_pay_idx = payment_statuses.index(current_order['payment_status']) if current_order['payment_status'] in payment_statuses else 0
                new_pay_status = st.selectbox("Payment Status", payment_statuses, index=cur_pay_idx)
                
            with u3:
                additional_received = st.number_input("Add Payment Received (₹)", min_value=0.0, step=500.0)
                
            col_date, col_dummy = st.columns(2)
            with col_date:
                try:
                    default_date = datetime.datetime.strptime(str(current_order['delivery_date']), '%Y-%m-%d').date()
                except Exception:
                    default_date = datetime.date.today()
                new_delivery = st.date_input("Update Delivery Target", default_date)
            
            st.markdown(f"**Current Fitting Log:** `{current_order['fitting_remarks'] or 'No remarks recorded.'}`")
            new_fitting_note = st.text_area("Append Fitting Notes / Adjustments", placeholder="e.g., First fitting: take in waist by 0.5 in, raise armhole 1/4 in.")
            
            update_btn = st.form_submit_button("Save Updates", use_container_width=True)
            if update_btn:
                updated_paid = paid_p + additional_received
                
                if updated_paid >= total_p and total_p > 0:
                    new_pay_status = "Fully Paid"
                elif updated_paid == (total_p / 2) and total_p > 0:
                    new_pay_status = "Half Paid"
                    
                appended_remarks = current_order['fitting_remarks'] or ""
                if new_fitting_note.strip():
                    appended_remarks = f"{appended_remarks} | [{datetime.date.today()}] {new_fitting_note.strip()}"
                    
                with get_db() as conn:
                    conn.cursor().execute("""
                    UPDATE orders 
                    SET workflow_status = ?, 
                        payment_status = ?,
                        amount_paid = ?,
                        delivery_date = ?,
                        fitting_remarks = ?
                    WHERE order_number = ?
                    """, (new_stage, new_pay_status, updated_paid, new_delivery, appended_remarks, selected_order_no))
                    conn.commit()
                    
                st.success(f"Order {selected_order_no} updated successfully!")
                st.rerun()
