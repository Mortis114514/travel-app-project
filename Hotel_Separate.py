import requests

API_KEY = "AIzaSyAMc4KPATogfZlGj7qpir34DyHFWjszKwU"
place_id = "ChIJx_JJOAQGAWARzm1G-Hxo4qE"

url = "https://maps.googleapis.com/maps/api/place/details/json"

params = {
    "place_id": place_id,
    "fields": "name,formatted_phone_number,website,url,hotel_star_rating",
    "key": API_KEY
}

res = requests.get(url, params=params)
print(res.json())
