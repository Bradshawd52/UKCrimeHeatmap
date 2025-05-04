from flask import Flask, render_template, request
import requests, os

app = Flask(__name__)

# Get coordinates from Postcode
def get_coordinates(postcode):
    url = f"https://api.postcodes.io/postcodes/{postcode}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        return data['result']['latitude'], data['result']['longitude']
    return None, None

# Geocoding for city name (using Nominatim API)
def get_geocode_by_city(city):
    url = f"https://nominatim.openstreetmap.org/search?city={city}&format=json&limit=1"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        if data:
            return float(data[0]['lat']), float(data[0]['lon'])
    return None, None

# Get Crime Data based on coordinates, date, and crime type
def get_crime_data(lat, lng, date, crime_type=None):
    url = f"https://data.police.uk/api/crimes-street/all-crime?lat={lat}&lng={lng}&date={date}"
    response = requests.get(url)
    if response.status_code == 200:
        crimes = response.json()

                
        if crime_type:
            crimes = [crime for crime in crimes if crime['category'] == crime_type]
        return crimes
    return []

def get_crime_data_for_date(lat, lng, date, crime_type=None):
    all_crimes = []

    # If the date is a year (e.g. '2025'), generate data for all 12 months of the year
    if len(date) == 4:  # If the date is just a year (e.g. '2025')
        for month in range(1, 13):
            month_str = f"{date}-{month:02d}"
            crimes = get_crime_data(lat, lng, month_str, crime_type)
            all_crimes.extend(crimes)
    else:  # Otherwise, it's a specific year-month (e.g. '2025-01')
        crimes = get_crime_data(lat, lng, date, crime_type)
        all_crimes.extend(crimes)

    return all_crimes


@app.route('/')
def index():

    postcode = request.args.get('postcode', '')
    city = request.args.get('city', '')
    date = request.args.get('date', '2025') 
    crime_type = request.args.get('crime_type', '')

    # If no postcode is provided, try to get coordinates based on city name
    lat, lng = None, None
    if postcode:
        lat, lng = get_coordinates(postcode)
    elif city:
        lat, lng = get_geocode_by_city(city)

    if not lat or not lng:
        
        lat, lng = get_geocode_by_city('Liverpool')

    crimes = get_crime_data_for_date(lat, lng, date, crime_type)
    
    num_crimes = len(crimes)

    # Available crime categories
    crime_categories = [
        'anti-social-behaviour', 'burglary', 'criminal-damage-arson', 'drugs', 'public-order', 'shoplifting', 'theft-from-the-person',
        'vehicle-crime', 'violent-crime', 'bicycle-theft', 'other-crime'
    ]


    return render_template(
        'index.html', 
        crimes=crimes, 
        crime_categories=crime_categories, 
        lat=lat, 
        lng=lng, 
        postcode=postcode, 
        city=city, 
        date=date,
        num_crimes=num_crimes
    )

if __name__ == '__main__':
    app.run(debug=False, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
