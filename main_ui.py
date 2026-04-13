"""
STREAMLIT UI - GOOGLE SHEETS DATA ENTRY (SIMPLE TEXT FORMAT)
हे चालवण्यासाठी: streamlit run streamlit_app.py
"""

import streamlit as st
import gspread
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
import os
from datetime import datetime
import pandas as pd
import time
import re

# --- Page Configuration ---
st.set_page_config(
    page_title="Google Sheets Data Entry",
    page_icon="📊",
    layout="wide"
)

# --- Background Image ---
BACKGROUND_IMAGE_URL = "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcT6VkIkJpjQFnlAtsLA9pFkFzo-h01XsN6cyw&s"

# --- Custom CSS ---
st.markdown(f"""
    <style>
    [data-testid="stAppViewContainer"] {{
        background-image: url("{BACKGROUND_IMAGE_URL}");
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
        background-attachment: fixed;
    }}
    [data-testid="stAppViewContainer"]::before {{
        content: "";
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: rgba(0,0,0,0.65);
        z-index: 0;
    }}
    [data-testid="stAppViewContainer"] > div {{
        position: relative;
        z-index: 1;
    }}
    [data-testid="stSidebar"] {{
        background-color: rgba(0,0,0,0.85);
        backdrop-filter: blur(10px);
        border-radius: 0 20px 20px 0;
    }}
    h1, h2, h3, .stMarkdown, label, .stTextInput label, .stSelectbox label {{
        color: white !important;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
    }}
    .stButton > button {{
        background: linear-gradient(135deg, #00b4db, #0083b0);
        color: white;
        border-radius: 30px;
        font-weight: bold;
        font-size: 1rem;
        padding: 0.5rem 1rem;
        border: none;
        transition: all 0.3s ease;
        width: 100%;
    }}
    .stButton > button:hover {{
        transform: scale(1.02);
        background: linear-gradient(135deg, #0083b0, #00b4db);
    }}
    .stDataFrame {{
        background-color: rgba(0,0,0,0.8);
        border-radius: 15px;
        padding: 10px;
    }}
    .success-box {{
        background: linear-gradient(135deg, #00b09b, #96c93d);
        padding: 1rem;
        border-radius: 15px;
        margin: 1rem 0;
        text-align: center;
        color: white;
    }}
    .flow-text {{
        font-family: monospace;
        font-size: 1rem;
        color: white;
        background: rgba(0,0,0,0.5);
        padding: 15px;
        border-radius: 10px;
        text-align: center;
    }}
    </style>
""", unsafe_allow_html=True)

# --- Initialize Session State ---
def init_session_state():
    if 'client' not in st.session_state:
        st.session_state.client = None
    if 'all_sheets' not in st.session_state:
        st.session_state.all_sheets = []
    if 'current_spreadsheet' not in st.session_state:
        st.session_state.current_spreadsheet = None
    if 'current_worksheet' not in st.session_state:
        st.session_state.current_worksheet = None
    if 'headers' not in st.session_state:
        st.session_state.headers = []
    if 'fields' not in st.session_state:
        st.session_state.fields = []
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'fields_loaded' not in st.session_state:
        st.session_state.fields_loaded = False
    if 'submit_key' not in st.session_state:
        st.session_state.submit_key = 0

init_session_state()

# --- Google API Scopes ---
SCOPES = ['https://www.googleapis.com/auth/spreadsheets',
          'https://www.googleapis.com/auth/drive']

# --- Authentication ---
def authenticate_user():
    try:
        creds = None
        if os.path.exists('token.json'):
            creds = Credentials.from_authorized_user_file('token.json', SCOPES)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
                creds = flow.run_local_server(port=0)
            with open('token.json', 'w') as token:
                token.write(creds.to_json())
        st.session_state.client = gspread.authorize(creds)
        st.session_state.authenticated = True
        return True, "✅ Successfully authenticated!"
    except FileNotFoundError:
        return False, "❌ credentials.json not found!"
    except Exception as e:
        return False, f"❌ Auth error: {e}"

# --- Get ALL Google Sheets ---
def get_all_google_sheets():
    try:
        files = st.session_state.client.list_spreadsheet_files()
        sheets = [{'name': f['name'], 'id': f['id']} for f in files]
        return sheets
    except Exception as e:
        st.error(f"Drive access error: {e}")
        return []

# --- Load Spreadsheet ---
def load_spreadsheet_by_id(sheet_id, sheet_name):
    try:
        spreadsheet = st.session_state.client.open_by_key(sheet_id)
        st.session_state.current_spreadsheet = spreadsheet
        st.session_state.current_spreadsheet_name = sheet_name
        st.session_state.all_worksheets = spreadsheet.worksheets()
        st.session_state.worksheet_names = [ws.title for ws in st.session_state.all_worksheets]
        return True, f"✅ Loaded '{sheet_name}'"
    except Exception as e:
        return False, f"❌ Failed to load: {e}"

# --- Load Fields ---
def load_fields_from_worksheet(worksheet_name):
    try:
        for ws in st.session_state.all_worksheets:
            if ws.title == worksheet_name:
                st.session_state.current_worksheet = ws
                break
        if not st.session_state.current_worksheet:
            return False, "Worksheet not found!"

        headers = st.session_state.current_worksheet.row_values(1)
        valid_fields = [h.strip() for h in headers if h and h.strip()]
        if not valid_fields:
            return False, "No headers in first row!"
        st.session_state.headers = headers
        st.session_state.fields = valid_fields
        st.session_state.fields_loaded = True
        return True, f"✅ Loaded {len(valid_fields)} fields"
    except Exception as e:
        return False, f"Error loading fields: {e}"

# --- Submit Data ---
def submit_data(form_data):
    try:
        if not st.session_state.current_worksheet:
            return False, "No worksheet selected!"

        row_data = []
        for header in st.session_state.headers:
            if header and header in form_data:
                row_data.append(str(form_data[header]).strip())
            else:
                row_data.append("")
        
        row_data.append(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        st.session_state.current_worksheet.append_row(row_data, value_input_option='USER_ENTERED')
        return True, "✅ Data saved successfully!"
    except Exception as e:
        return False, f"❌ Save failed: {e}"

# --- View Data ---
def view_worksheet_data(worksheet):
    try:
        data = worksheet.get_all_values()
        if len(data) > 1:
            df = pd.DataFrame(data[1:], columns=data[0])
            return df
        return pd.DataFrame()
    except Exception as e:
        st.error(f"View error: {e}")
        return pd.DataFrame()

# --- Dynamic Form ---
def create_input_field(field_name, current_value=""):
    field_lower = field_name.lower()
    
    if 'phone' in field_lower or 'mobile' in field_lower or 'contact' in field_lower:
        value = st.text_input(
            f"📞 {field_name}",
            value=current_value,
            placeholder="Enter 10 digit mobile number",
            key=f"input_{field_name}_{st.session_state.submit_key}"
        )
        if value and not re.match(r'^\d{10}$', str(value).strip()):
            st.error("❌ Phone number must be exactly 10 digits!")
        return value
    
    elif 'email' in field_lower or 'mail' in field_lower:
        value = st.text_input(
            f"📧 {field_name}",
            value=current_value,
            placeholder="Enter email address",
            key=f"input_{field_name}_{st.session_state.submit_key}"
        )
        if value and ('@' not in str(value) or '.' not in str(value)):
            st.error("❌ Please enter a valid email address!")
        return value
    
    elif 'date' in field_lower:
        value = st.date_input(
            f"📅 {field_name}",
            value=datetime.now().date() if not current_value else datetime.strptime(current_value, "%Y-%m-%d").date(),
            key=f"date_{field_name}_{st.session_state.submit_key}"
        )
        return value.strftime("%Y-%m-%d") if value else ""
    
    else:
        value = st.text_input(
            f"📌 {field_name}",
            value=current_value,
            placeholder=f"Enter {field_name}",
            key=f"input_{field_name}_{st.session_state.submit_key}"
        )
        return value

# --- MAIN UI ---
def main():
    init_session_state()

    # ========== SIMPLE TEXT FLOW WITH ARROWS ==========
    
    # Title
    st.markdown("<h1 style='text-align: center;'>📊 Google Sheets Data Entry</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: rgba(255,255,255,0.7);'>Streamlit + Google Sheets Integration</p>", unsafe_allow_html=True)
    
    # Simple Text Flow with Arrows
    st.markdown("""
    <div class="flow-text">
        <pre style="color: white; background: transparent; font-family: monospace; text-align: center;">
        
        🔐 Login  ───►  🔄 Refresh Sheet  ───►  📋 Select Sheet  ───►  📂 Load Sheet  
                                          │
                                          ▼
                          ✏️ Add Data  ───►  💾 Submit
        
        </pre>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")

    # Sidebar
    with st.sidebar:
        st.markdown("## 🔐 Login")
        if not st.session_state.authenticated:
            if st.button("🔑 Google Login", use_container_width=True):
                with st.spinner("Connecting..."):
                    ok, msg = authenticate_user()
                    if ok:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)
        else:
            st.success("✅ Logged in")
            
            if st.button("🔄 Refresh Sheet List", use_container_width=True):
                with st.spinner("Loading your sheets..."):
                    sheets = get_all_google_sheets()
                    if sheets:
                        st.session_state.all_sheets = sheets
                        st.success(f"Found {len(sheets)} sheets")
                    else:
                        st.warning("No sheets found")
                        st.session_state.all_sheets = []

            if st.session_state.all_sheets:
                st.markdown("### 📁 Your Google Sheets")
                sheet_names = [s['name'] for s in st.session_state.all_sheets]
                selected_name = st.selectbox("Select a Sheet", sheet_names, key="sheet_select")
                if selected_name:
                    selected = next(s for s in st.session_state.all_sheets if s['name'] == selected_name)
                    if st.button("📂 Load This Sheet", use_container_width=True):
                        with st.spinner("Loading..."):
                            ok, msg = load_spreadsheet_by_id(selected['id'], selected['name'])
                            if ok:
                                st.success(msg)
                                st.session_state.fields_loaded = False
                                st.rerun()
                            else:
                                st.error(msg)
            else:
                st.info("Click 'Refresh Sheet List' to see your sheets.")

            st.markdown("---")
            if st.button("🚪 Logout", use_container_width=True):
                if os.path.exists('token.json'):
                    os.remove('token.json')
                st.session_state.clear()
                st.rerun()

    # Main Area
    if not st.session_state.authenticated:
        st.info("👈 Please login with Google to see your sheets.")
    elif not st.session_state.current_spreadsheet:
        st.info("👈 Select a sheet from the sidebar and click 'Load This Sheet'.")
    else:
        st.markdown(f"<div class='success-box'>📂 Current: <strong>{st.session_state.current_spreadsheet_name}</strong><br>📑 Tabs: {', '.join(st.session_state.worksheet_names)}</div>", unsafe_allow_html=True)

        tab1, tab2 = st.tabs(["📝 Add Data", "📊 View Data"])

        # TAB 1: ADD DATA
        with tab1:
            if st.session_state.worksheet_names:
                selected_ws = st.selectbox("Select Tab (Worksheet)", st.session_state.worksheet_names, key="ws_select")
                
                if st.button("🔄 Load Form", use_container_width=True):
                    with st.spinner("Loading form..."):
                        ok, msg = load_fields_from_worksheet(selected_ws)
                        if ok:
                            st.success(msg)
                            st.session_state.submit_key += 1
                            st.rerun()
                        else:
                            st.error(msg)

                if st.session_state.fields_loaded:
                    st.markdown(f"### ✏️ Enter Data in: {selected_ws}")
                    
                    form_key = f"data_form_{st.session_state.submit_key}"
                    
                    with st.form(key=form_key):
                        form_vals = {}
                        
                        for field in st.session_state.fields:
                            form_vals[field] = create_input_field(field)
                        
                        submitted = st.form_submit_button("💾 Save to Sheet", use_container_width=True)
                        
                        if submitted:
                            errors = []
                            data_to_save = {}
                            
                            for field, value in form_vals.items():
                                if value and str(value).strip():
                                    field_lower = field.lower()
                                    value_str = str(value).strip()
                                    
                                    if 'phone' in field_lower or 'mobile' in field_lower or 'contact' in field_lower:
                                        if not re.match(r'^\d{10}$', value_str):
                                            errors.append(f"{field} must be exactly 10 digits!")
                                        else:
                                            data_to_save[field] = value_str
                                    
                                    elif 'email' in field_lower or 'mail' in field_lower:
                                        if '@' not in value_str or '.' not in value_str:
                                            errors.append(f"{field} must be a valid email address!")
                                        else:
                                            data_to_save[field] = value_str
                                    
                                    else:
                                        data_to_save[field] = value_str
                            
                            if errors:
                                for error in errors:
                                    st.error(error)
                            elif not data_to_save:
                                st.warning("Please fill at least one field!")
                            else:
                                with st.spinner("Saving..."):
                                    ok, msg = submit_data(data_to_save)
                                    if ok:
                                        st.success(msg)
                                        st.balloons()
                                        st.session_state.submit_key += 1
                                        time.sleep(1)
                                        st.rerun()
                                    else:
                                        st.error(msg)
                else:
                    st.info("Click 'Load Form' to start data entry.")
            else:
                st.error("No worksheets found!")

        # TAB 2: VIEW DATA
        with tab2:
            if st.session_state.worksheet_names:
                view_ws = st.selectbox("Select Tab to View", st.session_state.worksheet_names, key="view_ws")
                if st.button("🔍 Show Data", use_container_width=True):
                    with st.spinner("Fetching..."):
                        for ws in st.session_state.all_worksheets:
                            if ws.title == view_ws:
                                df = view_worksheet_data(ws)
                                break
                        if not df.empty:
                            st.success(f"Found {len(df)} records")
                            st.dataframe(df, use_container_width=True, height=400)
                            csv = df.to_csv(index=False)
                            st.download_button("📥 Download CSV", csv, f"{view_ws}.csv", "text/csv")
                        else:
                            st.info("No data found.")
            else:
                st.error("No worksheets found!")

if __name__ == "__main__":
    main()