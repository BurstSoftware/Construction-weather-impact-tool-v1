import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
WEATHER_API_KEY = os.getenv("OPENWEATHERMAP_API_KEY") or "YOUR_API_KEY_HERE"

# Streamlit app configuration
st.set_page_config(page_title="Construction Weather Impact Tool", layout="wide")
st.title("🏗️ Construction Weather Impact Tool")
st.markdown("Assess and plan for weather impacts on construction schedules and costs.")

# Sample task data (can be replaced with user-uploaded CSV or database)
tasks_data = {
    "Task": ["Concrete Pouring", "Roofing", "Excavation", "Framing"],
    "Start_Date": ["2025-05-01", "2025-05-05", "2025-05-03", "2025-05-07"],
    "Duration_Days": [3, 5, 2, 4],
    "Weather_Sensitivity": ["High", "High", "Medium", "Low"],
    "Cost_Per_Day": [5000, 3000, 2000, 2500]
}
tasks_df = pd.DataFrame(tasks_data)
tasks_df["Start_Date"] = pd.to_datetime(tasks_df["Start_Date"])

# Function to fetch weather forecast
def get_weather_forecast(city, days=7):
    url = f"http://api.openweathermap.org/data/2.5/forecast?q={city}&appid={WEATHER_API_KEY}&units=metric"
    response = requests.get(url)
    if response.status_code != 200:
        return None
    data = response.json()
    forecast = []
    for item in data["list"][:days*8]:  # 3-hourly forecast for specified days
        date = datetime.fromtimestamp(item["dt"])
        temp = item["main"]["temp"]
        weather = item["weather"][0]["main"]
        precipitation = item.get("rain", {}).get("3h", 0) or item.get("snow", {}).get("3h", 0)
        forecast.append({
            "Date": date,
            "Temperature_C": temp,
            "Weather": weather,
            "Precipitation_mm": precipitation
        })
    return pd.DataFrame(forecast)

# Function to assess weather impact on tasks
def assess_weather_impact(tasks_df, weather_df):
    impacts = []
    for _, task in tasks_df.iterrows():
        task_start = task["Start_Date"]
        task_end = task_start + timedelta(days=task["Duration_Days"])
        task_weather = weather_df[
            (weather_df["Date"] >= task_start) & (weather_df["Date"] <= task_end)
        ]
        delay_days = 0
        if task["Weather_Sensitivity"] == "High":
            delay_days = len(task_weather[task_weather["Precipitation_mm"] > 2]) // 2  # Assume heavy rain delays
        elif task["Weather_Sensitivity"] == "Medium":
            delay_days = len(task_weather[task_weather["Precipitation_mm"] > 5]) // 3
        cost_impact = delay_days * task["Cost_Per_Day"]
        impacts.append({
            "Task": task["Task"],
            "Delay_Days": delay_days,
            "Cost_Impact": cost_impact,
            "New_End_Date": task_end + timedelta(days=delay_days)
        })
    return pd.DataFrame(impacts)

# Sidebar for user inputs
st.sidebar.header("Project Settings")
city = st.sidebar.text_input("Enter Project City", value="New York")
forecast_days = st.sidebar.slider("Forecast Days", 1, 14, 7)
uploaded_file = st.sidebar.file_uploader("Upload Task Schedule (CSV)", type=["csv"])

# Load custom task data if uploaded
if uploaded_file:
    tasks_df = pd.read_csv(uploaded_file)
    tasks_df["Start_Date"] = pd.to_datetime(tasks_df["Start_Date"])

# Main content
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("Weather Forecast")
    weather_df = get_weather_forecast(city, forecast_days)
    if weather_df is None:
        st.error("Failed to fetch weather data. Check city name or API key.")
    else:
        st.dataframe(weather_df[["Date", "Temperature_C", "Weather", "Precipitation_mm"]])
        
        # Plot weather forecast
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=weather_df["Date"], y=weather_df["Temperature_C"],
            name="Temperature (°C)", line=dict(color="blue")
        ))
        fig.add_trace(go.Bar(
            x=weather_df["Date"], y=weather_df["Precipitation_mm"],
            name="Precipitation (mm)", yaxis="y2", opacity=0.4
        ))
        fig.update_layout(
            title="Weather Forecast",
            yaxis=dict(title="Temperature (°C)"),
            yaxis2=dict(title="Precipitation (mm)", overlaying="y", side="right"),
            xaxis=dict(title="Date")
        )
        st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader("Task Schedule")
    st.dataframe(tasks_df)

    st.subheader("Weather Impact Analysis")
    if weather_df is not None:
        impact_df = assess_weather_impact(tasks_df, weather_df)
        st.dataframe(impact_df)

        # Visualize impacts
        fig_impact = px.bar(
            impact_df,
            x="Task",
            y="Delay_Days",
            color="Cost_Impact",
            title="Weather Impact on Tasks",
            labels={"Delay_Days": "Delay (Days)", "Cost_Impact": "Cost Impact ($)"}
        )
        st.plotly_chart(fig_impact, use_container_width=True)

# Cost Estimator Integration (Placeholder)
st.subheader("Cost Adjustments")
if weather_df is not None:
    total_cost_impact = impact_df["Cost_Impact"].sum()
    st.write(f"**Total Additional Cost Due to Weather Delays:** ${total_cost_impact:,.2f}")
    st.markdown("Integrate with your **Cost Estimator Tool** to update project budget.")
else:
    st.warning("No weather data available for cost adjustments.")

# Footer
st.markdown("---")
st.markdown("Powered by OpenWeatherMap and Streamlit | Enhances project planning by mitigating weather-related delays.")
