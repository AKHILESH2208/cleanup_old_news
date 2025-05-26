import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime, timedelta, timezone
from dateutil.parser import parse

# Initialize Firebase
cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

# Get current time and two years ago
now = datetime.now(timezone.utc)
two_years_ago = now - timedelta(days=2 * 365)

# Reference locations
locations_ref = db.collection("locations")
locations = locations_ref.stream()

for loc_doc in locations:
    loc = loc_doc.to_dict()
    lat = loc.get("latitude")
    lng = loc.get("longitude")
    location_name = loc.get("location")

    if lat is None or lng is None:
        print(f"Skipping location with missing coordinates: {location_name}")
        continue

    # Query news_markers for this location
    news_query = db.collection("news_markers") \
        .where("latitude", "==", lat) \
        .where("longitude", "==", lng)

    news_docs = list(news_query.stream())

    if len(news_docs) < 3:
        print(f"Skipping {location_name}: only {len(news_docs)} news items.")
        continue

    print(f"Processing {location_name}: {len(news_docs)} news items found.")

    for doc in news_docs:
        news_data = doc.to_dict()
        timestamp_str = news_data.get("timestamp")

        if timestamp_str:
            try:
                timestamp_dt = parse(timestamp_str).replace(tzinfo=timezone.utc)
                if timestamp_dt < two_years_ago:
                    print(f"Deleting old news: {doc.id} from {location_name}")
                    doc.reference.delete()
            except Exception as e:
                print(f"Error parsing timestamp for {doc.id}: {e}")
        else:
            print(f"No timestamp found for {doc.id} in {location_name}")
