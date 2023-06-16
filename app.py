import sqlite3
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
from datetime import date
from dash import html, dcc, Dash
from dash.dependencies import Input, Output, State
import plotly.graph_objects as go
import dash_bootstrap_components as dbc

app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP], suppress_callback_exceptions=True)

# Connect to the database
conn = sqlite3.connect('car_data.db', check_same_thread=False)  # Added check_same_thread=False for threading issues
cursor = conn.cursor()

# Create a table to store the data if it doesn't exist
cursor.execute('''
    CREATE TABLE IF NOT EXISTS car_data (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        vehicle_no TEXT,
        start_km INTEGER,
        end_km INTEGER,
        fuel_used FLOAT,
        fuel_avg FLOAT,
        last_service_km INTEGER,
        date TEXT,
        last_tax_payment TEXT
    )
''')
conn.commit()

navbar = dbc.Navbar(
    [
        html.A(
            dbc.Row(
                [
                    dbc.Col(dbc.NavbarBrand("Car Dashboard", className="ml-2")),
                ],
                align="center",
                className="g-0",
            ),
            href="/",
        ),
        dbc.NavbarToggler(id="navbar-toggler"),
        dbc.Collapse(
            dbc.Nav(
                [
                    dcc.Dropdown(
                        id="vehicle-selection",
                        options=[
                            {'label': 'Vehicle 1', 'value': 'Vehicle 1'},
                            {'label': 'Vehicle 2', 'value': 'Vehicle 2'},
                            {'label': 'Vehicle 3', 'value': 'Vehicle 3'},
                        ],
                        placeholder="Select a vehicle",
                        className="ml-2",
                        style={"width": "300px"},
                    ),
                    dbc.NavLink("All Vehicles", href="/all-vehicles"),
                ],
                className="ml-auto",
                navbar=True,
            ),
            id="navbar-collapse",
            navbar=True,
        ),
    ],
    color="dark",
    dark=True,
)

app.layout = html.Div([
    dcc.Location(id="url", refresh=False),
    navbar,
    html.Div(id="page-content"),
])

@app.callback(Output("page-content", "children"), [Input("url", "pathname")])
def render_page_content(pathname):
    if pathname == "/all-vehicles":
        return html.Div([
    html.H1("All Vehicles"),
    dbc.Row([
        dbc.Col([
            html.H3("Vehicle 1"),
            dcc.Graph(id="vehicle-1-graphs"),
            dcc.Graph(id="vehicle-1-service-gauges", figure=go.Figure()),
            dcc.Graph(id="vehicle-1-tax-gauges", figure=go.Figure()),
        ], width=4),
        dbc.Col([
            html.H3("Vehicle 2"),
            dcc.Graph(id="vehicle-2-graphs"),
            dcc.Graph(id="vehicle-2-service-gauges", figure=go.Figure()),
            dcc.Graph(id="vehicle-2-tax-gauges", figure=go.Figure()),
        ], width=4),
        dbc.Col([
            html.H3("Vehicle 3"),
            dcc.Graph(id="vehicle-3-graphs"),
            dcc.Graph(id="vehicle-3-service-gauges", figure=go.Figure()),
            dcc.Graph(id="vehicle-3-tax-gauges", figure=go.Figure()),
        ], width=4),
    ])
])

    else:
            return html.Div([
        html.H1("Car Dashboard"),
        html.H3(id="vehicle-number", children="Vehicle Number"),
        html.Div([
            dcc.DatePickerSingle(
                id="date-picker",
                date=date.today(),
                display_format="DD-MM-YYYY",
                placeholder="Select a date"
            ),
            dcc.Input(id="start-km", type="number", placeholder="Start KM"),
            dcc.Input(id="end-km", type="number", placeholder="End KM"),
            dcc.Input(id="fuel-used", type="number", placeholder="Fuel Used (in Liters)"),
            dcc.Input(id="last-service-km", type="number", placeholder="Last Service KM"),
            html.H6('Tax', style={'margin-top': '20px'}),
            dcc.DatePickerSingle(
                id="last-tax-payment",
                date=date.today(),
                display_format="DD-MM-YYYY",
                placeholder="Last Tax Payment Date"
            ),
            html.Button("Submit", id="submit-button")
        ]),
        dcc.Graph(id="fuel-efficiency-gauge", figure=go.Figure()),
        dcc.Graph(id="service-gauge", figure=go.Figure()),
        dcc.Graph(id="tax-gauge", figure=go.Figure())
    ])




@app.callback(
    Output("fuel-efficiency-gauge", "figure"),
    Output("vehicle-number", "children"),
    Input("submit-button", "n_clicks"),
    State("vehicle-selection", "value"),
    State("date-picker", "date"),
    State("start-km", "value"),
    State("end-km", "value"),
    State("fuel-used", "value"),
    State("last-service-km", "value"),
    State("last-tax-payment", "date")
)
def update_fuel_efficiency(n, vehicle, selected_date, start_km, end_km, fuel_used, last_service_km, last_tax_payment):
    if n and vehicle and selected_date and start_km and end_km and fuel_used and last_service_km and last_tax_payment:
        distance_traveled = end_km - start_km
        fuel_efficiency = distance_traveled / fuel_used

        cursor.execute(
            "INSERT INTO car_data (vehicle_no, start_km, end_km, fuel_used, fuel_avg, last_service_km, date, last_tax_payment) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (vehicle, start_km, end_km, fuel_used, fuel_efficiency, last_service_km, selected_date, last_tax_payment)
        )
        conn.commit()

        return go.Figure(go.Indicator(
            mode="gauge+number",
            value=fuel_efficiency,
            title={'text': "Fuel Efficiency (KM/L)"},
            gauge={'axis': {'range': [None, 30]}}
        )), f"Vehicle Number: {vehicle}"
    else:
        return go.Figure(), "Vehicle Number"



@app.callback(
    Output("vehicle-1-graph", "figure"),
    Output("vehicle-2-graph", "figure"),
    Output("vehicle-3-graph", "figure"),
    Input("url", "pathname")
)
def update_vehicle_graphs(pathname):
    if pathname == "/all-vehicles":
        vehicles = ['Vehicle 1', 'Vehicle 2', 'Vehicle 3']
        figures = []

        for vehicle in vehicles:
            cursor.execute(
                "SELECT fuel_avg, date FROM car_data WHERE vehicle_no=? ORDER BY date ASC",
                (vehicle,)
            )
            rows = cursor.fetchall()

            if rows:
                fuel_avgs, dates = zip(*rows)
                figures.append(
                    go.Figure(go.Scatter(x=dates, y=fuel_avgs, mode='lines+markers', name=vehicle))
                )
            else:
                figures.append(go.Figure())

        return figures
    else:
        return go.Figure(), go.Figure(), go.Figure()

@app.callback(
    Output("vehicle-1-service-gauges", "figure"),
    Output("vehicle-1-tax-gauges", "figure"),
    Input("url", "pathname")
)
def update_vehicle_1_gauges(pathname):
    if pathname == "/all-vehicles":
        # Fetch the latest service and tax data for Vehicle 1
        cursor.execute(
            "SELECT last_service_km, last_tax_payment FROM car_data WHERE vehicle_no='Vehicle 1' ORDER BY date DESC LIMIT 1",
        )
        row = cursor.fetchone()

        # If data exists, update the Gauges
        if row:
            last_service_km, last_tax_payment = row
            last_tax_payment_date = datetime.strptime(last_tax_payment, "%Y-%m-%d")
            tax_due_date = last_tax_payment_date + timedelta(days=365)
            days_until_due = (tax_due_date - datetime.now()).days

            service_gauge = go.Figure(go.Indicator(
                mode="gauge+number",
                value=last_service_km,
                title={'text': "Last Service KM"},
                gauge={'axis': {'range': [None, 30000]}},
                number={'suffix': " KM"},
            ))

            tax_gauge = go.Figure(go.Indicator(
                mode="gauge+number",
                value=days_until_due,
                title={'text': "Days Until Tax Due"},
                gauge={'axis': {'range': [None, 365]}},
                number={'suffix': " Days"},
            ))

            return service_gauge, tax_gauge
        else:
            return go.Figure(), go.Figure()
    else:
        return go.Figure(), go.Figure()

# Repeat the above for Vehicle 2 and Vehicle 3, changing the IDs and the vehicle_no in the SQL query.

@app.callback(
    Output("vehicle-2-service-gauges", "figure"),
    Output("vehicle-2-tax-gauges", "figure"),
    Input("url", "pathname")
)
def update_vehicle_1_gauges(pathname):
    if pathname == "/all-vehicles":
        # Fetch the latest service and tax data for Vehicle 1
        cursor.execute(
            "SELECT last_service_km, last_tax_payment FROM car_data WHERE vehicle_no='Vehicle 2' ORDER BY date DESC LIMIT 1",
        )
        row = cursor.fetchone()

        # If data exists, update the Gauges
        if row:
            last_service_km, last_tax_payment = row
            last_tax_payment_date = datetime.strptime(last_tax_payment, "%Y-%m-%d")
            tax_due_date = last_tax_payment_date + timedelta(days=365)
            days_until_due = (tax_due_date - datetime.now()).days

            service_gauge = go.Figure(go.Indicator(
                mode="gauge+number",
                value=last_service_km,
                title={'text': "Last Service KM"},
                gauge={'axis': {'range': [None, 30000]}},
                number={'suffix': " KM"},
            ))

            tax_gauge = go.Figure(go.Indicator(
                mode="gauge+number",
                value=days_until_due,
                title={'text': "Days Until Tax Due"},
                gauge={'axis': {'range': [None, 365]}},
                number={'suffix': " Days"},
            ))

            return service_gauge, tax_gauge
        else:
            return go.Figure(), go.Figure()
    else:
        return go.Figure(), go.Figure()

# Repeat the above for Vehicle 3, changing the IDs and the vehicle_no in the SQL query.

@app.callback(
    Output("vehicle-3-service-gauges", "figure"),
    Output("vehicle-3-tax-gauges", "figure"),
    Input("url", "pathname")
)
def update_vehicle_1_gauges(pathname):
    if pathname == "/all-vehicles":
        # Fetch the latest service and tax data for Vehicle 1
        cursor.execute(
            "SELECT last_service_km, last_tax_payment FROM car_data WHERE vehicle_no='Vehicle 3' ORDER BY date DESC LIMIT 1",
        )
        row = cursor.fetchone()

        # If data exists, update the Gauges
        if row:
            last_service_km, last_tax_payment = row
            last_tax_payment_date = datetime.strptime(last_tax_payment, "%Y-%m-%d")
            tax_due_date = last_tax_payment_date + timedelta(days=365)
            days_until_due = (tax_due_date - datetime.now()).days

            service_gauge = go.Figure(go.Indicator(
                mode="gauge+number",
                value=last_service_km,
                title={'text': "Last Service KM"},
                gauge={'axis': {'range': [None, 30000]}},
                number={'suffix': " KM"},
            ))

            tax_gauge = go.Figure(go.Indicator(
                mode="gauge+number",
                value=days_until_due,
                title={'text': "Days Until Tax Due"},
                gauge={'axis': {'range': [None, 365]}},
                number={'suffix': " Days"},
            ))

            return service_gauge, tax_gauge
        else:
            return go.Figure(), go.Figure()
    else:
        return go.Figure(), go.Figure()

@app.callback(
    Output("vehicle-1-graphs", "figure"),
    Output("vehicle-2-graphs", "figure"),
    Output("vehicle-3-graphs", "figure"),
    Input("url", "pathname")
)
def update_vehicle_graphs(pathname):
    if pathname == "/all-vehicles":
        vehicles = ['Vehicle 1', 'Vehicle 2', 'Vehicle 3']
        figures = []

        for vehicle in vehicles:
            cursor.execute(
                "SELECT fuel_avg, date, last_service_km, last_tax_payment FROM car_data WHERE vehicle_no=? ORDER BY date DESC LIMIT 1",
                (vehicle,)
            )
            rows = cursor.fetchall()

            if rows:
                fuel_avg, date, last_service_km, last_tax_payment = rows[0]

                # Create a subplots with 2 rows and 1 column
                fig = make_subplots(rows=2, cols=1)

                # Add fuel efficiency line chart to the first row
                fig.add_trace(go.Scatter(x=[date], y=[fuel_avg], mode='lines+markers', name=vehicle), row=1, col=1)

                # Add last service KM gauge to the second row
                fig.add_trace(go.Indicator(
                    mode="gauge+number",
                    value=last_service_km,
                    title={'text': "Last Service KM"},
                    gauge={'axis': {'range': [None, 30000]}}  # Assuming max KM is 30000, adjust as per your needs
                ), row=2, col=1)

                # Add last tax payment date to the second row
                fig.add_trace(go.Indicator(
                    mode="number+date",
                    value=datetime.strptime(last_tax_payment, "%Y-%m-%d").timestamp(),  # Convert date to timestamp
                    title={'text': "Last Tax Payment"},
                ), row=2, col=1)

                figures.append(fig)
            else:
                figures.append(go.Figure())

        return figures
    else:
        return go.Figure(), go.Figure(), go.Figure()


@app.callback(
    Output("last-service-km", "value"),
    Input("vehicle-selection", "value")
)
def update_last_service_km(vehicle):
    cursor.execute(
        "SELECT last_service_km FROM car_data WHERE vehicle_no=? ORDER BY date DESC LIMIT 1",
        (vehicle,)
    )
    row = cursor.fetchone()
    if row:
        return row[0]
    else:
        return None 

@app.callback(
    Output("service-gauge", "figure"),
    [Input("submit-button", "n_clicks")],
    [State("end-km", "value"),
     State("last-service-km", "value")]
)
def update_service_gauge(n_clicks, end_km, last_service_km):
    if n_clicks is not None and end_km is not None and last_service_km is not None:
        # Check if the last service kilometer reading is greater than the current end kilometer reading
        if last_service_km > end_km:
            return go.Figure(data=go.Indicator(
                mode="number",
                value=0,
                domain={'x': [0, 1], 'y': [0, 1]},
                title={'text': "Error: Last service KM reading is greater than current end KM reading"},
            ))

        km_since_last_service = end_km - last_service_km

        # Define color of the bar based on km_since_last_service
        if km_since_last_service < 3000:
            bar_color = 'green'
        elif km_since_last_service < 6000:
            bar_color = 'yellow'
        else:
            bar_color = 'red'

        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=km_since_last_service,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={
                'text': "KM Since Last Service",
                'font': {'size': 30}  # Increase the size here
            },
            gauge={
                'axis': {'range': [None, 10000], 'tickwidth': 1, 'tickcolor': "darkblue"},
                'bar': {'color': bar_color},
                'bgcolor': "white",
                'borderwidth': 2,
                'bordercolor': "gray",
                'steps': [
                    {'range': [0, 3000], 'color': 'white'},
                    {'range': [3000, 6000], 'color': 'white'},
                    {'range': [6000, 10000], 'color': 'white'},
                ],
            },
            number={'suffix': " KM", 'font': {'size': 20}, 'valueformat': '0'},
        ))

        fig.update_layout(paper_bgcolor="lavender", font={'color': "darkblue", 'family': "Arial"})

        return fig
    # If last service KM reading is not provided
    elif last_service_km is None:
        return go.Figure(data=go.Indicator(
            mode="number",
            value=0,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': "Error: Last service KM reading not provided"},
        ))

    return go.Figure()

@app.callback(
    Output("last-tax-payment", "date"),
    Input("vehicle-selection", "value")
)
def update_last_tax_payment_date(vehicle):
    cursor_tax = conn.cursor()
    cursor_tax.execute(
        "SELECT last_tax_payment FROM car_data WHERE vehicle_no=? ORDER BY date DESC LIMIT 1",
        (vehicle,)
    )
    row = cursor_tax.fetchone()
    cursor_tax.close()
    if row:
        return datetime.strptime(row[0], "%Y-%m-%d").date()
    else:
        return None

@app.callback(
    Output("tax-gauge", "figure"),
    [Input("submit-button", "n_clicks"), Input("vehicle-selection", "value")],
    State("last-tax-payment", "date"),
)
def update_tax_gauge(n_clicks, vehicle, last_tax_payment):
    if vehicle and last_tax_payment:
        last_tax_payment_date = datetime.strptime(last_tax_payment, "%Y-%m-%d")
        tax_due_date = last_tax_payment_date + timedelta(days=365)
        days_until_due = (tax_due_date - datetime.now()).days

        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=days_until_due,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': "Days Until Tax Due"},
            gauge={'axis': {'range': [None, 365]}},
            number={'suffix': " Days"},
        ))

        return fig

    return go.Figure()




if __name__ == '__main__':
    app.run_server(debug=True)

# Close the database connection
conn.close()
