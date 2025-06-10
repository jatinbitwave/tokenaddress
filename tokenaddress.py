import streamlit as st
import pandas as pd
import requests
import time # To add a small delay between requests to be kind to the API

# --- Page Configuration ---
st.set_page_config(
    page_title="Token Address Finder",
    page_icon="🔗",
    layout="wide",
)

# --- Helper Function to convert DataFrame to CSV for download ---
@st.cache_data
def convert_df_to_csv(df):
    """Converts a DataFrame to a CSV string for downloading."""
    return df.to_csv(index=False).encode('utf-8')

# --- Function to fetch address and networkId from API ---
def get_token_data(base_url, ticker):
    """Fetches a single token address and networkId from the API."""
    # Ensure ticker is a string and handle potential float inputs from pandas
    if not isinstance(ticker, str):
        ticker = str(ticker).strip()
        
    if not ticker or pd.isna(ticker):
        return "Invalid Ticker", "Invalid Ticker"
        
    try:
        # Construct the full URL for the specific ticker
        api_url = f"{base_url}/{ticker}"
        response = requests.get(api_url, timeout=10)
        response.raise_for_status() # Raise an exception for bad status codes (4xx or 5xx)
        
        # The API returns a JSON like {"address": "0x...", "networkId": "..."}, so we extract the values
        data = response.json()
        address = data.get('address', 'Address not found')
        network_id = data.get('networkId', 'NetworkId not found')
        return address, network_id
        
    except requests.exceptions.HTTPError:
        return "Not Found", "Not Found" # Specifically for 404 or other HTTP errors
    except requests.exceptions.RequestException:
        # Handle network errors, timeouts etc.
        return "API Error", "API Error"
    except Exception:
        # Handle other potential errors like JSON parsing
        return "Processing Error", "Processing Error"

# --- Main Application UI ---
st.title("🔗 Token Address Finder")
st.markdown("""
This application is configured to process your specific report format.

**How to use:**
1.  **Upload your report** (CSV file).

# --- Step 1: Upload the file with token tickers ---
st.header("Step 1: Upload Your Balance Report File")
uploaded_tickers_file = st.file_uploader(
    "Upload a CSV file",
    type=['csv'],
    help="The app will process the first column of this file."
)

# --- Step 2: Process the data and display results ---
st.header("Step 2: Process and View Results")

if st.button("Validate", type="primary"):
    # The API URL is now hardcoded
    api_base_url = "https://address-svc-utyjy373hq-uc.a.run.app/symbols"

    if uploaded_tickers_file is None:
        st.warning("Please upload a CSV report file first.")
    else:
        with st.spinner('Processing your report... This may take a moment.'):
            try:
                # Load the uploaded CSV file into a pandas DataFrame, using the first row as the header.
                df = pd.read_csv(uploaded_tickers_file)
                
                # Assume the first column contains the tickers.
                ticker_column_name = df.columns[0]

                st.info(f"Found {len(df)} rows to process from column '{ticker_column_name}'. Starting API calls...")
                
                addresses = []
                network_ids = []
                progress_bar = st.progress(0)
                total_tickers = len(df)

                # Iterate through each ticker in the first column and fetch its data
                for i, ticker in enumerate(df[ticker_column_name]):
                    address, network_id = get_token_data(api_base_url, ticker)
                    addresses.append(address)
                    network_ids.append(network_id)
                    # Be kind to the API by adding a small delay
                    time.sleep(0.1)
                    # Update progress bar
                    progress_bar.progress((i + 1) / total_tickers)

                # Create the new columns with the specified names
                df['token address'] = addresses
                df['Blockchain'] = network_ids

                st.success("Processing complete!")
                st.subheader("Results")
                
                # Display the dataframe with its original headers plus the new ones.
                st.dataframe(df, use_container_width=True)

                # --- Download Button ---
                csv_to_download = convert_df_to_csv(df)
                st.download_button(
                   label="Download Results as CSV",
                   data=csv_to_download,
                   file_name="token_addresses_output.csv",
                   mime="text/csv",
                )

            except Exception as e:
                st.error(f"An error occurred during processing: {e}")
