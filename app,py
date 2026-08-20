import sqlite3
import datetime
import streamlit as st
import pandas as pd

# ---------------------------------------------------------
# DATABASE ENGINE SETUP
# ---------------------------------------------------------
DB_FILE = "master_tailor.db"

def get_db():
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as conn:
        cursor = conn.cursor()
        
        # 1. Clients Table
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
        
        # 2. Versioned Measurements Table
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
        
        # 3. Garment Orders Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_number TEXT UNIQUE NOT NULL,
            client_id INTEGER NOT NULL,
            measurement_id INTEGER NOT NULL,
            garment_type TEXT NOT NULL,
            fit_preference TEXT NOT NULL,
            fabric_details TEXT,
            delivery_date DATE,
            status TEXT CHECK(status IN ('Drafted', 'Cut', 'Basted Fitting', 'Alterations', 'Final Pressed', 'Delivered')) DEFAULT 'Drafted',
            fitting_remarks TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (client_id) REFERENCES clients (id),
            FOREIGN KEY (measurement_id) REFERENCES measurements (id)
        );
        """)
        conn.commit()

init_db()

# ---------------------------------------------------------
# BESPOKE EASE ENGINE
# ---------------------------------------------------------
def calculate_cutting_specs(chest, waist, hip, garment, fit_type, unit="Inches"):
    if not chest:
        return None
    
    # Standard wearing ease offsets in inches
    ease_matrix = {
        "Two-Piece Suit / Blazer": {"Slim": 3.0, "Regular": 4.5, "Relaxed": 6.0},
        "Dress Shirt": {"Slim": 2.5, "Regular": 4.0, "Relaxed": 5.5},
        "Straight Kurta": {"Slim": 3.5, "Regular": 5.0, "Relaxed": 6.5},
        "Nehru Jacket / Bandhgala": {"Slim": 2.5, "Regular": 3.5, "Relaxed": 5.0},
        "Sherwani / Achkan": {"Slim": 4.0, "Regular": 5.5, "Relaxed": 7.0}
    }
    
    chest_ease = ease_matrix.get(garment, {}).get(fit_type, 4.0)
    if unit == "Centimeters":
        chest_ease = chest_ease * 2.54
        
    finished_chest = chest + chest_ease
    half_chest = finished_chest / 2.0
    quarter_chest = finished_chest / 4.0
    
    return {
        "Net Chest": chest,
        "Ease Applied": f"+{chest_ease:.2f} {unit}",
        "Finished Garment Chest": f"{finished_chest:.2f} {unit}",
        "Half-Chest (Pattern Lay)": f"{half_chest:.2f} {unit}",
        "Quarter-Chest (Block Scale)": f"{quarter_chest:.2f} {unit}"
    }

# ---------------------------------------------------------
# UI CONFIGURATION & NAVIGATION
# ---------------------------------------------------------
st.set_page_config(page_title="Master Tailor Bespoke Management", layout="wide")

st.sidebar.title("✂️ Master Tailor OS")
menu = st.sidebar.radio("Navigation", [
    "Clients Directory",
    "Record Measurements",
    "Measurement History",
    "Cutting & Ease Engine",
    "Orders & Fitting Tracker"
])

# ---------------------------------------------------------
# VIEW 1: CLIENTS DIRECTORY
# ---------------------------------------------------------
if menu == "Clients Directory":
    st.header("👤 Client Registry")
    
    with st.expander("➕ Register New Client", expanded=False):
        with st.form("new_client_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                client_code = st.text_input("Client ID / Code*", placeholder="e.g., CL-2026-001")
                full_name = st.text_input("Full Name*")
                phone = st.text_input("Contact Number*")
                email = st.text_input("Email Address")
            with col2:
                posture_notes = st.text_area("Posture Characteristics", placeholder="e.g., Forward shoulders, erect stance, prominent abdomen...")
                asymmetry_notes = st.text_area("Asymmetry & Balance Notes", placeholder="e.g., Right shoulder drops 0.5 inches, right arm +0.25 inches...")
            
            submitted = st.form_submit_button("Save Client Profile")
            if submitted:
                if not client_code or not full_name or not phone:
                    st.error("Please fill in all mandatory fields (*).")
                else:
                    try:
                        with get_db() as conn:
                            conn.cursor().execute("""
                            INSERT INTO clients (client_code, full_name, phone, email, posture_notes, asymmetry_notes)
                            VALUES (?, ?, ?, ?, ?, ?)
                            """, (client_code.strip(), full_name.strip(), phone.strip(), email.strip(), posture_notes, asymmetry_notes))
                            conn.commit()
                        st.success(f"Client {full_name} registered successfully!")
                    except sqlite3.IntegrityError:
                        st.error("Client ID already exists. Use a unique identifier.")

    with get_db() as conn:
        clients_df = pd.read_sql_query("SELECT id, client_code, full_name, phone, posture_notes, asymmetry_notes, created_at FROM clients ORDER BY id DESC", conn)
    
    st.subheader("Client Records")
    if not clients_df.empty:
        search = st.text_input("🔍 Search by name, phone, or client code")
        if search:
            clients_df = clients_df[clients_df.apply(lambda row: search.lower() in row.astype(str).str.lower().values, axis=1)]
        st.dataframe(clients_df, use_container_width=True)
    else:
        st.info("No clients registered yet.")

# ---------------------------------------------------------
# VIEW 2: RECORD MEASUREMENTS
# ---------------------------------------------------------
elif menu == "Record Measurements":
    st.header("📏 Record New Measurement Set")
    
    with get_db() as conn:
        clients = conn.cursor().execute("SELECT id, client_code, full_name FROM clients ORDER BY full_name").fetchall()
    
    if not clients:
        st.warning("Please register a client first in the 'Clients Directory'.")
    else:
        client_dict = {f"{c['client_code']} - {c['full_name']}": c['id'] for c in clients}
        selected_client_label = st.selectbox("Select Client", list(client_dict.keys()))
        selected_client_id = client_dict[selected_client_label]
        
        with st.form("measurement_form"):
            col_m1, col_m2, col_m3 = st.columns(3)
            with col_m1:
                rev_label = st.text_input("Revision Name*", value="Revision 01 (Initial)")
            with col_m2:
                rec_date = st.date_input("Date Taken", datetime.date.today())
            with col_m3:
                unit = st.selectbox("Measurement Unit", ["Inches", "Centimeters"])
            
            st.markdown("---")
            st.subheader("1. Upper Body (Net Direct Measurements)")
            u1, u2, u3, u4 = st.columns(4)
            with u1:
                neck = st.number_input("Neck", min_value=0.0, step=0.25)
                chest_full = st.number_input("Full Chest*", min_value=0.0, step=0.25)
                chest_upper = st.number_input("Upper Chest", min_value=0.0, step=0.25)
            with u2:
                waist_stomach = st.number_input("Waist / Stomach", min_value=0.0, step=0.25)
                cross_shoulder = st.number_input("Cross Shoulder", min_value=0.0, step=0.25)
                back_width = st.number_input("Back Width", min_value=0.0, step=0.25)
            with u3:
                front_chest_width = st.number_input("Front Chest Width", min_value=0.0, step=0.25)
                armhole = st.number_input("Armhole Circumference", min_value=0.0, step=0.25)
                bicep = st.number_input("Bicep", min_value=0.0, step=0.25)
            with u4:
                wrist = st.number_input("Wrist", min_value=0.0, step=0.25)
                sleeve_length = st.number_input("Sleeve Length", min_value=0.0, step=0.25)
                full_length_jacket = st.number_input("Jacket / Top Length", min_value=0.0, step=0.25)
                nape_to_waist = st.number_input("Nape to Waist (Back)", min_value=0.0, step=0.25)

            st.markdown("---")
            st.subheader("2. Lower Body (Trousers & Pajamas)")
            l1, l2, l3, l4 = st.columns(4)
            with l1:
                trouser_waist = st.number_input("Trouser Waist", min_value=0.0, step=0.25)
                seat_hip = st.number_input("Seat / Hip", min_value=0.0, step=0.25)
            with l2:
                thigh = st.number_input("Thigh Circumference", min_value=0.0, step=0.25)
                knee = st.number_input("Knee Circumference", min_value=0.0, step=0.25)
            with l3:
                calf = st.number_input("Calf", min_value=0.0, step=0.25)
                bottom_opening = st.number_input("Bottom Opening / Hem", min_value=0.0, step=0.25)
            with l4:
                outseam = st.number_input("Outseam Length", min_value=0.0, step=0.25)
                inseam = st.number_input("Inseam", min_value=0.0, step=0.25)
                front_rise = st.number_input("Front Rise", min_value=0.0, step=0.25)
                crotch_depth = st.number_input("Total Crotch Depth", min_value=0.0, step=0.25)

            st.markdown("---")
            st.subheader("3. Indian Traditional Specifics")
            t1, t2, t3 = st.columns(3)
            with t1:
                kurta_length = st.number_input("Kurta Length", min_value=0.0, step=0.25)
            with t2:
                sherwani_length = st.number_input("Sherwani / Achkan Length", min_value=0.0, step=0.25)
            with t3:
                churidar_length = st.number_input("Churidar Length (Inc. Gathers)", min_value=0.0, step=0.25)

            m_notes = st.text_area("Measurement Session Notes / Specific Client Requests")

            save_m = st.form_submit_button("Record Measurements")
            if save_m:
                # Sanity validation check
                if outseam > 0 and inseam > 0 and outseam <= inseam:
                    st.error("Measurement Error: Outseam must be longer than Inseam.")
                else:
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
                    st.success(f"Saved {rev_label} successfully for {selected_client_label}!")

# ---------------------------------------------------------
# VIEW 3: MEASUREMENT HISTORY & AUDIT
# ---------------------------------------------------------
elif menu == "Measurement History":
    st.header("🗂️ Client Measurement Revisions")
    
    with get_db() as conn:
        clients = conn.cursor().execute("SELECT id, client_code, full_name FROM clients ORDER BY full_name").fetchall()
    
    if clients:
        client_dict = {f"{c['client_code']} - {c['full_name']}": c['id'] for c in clients}
        selected_client_label = st.selectbox("Select Client to View", list(client_dict.keys()))
        selected_client_id = client_dict[selected_client_label]
        
        with get_db() as conn:
            m_history = pd.read_sql_query(
                "SELECT * FROM measurements WHERE client_id = ? ORDER BY date_recorded DESC, id DESC", 
                conn, params=(selected_client_id,)
            )
            
        if not m_history.empty:
            st.dataframe(m_history, use_container_width=True)
        else:
            st.info("No measurements recorded for this client yet.")

# ---------------------------------------------------------
# VIEW 4: CUTTING & EASE ENGINE
# ---------------------------------------------------------
elif menu == "Cutting & Ease Engine":
    st.header("📐 Master Tailor Cutting & Ease Calculator")
    st.write("Calculate finished garment dimensions and pattern block distributions directly from raw body measurements.")
    
    col1, col2 = st.columns(2)
    with col1:
        garment = st.selectbox("Select Garment", [
            "Two-Piece Suit / Blazer", 
            "Dress Shirt", 
            "Straight Kurta", 
            "Nehru Jacket / Bandhgala", 
            "Sherwani / Achkan"
        ])
        fit_pref = st.select_slider("Fit Silhouette", options=["Slim", "Regular", "Relaxed"], value="Regular")
        unit_type = st.radio("Measurement Unit", ["Inches", "Centimeters"], horizontal=True)
    
    with col2:
        in_chest = st.number_input(f"Net Body Chest ({unit_type})", min_value=10.0, max_value=80.0, value=40.0, step=0.5)
        in_waist = st.number_input(f"Net Body Waist ({unit_type})", min_value=10.0, max_value=80.0, value=34.0, step=0.5)
        in_hip = st.number_input(f"Net Body Hip / Seat ({unit_type})", min_value=10.0, max_value=80.0, value=41.0, step=0.5)

    specs = calculate_cutting_specs(in_chest, in_waist, in_hip, garment, fit_pref, unit_type)
    
    if specs:
        st.markdown("---")
        st.subheader("Calculated Pattern Blueprint")
        cols = st.columns(len(specs))
        for col, (label, val) in zip(cols, specs.items()):
            col.metric(label=label, value=val)

# ---------------------------------------------------------
# VIEW 5: ORDERS & FITTING TRACKER
# ---------------------------------------------------------
elif menu == "Orders & Fitting Tracker":
    st.header("📋 Orders & Fitting Pipeline")
    
    tab1, tab2 = st.tabs(["Active Orders Overview", "Create New Order"])
    
    with tab2:
        with get_db() as conn:
            clients = conn.cursor().execute("SELECT id, client_code, full_name FROM clients ORDER BY full_name").fetchall()
        
        if clients:
            client_dict = {f"{c['client_code']} - {c['full_name']}": c['id'] for c in clients}
            selected_client_label = st.selectbox("Order Client", list(client_dict.keys()))
            selected_client_id = client_dict[selected_client_label]
            
            with get_db() as conn:
                revisions = conn.cursor().execute(
                    "SELECT id, revision_label, date_recorded FROM measurements WHERE client_id = ? ORDER BY id DESC", 
                    (selected_client_id,)
                ).fetchall()
            
            if not revisions:
                st.warning("This client has no measurements recorded. Please record measurements first.")
            else:
                rev_dict = {f"{r['revision_label']} ({r['date_recorded']})": r['id'] for r in revisions}
                
                with st.form("new_order_form"):
                    o_col1, o_col2 = st.columns(2)
                    with o_col1:
                        order_no = st.text_input("Order Number*", value=f"ORD-{datetime.date.today().strftime('%Y%m%d')}-01")
                        selected_rev = st.selectbox("Measurement Revision to Use*", list(rev_dict.keys()))
                        garment_type = st.selectbox("Garment", [
                            "Two-Piece Suit", "Three-Piece Suit", "Blazer", "Dress Trousers",
                            "Dress Shirt", "Kurta-Pajama", "Nehru Jacket", "Bandhgala", "Sherwani"
                        ])
                        fit = st.selectbox("Fit Preference", ["Slim", "Regular", "Relaxed", "Traditional Bespoke"])
                    with o_col2:
                        delivery = st.date_input("Target Delivery Date", datetime.date.today() + datetime.timedelta(days=14))
                        fabric = st.text_area("Fabric Details", placeholder="e.g., 280 GSM Merino Wool Navy Super 130s / Pure Irish Linen")
                        remarks = st.text_area("Initial Fitting Requirements / Remarks")
                        
                    create_order = st.form_submit_button("Submit Garment Order")
                    if create_order:
                        with get_db() as conn:
                            conn.cursor().execute("""
                            INSERT INTO orders (order_number, client_id, measurement_id, garment_type, fit_preference, fabric_details, delivery_date, fitting_remarks)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                            """, (order_no, selected_client_id, rev_dict[selected_rev], garment_type, fit, fabric, delivery, remarks))
                            conn.commit()
                        st.success(f"Order {order_no} created successfully!")
    
    with tab1:
        with get_db() as conn:
            orders_df = pd.read_sql_query("""
            SELECT o.id, o.order_number, c.full_name as client_name, o.garment_type, o.fit_preference, 
                   o.status, o.delivery_date, o.fabric_details, o.fitting_remarks
            FROM orders o
            JOIN clients c ON o.client_id = c.id
            ORDER BY o.delivery_date ASC
            """, conn)
            
        if not orders_df.empty:
            st.dataframe(orders_df, use_container_width=True)
            
            st.markdown("---")
            st.subheader("Update Garment Fitting Status")
            with st.form("update_status_form"):
                u_col1, u_col2, u_col3 = st.columns(3)
                with u_col1:
                    order_select = st.selectbox("Order ID", orders_df["order_number"].tolist())
                with u_col2:
                    new_status = st.selectbox("Update Status", [
                        "Drafted", "Cut", "Basted Fitting", "Alterations", "Final Pressed", "Delivered"
                    ])
                with u_col3:
                    new_remark = st.text_input("Add Fitting Note / Correction Record")
                
                update_btn = st.form_submit_button("Update Order")
                if update_btn:
                    with get_db() as conn:
                        conn.cursor().execute("""
                        UPDATE orders 
                        SET status = ?, fitting_remarks = fitting_remarks || ' | ' || ?
                        WHERE order_number = ?
                        """, (new_status, new_remark, order_select))
                        conn.commit()
                    st.success(f"Order {order_select} updated to '{new_status}'")
                    st.rerun()
        else:
            st.info("No active orders.")
