import requests
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta
import io
import numpy as np

def fetch_exchange_rates(start_date, end_date):
    """
    Fetch exchange rate data from the ECB API.
    """
    # Calculate the date range (ECB format: YYYY-MM-DD)
    start_str = start_date.strftime('%Y-%m-%d')
    end_str = end_date.strftime('%Y-%m-%d')
    
    # ECB Statistical Data Warehouse API URLs
    usd_url = f"https://sdw-wsrest.ecb.europa.eu/service/data/EXR/D.USD.EUR.SP00.A?startPeriod={start_str}&endPeriod={end_str}"
    chf_url = f"https://sdw-wsrest.ecb.europa.eu/service/data/EXR/D.CHF.EUR.SP00.A?startPeriod={start_str}&endPeriod={end_str}"
    
    # Request headers
    headers = {
        'Accept': 'text/csv',
        'Accept-Language': 'en'
    }
    
    # Fetch data for USD-EUR
    response_usd = requests.get(usd_url, headers=headers)
    if response_usd.status_code != 200:
        raise Exception(f"Failed to fetch USD-EUR data: {response_usd.status_code}")
    
    # Fetch data for CHF-EUR
    response_chf = requests.get(chf_url, headers=headers)
    if response_chf.status_code != 200:
        raise Exception(f"Failed to fetch CHF-EUR data: {response_chf.status_code}")
    
    # Parse CSV data
    df_usd = pd.read_csv(io.StringIO(response_usd.text), sep=',', thousands=',')
    df_chf = pd.read_csv(io.StringIO(response_chf.text), sep=',', thousands=',')
    
    # Process the dataframes to extract date and exchange rate
    df_usd = process_ecb_data(df_usd)
    df_chf = process_ecb_data(df_chf)
    
    # Merge dataframes on date
    df_merged = pd.merge(df_usd, df_chf, on='date', how='inner')
    
    return df_merged

def process_ecb_data(df):
    """
    Process the ECB data to extract date and exchange rate.
    """
    # Identify the columns containing date and exchange rate values
    time_col = [col for col in df.columns if 'TIME_PERIOD' in col][0]
    obs_col = [col for col in df.columns if 'OBS_VALUE' in col][0]
    
    # Create a new dataframe with just date and rate
    result_df = pd.DataFrame()
    result_df['date'] = pd.to_datetime(df[time_col])
    result_df['rate'] = df[obs_col].astype(float)
    
    return result_df

def plot_exchange_rates(data):
    """
    Create a scatter plot with USD-EUR on x-axis and EUR-CHF on y-axis.
    The inverse is calculated to get the correct representation.
    """
    # Calculate the inverse rates to get USD-EUR and EUR-CHF
    # ECB provides rates as USD per EUR and CHF per EUR
    # We need to invert USD/EUR but keep EUR/CHF (by inverting CHF/EUR)
    data['usd_eur'] = 1 / data['rate_x']  # USD per EUR -> EUR per USD -> invert to get USD-EUR
    data['eur_chf'] = 1 / data['rate_y']  # CHF per EUR -> EUR per CHF -> invert to get EUR-CHF
    
    # Create a scatter plot
    plt.figure(figsize=(12, 8))
    
    # Create scatter plot with date-based color gradient
    dates_num = mdates.date2num(data['date'])
    scatter = plt.scatter(data['usd_eur'], data['eur_chf'], 
                          c=dates_num, cmap='viridis', 
                          alpha=0.7, s=30)
    
    # Add color bar to show timeline
    cbar = plt.colorbar(scatter)
    cbar.ax.set_ylabel('Date', fontsize=12)
    
    # Format the colorbar's tick labels as dates
    cbar.ax.yaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
    cbar.ax.yaxis.set_major_locator(mdates.YearLocator(2))
    
    # Add labels and title
    plt.xlabel('USD-EUR Exchange Rate (USD per EUR)', fontsize=14)
    plt.ylabel('EUR-CHF Exchange Rate (EUR per CHF)', fontsize=14)
    plt.title('USD-EUR vs EUR-CHF Exchange Rates Correlation', fontsize=16)
    
    # Add a grid for better readability
    plt.grid(True, linestyle='--', alpha=0.7)
    
    # Add trendline
    z = np.polyfit(data['usd_eur'], data['eur_chf'], 1)
    p = np.poly1d(z)
    plt.plot(data['usd_eur'], p(data['usd_eur']), "r--", alpha=0.8)
    
    # Get correlation coefficient
    corr = data['usd_eur'].corr(data['eur_chf'])
    plt.annotate(f'Correlation: {corr:.2f}', 
                 xy=(0.05, 0.95), xycoords='axes fraction',
                 fontsize=12, bbox=dict(boxstyle="round,pad=0.3", fc="white", alpha=0.8))
    
    plt.tight_layout()
    plt.savefig('exchange_rates_correlation.png', dpi=300)
    plt.show()

if __name__ == "__main__":
    # Set the date range for the last 15 years
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365 * 15)
    
    # Fetch the data
    print("Fetching exchange rate data...")
    data = fetch_exchange_rates(start_date, end_date)
    
    # Plot the data
    print("Creating plot...")
    plot_exchange_rates(data)
    
    print("Done! Plot saved as 'exchange_rates_correlation.png'")