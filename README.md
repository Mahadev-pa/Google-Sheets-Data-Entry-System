# 📊 Google Sheets Data Entry System

A powerful, user-friendly web application built with **Streamlit** that connects to **Google Sheets API** for seamless data entry, validation, and management.

## ✨ Features

- 🔐 **Google OAuth Authentication** - Secure login with your Google account
- 📋 **Dynamic Form Generation** - Automatically creates form fields from sheet headers
- ✅ **Smart Validations** - Phone (10 digits), Email format, Date picker
- 🔄 **Real-time Sync** - Data instantly saved to Google Sheets
- 🚫 **No Duplicate Entries** - Prevents accidental multiple submissions
- 📊 **View & Export Data** - Display sheet data and download as CSV
- 🎨 **Attractive UI** - Gradient backgrounds, animated cards, responsive design
- 📱 **Mobile Friendly** - Works on all devices

## 🛠️ Tech Stack

- **Frontend/UI:** Streamlit
- **Backend:** Python
- **API:** Google Sheets API v4, Google Drive API
- **Authentication:** OAuth 2.0
- **Data Processing:** Pandas

## 🚀 Quick Start

### Prerequisites

```bash
pip install streamlit gspread google-auth pandas
