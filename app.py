import sqlite3
import datetime
import streamlit as st
import pandas as pd

# ---------------------------------------------------------
# PAGE SETUP & MODERN STYLING
# ---------------------------------------------------------
st.set_page_config(
    page_title="Master Tailor OS",
    page_icon="✂️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for modern bespoke card styling
st.markdown("""
<style>
    /* Card buttons styling */
    .stButton>button {
        border-radius: 12px;
        height: 3.5rem;
        font-weight: 600;
        font-size: 1.05rem;
        transition: all 0.2s ease-in-out;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 16px rgba(0,0,0,0.12);
    }
    /* Metric and section headers */
    .dashboard-header {
        text-align: center;
        margin-bottom: 2rem;
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# DATABASE SETUP
# ---------------------------------------------------------
DB_FILE = "master_tailor.db"

def get_db():
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Clients Table
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
        
        # Versioned Client Measurements Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS measurements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER NOT NULL,
            revision_label TEXT NOT NULL,
            unit TEXT CHECK(unit IN ('Inches', 'Centimeters')) NOT NULL DEFAULT 'Inches',
            date_recorded DATE NOT NULL,
            
            -- Upper Body
            neck REAL, chest_full REAL, chest_upper REAL, waist_stomach REAL,
            cross_shoulder REAL, back_width REAL, front_chest_width REAL,
            armhole REAL, bicep REAL, wrist REAL,
            sleeve_length REAL, nape_to_waist REAL, full_length_jacket REAL,
            
            -- Lower Body
            trouser_waist REAL, seat_hip REAL, thigh REAL, knee REAL,
            calf REAL, bottom_opening REAL, outseam REAL, inseam REAL,
            front_rise REAL, crotch_depth REAL,
            
            -- Indian Traditional Metrics
            kurta_length REAL, sherwani_length REAL, churidar_length REAL,
            
            notes TEXT,
            FOREIGN KEY (client_id) REFERENCES clients (id) ON DELETE CASCADE
        );
        """)
        
        # Dedicated Orders Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_number TEXT UNIQUE NOT NULL,
            client_id INTEGER NOT NULL,
            measurement_id INTEGER NOT NULL,
            garment_type TEXT NOT NULL,
            fit_preference TEXT NOT NULL,
            fabric_details TEXT,
            price REAL DEFAULT 0.0,
            advance_paid REAL DEFAULT 0.0,
            delivery_date DATE,
            status TEXT CHECK(status IN ('Drafted', 'Fabric Cut', 'Basted Fitting', 'Alterations', 'Final Pressed', 'Delivered')) DEFAULT 'Drafted',
            fitting_remarks TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (client_id) REFERENCES clients (id),
            FOREIGN KEY (measurement_id) REFERENCES measurements (id)
        );
        """)
        conn.commit()

init_db()

# ---------------------------------------------------------
# SESSION STATE NAVIGATION
# ---------------------------------------------------------
if "current_page" not in st.session_state:
    st.session_state.current_page = "Dashboard"

def set_page(page_name):
    st.session_state.current_page = page_name

# Sidebar Quick Nav
st.sidebar.title("✂️ Master Tailor")
st.sidebar.caption("Bespoke Client & Workshop Manager")

nav_options = [
    "🏠 Main Hub",
    "👤 Register Client",
    "📏 Record Measurements",
    "🗂️ View Client Records",
    "➕ Create New Order",
    "🔄 Update Orders & Fitting"
]

selected_sidebar = st.sidebar.radio(
    "Navigation", 
    nav_options, 
    index=[
        "Dashboard", "New Client", "New Measurement", 
        "Client Records", "New Order", "Update Orders"
    ].index(
        st.session_state.current_page if st.session_state.current_page in [
            "Dashboard", "New Client", "New Measurement", 
            "Client Records", "New Order", "Update Orders"
        ] else "Dashboard"
    )
)

# Sync sidebar with state
page_map = {
    "🏠 Main Hub": "Dashboard",
    "👤 Register Client": "New Client",
    "📏 Record Measurements": "New Measurement",
    "🗂️ View Client Records": "Client Records",
    "➕ Create New Order": "New Order",
    "🔄 Update Orders & Fitting": "Update Orders"
}
st.session_state.current_page = page_map[selected_sidebar]

# ---------------------------------------------------------
# 1. MAIN INTERACTIVE DASHBOARD HUB
# ---------------------------------------------------------
if st.session_state.current_page == "Dashboard":
    st.markdown("<div class='dashboard-header'><h1>✂️ Master Tailor Workshop Hub</h1><p>Select an action below to manage your clients, measurements, and active orders</p></div>", unsafe_allow_html=True)
    
    # Quick Status Metrics
    with get_db() as conn:
        total_clients = conn.cursor().execute("SELECT COUNT(*) FROM clients").fetchone()[0]
        active_orders = conn.cursor().execute("SELECT COUNT(*) FROM orders WHERE status != 'Delivered'").fetchone()[0]
        completed_orders = conn.cursor().execute("SELECT COUNT(*) FROM orders WHERE status = 'Delivered'").fetchone()[0]

    m1, m2, m3 = st.columns(3)
    m1.metric("👥 Total Clients", total_clients)
    m2.metric("🧵 In-Progress Garments", active_orders)
    m3.metric("✨ Delivered Orders", completed_orders)
    
    st.markdown("---")
    
    # Interactive Grid Cards
    st.subheader("⚡ Quick Actions")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("👤  Register New Client\n\nAdd new client profile, posture, and asymmetries", use_container_width=True):
            set_page("New Client")
            st.rerun()
            
        st.write("")
        if st.button("📏  Record Measurements\n\nTake complete body & garment measurements with date", use_container_width=True):
            set_page("New Measurement")
            st.rerun()
            
        st.write("")
        if st.button("🗂️  Client Database & History\n\nSearch clients, past revisions, and fitting logs", use_container_width=True):
            set_page("Client Records")
            st.rerun()

    with col2:
        if st.button("➕  Create New Garment Order\n\nAssign garment type, fabric, deadline, and price", use_container_width=True):
            set_page("New Order")
            st.rerun()
            
        st.write("")
        if st.button("🔄  Dedicated Order & Fitting Updater\n\nUpdate status, fitting drag notes, and delivery", use_container_width=True):
            set_page("Update Orders")
            st.rerun()

# ---------------------------------------------------------
# 2. REGISTER NEW CLIENT
# ---------------------------------------------------------
elif st.session_state.current_page == "New Client":
    st.header("👤 Register New Client Profile")
    if st.button("← Back to Hub"):
        set_page("Dashboard")
        st.rerun()
        
    with st.form("new_client_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            client_code = st.text_input("Client ID / Phone Number as Code*", placeholder="e.g., CL-982601")
            full_name = st.text_input("Client Full Name*")
            phone = st.text_input("Contact Number*")
            email = st.text_input("Email (Optional)")
        with c2:
            posture_notes = st.text_area("Posture Observations", placeholder="e.g., Erect stance, forward sloping shoulders, swayback...")
            asymmetry_notes = st.text_area("Physical Asymmetries", placeholder="e.g., Right shoulder 0.5 in lower, left arm 0.25 in longer...")
        
        submitted = st.form_submit_button("Save Client Profile", use_container_width=True)
        if submitted:
            if not client_code or not full_name or not phone:
                st.error("Please fill in the required fields (Client ID, Full Name, Contact Number).")
            else:
                try:
                    with get_db() as conn:
                        conn.cursor().execute("""
                        INSERT INTO clients (client_code, full_name, phone, email, posture_notes, asymmetry_notes)
                        VALUES (?, ?, ?, ?, ?, ?)
                        """, (client_code.strip(), full_name.strip(), phone.strip(), email.strip(), posture_notes, asymmetry_notes))
                        conn.commit()
                    st.success(f"Client {full_name} saved successfully!")
                except sqlite3.IntegrityError:
                    st.error("This Client ID already exists in your records. Please use a unique ID.")

# ---------------------------------------------------------
# 3. RECORD MEASUREMENTS
# ---------------------------------------------------------
elif st.session_state.current_page == "New Measurement":
    st.header("📏 Record Dated Client Measurements")
    if st.button("← Back to Hub"):
        set_page("Dashboard")
        st.rerun()
        
    with get_db() as conn:
        clients = conn.cursor().execute("SELECT id, client_code, full_name FROM clients ORDER BY full_name").fetchall()
    
    if not clients:
        st.warning("No clients found. Register a client first.")
    else:
        client_dict = {f"{c['client_code']} — {c['full_name']}": c['id'] for c in clients}
        selected_client_label = st.selectbox("Choose Client", list(client_dict.keys()))
        selected_client_id = client_dict[selected_client_label]
        
        with st.form("measurement_form"):
            h1, h2, h3 = st.columns(3)
            with h1:
                rev_label = st.text_input("Measurement Session Label*", value="Revision 01")
            with h2:
                rec_date = st.date_input("Date Taken", datetime.date.today())
            with h3:
                unit = st.selectbox("Measurement Unit", ["Inches", "Centimeters"])
            
            st.markdown("### Upper Body Dimensions")
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
                armhole = st.number_input("Armhole Circumference", min_value=0.0, step=0.25)
                bicep = st.number_input("Bicep", min_value=0.0, step=0.25)
            with u4:
                wrist = st.number_input("Wrist", min_value=0.0, step=0.25)
                sleeve_length = st.number_input("Sleeve Length", min_value=0.0, step=0.25)
                full_length_jacket = st.number_input("Coat / Top Length", min_value=0.0, step=0.25)
                nape_to_waist = st.number_input("Nape to Waist", min_value=0.0, step=0.25)

            st.markdown("### Lower Body Dimensions")
            l1, l2, l3, l4 = st.columns(4)
            with l1:
                trouser_waist = st.number_input("Trouser Waist", min_value=0.0, step=0.25)
                seat_hip = st.number_input("Seat / Hip", min_value=0.0, step=0.25)
            with l2:
                thigh = st.number_input("Thigh", min_value=0.0, step=0.25)
                knee = st.number_input("Knee", min_value=0.0, step=0.25)
            with l3:
                calf = st.number_input("Calf", min_value=0.0, step=0.25)
                bottom_opening = st.number_input("Bottom Opening / Hem", min_value=0.0, step=0.25)
            with l4:
                outseam = st.number_input("Outseam Length", min_value=0.0, step=0.25)
                inseam = st.number_input("Inseam Length", min_value=0.0, step=0.25)
                front_rise = st.number_input("Front Rise", min_value=0.0, step=0.25)
                crotch_depth = st.number_input("Crotch Depth", min_value=0.0, step=0.25)

            st.markdown("### Indian Traditional Specifics")
            t1, t2, t3 = st.columns(3)
            with t1:
                kurta_length = st.number_input("Kurta Length", min_value=0.0, step=0.25)
            with t2:
                sherwani_length = st.number_input("Sherwani Length", min_value=0.0, step=0.25)
            with t3:
                churidar_length = st.number_input("Churidar Total Length", min_value=0.0, step=0.25)

            m_notes = st.text_area("Specific Fitting / Customer Preference Notes")

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
# 4. VIEW CLIENT RECORDS & HISTORY
# ---------------------------------------------------------
elif st.session_state.current_page == "Client Records":
    st.header("🗂️ Client Profiles & Measurement Archive")
    if st.button("← Back to Hub"):
        set_page("Dashboard")
        st.rerun()
        
    with get_db() as conn:
        clients_df = pd.read_sql_query("SELECT id, client_code, full_name, phone, posture_notes, asymmetry_notes FROM clients ORDER BY full_name", conn)
        
    if not clients_df.empty:
        search_query = st.text_input("🔍 Search Client by Name or Phone")
        if search_query:
            clients_df = clients_df[clients_df.apply(lambda row: search_query.lower() in row.astype(str).str.lower().values, axis=1)]
            
        st.dataframe(clients_df, use_container_width=True)
        
        st.markdown("---")
        st.subheader("Inspection: Historical Measurements")
        client_options = {f"{r['client_code']} — {r['full_name']}": r['id'] for _, r in clients_df.iterrows()}
        if client_options:
            inspect_id = st.selectbox("Select Client to inspect full records", list(client_options.keys()))
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
# 5. CREATE NEW ORDER
# ---------------------------------------------------------
elif st.session_state.current_page == "New Order":
    st.header("➕ Create New Garment Order")
    if st.button("← Back to Hub"):
        set_page("Dashboard")
        st.rerun()
        
    with get_db() as conn:
        clients = conn.cursor().execute("SELECT id, client_code, full_name FROM clients ORDER BY full_name").fetchall()
        
    if not clients:
        st.warning("Register a client before creating orders.")
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
            st.error("This client has no recorded measurements. Please take measurements first.")
        else:
            rev_dict = {f"{r['revision_label']} (Dated: {r['date_recorded']})": r['id'] for r in revisions}
            
            with st.form("new_order_form"):
                o1, o2 = st.columns(2)
                with o1:
                    order_no = st.text_input("Order ID*", value=f"ORD-{datetime.date.today().strftime('%Y%m%d')}-01")
                    selected_rev = st.selectbox("Measurement Revision to Cut From*", list(rev_dict.keys()))
                    garment_type = st.selectbox("Garment", [
                        "Two-Piece Suit", "Three-Piece Suit", "Blazer / Sports Coat",
                        "Dress Trousers", "Dress Shirt", "Kurta Pajama",
                        "Nehru Jacket", "Bandhgala Suit", "Sherwani / Achkan", "Pathani Suit"
                    ])
                    fit_preference = st.selectbox("Fit Preference", ["Slim Fit", "Regular Fit", "Relaxed Fit", "Traditional Loose"])
                with o2:
                    delivery_date = st.date_input("Delivery Deadline", datetime.date.today() + datetime.timedelta(days=10))
                    price = st.number_input("Total Garment Price", min_value=0.0, step=100.0)
                    advance = st.number_input("Advance Paid", min_value=0.0, step=100.0)
                    fabric_details = st.text_area("Fabric & Mill Details", placeholder="e.g., Italian Wool 280 GSM, Black Silk lining...")
                    
                remarks = st.text_area("Specific Cutting or Design Instructions")
                
                place_order = st.form_submit_button("Submit Order", use_container_width=True)
                if place_order:
                    with get_db() as conn:
                        conn.cursor().execute("""
                        INSERT INTO orders (order_number, client_id, measurement_id, garment_type, fit_preference, fabric_details, price, advance_paid, delivery_date, fitting_remarks)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (order_no, selected_client_id, rev_dict[selected_rev], garment_type, fit_preference, fabric_details, price, advance, delivery_date, remarks))
                        conn.commit()
                    st.success(f"Order {order_no} created successfully!")

# ---------------------------------------------------------
# 6. DEDICATED ORDER UPDATING & FITTING WORKFLOW
# ---------------------------------------------------------
elif st.session_state.current_page == "Update Orders":
    st.header("🔄 Order Status & Fitting Workflow Updater")
    if st.button("← Back to Hub"):
        set_page("Dashboard")
        st.rerun()
        
    with get_db() as conn:
        orders_df = pd.read_sql_query("""
        SELECT o.id, o.order_number, c.full_name as client_name, c.phone, o.garment_type, 
               o.status, o.delivery_date, o.price, o.advance_paid, (o.price - o.advance_paid) as balance_due,
               o.fabric_details, o.fitting_remarks
        FROM orders o
        JOIN clients c ON o.client_id = c.id
        ORDER BY o.delivery_date ASC
        """, conn)
        
    if orders_df.empty:
        st.info("No active orders found in the database.")
    else:
        st.subheader("All Garment Orders")
        st.dataframe(orders_df, use_container_width=True)
        
        st.markdown("---")
        st.subheader("Update Order Status & Fitting Notes")
        
        order_list = orders_df["order_number"].tolist()
        selected_order_no = st.selectbox("Select Order to Update", order_list)
        
        # Get current order details
        current_order = orders_df[orders_df["order_number"] == selected_order_no].iloc[0]
        
        with st.form("update_order_page_form"):
            u1, u2, u3 = st.columns(3)
            
            with u1:
                status_options = ['Drafted', 'Fabric Cut', 'Basted Fitting', 'Alterations', 'Final Pressed', 'Delivered']
                current_status_idx = status_options.index(current_order['status']) if current_order['status'] in status_options else 0
                new_status = st.selectbox("Workflow Stage / Status", status_options, index=current_status_idx)
                
            with u2:
                new_delivery = st.date_input("Update Delivery Date", datetime.datetime.strptime(str(current_order['delivery_date']), '%Y-%m-%d').date() if current_order['delivery_date'] else datetime.date.today())
                
            with u3:
                additional_payment = st.number_input("Add Payment Received (Adds to advance)", min_value=0.0, step=100.0)
            
            st.markdown(f"**Current Fitting Notes:** `{current_order['fitting_remarks'] or 'None'}`")
            new_note = st.text_area("Append Fitting Observations / Drag Lines / Alterations Required", placeholder="e.g., First fitting: reduce neck point by 0.5 cm, rotate sleeve pitch backward.")
            
            update_submit = st.form_submit_button("Save & Update Order", use_container_width=True)
            if update_submit:
                with get_db() as conn:
                    # Update order record
                    appended_remarks = current_order['fitting_remarks'] or ""
                    if new_note.strip():
                        appended_remarks = f"{appended_remarks} | [{datetime.date.today()}] {new_note.strip()}"
                        
                    conn.cursor().execute("""
                    UPDATE orders 
                    SET status = ?, 
                        delivery_date = ?, 
                        advance_paid = advance_paid + ?, 
                        fitting_remarks = ?
                    WHERE order_number = ?
                    """, (new_status, new_delivery, additional_payment, appended_remarks, selected_order_no))
                    conn.commit()
                    
                st.success(f"Order {selected_order_no} updated to '{new_status}' successfully!")
                st.rerun()
