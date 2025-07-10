import json
import dash
from dash import dcc, html
import plotly.express as px
import pandas as pd
from dash.dependencies import Input, Output

# Function to load data
def load_data():
    with open("risk_data.json", "r") as file:
        return json.load(file)

# Convert JSON to DataFrame
def get_dataframe():
    risk_data = load_data()
    data_list = []
    for city, details in risk_data.items():
        data_list.append({
            "City": city,
            "Risk Level": details.get("Risk_level", "N/A"),
            "Cancer Percentage": details.get("Cancer Percentage", "N/A"),
            "Chronic Illness Percentage": details.get("Chronic Illness Percentage", "N/A"),
            "Mortality Rate": details.get("Mortality Rate", "N/A"),
            "Number of Hospitals": details.get("Number of Hospitals", "N/A"),
            "Cancer Care Centers": details.get("Cancer Care Centers", "N/A"),
            "Health Insurance Coverage": details.get("Health Insurance Coverage", "N/A")
        })
    return pd.DataFrame(data_list)

# Initialize app
app = dash.Dash(__name__)
server = app.server

# App Layout
app.layout = html.Div(style={
    'backgroundColor': '#F0F8FF',
    'fontFamily': 'Arial, sans-serif',
    'padding': '30px'
}, children=[
    html.H1("Health Risk Analytics Dashboard", style={
        'textAlign': 'center',
        'color': '#2C3E50',
        'marginBottom': '40px'
    }),

    html.Div([
        dcc.Dropdown(
            id="city-dropdown",
            placeholder="🔍 Select a City",
            style={'width': '60%', 'margin': '0 auto'}
        ),
    ], style={'textAlign': 'center'}),

    html.Br(),

    html.Div(id="city-details", style={
        "backgroundColor": "#FFFFFF",
        "padding": "25px",
        "borderRadius": "10px",
        "boxShadow": "0 4px 8px rgba(0,0,0,0.1)",
        "width": "60%",
        "margin": "0 auto",
        "textAlign": "left",
        "fontSize": "17px",
        "lineHeight": "1.8",
        "color": "#34495E"
    }),

    html.Br(),

    dcc.Graph(id="risk-level-chart")
])

# Populate dropdown
@app.callback(
    Output("city-dropdown", "options"),
    Input("city-dropdown", "value")  # dummy input to trigger
)
def update_dropdown(_):
    df = get_dataframe()
    return [{"label": city, "value": city} for city in df["City"]]

# Update details and chart
@app.callback(
    [Output("city-details", "children"),
     Output("risk-level-chart", "figure")],
    [Input("city-dropdown", "value")]
)
def update_info(selected_city):
    df = get_dataframe()
    if not selected_city or selected_city not in df["City"].values:
        return "", px.bar(title="Select a city to view health data.")

    city_info = df[df["City"] == selected_city].iloc[0]

    # Display details
    details = html.Div([
        html.H2(f"📍 {selected_city}", style={"color": "#2E86C1"}),
        html.P(f"🔸 Risk Level: {city_info['Risk Level']}"),
        html.P(f"🧬 Cancer Percentage: {city_info['Cancer Percentage']}"),
        html.P(f"🩺 Chronic Illness Percentage: {city_info['Chronic Illness Percentage']}"),
        html.P(f"⚰ Mortality Rate: {city_info['Mortality Rate']}"),
        html.P(f"🏥 Number of Hospitals: {city_info['Number of Hospitals']}"),
        html.P(f"🏨 Cancer Care Centers: {city_info['Cancer Care Centers']}"),
        html.P(f"🛡 Health Insurance Coverage: {city_info['Health Insurance Coverage']}")
    ])

    # Chart Data
    fig = px.bar(
        x=[
            "Cancer %", "Chronic Illness %", "Mortality Rate", 
            "Hospitals", "Care Centers", "Insurance %"
        ],
        y=[
            float(city_info["Cancer Percentage"].replace('%', '')) if isinstance(city_info["Cancer Percentage"], str) else city_info["Cancer Percentage"],
            float(city_info["Chronic Illness Percentage"].replace('%', '')) if isinstance(city_info["Chronic Illness Percentage"], str) else city_info["Chronic Illness Percentage"],
            float(city_info["Mortality Rate"].replace('%', '')) if isinstance(city_info["Mortality Rate"], str) else city_info["Mortality Rate"],
            int(city_info["Number of Hospitals"]),
            int(city_info["Cancer Care Centers"]),
            float(city_info["Health Insurance Coverage"].replace('%', '')) if isinstance(city_info["Health Insurance Coverage"], str) else city_info["Health Insurance Coverage"],
        ],
        labels={'x': 'Health Metrics', 'y': 'Values'},
        title=f"📊 Health Metrics for {selected_city}",
        color_discrete_sequence=["#FF6F61"]
    )
    fig.update_layout(
        xaxis_tickangle=-35,
        plot_bgcolor='#F9F9F9',
        paper_bgcolor='#F9F9F9',
        font=dict(color='#2C3E50')
    )

    return details, fig

# Run server
if __name__ == "__main__":
    app.run(debug=True)
