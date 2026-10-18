# Nagpur Public Transport Analytics Dashboard

A dark Streamlit prototype for exploring bus route occupancy and hourly demand using synthetic demonstration data.

## Files
- `app.py`: Streamlit dashboard
- `nagpur_city_bus_analytics_synthetic.csv`: project dataset
- `requirements.txt`: Python dependencies

## Run locally
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Deploy publicly
1. Upload all three files to a GitHub repository.
2. Visit https://share.streamlit.io/ and sign in with GitHub.
3. Choose **Create app**, select the repository and branch, and set the main file to `app.py`.
4. Click **Deploy** and share the resulting `*.streamlit.app` URL.

## Data disclaimer
The included dataset is synthetic demonstration data. The dashboard is not connected to live Nagpur city bus systems and its recommendations are illustrative.
