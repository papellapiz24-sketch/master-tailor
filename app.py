import io
import os
import sys
import shutil
import sqlite3
import datetime
import hashlib
import urllib.parse
from contextlib import contextmanager

import streamlit as st
import pandas as pd

# ---------------------------------------------------------
# 1. DATABASE & PERSISTENCE ENGINE
# ---------------------------------------------------------
APP_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(APP_DIR, "master_tailor.db")
BACKUP_DIR = os.path.join(APP_DIR, "backups")

os.makedirs(BACKUP_DIR, exist_ok=True)

@contextmanager
def get_db_connection():
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    try:
        yield conn
    finally:
        conn.close()

def auto_snapshot_backup():
    if os.path.exists(DB_FILE):
        today_tag = datetime.date.today().strftime("%Y%m%d")
        dest_path = os.path.join(BACKUP_DIR, f"auto_snapshot_{today_tag}.db")
        if not os.path.exists(dest_path):
            try:
                shutil.copy2(DB_FILE, dest_path)
            except Exception:
                pass

def init_enterprise_schema():
    auto_snapshot_backup()
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # System Settings
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );
        """)
        default_settings = [
            ('brand_name', 'BAMNIYA STUDIO'),
            ('brand_tagline', 'Bespoke Master Tailoring & Haute Couture'),
            ('theme_palette', 'Linen Warm Cream'),
            ('admin_master_key', 'ADMIN176920'),
            ('tailor_master_key', '176920'),
            ('admin_recovery_phone', ''),
            ('tally_ledger', 'Tailoring Sales'),
            ('tally_cash_ledger', 'Cash'),
            ('tally_bank_ledger', 'Bank Account')
        ]
        cursor.executemany("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", default_settings)

        # Clients Registry
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

        # Measurement Vault (Contains full torso, contra hips, and trouser length)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS measurements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER NOT NULL,
            revision_label TEXT DEFAULT 'Standard',
            garment_category TEXT DEFAULT 'Master Set',
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
            trouser_length REAL,
            trouser_waist REAL,
            front_rise REAL,
            crotch_depth REAL,
            thigh REAL,
            bottom_opening REAL,
            notes TEXT,
            FOREIGN KEY (client_id) REFERENCES clients (id) ON DELETE CASCADE
        );
        """)

        # Garment Price-Book & Worker Piece-Rate Catalog
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS garment_catalog (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            garment_name TEXT UNIQUE NOT NULL,
            default_selling_price REAL DEFAULT 0.0,
            worker_making_cost REAL DEFAULT 0.0
        );
        """)
        default_garments = [
            ("Kurta saya", 1800.0, 450.0),
            ("Kurta saya with izar", 2500.0, 650.0),
            ("Pehran", 2200.0, 500.0),
            ("Only kurta", 1200.0, 300.0),
            ("Kurta Short", 1000.0, 250.0),
            ("Pajama", 800.0, 200.0),
            ("Shirt", 950.0, 250.0),
            ("Trousers", 1100.0, 300.0),
            ("Sherwani", 9500.0, 2500.0),
            ("Nehru Jacket", 3500.0, 900.0),
            ("Waistcoat", 2800.0, 750.0),
            ("Two-Piece Suit", 8500.0, 2200.0),
            ("Safari Suit", 4500.0, 1100.0)
        ]
        cursor.executemany("INSERT OR IGNORE INTO garment_catalog (garment_name, default_selling_price, worker_making_cost) VALUES (?, ?, ?)", default_garments)

        # Worker Profiles & Payroll Directory
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS workers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            worker_code TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            phone TEXT NOT NULL,
            gov_id_number TEXT,
            role_designation TEXT DEFAULT 'Tailor / Stitcher',
            status TEXT DEFAULT 'Active',
            joined_date DATE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)

        # Orders & Allotments Ledger
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
            assigned_worker_id INTEGER,
            worker_payout_amount REAL DEFAULT 0.0,
            worker_payment_status TEXT DEFAULT 'Pending',
            fitting_remarks TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (client_id) REFERENCES clients (id) ON DELETE CASCADE,
            FOREIGN KEY (measurement_id) REFERENCES measurements (id) ON DELETE CASCADE,
            FOREIGN KEY (assigned_worker_id) REFERENCES workers (id) ON DELETE SET NULL
        );
        """)

        # Self-Healing Migrations for existing DB instances
        try: cursor.execute("ALTER TABLE measurements ADD COLUMN trouser_length REAL")
        except sqlite3.OperationalError: pass

        try: cursor.execute("ALTER TABLE orders ADD COLUMN assigned_worker_id INTEGER REFERENCES workers(id)")
        except sqlite3.OperationalError: pass

        try: cursor.execute("ALTER TABLE orders ADD COLUMN worker_payout_amount REAL DEFAULT 0.0")
        except sqlite3.OperationalError: pass

        try: cursor.execute("ALTER TABLE orders ADD COLUMN worker_payment_status TEXT DEFAULT 'Pending'")
        except sqlite3.OperationalError: pass

        # User Auth Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT DEFAULT 'Tailor',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)
        conn.commit()

def get_setting(key, default=""):
    with get_db_connection() as conn:
        row = conn.cursor().execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
        return row[0] if row else default

def set_setting(key, value):
    with get_db_connection() as conn:
        conn.cursor().execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value))
        conn.commit()

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def verify_user(username: str, password_raw: str):
    with get_db_connection() as conn:
        return conn.cursor().execute("SELECT * FROM users WHERE username = ? AND password_hash = ?", 
                                     (username.strip(), hash_password(password_raw))).fetchone()

def register_user(username: str, password_raw: str, role: str = 'Tailor'):
    with get_db_connection() as conn:
        conn.cursor().execute("INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
                            (username.strip(), hash_password(password_raw), role))
        conn.commit()

# ---------------------------------------------------------
# 2. MATHEMATICAL PATTERN DRAFTING & SVG VECTOR ENGINE
# ---------------------------------------------------------
class PatternDraftingEngine:
    FIT_EASE = {
        "Slim Fit": {"chest": 2.5, "waist": 2.0, "hip": 2.0, "thigh": 1.5, "armhole": 1.0},
        "Regular Fit": {"chest": 3.5, "waist": 3.0, "hip": 3.0, "thigh": 2.5, "armhole": 1.5},
        "Relaxed Fit": {"chest": 4.5, "waist": 4.0, "hip": 4.0, "thigh": 3.5, "armhole": 2.0},
        "Qasar fit": {"chest": 5.5, "waist": 5.0, "hip": 5.0, "thigh": 4.0, "armhole": 2.5},
        "Barik kali": {"chest": 4.0, "waist": 3.5, "hip": 6.0, "thigh": 3.0, "armhole": 1.5, "kali_flare": 8.0}
    }

    @staticmethod
    def draft_kurta(m: dict, fit: str = "Regular Fit", seam_allowance: float = 0.5) -> dict:
        ease = PatternDraftingEngine.FIT_EASE.get(fit, PatternDraftingEngine.FIT_EASE["Regular Fit"])
        length = float(m.get('full_length_jacket') or 40.0)
        neck = float(m.get('neck') or 15.0)
        shoulder = float(m.get('cross_shoulder') or 17.5)
        chest = float(m.get('chest_full') or 38.0)
        waist = float(m.get('waist_stomach') or 34.0)
        hip = float(m.get('seat_hip') or 40.0)
        wrist = float(m.get('wrist') or 9.5)
        
        half_shoulder = (shoulder / 2.0)
        neck_width = (neck / 6.0) + 0.25
        neck_depth_front = (neck / 6.0) + 0.75
        shoulder_slope = 1.25
        scye_depth = (chest / 4.0) - 0.5 + (ease['armhole'] / 2.0)
        waist_level = 16.5
        hip_level = 24.0
        
        chest_width = (chest / 4.0) + (ease['chest'] / 4.0)
        waist_width = (waist / 4.0) + (ease['waist'] / 4.0)
        hip_width = (hip / 4.0) + (ease['hip'] / 4.0)
        bottom_flare = hip_width + (ease.get('kali_flare', 2.5))
        sleeve_bicep = (chest / 3.0) + 1.0
        sleeve_wrist = (wrist / 2.0) + 0.75
        
        pts_front = [
            {"name": "Neck Point", "x": neck_width, "y": 0.0},
            {"name": "Shoulder Tip", "x": half_shoulder, "y": shoulder_slope},
            {"name": "Armhole Notch", "x": half_shoulder - 0.5, "y": scye_depth * 0.65},
            {"name": "Chest (Underarm)", "x": chest_width, "y": scye_depth},
            {"name": "Waist Point", "x": waist_width, "y": waist_level},
            {"name": "Hip / Slit Top", "x": hip_width, "y": hip_level},
            {"name": "Bottom Hem", "x": bottom_flare, "y": length},
            {"name": "Center Bottom Fold", "x": 0.0, "y": length},
            {"name": "Front Neck Depth", "x": 0.0, "y": neck_depth_front},
            {"name": "Center Neck Top", "x": 0.0, "y": 0.0}
        ]
        
        return {
            "garment": "Kurta / Upper Body Panel", "fit": fit, "unit": m.get('unit', 'Inches'),
            "seam_allowance": seam_allowance,
            "metrics": {
                "Fabric Cut Length": length + 2.0,
                "Chest Line Width (1/4)": round(chest_width, 2),
                "Waist Line Width (1/4)": round(waist_width, 2),
                "Hip / Slit Width (1/4)": round(hip_width, 2),
                "Bottom Flare Width (1/4)": round(bottom_flare, 2),
                "Armhole Scye Depth": round(scye_depth, 2),
                "Shoulder Half Width": round(half_shoulder, 2),
                "Sleeve Bicep Half": round(sleeve_bicep, 2),
                "Sleeve Cuff Half": round(sleeve_wrist, 2)
            },
            "points": pts_front
        }

    @staticmethod
    def draft_trouser(m: dict, fit: str = "Regular Fit", seam_allowance: float = 0.5) -> dict:
        ease = PatternDraftingEngine.FIT_EASE.get(fit, PatternDraftingEngine.FIT_EASE["Regular Fit"])
        t_length = float(m.get('trouser_length') or 39.0)
        waist = float(m.get('trouser_waist') or 34.0)
        seat = float(m.get('seat_hip') or 40.0)
        frise = float(m.get('front_rise') or 10.5)
        thigh = float(m.get('thigh') or 24.0)
        bottom = float(m.get('bottom_opening') or 15.0)
        
        crotch_depth = frise if frise > 0 else (seat / 4.0) + 1.0
        waist_width = (waist / 4.0) + 0.75
        hip_width = (seat / 4.0) + (ease['hip'] / 4.0)
        crotch_extension = (seat / 16.0) + 0.25
        thigh_width = (thigh / 2.0) + (ease['thigh'] / 2.0)
        knee_level = (t_length / 2.0) + 2.0
        knee_width = (thigh_width * 0.78)
        bottom_half = (bottom / 2.0)
        
        pts_trouser = [
            {"name": "Waist Side", "x": 0.0, "y": 0.0},
            {"name": "Waist Center", "x": waist_width, "y": 0.0},
            {"name": "Crotch Point", "x": hip_width + crotch_extension, "y": crotch_depth},
            {"name": "Inseam Knee", "x": (knee_width / 2.0) + (hip_width / 2.0), "y": knee_level},
            {"name": "Inseam Hem", "x": (bottom_half / 2.0) + (hip_width / 2.0), "y": t_length},
            {"name": "Outseam Hem", "x": (hip_width / 2.0) - (bottom_half / 2.0), "y": t_length},
            {"name": "Outseam Knee", "x": (hip_width / 2.0) - (knee_width / 2.0), "y": knee_level},
            {"name": "Hip Level Outseam", "x": 0.0, "y": crotch_depth * 0.65}
        ]

        return {
            "garment": "Trouser / Pajama Front Panel", "fit": fit, "unit": m.get('unit', 'Inches'),
            "seam_allowance": seam_allowance,
            "metrics": {
                "Total Cut Length": t_length + 2.5,
                "Waist Band (1/4)": round(waist_width, 2),
                "Crotch Depth Line": round(crotch_depth, 2),
                "Total Thigh Width (Half)": round(thigh_width, 2),
                "Knee Level Line": round(knee_level, 2),
                "Knee Width (Half)": round(knee_width, 2),
                "Bottom Opening (Half)": round(bottom_half, 2)
            },
            "points": pts_trouser
        }

    @staticmethod
    def render_svg_pattern(draft: dict, width_px: int = 550, height_px: int = 800) -> str:
        scale = 12.5
        padding = 50
        pts = draft["points"]
        
        path_d = f"M {pts[0]['x'] * scale + padding},{pts[0]['y'] * scale + padding}"
        for pt in pts[1:]:
            path_d += f" L {pt['x'] * scale + padding},{pt['y'] * scale + padding}"
        path_d += " Z"

        markers = ""
        for pt in pts:
            px = pt['x'] * scale + padding
            py = pt['y'] * scale + padding
            markers += f"""
                <circle cx="{px}" cy="{py}" r="4" fill="#8C5E32" />
                <text x="{px + 6}" y="{py - 4}" font-size="10" font-family="sans-serif" font-weight="bold" fill="#111827">{pt['name']} ({pt['x']:.1f}\", {pt['y']:.1f}\")</text>
            """

        return f"""
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width_px} {height_px}" style="background-color:#FDFCF7; border:2px solid #D5C8B8; border-radius:12px; width:100%; height:auto;">
            <defs>
                <pattern id="grid" width="25" height="25" patternUnits="userSpaceOnUse">
                    <path d="M 25 0 L 0 0 0 25" fill="none" stroke="#EFECE6" stroke-width="1"/>
                </pattern>
            </defs>
            <rect width="100%" height="100%" fill="url(#grid)" />
            <text x="20" y="30" font-family="'Cinzel', serif" font-size="14" font-weight="bold" fill="#2B2118">{draft['garment'].upper()} — {draft['fit'].upper()}</text>
            <text x="20" y="45" font-family="sans-serif" font-size="10" fill="#6B7280">Calculated Seam Allowance: {draft['seam_allowance']}\" | Scale: Parametric Bespoke</text>
            <path d="{path_d}" fill="rgba(140, 94, 50, 0.08)" stroke="#8C5E32" stroke-width="2.5" stroke-linejoin="round" />
            {markers}
            <line x1="{padding}" y1="{padding}" x2="{padding}" y2="{pts[7]['y'] * scale + padding if len(pts) > 7 else height_px - 50}" stroke="#DC2626" stroke-width="2" stroke-dasharray="6,4" />
            <text x="{padding + 8}" y="{height_px / 2}" font-size="10" font-weight="bold" fill="#DC2626" transform="rotate(-90 {padding + 8} {height_px / 2})">◄ CENTER GRAIN FOLD LINE ►</text>
        </svg>
        """

# ---------------------------------------------------------
# 3. A5 RECEIPT & APOCALYPSE EXCEL EXPORT ENGINE
# ---------------------------------------------------------
def generate_a5_receipt_html(data: dict, brand_name: str, brand_tagline: str) -> str:
    total_amt = float(data.get('total_amount') or 0.0)
    paid_amt = float(data.get('amount_paid') or 0.0)
    bal_amt = total_amt - paid_amt

    return f"""<!DOCTYPE html><html><head><meta charset='utf-8'>
    <title>Receipt_{data['order_number']}</title>
    <style>
    @page {{ size: A5 portrait; margin: 4mm; }}
    * {{ box-sizing: border-box; font-family: Courier New, Courier, monospace; color: #000; }}
    @media print {{ .no-print {{ display: none !important; }} }}
    </style>
    </head>
    <body style='margin:0; padding:6px; font-size:11.5px; line-height:1.25;'>
    <button class='no-print' onclick='window.print()' style='display:block; width:100%; max-width:138mm; margin:0 auto 8px auto; background:#111827; color:#FFF; border:none; padding:8px; font-size:13px; font-weight:bold; cursor:pointer; border-radius:4px;'>PRINT RECEIPT (A5)</button>
    <div style='width:100%; max-width:138mm; margin:0 auto; border:1.5px solid #000; padding:8px 10px;'>
        <div style='text-align:center;'>
            <div style='font-size:15px; font-weight:bold; letter-spacing:1px;'>{brand_name}</div>
            <div style='font-size:9.5px; text-transform:uppercase;'>{brand_tagline}</div>
            <div style='font-size:10.5px; font-weight:bold; margin-top:2px;'>SALES & BESPOKE MEASUREMENT SLIP</div>
        </div>
        <hr style='border:none; border-top:1px dashed #000; margin:5px 0;'>
        <table style='width:100%; border-collapse:collapse; font-size:10.5px;'>
            <tr><td><b>CLIENT:</b> {data['client_name']}</td><td style='text-align:right;'><b>DATE:</b> {str(data['created_at'])[:10]}</td></tr>
            <tr><td><b>CLIENT ID:</b> {data['client_code']}</td><td style='text-align:right;'><b>ORDER #:</b> {data['order_number']}</td></tr>
            <tr><td><b>PHONE:</b> {data['phone']}</td><td style='text-align:right;'><b>FIT:</b> <b>{data['fit_preference']}</b></td></tr>
            <tr><td colspan='2'><b>GARMENT:</b> {data['garment_type']}</td></tr>
            <tr><td colspan='2'><b>DELIVERY:</b> {data['delivery_date']}</td></tr>
        </table>
        <hr style='border:none; border-top:1px dashed #000; margin:5px 0;'>
        <div style='font-weight:bold; font-size:10.5px; text-align:center; margin-bottom:3px;'>[ MEASUREMENT METRICS ({data['unit']}) ]</div>
        <table style='width:100%; border-collapse:collapse; font-size:10px;'>
            <tr style='background:#EEE; text-align:center;'>
                <th colspan='2' style='border:1px solid #000; padding:2px;'>UPPER BODY (TORSO)</th>
                <th colspan='2' style='border:1px solid #000; padding:2px;'>LOWER SIDE</th>
            </tr>
            <tr>
                <td style='border:1px solid #000; padding:2px 4px;'>Length (Top)</td>
                <td style='border:1px solid #000; padding:2px 4px; text-align:center;'><b>{data.get('full_length_jacket') or '-'}</b></td>
                <td style='border:1px solid #000; padding:2px 4px;'>Length (Bottom)</td>
                <td style='border:1px solid #000; padding:2px 4px; text-align:center;'><b>{data.get('trouser_length') or '-'}</b></td>
            </tr>
            <tr>
                <td style='border:1px solid #000; padding:2px 4px;'>Neck</td>
                <td style='border:1px solid #000; padding:2px 4px; text-align:center;'><b>{data.get('neck') or '-'}</b></td>
                <td style='border:1px solid #000; padding:2px 4px;'>Waist</td>
                <td style='border:1px solid #000; padding:2px 4px; text-align:center;'><b>{data.get('trouser_waist') or '-'}</b></td>
            </tr>
            <tr>
                <td style='border:1px solid #000; padding:2px 4px;'>Shoulder</td>
                <td style='border:1px solid #000; padding:2px 4px; text-align:center;'><b>{data.get('cross_shoulder') or '-'}</b></td>
                <td style='border:1px solid #000; padding:2px 4px;'>Front Rise</td>
                <td style='border:1px solid #000; padding:2px 4px; text-align:center;'><b>{data.get('front_rise') or '-'}</b></td>
            </tr>
            <tr>
                <td style='border:1px solid #000; padding:2px 4px;'>Chest</td>
                <td style='border:1px solid #000; padding:2px 4px; text-align:center;'><b>{data.get('chest_full') or '-'}</b></td>
                <td style='border:1px solid #000; padding:2px 4px;'>Crotch Depth</td>
                <td style='border:1px solid #000; padding:2px 4px; text-align:center;'><b>{data.get('crotch_depth') or '-'}</b></td>
            </tr>
            <tr>
                <td style='border:1px solid #000; padding:2px 4px;'>Stomach</td>
                <td style='border:1px solid #000; padding:2px 4px; text-align:center;'><b>{data.get('waist_stomach') or '-'}</b></td>
                <td style='border:1px solid #000; padding:2px 4px;'>Seat / Hips (Contra)</td>
                <td style='border:1px solid #000; padding:2px 4px; text-align:center;'><b>{data.get('seat_hip') or '-'}</b></td>
            </tr>
            <tr>
                <td style='border:1px solid #000; padding:2px 4px;'>Hips / Seat (Torso)</td>
                <td style='border:1px solid #000; padding:2px 4px; text-align:center;'><b>{data.get('seat_hip') or '-'}</b></td>
                <td style='border:1px solid #000; padding:2px 4px;'>Thigh</td>
                <td style='border:1px solid #000; padding:2px 4px; text-align:center;'><b>{data.get('thigh') or '-'}</b></td>
            </tr>
            <tr>
                <td style='border:1px solid #000; padding:2px 4px;'>Armhole</td>
                <td style='border:1px solid #000; padding:2px 4px; text-align:center;'><b>{data.get('armhole') or '-'}</b></td>
                <td style='border:1px solid #000; padding:2px 4px;'>Bottom Opening</td>
                <td style='border:1px solid #000; padding:2px 4px; text-align:center;'><b>{data.get('bottom_opening') or '-'}</b></td>
            </tr>
            <tr>
                <td style='border:1px solid #000; padding:2px 4px;'>Sleeve</td>
                <td style='border:1px solid #000; padding:2px 4px; text-align:center;'><b>{data.get('sleeve_length') or '-'}</b></td>
                <td style='border:1px solid #000; padding:2px 4px; background:#FAFAFA;'>-</td>
                <td style='border:1px solid #000; padding:2px 4px; background:#FAFAFA; text-align:center;'>-</td>
            </tr>
            <tr>
                <td style='border:1px solid #000; padding:2px 4px;'>Wrist</td>
                <td style='border:1px solid #000; padding:2px 4px; text-align:center;'><b>{data.get('wrist') or '-'}</b></td>
                <td style='border:1px solid #000; padding:2px 4px; background:#FAFAFA;'>-</td>
                <td style='border:1px solid #000; padding:2px 4px; background:#FAFAFA; text-align:center;'>-</td>
            </tr>
        </table>
        <hr style='border:none; border-top:1px dashed #000; margin:5px 0;'>
        <table style='width:100%; border-collapse:collapse; font-size:10.5px;'>
            <tr><td><b>TOTAL AMOUNT:</b></td><td style='text-align:right; font-weight:bold;'>Rs. {total_amt:,.2f}</td></tr>
            <tr><td><b>AMOUNT RECEIVED:</b></td><td style='text-align:right;'>Rs. {paid_amt:,.2f}</td></tr>
            <tr><td style='font-weight:bold;'>BALANCE DUE:</td><td style='text-align:right; font-weight:bold; font-size:12px;'>Rs. {bal_amt:,.2f}</td></tr>
            <tr><td><b>PAYMENT MODE:</b></td><td style='text-align:right;'>{data.get('payment_mode') or 'Cash'}</td></tr>
            <tr><td><b>PAYMENT STAGE:</b></td><td style='text-align:right; font-weight:bold;'>{data.get('payment_status') or 'Due'}</td></tr>
        </table>
        <hr style='border:none; border-top:1px dashed #000; margin:5px 0;'>
        <div style='text-align:center; font-size:9px;'>THANK YOU FOR CHOOSING {brand_name}<br>Bespoke Master Craftsmanship Guaranteed</div>
        <br>
        <table style='width:100%; font-size:9px;'><tr><td>CLIENT SIGN: ____________</td><td style='text-align:right;'>MASTER TAILOR: ____________</td></tr></table>
    </div>
    </body></html>"""

def build_apocalypse_excel_buffer():
    with get_db_connection() as conn:
        df_master = pd.read_sql_query("""
            SELECT 
                o.order_number AS [Order Reference],
                o.workflow_status AS [Workshop Stage],
                o.garment_type AS [Garment Type],
                o.fit_preference AS [Fit Preference],
                o.delivery_date AS [Target Delivery Date],
                w.name AS [Assigned Craftsman],
                o.worker_payout_amount AS [Craftsman Payout (INR)],
                o.worker_payment_status AS [Craftsman Payout Status],
                o.total_amount AS [Total Price (INR)],
                o.amount_paid AS [Amount Received (INR)],
                (o.total_amount - o.amount_paid) AS [Balance Due (INR)],
                o.payment_status AS [Payment Status],
                c.client_code AS [Client ID],
                c.full_name AS [Client Name],
                c.phone AS [Client Phone],
                m.full_length_jacket AS [Top Length],
                m.trouser_length AS [Bottom Length],
                m.neck AS [Neck],
                m.cross_shoulder AS [Shoulder],
                m.chest_full AS [Chest],
                m.waist_stomach AS [Stomach],
                m.seat_hip AS [Hips],
                m.trouser_waist AS [Waist],
                m.bottom_opening AS [Bottom Opening],
                o.created_at AS [Order Date]
            FROM orders o
            LEFT JOIN clients c ON o.client_id = c.id
            LEFT JOIN measurements m ON o.measurement_id = m.id
            LEFT JOIN workers w ON o.assigned_worker_id = w.id
            ORDER BY o.id DESC
        """, conn)

        df_clients = pd.read_sql_query("SELECT * FROM clients ORDER BY id ASC", conn)
        df_workers = pd.read_sql_query("SELECT * FROM workers ORDER BY id ASC", conn)
        df_rate_card = pd.read_sql_query("SELECT * FROM garment_catalog ORDER BY id ASC", conn)
        df_measurements = pd.read_sql_query("SELECT * FROM measurements ORDER BY id ASC", conn)
        df_orders = pd.read_sql_query("SELECT * FROM orders ORDER BY id ASC", conn)
        df_settings = pd.read_sql_query("SELECT * FROM settings", conn)

    excel_buffer = io.BytesIO()
    with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
        df_master.to_excel(writer, sheet_name='Master_Ledger', index=False)
        df_orders.to_excel(writer, sheet_name='Orders_Detailed', index=False)
        df_workers.to_excel(writer, sheet_name='Workers_Directory', index=False)
        df_rate_card.to_excel(writer, sheet_name='Garment_Price_Book', index=False)
        df_measurements.to_excel(writer, sheet_name='Measurements_Vault', index=False)
        df_clients.to_excel(writer, sheet_name='Clients_Directory', index=False)
        df_settings.to_excel(writer, sheet_name='System_Settings', index=False)

    return excel_buffer.getvalue()

def build_tally_xml(sales_acc: str, cash_acc: str, bank_acc: str) -> str:
    with get_db_connection() as conn:
        orders_df = pd.read_sql_query("SELECT o.*, c.full_name AS client_name FROM orders o LEFT JOIN clients c ON o.client_id = c.id ORDER BY o.id ASC", conn)

    xml = ['<ENVELOPE>', '  <HEADER><TALLYREQUEST>Import Data</TALLYREQUEST></HEADER>', '  <BODY>', '    <IMPORTDATA>', '      <REQUESTDESC><REPORTNAME>Vouchers</REPORTNAME></REQUESTDESC>', '      <REQUESTDATA>']
    for _, ord_row in orders_df.iterrows():
        v_date = datetime.date.today().strftime('%Y%m%d')
        if ord_row['created_at']:
            try: v_date = str(ord_row['created_at'])[:10].replace('-', '')
            except Exception: pass
        total_val, paid_val = float(ord_row.get('total_amount') or 0.0), float(ord_row.get('amount_paid') or 0.0)
        client_party = str(ord_row.get('client_name') or 'Direct Client').replace('&', '&amp;').replace('<', '&lt;')
        ord_ref = str(ord_row.get('order_number') or '')
        debit_ledger = cash_acc if 'Cash' in str(ord_row.get('payment_mode') or 'Cash') else bank_acc

        xml.append('        <TALLYMESSAGE xmlns:UDF="TallyUDF"><VOUCHER VCHTYPE="Sales" ACTION="Create">')
        xml.append(f'            <DATE>{v_date}</DATE><VOUCHERTYPENAME>Sales</VOUCHERTYPENAME><VOUCHERNUMBER>{ord_ref}</VOUCHERNUMBER><PARTYLEDGERNAME>{client_party}</PARTYLEDGERNAME>')
        xml.append(f'            <ALLLEDGERENTRIES.LIST><LEDGERNAME>{client_party}</LEDGERNAME><ISDEEMEDPOSITIVE>Yes</ISDEEMEDPOSITIVE><AMOUNT>-{total_val:.2f}</AMOUNT></ALLLEDGERENTRIES.LIST>')
        xml.append(f'            <ALLLEDGERENTRIES.LIST><LEDGERNAME>{sales_acc}</LEDGERNAME><ISDEEMEDPOSITIVE>No</ISDEEMEDPOSITIVE><AMOUNT>{total_val:.2f}</AMOUNT></ALLLEDGERENTRIES.LIST>')
        xml.append('        </VOUCHER></TALLYMESSAGE>')
        if paid_val > 0:
            xml.append('        <TALLYMESSAGE xmlns:UDF="TallyUDF"><VOUCHER VCHTYPE="Receipt" ACTION="Create">')
            xml.append(f'            <DATE>{v_date}</DATE><VOUCHERTYPENAME>Receipt</VOUCHERTYPENAME><VOUCHERNUMBER>RCT-{ord_ref}</VOUCHERNUMBER><PARTYLEDGERNAME>{client_party}</PARTYLEDGERNAME>')
            xml.append(f'            <ALLLEDGERENTRIES.LIST><LEDGERNAME>{debit_ledger}</LEDGERNAME><ISDEEMEDPOSITIVE>Yes</ISDEEMEDPOSITIVE><AMOUNT>-{paid_val:.2f}</AMOUNT></ALLLEDGERENTRIES.LIST>')
            xml.append(f'            <ALLLEDGERENTRIES.LIST><LEDGERNAME>{client_party}</LEDGERNAME><ISDEEMEDPOSITIVE>No</ISDEEMEDPOSITIVE><AMOUNT>{paid_val:.2f}</AMOUNT></ALLLEDGERENTRIES.LIST>')
            xml.append('        </VOUCHER></TALLYMESSAGE>')
    xml.extend(['      </REQUESTDATA>', '    </IMPORTDATA>', '  </BODY>', '</ENVELOPE>'])
    return "\n".join(xml)

# ---------------------------------------------------------
# 4. STREAMLIT APP ENGINE & UI STYLING
# ---------------------------------------------------------
st.set_page_config(
    page_title="Studio Management Suite",
    page_icon="✂️",
    layout="wide",
    initial_sidebar_state="expanded"
)

init_enterprise_schema()

BRAND_NAME = get_setting("brand_name", "BAMNIYA STUDIO")
BRAND_TAGLINE = get_setting("brand_tagline", "Bespoke Master Tailoring & Haute Couture")
CURRENT_THEME = get_setting("theme_palette", "Linen Warm Cream")

COLOR_PALETTES = {
    "Linen Warm Cream": {
        "bg": "#F8F5EE", "text": "#1A1612", "card_bg": "#FFFFFF", "border": "#A89885",
        "input_border": "#8C7B68", "focus_border": "#2B2118", "input_bg": "#FFFFFF",
        "btn_bg": "#2B2118", "btn_hover": "#453628", "accent_banner": "#EADBCE",
        "accent_banner_text": "#1A1612", "brand_accent": "#8C5E32", "sidebar_bg": "#1E1813"
    },
    "Ivory Royal Navy": {
        "bg": "#F4F7FB", "text": "#0B1526", "card_bg": "#FFFFFF", "border": "#9DB7D5",
        "input_border": "#5B84B1", "focus_border": "#0B2545", "input_bg": "#FFFFFF",
        "btn_bg": "#0B2545", "btn_hover": "#133D6E", "accent_banner": "#D9E6F5",
        "accent_banner_text": "#0B1526", "brand_accent": "#134B8A", "sidebar_bg": "#07172B"
    },
    "Soft Sage Atelier": {
        "bg": "#F3F7F4", "text": "#102318", "card_bg": "#FFFFFF", "border": "#92B8A0",
        "input_border": "#5A8B6B", "focus_border": "#173B25", "input_bg": "#FFFFFF",
        "btn_bg": "#173B25", "btn_hover": "#245738", "accent_banner": "#D8EADB",
        "accent_banner_text": "#102318", "brand_accent": "#2B6B44", "sidebar_bg": "#0D2115"
    }
}
active_pal = COLOR_PALETTES.get(CURRENT_THEME, COLOR_PALETTES["Linen Warm Cream"])

st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@700;800&family=Plus+Jakarta+Sans:wght@500;600;700;800&display=swap');

    .stApp {{ background-color: {active_pal['bg']} !important; color: {active_pal['text']} !important; font-family: 'Plus Jakarta Sans', sans-serif !important; }}
    .stApp p, .stApp span, .stApp label, .stApp h1, .stApp h2, .stApp h3, .stApp h4, .stMarkdown p {{ color: {active_pal['text']} !important; }}
    label[data-testid="stWidgetLabel"] p, label[data-testid="stWidgetLabel"] span {{ color: #111827 !important; font-weight: 800 !important; font-size: 0.95rem !important; }}

    div[data-baseweb="input"], div[data-baseweb="base-input"], div[data-baseweb="textarea"],
    div[data-testid="stTextInput"] > div > div, div[data-testid="stNumberInput"] > div > div,
    div[data-testid="stTextArea"] > div > div, div[data-testid="stDateInput"] > div > div,
    div[data-baseweb="select"] > div {{
        background-color: #FFFFFF !important;
        border: 2px solid {active_pal['input_border']} !important;
        border-radius: 10px !important;
    }}
    div[data-baseweb="input"]:focus-within, div[data-baseweb="base-input"]:focus-within,
    div[data-baseweb="textarea"]:focus-within, div[data-testid="stTextInput"] > div > div:focus-within,
    div[data-testid="stNumberInput"] > div > div:focus-within, div[data-testid="stTextArea"] > div > div:focus-within,
    div[data-testid="stDateInput"] > div > div:focus-within, div[data-baseweb="select"] > div:focus-within {{
        border: 2px solid {active_pal['focus_border']} !important;
        box-shadow: 0 0 0 2px rgba(0,0,0,0.15) !important;
    }}

    input, textarea, select,
    .stTextInput input, .stNumberInput input, .stTextArea textarea, .stDateInput input,
    div[data-baseweb="input"] input, div[data-baseweb="base-input"] input, div[data-baseweb="textarea"] textarea {{
        color: #000000 !important;
        -webkit-text-fill-color: #000000 !important;
        background-color: #FFFFFF !important;
        font-size: 1rem !important;
        font-weight: 700 !important;
        opacity: 1 !important;
    }}

    ::placeholder, input::placeholder, textarea::placeholder {{
        color: #6B7280 !important;
        -webkit-text-fill-color: #6B7280 !important;
        font-weight: 500 !important;
    }}

    div[data-baseweb="select"] span, div[data-baseweb="select"] div {{ color: #000000 !important; font-weight: 700 !important; }}

    .stButton > button {{
        background-color: {active_pal['btn_bg']} !important; border: 2px solid {active_pal['btn_bg']} !important;
        border-radius: 12px !important; min-height: 3.2rem !important; font-weight: 800 !important; font-size: 1rem !important;
    }}
    .stButton > button p, .stButton > button span, .stButton > button div {{ color: #FFFFFF !important; -webkit-text-fill-color: #FFFFFF !important; font-weight: 800 !important; }}
    .stButton > button:hover {{ background-color: {active_pal['btn_hover']} !important; border-color: {active_pal['btn_hover']} !important; transform: translateY(-2px) !important; }}
    .section-title-btn {{ background: {active_pal['accent_banner']} !important; color: {active_pal['accent_banner_text']} !important; border: 2px solid {active_pal['border']} !important; padding: 0.5rem 1.2rem; border-radius: 10px; font-size: 1.15rem; font-weight: 800; display: inline-block; margin: 0.8rem 0; }}
    div[data-testid="stMetric"] {{ background: {active_pal['card_bg']} !important; border: 2px solid {active_pal['border']} !important; padding: 1rem !important; border-radius: 14px !important; }}
    section[data-testid="stSidebar"] {{ background-color: {active_pal['sidebar_bg']} !important; border-right: 2px solid {active_pal['border']} !important; }}
    section[data-testid="stSidebar"] p, section[data-testid="stSidebar"] span, section[data-testid="stSidebar"] h1, section[data-testid="stSidebar"] h2, section[data-testid="stSidebar"] h3 {{ color: #FFFFFF !important; }}
    section[data-testid="stSidebar"] .stButton > button {{ background-color: rgba(255, 255, 255, 0.12) !important; border: 1px solid rgba(255, 255, 255, 0.25) !important; min-height: 2.8rem !important; }}
    section[data-testid="stSidebar"] .stButton > button p {{ color: #FFFFFF !important; -webkit-text-fill-color: #FFFFFF !important; }}
    .brand-title {{ font-family: 'Cinzel', serif !important; font-size: 2.8rem; font-weight: 800; text-align: center; color: {active_pal['text']} !important; margin-bottom: 0.1rem; }}
    .brand-tagline {{ text-align: center; color: {active_pal['brand_accent']} !important; font-size: 0.95rem; letter-spacing: 2px; text-transform: uppercase; margin-bottom: 1.2rem; font-weight: 700; }}
    .order-card {{ background: #FFFFFF !important; border: 1.5px solid {active_pal['border']} !important; border-radius: 12px; padding: 1.2rem; margin-bottom: 1rem; }}
    .order-card * {{ color: {active_pal['text']} !important; }}
</style>
""", unsafe_allow_html=True)

# Tally Sequential Stepper Engine (JS)
st.components.v1.html("""
<script>
(function() {
    function getRootDocument() { try { return window.parent.document || window.document; } catch (e) { return window.document; } }
    function handleTallyEnter(e) {
        if (e.key !== 'Enter') return;
        const doc = getRootDocument();
        const active = doc.activeElement;
        if (!active) return;
        const isInput = active.tagName === 'INPUT' && !['button', 'submit', 'checkbox', 'radio', 'file'].includes(active.type);
        const isTextArea = active.tagName === 'TEXTAREA';
        if (isInput || isTextArea) {
            if (isTextArea && e.shiftKey) return;
            e.preventDefault(); e.stopPropagation();
            active.dispatchEvent(new Event('input', { bubbles: true }));
            active.dispatchEvent(new Event('change', { bubbles: true }));
            const elements = Array.from(doc.querySelectorAll('input:not([type="hidden"]):not([disabled]):not([type="submit"]):not([type="button"]), textarea:not([disabled])')).filter(el => {
                const style = window.getComputedStyle(el);
                const rect = el.getBoundingClientRect();
                return rect.width > 0 && rect.height > 0 && style.visibility !== 'hidden' && style.display !== 'none';
            });
            const idx = elements.indexOf(active);
            if (idx > -1 && idx < elements.length - 1) {
                elements[idx + 1].focus();
                if (typeof elements[idx + 1].select === 'function') elements[idx + 1].select();
            } else if (idx === elements.length - 1) {
                const saveBtns = Array.from(doc.querySelectorAll('button')).filter(b => b.innerText && (b.innerText.includes('Save') || b.innerText.includes('Submit') || b.innerText.includes('Proceed')));
                if (saveBtns.length > 0) { saveBtns[0].focus(); setTimeout(() => saveBtns[0].click(), 250); }
            }
        }
    }
    const doc = getRootDocument();
    doc.removeEventListener('keydown', handleTallyEnter, true);
    doc.addEventListener('keydown', handleTallyEnter, true);
})();
</script>
""", height=0, width=0)

# Session State Routing
if "authenticated" not in st.session_state: st.session_state.authenticated = False
if "is_admin" not in st.session_state: st.session_state.is_admin = False
if "username" not in st.session_state: st.session_state.username = ""
if "page" not in st.session_state: st.session_state.page = "Dashboard"
if "active_client_id" not in st.session_state: st.session_state.active_client_id = None
if "active_order_no" not in st.session_state: st.session_state.active_order_no = None
if "selected_garment_type" not in st.session_state: st.session_state.selected_garment_type = None

def navigate(page_name):
    st.session_state.page = page_name

# ---------------------------------------------------------
# AUTHENTICATION GATEWAY
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
                u_name = st.text_input("Username / Master Key", type="password")
                p_word = st.text_input("Password", type="password")
                if st.form_submit_button("Sign In to Studio Hub", use_container_width=True):
                    code = u_name.strip() or p_word.strip()
                    if code == current_admin_key:
                        st.session_state.authenticated, st.session_state.is_admin, st.session_state.username = True, True, "Administrator"
                        navigate("Dashboard"); st.rerun()
                    elif code == current_tailor_key:
                        st.session_state.authenticated, st.session_state.is_admin, st.session_state.username = True, False, f"Staff Master ({BRAND_NAME})"
                        navigate("Dashboard"); st.rerun()
                    elif u_name and p_word and verify_user(u_name, p_word):
                        st.session_state.authenticated, st.session_state.is_admin, st.session_state.username = True, False, u_name.strip()
                        navigate("Dashboard"); st.rerun()
                    else:
                        st.error("Invalid credentials.")
        elif auth_tab == "Forgot Password / Reset":
            st.subheader("Reset Admin Master Password")
            if not saved_phone:
                st.warning("No recovery phone number configured in Admin Panel.")
            else:
                with st.form("reset_pwd_form"):
                    verify_p = st.text_input("Registered Admin Phone Number")
                    new_p = st.text_input("New Admin Password", type="password")
                    conf_p = st.text_input("Confirm New Password", type="password")
                    if st.form_submit_button("Reset Password", use_container_width=True):
                        if "".join(filter(str.isdigit, verify_p)) == "".join(filter(str.isdigit, saved_phone)) and new_p and new_p == conf_p:
                            set_setting("admin_master_key", new_p.strip())
                            st.success("Admin Master Password updated!")
                        else:
                            st.error("Phone verification failed.")
        else:
            with st.form("signup_form"):
                st.subheader("New Staff Registration")
                nu, np = st.text_input("Choose Username*"), st.text_input("Create Password*", type="password")
                if st.form_submit_button("Register Account", use_container_width=True) and nu and np:
                    try:
                        register_user(nu, np)
                        st.success("Account created successfully!")
                    except sqlite3.IntegrityError:
                        st.error("Username already exists.")
    st.stop()

# ---------------------------------------------------------
# SIDEBAR
# ---------------------------------------------------------
st.sidebar.markdown(f"## ✂️ **{BRAND_NAME}**")
st.sidebar.caption(f"Operator: **{st.session_state.username}**")
st.sidebar.markdown("---")
sidebar_links = [
    ("Main Hub (Home)", "Dashboard"),
    ("1. Register Client", "New Client"),
    ("2. Record Measurements", "New Measurement"),
    ("3. New Order & Allotment", "New Order"),
    ("4. Print Receipt", "Print Slip"),
    ("5. Workshop & Allotment", "Order Tracking"),
    ("6. Craftsmen & Payroll", "Workers"),
    ("7. ✂️ Pattern Studio", "Pattern Studio"),
    ("8. Order Status & Sales", "Order Status"),
    ("9. Client Database", "Client Records")
]
for label, p_target in sidebar_links:
    if st.sidebar.button(label, use_container_width=True):
        navigate(p_target)
        st.rerun()

if st.session_state.is_admin:
    if st.sidebar.button("Admin Control & Price Book", use_container_width=True):
        navigate("Admin Settings")
        st.rerun()

st.sidebar.markdown("---")
if st.sidebar.button("Logout", use_container_width=True):
    st.session_state.authenticated = False
    st.rerun()

# ---------------------------------------------------------
# 0. MAIN HUB
# ---------------------------------------------------------
if st.session_state.page == "Dashboard":
    st.markdown(f"<div class='brand-title'>{BRAND_NAME}</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='brand-tagline'>{BRAND_TAGLINE}</div>", unsafe_allow_html=True)
    with get_db_connection() as conn:
        total_clients = conn.cursor().execute("SELECT COUNT(*) FROM clients").fetchone()[0]
        active_orders = conn.cursor().execute("SELECT COUNT(*) FROM orders WHERE workflow_status != 'Delivered'").fetchone()[0]
        total_workers = conn.cursor().execute("SELECT COUNT(*) FROM workers WHERE status = 'Active'").fetchone()[0]
        pending_payroll = conn.cursor().execute("SELECT COALESCE(SUM(worker_payout_amount), 0) FROM orders WHERE worker_payment_status = 'Pending' AND assigned_worker_id IS NOT NULL").fetchone()[0]

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Clients", f"{total_clients}")
    c2.metric("In Workshop", f"{active_orders}")
    c3.metric("Active Craftsmen", f"{total_workers}")
    c4.metric("Pending Piece Payroll", f"₹{pending_payroll:,.0f}")
    
    st.markdown("<div class='section-title-btn'>Studio Action Centre</div>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Register New Client", key="hub_btn_client", use_container_width=True): navigate("New Client"); st.rerun()
        if st.button("Record Measurements", key="hub_btn_meas", use_container_width=True): navigate("New Measurement"); st.rerun()
        if st.button("Create Order & Allot Work", key="hub_btn_order", use_container_width=True): navigate("New Order"); st.rerun()
    with col2:
        if st.button("Workshop Allotments & Tracking", key="hub_btn_track", use_container_width=True): navigate("Order Tracking"); st.rerun()
        if st.button("Craftsmen Ledger & Daily Tasks", key="hub_btn_workers", use_container_width=True): navigate("Workers"); st.rerun()
        if st.button("✂️ Master Pattern Studio", key="hub_btn_pat", use_container_width=True): navigate("Pattern Studio"); st.rerun()

# ---------------------------------------------------------
# 1. REGISTER CLIENT
# ---------------------------------------------------------
elif st.session_state.page == "New Client":
    st.markdown("<div class='section-title-btn'>Step 1: Register Client Profile</div>", unsafe_allow_html=True)
    if st.button("← Back to Main Hub", key="back_client"): navigate("Dashboard"); st.rerun()
    with get_db_connection() as conn:
        rows = conn.cursor().execute("SELECT client_code FROM clients").fetchall()
        highest = max([int(r[0]) for r in rows if str(r[0]).isdigit()] or [0])
        default_code = f"{highest + 1:03d}"
    c1, c2 = st.columns(2)
    with c1:
        ccode = st.text_input("Client ID *", value=default_code)
        cname = st.text_input("Full Name *")
        cphone = st.text_input("Contact Number *")
        cemail = st.text_input("Email (Optional)")
    with c2:
        posture = st.text_area("Posture Observations", placeholder="e.g., Erect stance, sloping shoulders...")
        asymmetry = st.text_area("Asymmetry Notes", placeholder="e.g., Right shoulder 0.5 in lower...")
    if st.button("Save & Proceed to Measurements →", use_container_width=True) and ccode and cname and cphone:
        try:
            with get_db_connection() as conn:
                cur = conn.cursor()
                cur.execute("INSERT INTO clients (client_code, full_name, phone, email, posture_notes, asymmetry_notes) VALUES (?, ?, ?, ?, ?, ?)",
                            (ccode.strip(), cname.strip(), cphone.strip(), cemail.strip(), posture, asymmetry))
                new_id = cur.lastrowid
                conn.commit()
            st.session_state.active_client_id = new_id
            st.success(f"Client '{cname}' registered!")
            navigate("New Measurement"); st.rerun()
        except sqlite3.IntegrityError:
            st.error("Client ID or Phone already exists.")

# ---------------------------------------------------------
# 2. MEASUREMENTS (DYNAMIC GARMENT REMEMBERING & CONTRA HIPS)
# ---------------------------------------------------------
elif st.session_state.page == "New Measurement":
    st.markdown("<div class='section-title-btn'>Step 2: Record Client Measurements</div>", unsafe_allow_html=True)
    if st.button("← Back to Main Hub", key="back_meas"): navigate("Dashboard"); st.rerun()
    with get_db_connection() as conn:
        clients = conn.cursor().execute("SELECT id, client_code, full_name FROM clients ORDER BY id DESC").fetchall()
        catalog_rows = conn.cursor().execute("SELECT garment_name FROM garment_catalog ORDER BY id ASC").fetchall()
        garment_opts = [r['garment_name'] for r in catalog_rows] or ["Kurta saya", "Shirt", "Trousers", "Two-Piece Suit"]

    if not clients:
        st.warning("Please register a client first.")
    else:
        cdict = {f"{c['client_code']} — {c['full_name']}": c['id'] for c in clients}
        d_idx = list(cdict.values()).index(st.session_state.active_client_id) if st.session_state.active_client_id in cdict.values() else 0
        sel_c_label = st.selectbox("Client Selection", list(cdict.keys()), index=d_idx)
        sel_c_id = cdict[sel_c_label]
        st.session_state.active_client_id = sel_c_id
        
        with get_db_connection() as conn:
            prev_m = conn.cursor().execute("SELECT * FROM measurements WHERE client_id = ? ORDER BY id DESC LIMIT 1", (sel_c_id,)).fetchone()
        
        default_garment_idx = 0
        if st.session_state.selected_garment_type and st.session_state.selected_garment_type in garment_opts:
            default_garment_idx = garment_opts.index(st.session_state.selected_garment_type)
        elif prev_m and prev_m['garment_category'] in garment_opts:
            default_garment_idx = garment_opts.index(prev_m['garment_category'])

        sel_garment = st.selectbox("Choose Garment Type to Record*", garment_opts, index=default_garment_idx)
        
        h1, h2 = st.columns(2)
        with h1: rdate = st.date_input("Date Taken", datetime.date.today())
        with h2: unit = st.selectbox("Measurement Unit", ["Inches", "Centimeters"])
        
        # --- UPPER BODY / TORSO ---
        st.markdown("<div class='section-title-btn'>Upper Body (Torso) Dimensions</div>", unsafe_allow_html=True)
        flen = st.number_input("Length (Top / Kurta / Shirt / Coat)", value=float(prev_m['full_length_jacket']) if prev_m and prev_m['full_length_jacket'] else None, min_value=0.0, step=0.25, placeholder="0.00")
        neck = st.number_input("Neck", value=float(prev_m['neck']) if prev_m and prev_m['neck'] else None, min_value=0.0, step=0.25, placeholder="0.00")
        shld = st.number_input("Shoulder", value=float(prev_m['cross_shoulder']) if prev_m and prev_m['cross_shoulder'] else None, min_value=0.0, step=0.25, placeholder="0.00")
        chest = st.number_input("Chest", value=float(prev_m['chest_full']) if prev_m and prev_m['chest_full'] else None, min_value=0.0, step=0.25, placeholder="0.00")
        stom = st.number_input("Stomach", value=float(prev_m['waist_stomach']) if prev_m and prev_m['waist_stomach'] else None, min_value=0.0, step=0.25, placeholder="0.00")
        hips_upper = st.number_input("Hips / Seat (Torso Contra Entry)", value=float(prev_m['seat_hip']) if prev_m and prev_m['seat_hip'] else None, min_value=0.0, step=0.25, placeholder="0.00", key="hips_torso")
        armh = st.number_input("Armhole", value=float(prev_m['armhole']) if prev_m and prev_m['armhole'] else None, min_value=0.0, step=0.25, placeholder="0.00")
        slv = st.number_input("Sleeve", value=float(prev_m['sleeve_length']) if prev_m and prev_m['sleeve_length'] else None, min_value=0.0, step=0.25, placeholder="0.00")
        wrst = st.number_input("Wrist", value=float(prev_m['wrist']) if prev_m and prev_m['wrist'] else None, min_value=0.0, step=0.25, placeholder="0.00")

        # --- LOWER BODY ---
        st.markdown("<div class='section-title-btn'>Lower Side Dimensions</div>", unsafe_allow_html=True)
        tlen = st.number_input("Length (Trouser / Pajama / Salwar)", value=float(prev_m['trouser_length']) if prev_m and 'trouser_length' in prev_m.keys() and prev_m['trouser_length'] else None, min_value=0.0, step=0.25, placeholder="0.00")
        waist = st.number_input("Waist", value=float(prev_m['trouser_waist']) if prev_m and prev_m['trouser_waist'] else None, min_value=0.0, step=0.25, placeholder="0.00")
        frise = st.number_input("Front Rise", value=float(prev_m['front_rise']) if prev_m and prev_m['front_rise'] else None, min_value=0.0, step=0.25, placeholder="0.00")
        crotch = st.number_input("Crotch Depth", value=float(prev_m['crotch_depth']) if prev_m and prev_m['crotch_depth'] else None, min_value=0.0, step=0.25, placeholder="0.00")
        hips_lower = st.number_input("Seat / Hips (Lower Contra Entry)", value=float(hips_upper) if hips_upper is not None else (float(prev_m['seat_hip']) if prev_m and prev_m['seat_hip'] else None), min_value=0.0, step=0.25, placeholder="0.00", key="hips_bottom")
        thigh = st.number_input("Thigh", value=float(prev_m['thigh']) if prev_m and prev_m['thigh'] else None, min_value=0.0, step=0.25, placeholder="0.00")
        bot = st.number_input("Bottom Opening (Mori / Hem)", value=float(prev_m['bottom_opening']) if prev_m and prev_m['bottom_opening'] else None, min_value=0.0, step=0.25, placeholder="0.00")

        final_seat_hips = hips_lower if hips_lower is not None else hips_upper

        mnotes = st.text_area("Measurement Session Notes", value=str(prev_m['notes'] or "") if prev_m else "")
        if st.button(f"Save '{sel_garment}' & Proceed to Order / Billing →", use_container_width=True):
            with get_db_connection() as conn:
                conn.cursor().execute("""
                INSERT INTO measurements (
                    client_id, revision_label, garment_category, unit, date_recorded, 
                    full_length_jacket, neck, cross_shoulder, chest_full, waist_stomach, 
                    seat_hip, armhole, sleeve_length, wrist, 
                    trouser_length, trouser_waist, front_rise, crotch_depth, thigh, bottom_opening, notes
                ) VALUES (?, 'Standard', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    sel_c_id, sel_garment, unit, rdate, 
                    flen, neck, shld, chest, stom, 
                    final_seat_hips, armh, slv, wrst, 
                    tlen, waist, frise, crotch, thigh, bot, mnotes
                ))
                conn.commit()
            st.session_state.selected_garment_type = sel_garment
            st.success(f"Measurements saved strictly for '{sel_garment}'!")
            navigate("New Order"); st.rerun()

# ---------------------------------------------------------
# 3. NEW ORDER (WITH QASAR FIT & BARIK KALI)
# ---------------------------------------------------------
elif st.session_state.page == "New Order":
    st.markdown("<div class='section-title-btn'>New Order Booking, Auto-Billing & Work Allotment</div>", unsafe_allow_html=True)
    if st.button("← Back to Main Hub", key="back_ord"): navigate("Dashboard"); st.rerun()
    with get_db_connection() as conn:
        clients = conn.cursor().execute("SELECT id, client_code, full_name, phone FROM clients ORDER BY full_name ASC").fetchall()
        workers = conn.cursor().execute("SELECT id, worker_code, name, role_designation FROM workers WHERE status = 'Active' ORDER BY name ASC").fetchall()
        catalog = conn.cursor().execute("SELECT * FROM garment_catalog ORDER BY id ASC").fetchall()
        rows = conn.cursor().execute("SELECT order_number FROM orders").fetchall()
        highest_order = max([int(r[0]) for r in rows if str(r[0]).isdigit()] or [10000])
        next_order_id = str(highest_order + 1)
        
    catalog_dict = {item['garment_name']: (float(item['default_selling_price']), float(item['worker_making_cost'])) for item in catalog}
    
    if not clients:
        st.warning("Please register a client before billing.")
    else:
        copts = {f"{c['full_name']} (Phone: {c['phone']} | ID: {c['client_code']})": c['id'] for c in clients}
        d_idx = list(copts.values()).index(st.session_state.active_client_id) if st.session_state.active_client_id in copts.values() else 0
        sel_c_label = st.selectbox("Search & Select Client", list(copts.keys()), index=d_idx)
        sel_c_id = copts[sel_c_label]
        st.session_state.active_client_id = sel_c_id
        
        with get_db_connection() as conn:
            latest_m = conn.cursor().execute("SELECT * FROM measurements WHERE client_id = ? ORDER BY id DESC LIMIT 1", (sel_c_id,)).fetchone()
            
        if not latest_m:
            st.error("No measurements recorded for this client.")
            if st.button("Record Measurements Now →", use_container_width=True): navigate("New Measurement"); st.rerun()
        else:
            m_id = latest_m['id']
            recorded_garment = latest_m['garment_category']
            catalog_keys = list(catalog_dict.keys())
            g_idx = catalog_keys.index(recorded_garment) if recorded_garment in catalog_keys else 0
            
            o1, o2 = st.columns(2)
            with o1:
                ord_no = st.text_input("Order Reference ID*", value=next_order_id)
                g_type = st.selectbox("Garment to Stitch*", catalog_keys, index=g_idx)
                
                fit_options = ["Slim Fit", "Regular Fit", "Relaxed Fit", "Qasar fit", "Barik kali"]
                fit_pref = st.selectbox("Fit Preference", fit_options)
                
                auto_sell_p, auto_making_p = catalog_dict.get(g_type, (1500.0, 400.0))
                
                st.markdown("<div class='section-title-btn'>Worker Allotment (Cloth Making)</div>", unsafe_allow_html=True)
                worker_opts = {"Unassigned / Later Allotment": None}
                for w in workers:
                    worker_opts[f"{w['name']} ({w['worker_code']} - {w['role_designation']})"] = w['id']
                
                sel_w_label = st.selectbox("Assign Craftsman / Tailor for this Garment", list(worker_opts.keys()))
                assigned_w_id = worker_opts[sel_w_label]
                worker_cost = st.number_input("Worker Piece-Rate Making Cost (₹)", value=float(auto_making_p), step=50.0)

            with o2:
                tot_p = st.number_input("Total Client Price (₹)* [Auto-filled]", value=float(auto_sell_p), step=100.0)
                amt_p = st.number_input("Initial Advance Paid (₹)", value=0.0, step=500.0)
                pay_m = st.selectbox("Payment Mode*", ["Cash", "UPI / QR", "Credit/Debit Card", "Bank Transfer"])
                
                c_tot, c_paid = float(tot_p or 0.0), float(amt_p or 0.0)
                auto_stat = "Fully Paid" if (c_paid >= c_tot and c_tot > 0) else ("Half Paid" if c_paid == (c_tot/2) and c_tot > 0 else ("Advance Paid" if c_paid > 0 else "Due"))
                pay_stat = st.selectbox("Payment Status*", ["Due", "Advance Paid", "Half Paid", "Fully Paid"], index=["Due", "Advance Paid", "Half Paid", "Fully Paid"].index(auto_stat))
                deliv_d = st.date_input("Target Delivery Date", datetime.date.today() + datetime.timedelta(days=12))

            fabric_d = st.text_area("Fabric Specifications & Mill Details")
            fit_rem = st.text_area("Specific Cutting / Fitting Requirements")
            if st.button(f"Submit Order for '{g_type}' & Generate Receipt →", use_container_width=True):
                with get_db_connection() as conn:
                    conn.cursor().execute("""
                    INSERT INTO orders (
                        order_number, client_id, measurement_id, garment_type, fit_preference, 
                        fabric_details, total_amount, amount_paid, payment_mode, payment_status, delivery_date, 
                        assigned_worker_id, worker_payout_amount, worker_payment_status, fitting_remarks
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Pending', ?)
                    """, (
                        ord_no.strip(), sel_c_id, m_id, g_type, fit_pref,
                        fabric_d, c_tot, c_paid, pay_m, pay_stat, deliv_d,
                        assigned_w_id, worker_cost, fit_rem
                    ))
                    conn.commit()
                st.session_state.active_order_no = ord_no.strip()
                st.success(f"Order {ord_no} for '{g_type}' booked successfully!")
                navigate("Print Slip"); st.rerun()

# ---------------------------------------------------------
# 4. PRINT RECEIPT
# ---------------------------------------------------------
elif st.session_state.page == "Print Slip":
    st.markdown("<div class='section-title-btn'>Step 4: Print A5 Receipt Slip</div>", unsafe_allow_html=True)
    if st.button("← Back to Main Hub", key="back_slip"): navigate("Dashboard"); st.rerun()
    with get_db_connection() as conn:
        orders = conn.cursor().execute("SELECT o.order_number, c.full_name FROM orders o JOIN clients c ON o.client_id = c.id ORDER BY o.id DESC").fetchall()
    if not orders:
        st.info("No orders found to print.")
    else:
        opts = {f"{o['order_number']} — {o['full_name']}": o['order_number'] for o in orders}
        d_idx = list(opts.values()).index(st.session_state.active_order_no) if st.session_state.active_order_no in opts.values() else 0
        sel_order = st.selectbox("Select Order", list(opts.keys()), index=d_idx)
        ord_no = opts[sel_order]
        with get_db_connection() as conn:
            slip_data = conn.cursor().execute("""
            SELECT o.*, c.client_code, c.full_name AS client_name, c.phone, c.email,
                   m.unit, m.neck, m.chest_full, m.waist_stomach, m.cross_shoulder, m.armhole, m.wrist, 
                   m.sleeve_length, m.full_length_jacket, m.trouser_length, m.trouser_waist, m.seat_hip, 
                   m.thigh, m.bottom_opening, m.front_rise, m.crotch_depth
            FROM orders o 
            JOIN clients c ON o.client_id = c.id 
            JOIN measurements m ON o.measurement_id = m.id 
            WHERE o.order_number = ?
            """, (ord_no,)).fetchone()
        if slip_data:
            receipt_html = generate_a5_receipt_html(dict(slip_data), BRAND_NAME, BRAND_TAGLINE)
            st.components.v1.html(receipt_html, height=720, scrolling=True)

# ---------------------------------------------------------
# 5. WORKSHOP TRACKING & WORKER ALLOTMENTS
# ---------------------------------------------------------
elif st.session_state.page == "Order Tracking":
    st.markdown("<div class='section-title-btn'>Workshop Production & Craftsmen Allotments</div>", unsafe_allow_html=True)
    if st.button("← Back to Main Hub", key="back_tr"): navigate("Dashboard"); st.rerun()
    
    with get_db_connection() as conn:
        df = pd.read_sql_query("""
            SELECT o.id, o.order_number, c.full_name AS client_name, c.phone, o.garment_type, 
                   o.workflow_status, o.delivery_date, o.assigned_worker_id, w.name as worker_name,
                   o.worker_payout_amount, o.worker_payment_status
            FROM orders o 
            JOIN clients c ON o.client_id = c.id 
            LEFT JOIN workers w ON o.assigned_worker_id = w.id
            ORDER BY o.delivery_date ASC
        """, conn)
        workers_list = conn.cursor().execute("SELECT id, name, worker_code FROM workers WHERE status = 'Active'").fetchall()

    if df.empty:
        st.info("No orders in workshop production.")
    else:
        stages = ['Drafted', 'Fabric Cut', 'Basted Fitting', 'Alterations', 'Final Pressed', 'Delivered']
        worker_map = {f"{w['name']} ({w['worker_code']})": w['id'] for w in workers_list}
        worker_map["Unassigned"] = None
        
        for _, r in df.iterrows():
            w_disp = r['worker_name'] if r['worker_name'] else 'Unassigned'
            st.markdown(f"""
            <div class='order-card'>
                <b>{r['order_number']} — {r['garment_type']}</b> (Client: {r['client_name']}) | 
                Target: <b>{r['delivery_date']}</b> | Assigned Tailor: <b>{w_disp}</b> (Making Fee: ₹{r['worker_payout_amount']:,.0f})<br>
                Stage: <b>{r['workflow_status']}</b> | Craftsman Payout: <b>{r['worker_payment_status']}</b>
            </div>
            """, unsafe_allow_html=True)
            
            c_stg, c_work, c_del = st.columns([2, 2, 1])
            with c_stg:
                cur_idx = stages.index(r['workflow_status']) if r['workflow_status'] in stages else 0
                nstg = st.selectbox("Stage", stages, index=cur_idx, key=f"stg_{r['order_number']}")
                if nstg != r['workflow_status']:
                    with get_db_connection() as conn:
                        conn.cursor().execute("UPDATE orders SET workflow_status = ? WHERE order_number = ?", (nstg, r['order_number']))
                        conn.commit()
                    st.rerun()
            with c_work:
                curr_w_label = "Unassigned"
                for k, v in worker_map.items():
                    if v == r['assigned_worker_id']:
                        curr_w_label = k
                        break
                new_w_label = st.selectbox("Re-Allot Craftsman", list(worker_map.keys()), index=list(worker_map.keys()).index(curr_w_label), key=f"allot_{r['order_number']}")
                if worker_map[new_w_label] != r['assigned_worker_id']:
                    with get_db_connection() as conn:
                        conn.cursor().execute("UPDATE orders SET assigned_worker_id = ? WHERE order_number = ?", (worker_map[new_w_label], r['order_number']))
                        conn.commit()
                    st.rerun()
            with c_del:
                if st.button("Delete", key=f"del_o_{r['order_number']}", use_container_width=True):
                    with get_db_connection() as conn:
                        conn.cursor().execute("DELETE FROM orders WHERE order_number = ?", (r['order_number'],))
                        conn.commit()
                    st.rerun()

# ---------------------------------------------------------
# 6. WORKER PROFILES, DAILY TASKS & PAYROLL LEDGER
# ---------------------------------------------------------
elif st.session_state.page == "Workers":
    st.markdown("<div class='section-title-btn'>Craftsmen Management, Daily Tasks & Piece-Rate Payroll</div>", unsafe_allow_html=True)
    if st.button("← Back to Main Hub", key="back_workers"): navigate("Dashboard"); st.rerun()
    
    tab_workers, tab_add_worker, tab_payouts = st.tabs(["Craftsmen Profiles & Performance", "Register New Craftsman", "Pay Craftsman Commissions"])
    
    with tab_workers:
        with get_db_connection() as conn:
            workers_df = pd.read_sql_query("SELECT * FROM workers ORDER BY id DESC", conn)
            orders_df = pd.read_sql_query("SELECT o.*, c.full_name as client_name FROM orders o JOIN clients c ON o.client_id = c.id WHERE o.assigned_worker_id IS NOT NULL", conn)
            
        if workers_df.empty:
            st.info("No craftsmen profiles registered yet.")
        else:
            for _, w in workers_df.iterrows():
                w_orders = orders_df[orders_df['assigned_worker_id'] == w['id']]
                completed_orders = w_orders[w_orders['workflow_status'].isin(['Final Pressed', 'Delivered'])]
                pending_pay = w_orders[w_orders['worker_payment_status'] == 'Pending']['worker_payout_amount'].sum()
                settled_pay = w_orders[w_orders['worker_payment_status'] == 'Settled']['worker_payout_amount'].sum()
                
                with st.container():
                    st.markdown(f"""
                    <div class='order-card'>
                        <div style="display:flex; justify-content:space-between;">
                            <h3>{w['name']} ({w['worker_code']}) — {w['role_designation']}</h3>
                            <span style="font-weight:800; font-size:1.1rem; color:{active_pal['brand_accent']};">Status: {w['status']}</span>
                        </div>
                        <b>Phone:</b> {w['phone']} | <b>Govt ID:</b> {w['gov_id_number'] or 'N/A'}<br>
                        <b>Total Allotted:</b> {len(w_orders)} | <b>Completed:</b> {len(completed_orders)} | 
                        <b>Unpaid Due:</b> ₹{pending_pay:,.0f} | <b>Total Settled:</b> ₹{settled_pay:,.0f}
                    </div>
                    """, unsafe_allow_html=True)
                    with st.expander(f"View Allotment History for {w['name']}"):
                        if w_orders.empty: st.caption("No garments allotted.")
                        else: st.dataframe(w_orders[['order_number', 'garment_type', 'client_name', 'workflow_status', 'worker_payout_amount', 'worker_payment_status', 'created_at']], use_container_width=True)

    with tab_add_worker:
        with st.form("new_worker_form"):
            st.subheader("Register New Workshop Craftsman")
            w1, w2 = st.columns(2)
            with w1:
                w_code = st.text_input("Worker ID / Code*", value=f"WRK-{datetime.date.today().strftime('%y')}{datetime.datetime.now().strftime('%M%S')}")
                w_name = st.text_input("Craftsman Full Name*")
                w_phone = st.text_input("Contact Phone Number*")
            with w2:
                w_govid = st.text_input("Govt ID Number (Aadhaar / Voter ID)")
                w_role = st.selectbox("Designation", ["Master Tailor / Cutter", "Coat Stitcher", "Pant Stitcher", "Kurta Specialist", "Sherwani Hand-Embroiderer", "Ironing & Finisher", "General Assistant"])
                w_status = st.selectbox("Status", ["Active", "On Leave", "Inactive"])
                
            if st.form_submit_button("Register Craftsman Profile", use_container_width=True) and w_name and w_phone:
                try:
                    with get_db_connection() as conn:
                        conn.cursor().execute("INSERT INTO workers (worker_code, name, phone, gov_id_number, role_designation, status, joined_date) VALUES (?, ?, ?, ?, ?, ?, ?)",
                                            (w_code.strip(), w_name.strip(), w_phone.strip(), w_govid.strip(), w_role, w_status, datetime.date.today()))
                        conn.commit()
                    st.success(f"Profile created for {w_name}!")
                    st.rerun()
                except sqlite3.IntegrityError:
                    st.error("Worker Code already registered.")

    with tab_payouts:
        st.subheader("💸 Settle Craftsman Piece-Rate Commissions")
        with get_db_connection() as conn:
            pending_df = pd.read_sql_query("SELECT o.id, o.order_number, w.name as worker_name, w.worker_code, o.garment_type, o.workflow_status, o.worker_payout_amount FROM orders o JOIN workers w ON o.assigned_worker_id = w.id WHERE o.worker_payment_status = 'Pending' ORDER BY o.id DESC", conn)
            
        if pending_df.empty:
            st.success("All craftsman piece-rate commissions are completely settled!")
        else:
            for _, pr in pending_df.iterrows():
                c_p1, c_p2 = st.columns([3.5, 1])
                with c_p1:
                    st.markdown(f"**{pr['worker_name']}** ({pr['worker_code']}) — Order: `{pr['order_number']}` ({pr['garment_type']}) | Stage: `{pr['workflow_status']}` | **Due: ₹{pr['worker_payout_amount']:,.2f}**")
                with c_p2:
                    if st.button(f"Mark Paid (₹{pr['worker_payout_amount']:,.0f})", key=f"pay_wrk_{pr['id']}", use_container_width=True):
                        with get_db_connection() as conn:
                            conn.cursor().execute("UPDATE orders SET worker_payment_status = 'Settled' WHERE id = ?", (pr['id'],))
                            conn.commit()
                        st.success("Payment marked as settled!")
                        st.rerun()

# ---------------------------------------------------------
# 7. MASTER PATTERN STUDIO (2D VECTOR CUTTING BLUEPRINTS)
# ---------------------------------------------------------
elif st.session_state.page == "Pattern Studio":
    st.markdown("<div class='section-title-btn'>✂️ Master Pattern Studio & Parametric Cutting Engine</div>", unsafe_allow_html=True)
    if st.button("← Back to Main Hub", key="back_pat"): navigate("Dashboard"); st.rerun()

    with get_db_connection() as conn:
        clients = conn.cursor().execute("SELECT id, client_code, full_name, phone FROM clients ORDER BY full_name ASC").fetchall()

    if not clients:
        st.warning("Please register a client with measurements first.")
    else:
        cdict = {f"{c['full_name']} (ID: {c['client_code']})": c['id'] for c in clients}
        d_idx = list(cdict.values()).index(st.session_state.active_client_id) if st.session_state.active_client_id in cdict.values() else 0
        sel_c_label = st.selectbox("Select Client for Pattern Generation", list(cdict.keys()), index=d_idx)
        sel_c_id = cdict[sel_c_label]

        with get_db_connection() as conn:
            m_row = conn.cursor().execute("SELECT * FROM measurements WHERE client_id = ? ORDER BY id DESC LIMIT 1", (sel_c_id,)).fetchone()

        if not m_row:
            st.error("No measurements recorded for this client. Please record measurements first.")
        else:
            m_data = dict(m_row)
            c_p1, c_p2, c_p3 = st.columns([1.5, 1.5, 1])
            with c_p1:
                pattern_garment = st.selectbox("Draft Garment Block", ["Kurta / Upper Body Panel", "Trouser / Pajama Front Panel"])
            with c_p2:
                pattern_fit = st.selectbox("Apply Fit Ease Calculation", ["Slim Fit", "Regular Fit", "Relaxed Fit", "Qasar fit", "Barik kali"], index=3)
            with c_p3:
                seam_allowance = st.number_input("Seam Allowance (Inches)", value=0.5, step=0.25)

            if "Kurta" in pattern_garment:
                draft = PatternDraftingEngine.draft_kurta(m_data, pattern_fit, seam_allowance)
            else:
                draft = PatternDraftingEngine.draft_trouser(m_data, pattern_fit, seam_allowance)

            col_diagram, col_chalk = st.columns([1.3, 1])
            with col_diagram:
                st.markdown("#### 📐 Parametric 2D Blueprint (Center Fold)")
                svg_code = PatternDraftingEngine.render_svg_pattern(draft)
                st.components.v1.html(svg_code, height=720, scrolling=True)
                st.download_button(
                    label="💾 Export Cutting Pattern Vector (.SVG)",
                    data=svg_code,
                    file_name=f"{m_data.get('garment_category', 'Pattern')}_{pattern_fit}_{sel_c_id}.svg",
                    mime="image/svg+xml",
                    use_container_width=True
                )

            with col_chalk:
                st.markdown("#### ✂️ Master Cutter Chalking Table")
                st.info(f"**Garment Block:** {draft['garment']}\n**Applied Fit:** {draft['fit']}\n**Client Unit:** {draft['unit']}")
                metrics_df = pd.DataFrame(list(draft["metrics"].items()), columns=["Chalk Marking Parameter", "Exact Dimension (Inches)"])
                st.dataframe(metrics_df, use_container_width=True, hide_index=True)

                st.markdown("#### 📍 Coordinate Nodes for Workshop Masters")
                pts_df = pd.DataFrame(draft["points"])
                st.dataframe(pts_df, use_container_width=True, hide_index=True)

# ---------------------------------------------------------
# 8. FINANCIAL SALES REPORT
# ---------------------------------------------------------
elif st.session_state.page == "Order Status":
    st.markdown("<div class='section-title-btn'>Order Status & Financial Sales Report</div>", unsafe_allow_html=True)
    if st.button("← Back to Main Hub", key="back_fin"): navigate("Dashboard"); st.rerun()
    with get_db_connection() as conn:
        df = pd.read_sql_query("""
            SELECT o.order_number, c.full_name AS client_name, c.phone, o.garment_type, o.payment_status, 
                   o.total_amount, o.amount_paid, (o.total_amount - o.amount_paid) as balance_due,
                   w.name AS craftsman, o.worker_payout_amount, o.worker_payment_status
            FROM orders o 
            JOIN clients c ON o.client_id = c.id
            LEFT JOIN workers w ON o.assigned_worker_id = w.id
        """, conn)
        
    if df.empty:
        st.info("No billing records found.")
    else:
        tot_rev, tot_col = df['total_amount'].sum(), df['amount_paid'].sum()
        m1, m2, m3 = st.columns(3)
        m1.metric("Gross Sales Booked", f"₹{tot_rev:,.2f}")
        m2.metric("Payments Collected", f"₹{tot_col:,.2f}")
        m3.metric("Outstanding Balance Due", f"₹{(tot_rev - tot_col):,.2f}")
        st.dataframe(df, use_container_width=True)
        
        st.markdown("### 💬 Outstanding Payment Reminders & Settlements")
        unpaid = df[df['balance_due'] > 0]
        for _, uo in unpaid.iterrows():
            c_d, c_msg, c_set = st.columns([2.5, 1.5, 1.2])
            with c_d:
                st.markdown(f"**{uo['client_name']}** (`{uo['phone']}`) | Due: **₹{uo['balance_due']:,.2f}**")
            with c_msg:
                clean_p = "".join(filter(str.isdigit, str(uo['phone'])))
                if len(clean_p) == 10: clean_p = "91" + clean_p
                wa_txt = f"Dear {uo['client_name']},\nReminder from *{BRAND_NAME}* regarding order *{uo['order_number']}*.\nBalance Due: *₹{uo['balance_due']:,.2f}*."
                st.markdown(f"""<a href="https://wa.me/{clean_p}?text={urllib.parse.quote(wa_txt)}" target="_blank"><button style="width:100%; background:#25D366; color:#FFF; border:none; border-radius:8px; padding:6px; font-weight:bold;">💬 Send WhatsApp</button></a>""", unsafe_allow_html=True)
            with c_set:
                if st.button(f"Mark Full Paid", key=f"rec_{uo['order_number']}", use_container_width=True):
                    with get_db_connection() as conn:
                        conn.cursor().execute("UPDATE orders SET amount_paid = total_amount, payment_status = 'Fully Paid' WHERE order_number = ?", (uo['order_number'],))
                        conn.commit()
                    st.rerun()

# ---------------------------------------------------------
# 9. CLIENT DATABASE
# ---------------------------------------------------------
elif st.session_state.page == "Client Records":
    st.markdown("<div class='section-title-btn'>Client Database</div>", unsafe_allow_html=True)
    if st.button("← Back to Main Hub", key="back_cdb"): navigate("Dashboard"); st.rerun()
    with get_db_connection() as conn:
        clients_df = pd.read_sql_query("SELECT id, client_code, full_name, phone, posture_notes, asymmetry_notes FROM clients ORDER BY full_name", conn)
    sq = st.text_input("Search Client by Name or Phone")
    if sq: clients_df = clients_df[clients_df.apply(lambda r: sq.lower() in r.astype(str).str.lower().values, axis=1)]
    for _, c in clients_df.iterrows():
        c_i, c_a, c_d = st.columns([3, 2, 0.8])
        with c_i: st.markdown(f"**{c['full_name']}** (ID: `{c['client_code']}` | Phone: `{c['phone']}`)")
        with c_a:
            with st.popover(f"Actions for {c['full_name']}"):
                if st.button("Update Measurements", key=f"um_{c['id']}", use_container_width=True):
                    st.session_state.active_client_id = c['id']
                    navigate("New Measurement"); st.rerun()
                if st.button("Book Order", key=f"bo_{c['id']}", use_container_width=True):
                    st.session_state.active_client_id = c['id']
                    navigate("New Order"); st.rerun()
        with c_d:
            if st.button("Delete", key=f"del_c_{c['id']}", use_container_width=True):
                with get_db_connection() as conn:
                    conn.cursor().execute("DELETE FROM clients WHERE id = ?", (c['id'],))
                    conn.commit()
                st.rerun()

# ---------------------------------------------------------
# 10. ADMIN PANEL (PRICE-BOOK & MASTER CONFIGURATION)
# ---------------------------------------------------------
elif st.session_state.page == "Admin Settings":
    if not st.session_state.is_admin:
        st.error("Unauthorized access. Administrator Master Password required.")
        st.stop()
        
    st.markdown("<div class='section-title-btn'>Admin Control Panel & Price Book</div>", unsafe_allow_html=True)
    if st.button("← Back to Main Hub", key="back_adm"): navigate("Dashboard"); st.rerun()

    st.markdown("### 🏷️ Studio Garment Price Book & Worker Piece-Rate Card")
    st.write("Set fixed selling prices for clients and fixed stitching fees for workers. New orders will automatically populate with these amounts.")
    
    with get_db_connection() as conn:
        cat_df = pd.read_sql_query("SELECT * FROM garment_catalog ORDER BY id ASC", conn)
        
    for _, row in cat_df.iterrows():
        cp1, cp2, cp3, cp4 = st.columns([2, 1.5, 1.5, 1])
        with cp1:
            g_name = st.text_input("Garment", value=row['garment_name'], key=f"gname_{row['id']}")
        with cp2:
            s_price = st.number_input("Client Price (₹)", value=float(row['default_selling_price']), step=100.0, key=f"sprice_{row['id']}")
        with cp3:
            w_cost = st.number_input("Worker Piece Rate (₹)", value=float(row['worker_making_cost']), step=50.0, key=f"wcost_{row['id']}")
        with cp4:
            st.write("")
            if st.button("Save", key=f"save_rate_{row['id']}", use_container_width=True):
                with get_db_connection() as conn:
                    conn.cursor().execute("UPDATE garment_catalog SET garment_name = ?, default_selling_price = ?, worker_making_cost = ? WHERE id = ?", (g_name, s_price, w_cost, row['id']))
                    conn.commit()
                st.success(f"Updated {g_name} rate!")
                st.rerun()

    with st.expander("➕ Add New Garment to Studio Price Book"):
        with st.form("add_new_catalog_item"):
            ng1, ng2, ng3 = st.columns(3)
            with ng1: n_gname = st.text_input("New Garment Name*")
            with ng2: n_sprice = st.number_input("Default Selling Price (₹)*", value=1500.0, step=100.0)
            with ng3: n_wcost = st.number_input("Worker Stitching Fee (₹)*", value=400.0, step=50.0)
            if st.form_submit_button("Add Garment to Catalog") and n_gname:
                with get_db_connection() as conn:
                    conn.cursor().execute("INSERT OR IGNORE INTO garment_catalog (garment_name, default_selling_price, worker_making_cost) VALUES (?, ?, ?)", (n_gname.strip(), n_sprice, n_wcost))
                    conn.commit()
                st.success("New garment added to Price Book!")
                st.rerun()

    st.markdown("---")
    st.markdown("### 💾 Local Storage & Snapshot Backups")
    st.info(f"**Database Location:** `{DB_FILE}`")
    c_bk1, c_bk2 = st.columns(2)
    with c_bk1:
        if st.button("🔄 Create Manual Snapshot Backup", use_container_width=True):
            ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            bpath = os.path.join(BACKUP_DIR, f"manual_backup_{ts}.db")
            shutil.copy2(DB_FILE, bpath)
            st.success(f"Backup saved: `{os.path.basename(bpath)}`")
    with c_bk2:
        bk_files = [f for f in os.listdir(BACKUP_DIR) if f.endswith(".db")]
        if bk_files:
            s_bk = st.selectbox("Select Backup to Restore", sorted(bk_files, reverse=True))
            if st.button("⚠️ Restore Selected Backup", use_container_width=True):
                shutil.copy2(os.path.join(BACKUP_DIR, s_bk), DB_FILE)
                st.success("Database restored successfully!")
                st.rerun()

    st.markdown("---")
    st.markdown("### 🏛️ Apocalypse-Grade Master Data Backup (Excel .xlsx)")
    st.download_button(
        label="🛡️ Download Apocalypse Master Backup (Full Excel .xlsx)",
        data=build_apocalypse_excel_buffer(),
        file_name=f"{BRAND_NAME.replace(' ', '_')}_Apocalypse_Backup_{datetime.date.today().strftime('%Y-%m-%d')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True
    )

    st.markdown("---")
    st.markdown("### Studio Branding & Security Configurations")
    with st.form("admin_settings_form"):
        b_name = st.text_input("Brand Name", value=BRAND_NAME)
        b_tag = st.text_input("Brand Tagline", value=BRAND_TAGLINE)
        adm_pwd = st.text_input("Admin Password", value=get_setting("admin_master_key", "ADMIN176920"), type="password")
        tlr_pwd = st.text_input("Tailor Password", value=get_setting("tailor_master_key", "176920"), type="password")
        rec_phone = st.text_input("Admin Recovery Phone", value=get_setting("admin_recovery_phone", ""))
        chosen_theme = st.selectbox("Theme Palette", list(COLOR_PALETTES.keys()), index=list(COLOR_PALETTES.keys()).index(CURRENT_THEME) if CURRENT_THEME in COLOR_PALETTES else 0)
        if st.form_submit_button("Save Studio Configurations", use_container_width=True):
            set_setting("brand_name", b_name.strip())
            set_setting("brand_tagline", b_tag.strip())
            set_setting("admin_master_key", adm_pwd.strip())
            set_setting("tailor_master_key", tlr_pwd.strip())
            set_setting("admin_recovery_phone", rec_phone.strip())
            set_setting("theme_palette", chosen_theme)
            st.success("Configurations updated successfully!")
            st.rerun()

    st.markdown("---")
    st.markdown("### Tally Prime XML Integration")
    s_acc = st.text_input("Sales Ledger Name", value=get_setting("tally_ledger", "Tailoring Sales"))
    c_acc = st.text_input("Cash Ledger Name", value=get_setting("tally_cash_ledger", "Cash"))
    b_acc = st.text_input("Bank Ledger Name", value=get_setting("tally_bank_ledger", "Bank Account"))
    st.download_button(
        label="Export Sales & Receipts for Tally Prime (.xml)",
        data=build_tally_xml(s_acc, c_acc, b_acc),
        file_name=f"Tally_Vouchers_{datetime.date.today().strftime('%Y-%m-%d')}.xml",
        mime="application/xml",
        use_container_width=True
    )
