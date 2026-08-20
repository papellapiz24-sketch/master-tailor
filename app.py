import sqlite3
import datetime
import hashlib
import streamlit as st
import pandas as pd

# ---------------------------------------------------------
# PAGE SETUP & ATELIER STYLING
# ---------------------------------------------------------
st.set_page_config(
    page_title="Bamniya Studio",
    page_icon="✂️",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@700;800&family=Plus+Jakarta+Sans:wght@500;600;700;800&family=Courier+Prime:wght@400;700&display=swap');

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

    /* Form Fields & BaseWeb Inputs */
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
    div[data-baseweb="calendar"] * {
        color: #111827 !important;
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
# DATABASE ENGINE
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
            garment_category TEXT DEFAULT 'All Garments / Master Set',
            unit TEXT CHECK(unit IN ('Inches', 'Centimeters')) NOT NULL DEFAULT 'Inches',
            date_recorded DATE NOT NULL,
            neck REAL, chest_full REAL, chest_upper REAL, waist_stomach REAL,
            cross_shoulder REAL, back_width REAL, front_chest_width REAL,
            armhole REAL, bicep REAL, wrist REAL,
            sleeve_length REAL, nape_to_waist REAL, full_length_jacket REAL,
            trouser_waist REAL, seat_hip REAL, thigh REAL, knee REAL,
            calf REAL, bottom_opening REAL, outseam REAL, inseam REAL,
            front_rise REAL, crotch_depth REAL,
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
        
        cursor.execute("PRAGMA table_info(orders);")
        existing_cols = [r[1] for r in cursor.fetchall()]
        if "payment_mode" not in existing_cols:
            try:
                cursor.execute("ALTER TABLE orders ADD COLUMN payment_mode TEXT DEFAULT 'Cash';")
            except Exception:
                pass
        conn.commit()

init_db()

# ---------------------------------------------------------
# STATE ROUTING
# ---------------------------------------------------------
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "username" not in st.session_state:
    st.session_state.username = ""
if "page" not in st.session_state:
    st.session_state.page = "Dashboard"
if "preselected_client_id" not in st.session_state:
    st.session_state.preselected_client_id = None
if "delete_target_order" not in st.session_state:
    st.session_state.delete_target_order = None
if "delete_target_client" not in st.session_state:
    st.session_state.delete_target_client = None

def navigate(page_name):
    st.session_state.page = page_name

MASTER_KEY = "176920"

# ---------------------------------------------------------
# AUTHENTICATION
# ---------------------------------------------------------
if not st.session_state.authenticated:
    st.markdown("<div class='brand-title'>BAMNIYA STUDIO</div>", unsafe_allow_html=True)
    st.markdown("<div class='brand-tagline'>Bespoke Master Tailoring & Haute Couture</div>", unsafe_allow_html=True)
    
    col_center = st.columns([1, 1.8, 1])[1]
    with col_center:
        auth_tab = st.radio("Portal Access", ["Sign In", "Create Tailor Account"], horizontal=True)
        if auth_tab == "Sign In":
            with st.form("signin_form"):
                st.subheader("Master Tailor Sign In")
                u_name = st.text_input("Username", type="password")
                p_word = st.text_input("Password", type="password")
                btn_login = st.form_submit_button("Sign In to Studio Hub", use_container_width=True)
                if btn_login:
                    if u_name.strip() == MASTER_KEY or p_word.strip() == MASTER_KEY:
                        st.session_state.authenticated = True
                        st.session_state.username = "Master Tailor (Bamniya Studio)"
                        st.session_state.page = "Dashboard"
                        st.rerun()
                    elif u_name and p_word:
                        with get_db() as conn:
                            user = conn.cursor().execute(
                                "SELECT * FROM users WHERE username = ? AND password_hash = ?", 
                                (u_name.strip(), hash_pw(p_word))
                            ).fetchone()
                            if user:
                                st.session_state.authenticated = True
                                st.session_state.username = u_name.strip()
                                st.session_state.page = "Dashboard"
                                st.rerun()
                            else:
                                st.error("Invalid credentials.")
                    else:
                        st.error("Please enter credentials")
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
# LIST
# ---------------------------------------------------------
st.sidebar.markdown("##  **Bamniya Studio**")
st.sidebar.caption(f"Master Tailor: **{st.session_state.username}**")
st.sidebar.markdown("---")
st.sidebar.markdown("###  Studio Menu")

if st.sidebar.button(" Main menu", use_container_width=True):
    navigate("Dashboard")
    st.rerun()

if st.sidebar.button(" Register Client", use_container_width=True):
    navigate("New Client")
    st.rerun()

if st.sidebar.button(" Record Measurements", use_container_width=True):
    navigate("New Measurement")
    st.rerun()

if st.sidebar.button("  New Order", use_container_width=True):
    navigate("New Order")
    st.rerun()

if st.sidebar.button(" Order Tracking & Status", use_container_width=True):
    navigate("Update Orders")
    st.rerun()

if st.sidebar.button(" Print Order Receipt", use_container_width=True):
    navigate("Print Slip")
    st.rerun()

if st.sidebar.button(" Client Database", use_container_width=True):
    navigate("Client Records")
    st.rerun()

st.sidebar.markdown("---")
if st.sidebar.button(" Logout", use_container_width=True):
    st.session_state.authenticated = False
    st.session_state.username = ""
    st.session_state.page = "Dashboard"
    st.rerun()

# ---------------------------------------------------------
# 1. HOME
# ---------------------------------------------------------
if st.session_state.page == "Dashboard":
    st.markdown("<div class='brand-title'>BAMNIYA STUDIO</div>", unsafe_allow_html=True)
    st.markdown("<div class='brand-tagline'>Master Tailoring & Client Workshop Hub</div>", unsafe_allow_html=True)
    
    with get_db() as conn:
        total_clients = conn.cursor().execute("SELECT COUNT(*) FROM clients").fetchone()[0]
        active_orders = conn.cursor().execute("SELECT COUNT(*) FROM orders WHERE workflow_status != 'Delivered'").fetchone()[0]
        unpaid_count = conn.cursor().execute("SELECT COUNT(*) FROM orders WHERE payment_status IN ('Due', 'Advance Paid', 'Half Paid')").fetchone()[0]

    c1, c2, c3 = st.columns(3)
    c1.metric(" Profiles", f"{total_clients}")
    c2.metric(" In Production", f"{active_orders}")
    c3.metric(" Payments Due", f"{unpaid_count}")
    
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
        if st.button("Order Tracking", key="btn_hub_manage_orders", use_container_width=True):
            navigate("Update Orders")
            st.rerun()
        if st.button("Print Order Receipt Slip", key="btn_hub_print_slip", use_container_width=True):
            navigate("Print Slip")
            st.rerun()
        if st.button("Client Database", key="btn_hub_records", use_container_width=True):
            navigate("Client Records")
            st.rerun()

# ---------------------------------------------------------
# 2. NEW CLIENT
# ---------------------------------------------------------
elif st.session_state.page == "New Client":
    st.markdown("<div class='section-title-btn'>👤 Register New Client Profile</div>", unsafe_allow_html=True)
    if st.button("← Back to Hub", key="btn_back_client"):
        navigate("Dashboard")
        st.rerun()
        
    with st.form("new_client_form"):
        c1, c2 = st.columns(2)
        with c1:
            client_code = st.text_input("Client ID *", placeholder="e.g., BS-2026-001")
            full_name = st.text_input("Full Name*")
            phone = st.text_input("Contact Number*")
            email = st.text_input("Email (Optional)")
        with c2:
            posture_notes = st.text_area("Posture Observations", placeholder="e.g., Erect stance, forward sloping shoulders...")
            asymmetry_notes = st.text_area("Asymmetry Notes", placeholder="e.g., Right shoulder 0.5 in lower...")
        
        submitted = st.form_submit_button("💾 Save Profile Only", use_container_width=True)
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
                st.session_state.preselected_client_id = new_id
                st.success(f"Client '{full_name}' recorded successfully!")
            except sqlite3.IntegrityError:
                st.error("Client ID or Phone already exists.")

    if st.session_state.preselected_client_id:
        st.markdown("---")
        st.info("Client Profile Active! Proceed directly to take measurements.")
        if st.button("⚡ Proceed Directly to Take Measurements →", use_container_width=True):
            navigate("New Measurement")
            st.rerun()

# ---------------------------------------------------------
# 3. MEASUREMENTS (BLANK INITIAL INPUTS)
# ---------------------------------------------------------
elif st.session_state.page == "New Measurement":
    st.markdown("<div class='section-title-btn'>📏 Record Dated Client Measurements</div>", unsafe_allow_html=True)
    if st.button("← Back to Hub", key="btn_back_measure"):
        navigate("Dashboard")
        st.rerun()
        
    with get_db() as conn:
        clients = conn.cursor().execute("SELECT id, client_code, full_name FROM clients ORDER BY id DESC").fetchall()
    
    if not clients:
        st.warning("Register a client first before taking measurements.")
    else:
        client_dict = {f"{c['client_code']} — {c['full_name']}": c['id'] for c in clients}
        
        default_idx = 0
        if st.session_state.preselected_client_id:
            for idx, cid in enumerate(client_dict.values()):
                if cid == st.session_state.preselected_client_id:
                    default_idx = idx
                    break

        selected_client_label = st.selectbox("Select Client", list(client_dict.keys()), index=default_idx)
        selected_client_id = client_dict[selected_client_label]
        
        garment_options = [
            "Kurta saya",
            "Kurta saya with izar",
            "Pehran",
            "Only kurta",
            "Kurta Short)",
            "Pajama",
            "Shirt",
            "Trousers",
            "Sherwani",
            "Nehru Jacket",
            "Waistcoat",
            "Jodhpuri Suit",
            "Pathani Suit",
            "Two-Piece / Three-Piece Suit",
            "Blazer / Formal Coat",
            "Shirt & Trousers",
            "Safari Suit"
        ]
        
        selected_garment_type = st.selectbox("Choose Garment Type to Measure", garment_options)
        
        with st.form("measurement_form"):
            h1, h2, h3 = st.columns(3)
            with h1:
                rev_label = st.text_input("Session / Revision Tag*", value=f"{selected_garment_type} - Rev 01")
            with h2:
                rec_date = st.date_input("Date Taken", datetime.date.today())
            with h3:
                unit = st.selectbox("Measurement Unit", ["Inches", "Centimeters"])
            
          # --- ENTER KEY AUTO-JUMP SCRIPT ---
            st.components.v1.html("""
            <script>
            window.parent.document.addEventListener('keydown', function(e) {
                if (e.key === 'Enter') {
                    const active = window.parent.document.activeElement;
                    if (active && (active.tagName === 'INPUT' || active.tagName === 'TEXTAREA')) {
                        const inputs = Array.from(window.parent.document.querySelectorAll('input[type="number"], input[type="text"], textarea'));
                        const index = inputs.indexOf(active);
                        if (index > -1 && index < inputs.length - 1) {
                            e.preventDefault();
                            inputs[index + 1].focus();
                        }
                    }
                }
            });
            </script>
            """, height=0, width=0)

            # --- 1. UPPER BODY (VERTICAL) ---
            st.markdown("<div class='section-title-btn'>Upper Body Dimensions</div>", unsafe_allow_html=True)
            full_length_jacket = st.number_input("Length", value=None, min_value=0.0, step=0.25, placeholder="0.00")
            neck = st.number_input("Neck", value=None, min_value=0.0, step=0.25, placeholder="0.00")
            cross_shoulder = st.number_input("Shoulder", value=None, min_value=0.0, step=0.25, placeholder="0.00")
            chest_full = st.number_input("Chest", value=None, min_value=0.0, step=0.25, placeholder="0.00")
            waist_stomach = st.number_input("Stomach", value=None, min_value=0.0, step=0.25, placeholder="0.00")
            seat_hip = st.number_input("Hips", value=None, min_value=0.0, step=0.25, placeholder="0.00")
            armhole = st.number_input("Armhole", value=None, min_value=0.0, step=0.25, placeholder="0.00")
            sleeve_length = st.number_input("Sleeve", value=None, min_value=0.0, step=0.25, placeholder="0.00")
            wrist = st.number_input("Wrist", value=None, min_value=0.0, step=0.25, placeholder="0.00")

            # --- 2. LOWER SIDE (VERTICAL) ---
            st.markdown("<div class='section-title-btn'>Lower Side Dimensions</div>", unsafe_allow_html=True)
            trouser_waist = st.number_input("Waist", value=None, min_value=0.0, step=0.25, placeholder="0.00")
            front_rise = st.number_input("Front Rise", value=None, min_value=0.0, step=0.25, placeholder="0.00")
            crotch_depth = st.number_input("Crotch", value=None, min_value=0.0, step=0.25, placeholder="0.00")
            lower_seat = st.number_input("Seat", value=None, min_value=0.0, step=0.25, placeholder="0.00")
            thigh = st.number_input("Thigh", value=None, min_value=0.0, step=0.25, placeholder="0.00")
            bottom_opening = st.number_input("Bottom Opening", value=None, min_value=0.0, step=0.25, placeholder="0.00")

            m_notes = st.text_area("Measurement Session & Fit Notes", placeholder="e.g., Slim tapering requested...")
            save_m = st.form_submit_button("💾 Save Measurements to Client File", use_container_width=True)
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
                        selected_client_id, rev_label, selected_garment_type, unit, rec_date,
                        full_length_jacket, neck, cross_shoulder, chest_full, waist_stomach,
                        seat_hip or lower_seat, armhole, sleeve_length, wrist, trouser_waist,
                        front_rise, crotch_depth, thigh, bottom_opening, m_notes
                    ))
                    conn.commit()
                st.success(f"Measurements saved for {selected_client_label}!")
# ---------------------------------------------------------
# 4. NEW ORDER (BLANK INITIAL PRICING INPUTS)
# ---------------------------------------------------------
elif st.session_state.page == "New Order":
    st.markdown("<div class='section-title-btn'>➕ Create New Garment Order</div>", unsafe_allow_html=True)
    if st.button("← Back to Hub", key="btn_back_new_order"):
        navigate("Dashboard")
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
                "SELECT id, revision_label, garment_category, date_recorded FROM measurements WHERE client_id = ? ORDER BY id DESC", 
                (selected_client_id,)
            ).fetchall()
            
        if not revisions:
            st.error("No measurement sets found for this client. Please take measurements first.")
        else:
            rev_dict = {f"{r['revision_label']} [{r['garment_category'] or 'Master'}] ({r['date_recorded']})": r['id'] for r in revisions}
            with st.form("new_order_form"):
                o1, o2 = st.columns(2)
                with o1:
                    order_no = st.text_input("Order Reference ID*", value=f"BS-{datetime.date.today().strftime('%Y%m%d')}-01")
                    selected_rev = st.selectbox("Cutting Measurement Revision*", list(rev_dict.keys()))
                    garment_type = st.selectbox("Garment to Stitch", [
                        "Kurta saya", "Kurta saya with izar", "Pehran", "Only kurta",
                        "Kurta Short)", "Pajama", "Shirt", "Trousers", "Sherwani",
                        "Nehru Jacket", "Waistcoat", "Jodhpuri Suit", "Pathani Suit",
                        "Two-Piece / Three-Piece Suit", "Blazer / Formal Coat",
                        "Shirt & Trousers", "Safari Suit"
                    ])
                    fit_preference = st.selectbox("Fit Preference", ["Slim Fit", "Regular Fit", "Relaxed Fit", "Traditional Loose"])
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
                
                place_order = st.form_submit_button("Submit Garment Order", use_container_width=True)
                if place_order:
                    with get_db() as conn:
                        conn.cursor().execute("""
                        INSERT INTO orders (
                            order_number, client_id, measurement_id, garment_type, fit_preference, 
                            fabric_details, total_amount, amount_paid, payment_mode, payment_status, delivery_date, fitting_remarks
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            order_no, selected_client_id, rev_dict[selected_rev], garment_type, fit_preference,
                            fabric_details, calc_total, calc_paid, payment_mode, payment_status, delivery_date, remarks
                        ))
                        conn.commit()
                    st.success(f"Order {order_no} created successfully under Bamniya Studio!")

# ---------------------------------------------------------
# 5. ORDER TRACKING
# ---------------------------------------------------------
elif st.session_state.page == "Update Orders":
    st.markdown("<div class='section-title-btn'>📦 Minimalist Order Tracking & Workshop Progress</div>", unsafe_allow_html=True)
    if st.button("← Back to Hub", key="btn_back_update_orders"):
        navigate("Dashboard")
        st.rerun()
        
    with get_db() as conn:
        orders_df = pd.read_sql_query("""
        SELECT o.id, o.order_number, c.full_name as client_name, c.phone, o.garment_type, 
               o.workflow_status, o.payment_status, o.payment_mode, o.total_amount, o.amount_paid,
               (o.total_amount - o.amount_paid) as balance_due,
               o.delivery_date, o.fabric_details, o.fitting_remarks
        FROM orders o
        JOIN clients c ON o.client_id = c.id
        ORDER BY o.delivery_date ASC
        """, conn)
        
    if orders_df.empty:
        st.info("No active garment orders in production.")
    else:
        filter_q = st.text_input("🔍 Filter Orders by Client Name, Phone or Order #")
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
                    <p style="margin: 0.3rem 0;"><b>Client:</b> {order['client_name']} ({order['phone']}) | <b>Payment:</b> {order['payment_status']} (Paid ₹{order['amount_paid']:,.0f} / Total ₹{order['total_amount']:,.0f} via {order['payment_mode'] or 'Cash'})</p>
                </div>
                """, unsafe_allow_html=True)
                
                c_stage, c_pay, c_del = st.columns([2, 1.5, 1])
                with c_stage:
                    cur_idx = stages.index(order['workflow_status']) if order['workflow_status'] in stages else 0
                    new_stage = st.selectbox("Stage", stages, index=cur_idx, key=f"stg_{order['order_number']}")
                    if new_stage != order['workflow_status']:
                        with get_db() as conn:
                            conn.cursor().execute("UPDATE orders SET workflow_status = ? WHERE order_number = ?", (new_stage, order['order_number']))
                            conn.commit()
                        st.rerun()
                        
                with c_pay:
                    cur_paid = float(order['amount_paid'] or 0.0)
                    total_p = float(order['total_amount'] or 0.0)
                    if cur_paid < total_p:
                        if st.button(f"Mark Full (₹{total_p - cur_paid:.0f})", key=f"pay_{order['order_number']}", use_container_width=True):
                            with get_db() as conn:
                                conn.cursor().execute("UPDATE orders SET amount_paid = total_amount, payment_status = 'Fully Paid' WHERE order_number = ?", (order['order_number'],))
                                conn.commit()
                            st.rerun()
                    else:
                        st.success("✅ Fully Paid")

                with c_del:
                    if st.button(f"🗑️ Delete", key=f"del_{order['order_number']}", use_container_width=True):
                        st.session_state.delete_target_order = order['order_number']
                
                if st.session_state.delete_target_order == order['order_number']:
                    st.warning(f"Confirm deleting {order['order_number']} permanently?")
                    y_col, n_col = st.columns(2)
                    with y_col:
                        if st.button("✅ Yes, Delete", key=f"y_{order['order_number']}", use_container_width=True):
                            with get_db() as conn:
                                conn.cursor().execute("DELETE FROM orders WHERE order_number = ?", (order['order_number'],))
                                conn.commit()
                            st.session_state.delete_target_order = None
                            st.rerun()
                    with n_col:
                        if st.button("❌ Cancel", key=f"n_{order['order_number']}", use_container_width=True):
                            st.session_state.delete_target_order = None
                            st.rerun()
                st.markdown("<hr style='margin:0.5rem 0 1rem 0; border:0.5px solid #E5DCCE;'>", unsafe_allow_html=True)

# ---------------------------------------------------------
# 6. RECEIPT
# ---------------------------------------------------------
elif st.session_state.page == "Print Slip":
    st.markdown("<div class='section-title-btn'>🧾 A5 Order Receipt Slip</div>", unsafe_allow_html=True)
    if st.button("← Back to Hub", key="btn_back_slip"):
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
        selected_slip_order = st.selectbox("Select Order Reference", list(order_opts.keys()))
        ord_no = order_opts[selected_slip_order]
        
        with get_db() as conn:
            slip_data = conn.cursor().execute("""
            SELECT o.*, c.client_code, c.full_name as client_name, c.phone, c.email,
                   m.unit, m.neck, m.chest_full, m.chest_upper, m.waist_stomach, m.cross_shoulder,
                   m.back_width, m.front_chest_width, m.armhole, m.bicep, m.wrist, m.sleeve_length,
                   m.nape_to_waist, m.full_length_jacket, m.trouser_waist, m.seat_hip, m.thigh,
                   m.knee, m.calf, m.bottom_opening, m.outseam, m.inseam, m.front_rise, m.crotch_depth
            FROM orders o
            JOIN clients c ON o.client_id = c.id
            JOIN measurements m ON o.measurement_id = m.id
            WHERE o.order_number = ?
            """, (ord_no,)).fetchone()
            
        if slip_data:
            total_amt = float(slip_data['total_amount'] or 0.0)
            paid_amt = float(slip_data['amount_paid'] or 0.0)
            bal_amt = total_amt - paid_amt
            
            store_name = "BAMNIYA STUDIO"
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

            pure_receipt_html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>Receipt_{ord_id}</title>
<style>
  @page {{
    size: A5 portrait;
    margin: 5mm;
  }}
  * {{
    box-sizing: border-box;
    font-family: 'Courier New', Courier, monospace;
    color: #000000;
  }}
  body {{
    margin: 0;
    padding: 6px;
    background: #FFFFFF;
    font-size: 12px;
    line-height: 1.3;
  }}
  .ticket {{
    width: 100%;
    max-width: 138mm;
    margin: 0 auto;
    border: 1px solid #000000;
    padding: 10px 12px;
  }}
  .center {{ text-align: center; }}
  .right {{ text-align: right; }}
  .bold {{ font-weight: bold; }}
  .title {{ font-size: 16px; font-weight: bold; margin: 0; letter-spacing: 1px; }}
  .sub {{ font-size: 10px; margin: 2px 0; text-transform: uppercase; }}
  .dash {{ border: none; border-top: 1px dashed #000; margin: 6px 0; }}
  table {{ width: 100%; border-collapse: collapse; }}
  td, th {{ padding: 2px 0; vertical-align: top; }}
  .grid-table {{ margin: 4px 0; }}
  .grid-table td, .grid-table th {{
    border: 1px solid #000;
    padding: 3px 4px;
    font-size: 11px;
  }}
  .print-btn {{
    display: block;
    width: 100%;
    background: #111827;
    color: #FFFFFF;
    border: none;
    padding: 10px;
    font-size: 14px;
    font-weight: bold;
    cursor: pointer;
    border-radius: 6px;
    margin-bottom: 10px;
  }}
  @media print {{
    .print-btn {{ display: none !important; }}
    body {{ padding: 0 !important; }}
    .ticket {{ border: 1px solid #000 !important; }}
  }}
</style>
</head>
<body>
  <button class="print-btn" onclick="window.print()">🖨️ CLICK HERE TO PRINT RECEIPT (A5)</button>
  <div class="ticket">
    <div class="center">
      <div class="title">{store_name}</div>
      <div class="sub">Bespoke Master Tailoring Atelier</div>
      <div class="bold" style="font-size: 11px;">SALES & MEASUREMENT RECEIPT</div>
    </div>
    <hr class="dash">
    <table>
      <tr><td><b>CLIENT:</b> {c_name}</td><td class="right"><b>DATE:</b> {book_date}</td></tr>
      <tr><td><b>ID:</b> {c_id}</td><td class="right"><b>ORDER #:</b> {ord_id}</td></tr>
      <tr><td colspan="2"><b>PHONE:</b> {c_phone}</td></tr>
      <tr><td colspan="2"><b>GARMENT:</b> {garment} ({fit})</td></tr>
      <tr><td colspan="2"><b>COMPLETION DATE:</b> {del_date}</td></tr>
    </table>
    <hr class="dash">
    <div class="bold" style="font-size: 11px;">[ MEASUREMENTS ({unit}) ]</div>
    <table class="grid-table">
      <tr style="background:#EEEEEE;">
        <th>PART</th><th>SPEC</th><th>PART</th><th>SPEC</th>
      </tr>
      <tr>
        <td>Neck</td><td><b>{slip_data['neck'] or '-'}</b></td>
        <td>Full Length</td><td><b>{slip_data['full_length_jacket'] or '-'}</b></td>
      </tr>
      <tr>
        <td>Chest (Full)</td><td><b>{slip_data['chest_full'] or '-'}</b></td>
        <td>Trouser Waist</td><td><b>{slip_data['trouser_waist'] or '-'}</b></td>
      </tr>
      <tr>
        <td>Upper Chest</td><td><b>{slip_data['chest_upper'] or '-'}</b></td>
        <td>Seat / Hip</td><td><b>{slip_data['seat_hip'] or '-'}</b></td>
      </tr>
      <tr>
        <td>Stomach/Waist</td><td><b>{slip_data['waist_stomach'] or '-'}</b></td>
        <td>Thigh</td><td><b>{slip_data['thigh'] or '-'}</b></td>
      </tr>
      <tr>
        <td>Shoulder</td><td><b>{slip_data['cross_shoulder'] or '-'}</b></td>
        <td>Knee</td><td><b>{slip_data['knee'] or '-'}</b></td>
      </tr>
      <tr>
        <td>Armhole</td><td><b>{slip_data['armhole'] or '-'}</b></td>
        <td>Bottom Opening</td><td><b>{slip_data['bottom_opening'] or '-'}</b></td>
      </tr>
      <tr>
        <td>Bicep</td><td><b>{slip_data['bicep'] or '-'}</b></td>
        <td>Outseam</td><td><b>{slip_data['outseam'] or '-'}</b></td>
      </tr>
      <tr>
        <td>Sleeve</td><td><b>{slip_data['sleeve_length'] or '-'}</b></td>
        <td>Inseam/Rise</td><td><b>{slip_data['inseam'] or '-'}/{slip_data['front_rise'] or '-'}</b></td>
      </tr>
    </table>
    <hr class="dash">
    <table>
      <tr><td><b>TOTAL AMOUNT:</b></td><td class="right bold">Rs. {total_amt:,.2f}</td></tr>
      <tr><td><b>AMOUNT PAID:</b></td><td class="right">Rs. {paid_amt:,.2f}</td></tr>
      <tr><td class="bold">BALANCE DUE:</td><td class="right bold" style="font-size:13px;">Rs. {bal_amt:,.2f}</td></tr>
      <tr><td><b>PAYMENT MODE:</b></td><td class="right">{pay_mode}</td></tr>
      <tr><td><b>PAYMENT STAGE:</b></td><td class="right bold">{pay_stat}</td></tr>
    </table>
    <hr class="dash">
    <div class="center" style="font-size: 10px;">
      THANK YOU FOR CHOOSING {store_name}<br>
      Exact Fit & Master Craftsmanship Guaranteed
    </div>
    <br>
    <table style="font-size: 9.5px;">
      <tr>
        <td>CLIENT SIGN: ____________</td>
        <td class="right">MASTER TAILOR: ____________</td>
      </tr>
    </table>
  </div>
</body>
</html>"""

            d_col, _ = st.columns([1.5, 2.5])
            with d_col:
                st.download_button(
                    label="💾 Download HTML Slip (Direct Print)",
                    data=pure_receipt_html,
                    file_name=f"Receipt_{ord_id}.html",
                    mime="text/html",
                    use_container_width=True
                )

            st.components.v1.html(pure_receipt_html, height=650, scrolling=True)

# ---------------------------------------------------------
# 7. CLIENT DATABASE
# ---------------------------------------------------------
elif st.session_state.page == "Client Records":
    st.markdown("<div class='section-title-btn'>Client Database</div>", unsafe_allow_html=True)
    if st.button("← Back to Hub", key="btn_back_records"):
        navigate("Dashboard")
        st.rerun()
        
    with get_db() as conn:
        clients_df = pd.read_sql_query("SELECT id, client_code, full_name, phone, posture_notes, asymmetry_notes FROM clients ORDER BY full_name", conn)
        
    if not clients_df.empty:
        search = st.text_input("Search Client by Name or Phone Number")
        if search:
            clients_df = clients_df[clients_df.apply(lambda row: search.lower() in row.astype(str).str.lower().values, axis=1)]
        st.dataframe(clients_df, use_container_width=True)
        
        st.markdown("<div class='section-title-btn'>Manage Client</div>", unsafe_allow_html=True)
        client_options = {f"{r['client_code']} — {r['full_name']}": r['id'] for _, r in clients_df.iterrows()}
        if client_options:
            c_sel, c_del_cli = st.columns([3, 1])
            with c_sel:
                inspect_label = st.selectbox("Select Client", list(client_options.keys()))
                cid = client_options[inspect_label]
            with c_del_cli:
                st.write("")
                st.write("")
                if st.button("Delete Client Profile", use_container_width=True):
                    st.session_state.delete_target_client = cid

            if st.session_state.delete_target_client == cid:
                st.error(f"Are you sure you want to permanently delete {inspect_label} and all their records?")
                cy_col, cn_col = st.columns(2)
                with cy_col:
                    if st.button("Yes, Delete Entire Client History", use_container_width=True):
                        with get_db() as conn:
                            conn.cursor().execute("DELETE FROM clients WHERE id = ?", (cid,))
                            conn.commit()
                        st.session_state.delete_target_client = None
                        st.success("Client deleted.")
                        st.rerun()
                with cn_col:
                    if st.button("Cancel Deletion", use_container_width=True):
                        st.session_state.delete_target_client = None
                        st.rerun()
    else:
        st.info("No client records found.")
