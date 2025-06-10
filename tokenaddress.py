import streamlit as st
import pandas as pd
import requests
import time # To add a small delay between requests to be kind to the API

# --- Page Configuration ---
st.set_page_config(
    page_title="Token Address Finder",
    page_icon="�",
    layout="wide",
)

# --- Helper Function to convert DataFrame to CSV for download ---
@st.cache_data
def convert_df_to_csv(df):
    """Converts a DataFrame to a CSV string for downloading."""
    return df.to_csv(index=False).encode('utf-8')

# --- Function to fetch address from API ---
def get_address(base_url, ticker):
    """Fetches a single token address from the API."""
    # Ensure ticker is a string and handle potential float inputs from pandas
    if not isinstance(ticker, str):
        ticker = str(ticker).strip()
        
    if not ticker or pd.isna(ticker):
        return "Invalid Ticker"
        
    try:
        # Construct the full URL for the specific ticker
        api_url = f"{base_url}/{ticker}"
        response = requests.get(api_url, timeout=10)
        response.raise_for_status() # Raise an exception for bad status codes (4xx or 5xx)
        # The API returns a JSON like {"address": "0x..."}, so we extract the value
        return response.json().get('address', 'Address key not found')
    except requests.exceptions.HTTPError:
        return "Not Found" # Specifically for 404 or other HTTP errors
    except requests.exceptions.RequestException:
        # Handle network errors, timeouts etc.
        return "API Error"
    except Exception:
        # Handle other potential errors like JSON parsing
        return "Processing Error"

# --- Main Application UI ---
st.title("🔗 Token Address Finder")
st.markdown("""
This application is configured to process your specific report format.

**How to use:**
1.  **Upload your report** (Excel file). The app will automatically read the **first tab**.
2.  The app will assume tickers are in **Column A**.
3.  **Provide the base API URL.** The app will append each ticker to this URL to find its address.
4.  Click the **'Find Addresses'** button to see the results. The new addresses will be in a column named `token address`.
""")

# --- Step 1: Upload the file with token tickers ---
st.header("Step 1: Upload Your Report File")
uploaded_tickers_file = st.file_uploader(
    "Upload an Excel file",
    type=['xlsx'],
    help="The app will process the first sheet of this file."
)

# --- Step 2: Provide the API endpoint ---
st.header("Step 2: Provide the API Base URL")
api_base_url = st.text_input(
    "Enter the API base URL:",
    "https://address-svc-utyjy373hq-uc.a.run.app/symbols",
    help="The app will append '/{ticker}' from Column A to this URL for each token."
)


# --- Step 3: Process the data and display results ---
st.header("Step 3: Process and View Results")

if st.button("Find Addresses", type="primary"):
    if uploaded_tickers_file is None:
        st.warning("Please upload an Excel report file first.")
    elif not api_base_url:
        st.warning("Please provide the API base URL.")
    else:
        with st.spinner('Processing your report... This may take a moment.'):
            try:
                # Load the first sheet of the uploaded Excel file into a pandas DataFrame
                df = pd.read_excel(uploaded_tickers_file, sheet_name=0, header=None)
                
                # Assume the first column (Column A) contains the tickers.
                # Let's get the name of the first column to use it.
                ticker_column = df.columns[0]

                st.info(f"Found {len(df)} rows to process from Column A. Starting API calls...")
                
                addresses = []
                progress_bar = st.progress(0)
                total_tickers = len(df)

                # Iterate through each ticker in the first column and fetch its address
                for i, ticker in enumerate(df[ticker_column]):
                    address = get_address(api_base_url, ticker)
                    addresses.append(address)
                    # Be kind to the API by adding a small delay
                    time.sleep(0.1)
                    # Update progress bar
                    progress_bar.progress((i + 1) / total_tickers)

                # Create the new column with the specified name "token address"
                # This will be added as the last column, which will be 'G' if you have A-F.
                df['token address'] = addresses

                st.success("Processing complete!")
                st.subheader("Results")
                # Display the dataframe, but this time with headers for clarity
                # Rename original columns for display since we read with header=None
                df.columns = [f'Column {chr(65+i)}' for i in range(len(df.columns)-1)] + ['token address']
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

�
