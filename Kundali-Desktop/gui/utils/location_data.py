"""Offline administrative hierarchy helpers for native location entry."""
from __future__ import annotations

from typing import Iterable, Optional


NEPAL_PROVINCES = {
    "Koshi": [
        "Bhojpur", "Dhankuta", "Ilam", "Jhapa", "Khotang", "Morang",
        "Okhaldhunga", "Panchthar", "Sankhuwasabha", "Solukhumbu",
        "Sunsari", "Taplejung", "Terhathum", "Udayapur",
    ],
    "Madhesh": [
        "Bara", "Dhanusha", "Mahottari", "Parsa", "Rautahat", "Saptari",
        "Sarlahi", "Siraha",
    ],
    "Bagmati": [
        "Bhaktapur", "Chitwan", "Dhading", "Dolakha", "Kathmandu",
        "Kavrepalanchok", "Lalitpur", "Makwanpur", "Nuwakot", "Ramechhap",
        "Rasuwa", "Sindhuli", "Sindhupalchok",
    ],
    "Gandaki": [
        "Baglung", "Gorkha", "Kaski", "Lamjung", "Manang", "Mustang",
        "Myagdi", "Nawalpur", "Parbat", "Syangja", "Tanahun",
    ],
    "Lumbini": [
        "Arghakhanchi", "Banke", "Bardiya", "Dang", "Gulmi", "Kapilvastu",
        "Nawalparasi West", "Palpa", "Pyuthan", "Rolpa", "Rukum East",
        "Rupandehi",
    ],
    "Karnali": [
        "Dailekh", "Dolpa", "Humla", "Jajarkot", "Jumla", "Kalikot",
        "Mugu", "Rukum West", "Salyan", "Surkhet",
    ],
    "Sudurpashchim": [
        "Achham", "Baitadi", "Bajhang", "Bajura", "Dadeldhura", "Darchula",
        "Doti", "Kailali", "Kanchanpur",
    ],
}

NEPAL_PROVINCE_NE = {
    "Koshi": "कोशी", "Madhesh": "मधेश", "Bagmati": "बागमती",
    "Gandaki": "गण्डकी", "Lumbini": "लुम्बिनी", "Karnali": "कर्णाली",
    "Sudurpashchim": "सुदूरपश्चिम",
}

# District-center coordinates imported from the former Web preset list.  These
# are administrative reference points, not a claim that every settlement is
# represented. Nepal uses one IANA timezone nationwide.
_NEPAL_DISTRICT_ROWS = [
    ("Taplejung", "ताप्लेजुङ", 27.3566, 87.669),
    ("Panchthar", "पाँचथर", 27.1333, 87.7833),
    ("Ilam", "इलाम", 26.9108, 87.9244),
    ("Jhapa", "झापा", 26.5407, 87.899),
    ("Morang", "मोरङ", 26.6534, 87.3248),
    ("Sunsari", "सुनसरी", 26.7165, 87.1744),
    ("Dhankuta", "धनकुटा", 26.9833, 87.3333),
    ("Terhathum", "तेह्रथुम", 27.1, 87.55),
    ("Sankhuwasabha", "सङ्खुवासभा", 27.55, 87.1333),
    ("Bhojpur", "भोजपुर", 27.1717, 87.0563),
    ("Solukhumbu", "सोलुखुम्बु", 27.6644, 86.5837),
    ("Okhaldhunga", "ओखलढुङ्गा", 27.3091, 86.504),
    ("Khotang", "खोटाङ", 27.0251, 86.8393),
    ("Udayapur", "उदयपुर", 26.8882, 86.5353),
    ("Saptari", "सप्तरी", 26.6009, 86.7074),
    ("Siraha", "सिरहा", 26.6543, 86.2066),
    ("Dhanusha", "धनुषा", 26.8154, 85.9328),
    ("Mahottari", "महोत्तरी", 26.6533, 85.7953),
    ("Sarlahi", "सर्लाही", 27.0228, 85.5722),
    ("Rautahat", "रौतहट", 27.0107, 85.2825),
    ("Bara", "बारा", 27.016, 85.0165),
    ("Parsa", "पर्सा", 27.0833, 84.8667),
    ("Kathmandu", "काठमाडौं", 27.7172, 85.324),
    ("Lalitpur", "ललितपुर", 27.671, 85.324),
    ("Bhaktapur", "भक्तपुर", 27.672, 85.4298),
    ("Nuwakot", "नुवाकोट", 27.9101, 85.1682),
    ("Rasuwa", "रसुवा", 28.1, 85.4),
    ("Dhading", "धादिङ", 27.8698, 84.9121),
    ("Makwanpur", "मकवानपुर", 27.4329, 85.0352),
    ("Sindhuli", "सिन्धुली", 27.2496, 85.9706),
    ("Ramechhap", "रामेछाप", 27.3281, 86.0852),
    ("Dolakha", "दोलखा", 27.6672, 86.0826),
    ("Sindhupalchok", "सिन्धुपाल्चोक", 27.9441, 85.6897),
    ("Kavrepalanchok", "काभ्रेपलाञ्चोक", 27.5291, 85.6857),
    ("Chitwan", "चितवन", 27.5291, 84.3542),
    ("Gorkha", "गोरखा", 28.0, 84.6333),
    ("Lamjung", "लमजुङ", 28.2, 84.35),
    ("Tanahun", "तनहुँ", 27.9, 84.35),
    ("Syangja", "स्याङ्जा", 28.0, 83.8833),
    ("Kaski", "कास्की", 28.2096, 83.9856),
    ("Manang", "मनाङ", 28.6667, 84.0167),
    ("Mustang", "मुस्ताङ", 28.9847, 83.7399),
    ("Myagdi", "म्याग्दी", 28.5, 83.5667),
    ("Nawalpur", "नवलपरासी पूर्व", 27.6833, 83.9167),
    ("Parbat", "पर्वत", 28.2333, 83.65),
    ("Baglung", "बागलुङ", 28.2664, 83.5858),
    ("Gulmi", "गुल्मी", 28.0667, 83.2667),
    ("Palpa", "पाल्पा", 27.8667, 83.55),
    ("Nawalparasi West", "नवलपरासी पश्चिम", 27.5611, 83.6928),
    ("Rupandehi", "रूपन्देही", 27.5, 83.35),
    ("Kapilvastu", "कपिलवस्तु", 27.5833, 83.05),
    ("Arghakhanchi", "अर्घाखाँची", 27.95, 83.1),
    ("Pyuthan", "प्युठान", 28.1011, 82.8629),
    ("Rolpa", "रोल्पा", 28.35, 82.7333),
    ("Rukum East", "रुकुम पूर्व", 28.6167, 82.6167),
    ("Banke", "बाँके", 28.0667, 81.5667),
    ("Bardiya", "बर्दिया", 28.3544, 81.2751),
    ("Dang", "दाङ", 27.9833, 82.4),
    ("Dolpa", "डोल्पा", 29.0667, 82.9167),
    ("Mugu", "मुगु", 29.55, 82.15),
    ("Humla", "हुम्ला", 30.0833, 81.85),
    ("Jumla", "जुम्ला", 29.2744, 82.1835),
    ("Kalikot", "कालिकोट", 29.1667, 81.7833),
    ("Dailekh", "दैलेख", 28.8333, 81.7167),
    ("Jajarkot", "जाजरकोट", 28.7014, 82.1928),
    ("Rukum West", "रुकुम पश्चिम", 28.6167, 82.35),
    ("Salyan", "सल्यान", 28.3667, 82.15),
    ("Surkhet", "सुर्खेत", 28.6, 81.6167),
    ("Bajura", "बाजुरा", 29.4167, 81.35),
    ("Bajhang", "बझाङ", 29.6667, 81.2167),
    ("Achham", "अछाम", 29.1167, 81.15),
    ("Doti", "डोटी", 29.2667, 80.9667),
    ("Kailali", "कैलाली", 28.6333, 80.7167),
    ("Kanchanpur", "कञ्चनपुर", 28.8333, 80.1833),
    ("Darchula", "दार्चुला", 29.85, 80.55),
    ("Baitadi", "बैतडी", 29.5333, 80.55),
    ("Dadeldhura", "डडेलधुरा", 29.3, 80.5333),
]

# City -> district mapping for the curated Nepal city set.  Keys use the bare
# city name (parenthetical aliases resolve via _city_region).
NEPAL_CITY_DISTRICTS = {
    # Bagmati
    "Kathmandu": "Kathmandu", "Lalitpur": "Lalitpur", "Bhaktapur": "Bhaktapur",
    "Kirtipur": "Kathmandu", "Madhyapur Thimi": "Bhaktapur",
    "Budhanilkantha": "Kathmandu", "Tokha": "Kathmandu",
    "Chitwan": "Chitwan", "Bharatpur": "Chitwan",
    "Hetauda": "Makwanpur", "Banepa": "Kavrepalanchok",
    "Dhulikhel": "Kavrepalanchok", "Panauti": "Kavrepalanchok",
    "Bidur": "Nuwakot", "Dhading Besi": "Dhading",
    "Sindhuli": "Sindhuli", "Ramechhap": "Ramechhap", "Dolakha": "Dolakha",
    "Chautara": "Sindhupalchok", "Dhunche": "Rasuwa",
    # Gandaki
    "Pokhara": "Kaski", "Lekhnath": "Kaski", "Gorkha": "Gorkha",
    "Damauli": "Tanahun", "Besisahar": "Lamjung", "Baglung": "Baglung",
    "Beni": "Myagdi", "Kusma": "Parbat", "Putalibazar": "Syangja",
    "Waling": "Syangja", "Kawasoti": "Nawalpur", "Jomsom": "Mustang",
    "Chame": "Manang",
    # Koshi
    "Biratnagar": "Morang", "Dharan": "Sunsari", "Itahari": "Sunsari",
    "Inaruwa": "Sunsari", "Damak": "Jhapa", "Bhadrapur": "Jhapa",
    "Birtamod": "Jhapa", "Mechinagar": "Jhapa", "Ilam": "Ilam",
    "Dhankuta": "Dhankuta", "Bhojpur": "Bhojpur", "Phidim": "Panchthar",
    "Fungling": "Taplejung", "Myanglung": "Terhathum",
    "Khandbari": "Sankhuwasabha", "Salleri": "Solukhumbu",
    "Okhaldhunga": "Okhaldhunga", "Diktel": "Khotang", "Gaighat": "Udayapur",
    # Madhesh
    "Janakpur": "Dhanusha", "Birgunj": "Parsa", "Jitpur Simara": "Bara",
    "Kalaiya": "Bara", "Gaur": "Rautahat", "Malangwa": "Sarlahi",
    "Jaleshwar": "Mahottari", "Siraha": "Siraha", "Lahan": "Siraha",
    "Rajbiraj": "Saptari",
    # Lumbini
    "Butwal": "Rupandehi", "Siddharthanagar": "Rupandehi",
    "Lumbini Cultural": "Kapilvastu", "Taulihawa": "Kapilvastu",
    "Nepalgunj": "Banke", "Kohalpur": "Banke", "Gulariya": "Bardiya",
    "Ghorahi": "Dang", "Tulsipur": "Dang", "Lamahi": "Dang",
    "Tansen": "Palpa", "Ramgram": "Nawalparasi West",
    "Sandhikharka": "Arghakhanchi", "Tamghas": "Gulmi",
    "Pyuthan": "Pyuthan", "Liwang": "Rolpa", "Rukumkot": "Rukum East",
    # Karnali
    "Birendranagar": "Surkhet", "Jumla": "Jumla", "Dailekh": "Dailekh",
    "Jajarkot": "Jajarkot", "Salyan": "Salyan", "Musikot": "Rukum West",
    "Manma": "Kalikot", "Gamgadhi": "Mugu", "Simikot": "Humla",
    "Dunai": "Dolpa",
    # Sudurpashchim
    "Dhangadhi": "Kailali", "Tikapur": "Kailali",
    "Bhimdatta": "Kanchanpur", "Amargadhi": "Dadeldhura",
    "Dasharathchand": "Baitadi", "Darchula": "Darchula",
    "Dipayal Silgadhi": "Doti", "Mangalsen": "Achham",
    "Chainpur": "Bajhang", "Martadi": "Bajura",
}

# Region labels represented by the curated Indian city set.
INDIA_CITY_REGIONS = {
    "New Delhi": "Delhi", "Delhi (Old Delhi)": "Delhi",
    "Mumbai": "Maharashtra", "Pune": "Maharashtra", "Nagpur": "Maharashtra",
    "Nashik": "Maharashtra", "Aurangabad": "Maharashtra", "Thane": "Maharashtra",
    "Navi Mumbai": "Maharashtra", "Solapur": "Maharashtra", "Kolhapur": "Maharashtra",
    "Amravati": "Maharashtra", "Akola": "Maharashtra", "Latur": "Maharashtra",
    "Nanded": "Maharashtra", "Jalgaon": "Maharashtra", "Chandrapur": "Maharashtra",
    "Ratnagiri": "Maharashtra", "Sangli": "Maharashtra",
    "Ahmedabad": "Gujarat", "Surat": "Gujarat", "Vadodara": "Gujarat",
    "Rajkot": "Gujarat", "Gandhinagar": "Gujarat", "Bhavnagar": "Gujarat",
    "Jamnagar": "Gujarat", "Junagadh": "Gujarat", "Gandhidham": "Gujarat",
    "Bhuj": "Gujarat", "Mehsana": "Gujarat", "Anand": "Gujarat",
    "Jaipur": "Rajasthan", "Jodhpur": "Rajasthan", "Udaipur": "Rajasthan",
    "Bikaner": "Rajasthan", "Kota": "Rajasthan", "Ajmer": "Rajasthan",
    "Alwar": "Rajasthan", "Bharatpur": "Rajasthan", "Sikar": "Rajasthan",
    "Pali": "Rajasthan", "Bhilwara": "Rajasthan",
    "Lucknow": "Uttar Pradesh", "Kanpur": "Uttar Pradesh", "Agra": "Uttar Pradesh",
    "Varanasi": "Uttar Pradesh", "Prayagraj (Allahabad)": "Uttar Pradesh",
    "Meerut": "Uttar Pradesh", "Ghaziabad": "Uttar Pradesh", "Noida": "Uttar Pradesh",
    "Greater Noida": "Uttar Pradesh",
    "Bareilly": "Uttar Pradesh", "Aligarh": "Uttar Pradesh", "Moradabad": "Uttar Pradesh",
    "Saharanpur": "Uttar Pradesh", "Gorakhpur": "Uttar Pradesh", "Jhansi": "Uttar Pradesh",
    "Firozabad": "Uttar Pradesh", "Muzaffarnagar": "Uttar Pradesh",
    "Mathura": "Uttar Pradesh", "Ayodhya": "Uttar Pradesh",
    "Indore": "Madhya Pradesh", "Bhopal": "Madhya Pradesh", "Gwalior": "Madhya Pradesh",
    "Jabalpur": "Madhya Pradesh", "Ujjain": "Madhya Pradesh", "Sagar": "Madhya Pradesh",
    "Rewa": "Madhya Pradesh", "Satna": "Madhya Pradesh", "Ratlam": "Madhya Pradesh",
    "Dewas": "Madhya Pradesh", "Chhindwara": "Madhya Pradesh",
    "Kolkata": "West Bengal", "Siliguri": "West Bengal", "Asansol": "West Bengal",
    "Durgapur": "West Bengal", "Howrah": "West Bengal", "Darjeeling": "West Bengal",
    "Kharagpur": "West Bengal", "Malda": "West Bengal",
    "Patna": "Bihar", "Gaya": "Bihar", "Bhagalpur": "Bihar",
    "Muzaffarpur": "Bihar", "Darbhanga": "Bihar", "Purnia": "Bihar", "Arrah": "Bihar",
    "Ranchi": "Jharkhand", "Jamshedpur": "Jharkhand", "Dhanbad": "Jharkhand",
    "Bokaro": "Jharkhand", "Hazaribagh": "Jharkhand", "Deoghar": "Jharkhand",
    "Raipur": "Chhattisgarh", "Bhilai": "Chhattisgarh", "Bilaspur": "Chhattisgarh",
    "Korba": "Chhattisgarh", "Raigarh": "Chhattisgarh", "Durg": "Chhattisgarh",
    "Bhubaneswar": "Odisha", "Cuttack": "Odisha", "Rourkela": "Odisha",
    "Berhampur": "Odisha", "Sambalpur": "Odisha", "Puri": "Odisha",
    "Bengaluru": "Karnataka", "Mysore": "Karnataka", "Mangalore": "Karnataka",
    "Hubli (Hubballi)": "Karnataka", "Belgaum (Belagavi)": "Karnataka",
    "Gulbarga (Kalaburagi)": "Karnataka", "Davanagere": "Karnataka",
    "Shimoga (Shivamogga)": "Karnataka", "Tumkur": "Karnataka",
    "Bijapur (Vijayapura)": "Karnataka", "Udupi": "Karnataka",
    "Thiruvananthapuram": "Kerala", "Kochi (Cochin)": "Kerala",
    "Kozhikode (Calicut)": "Kerala", "Thrissur": "Kerala", "Kollam": "Kerala",
    "Palakkad": "Kerala", "Kannur": "Kerala", "Alappuzha": "Kerala",
    "Chennai": "Tamil Nadu", "Coimbatore": "Tamil Nadu", "Madurai": "Tamil Nadu",
    "Salem": "Tamil Nadu", "Tiruchirappalli": "Tamil Nadu", "Tirunelveli": "Tamil Nadu",
    "Vellore": "Tamil Nadu", "Erode": "Tamil Nadu", "Thanjavur": "Tamil Nadu",
    "Kumbakonam": "Tamil Nadu", "Dindigul": "Tamil Nadu", "Cuddalore": "Tamil Nadu",
    "Visakhapatnam": "Andhra Pradesh", "Vijayawada": "Andhra Pradesh",
    "Guntur": "Andhra Pradesh", "Nellore": "Andhra Pradesh", "Tirupati": "Andhra Pradesh",
    "Kurnool": "Andhra Pradesh", "Rajahmundry": "Andhra Pradesh",
    "Kakinada": "Andhra Pradesh", "Anantapur": "Andhra Pradesh", "Kadapa": "Andhra Pradesh",
    "Nandyal": "Andhra Pradesh", "Ongole": "Andhra Pradesh",
    "Machilipatnam": "Andhra Pradesh", "Bhimavaram": "Andhra Pradesh",
    "Srikakulam": "Andhra Pradesh",
    "Hyderabad": "Telangana", "Warangal": "Telangana", "Nizamabad": "Telangana",
    "Karimnagar": "Telangana", "Khammam": "Telangana", "Adilabad": "Telangana",
    "Secunderabad": "Telangana",
    "Ludhiana": "Punjab", "Amritsar": "Punjab", "Jalandhar": "Punjab",
    "Patiala": "Punjab", "Bathinda": "Punjab", "Hoshiarpur": "Punjab",
    "Pathankot": "Punjab", "Moga": "Punjab", "Sangrur": "Punjab",
    "Faridabad": "Haryana", "Gurgaon (Gurugram)": "Haryana", "Ambala": "Haryana",
    "Panipat": "Haryana", "Karnal": "Haryana", "Rohtak": "Haryana",
    "Hisar": "Haryana", "Yamunanagar": "Haryana",
    "Shimla": "Himachal Pradesh", "Dharamshala": "Himachal Pradesh",
    "Mandi": "Himachal Pradesh", "Solan": "Himachal Pradesh", "Kullu": "Himachal Pradesh",
    "Dehradun": "Uttarakhand", "Haridwar": "Uttarakhand", "Rishikesh": "Uttarakhand",
    "Haldwani": "Uttarakhand", "Nainital": "Uttarakhand", "Roorkee": "Uttarakhand",
    "Srinagar": "Jammu and Kashmir", "Jammu": "Jammu and Kashmir",
    "Anantnag": "Jammu and Kashmir", "Baramulla": "Jammu and Kashmir",
    "Leh": "Ladakh", "Chandigarh": "Chandigarh",
    "Guwahati": "Assam", "Silchar": "Assam", "Dibrugarh": "Assam",
    "Jorhat": "Assam", "Nagaon": "Assam", "Imphal": "Manipur",
    "Aizawl": "Mizoram", "Kohima": "Nagaland", "Shillong": "Meghalaya",
    "Itanagar": "Arunachal Pradesh", "Agartala": "Tripura", "Gangtok": "Sikkim",
    "Panaji (Goa)": "Goa", "Margao": "Goa", "Vasco da Gama": "Goa",
    "Namchi": "Sikkim", "Puducherry": "Puducherry",
    "Port Blair (Andaman)": "Andaman and Nicobar Islands",
    "Kavaratti (Lakshadweep)": "Lakshadweep",
    "Silvassa (Dadra & Nagar Haveli)": "Dadra and Nagar Haveli",
    "Daman": "Daman and Diu",
}


# State/Province (first-level administrative division) for every city outside
# Nepal and India in cities_data.py.  Parenthetical aliases (alternate city
# names) resolve to their base city; parenthetical state disambiguators are
# stored verbatim so they never collide with an unrelated same-name city.
WORLD_CITY_REGIONS = {
    "USA": {
        "New York": "New York", "Brooklyn": "New York", "Queens": "New York",
        "Buffalo": "New York", "Albany": "New York",
        "Boston": "Massachusetts", "Cambridge": "Massachusetts",
        "Worcester": "Massachusetts",
        "Philadelphia": "Pennsylvania", "Pittsburgh": "Pennsylvania",
        "Allentown": "Pennsylvania",
        "Washington DC": "District of Columbia",
        "Baltimore": "Maryland",
        "Richmond": "Virginia", "Virginia Beach": "Virginia", "Norfolk": "Virginia",
        "Arlington": "Virginia",
        "Atlanta": "Georgia", "Augusta": "Georgia", "Savannah": "Georgia",
        "Miami": "Florida", "Orlando": "Florida", "Tampa": "Florida",
        "Jacksonville": "Florida", "Fort Lauderdale": "Florida",
        "Tallahassee": "Florida",
        "Charlotte": "North Carolina", "Raleigh": "North Carolina",
        "Durham": "North Carolina", "Greensboro": "North Carolina",
        "Columbia": "South Carolina", "Charleston": "South Carolina",
        "Detroit": "Michigan", "Grand Rapids": "Michigan", "Ann Arbor": "Michigan",
        "Columbus": "Ohio", "Cleveland": "Ohio", "Cincinnati": "Ohio",
        "Indianapolis": "Indiana", "Fort Wayne": "Indiana",
        "Louisville": "Kentucky", "Lexington": "Kentucky",
        "Jersey City": "New Jersey", "Newark": "New Jersey", "Edison": "New Jersey",
        "Hartford": "Connecticut", "New Haven": "Connecticut",
        "Providence": "Rhode Island",
        "Portland (Maine)": "Maine",
        "Manchester (NH)": "New Hampshire",
        "Burlington": "Vermont",
        "Wilmington": "Delaware",
        "Charleston (WV)": "West Virginia",
        "Chicago": "Illinois", "Naperville": "Illinois",
        "Houston": "Texas", "Dallas": "Texas", "Fort Worth": "Texas",
        "Austin": "Texas", "San Antonio": "Texas", "Plano": "Texas",
        "Irving": "Texas", "Frisco": "Texas", "El Paso": "Texas",
        "Minneapolis": "Minnesota", "St. Paul": "Minnesota",
        "Milwaukee": "Wisconsin", "Madison": "Wisconsin",
        "St. Louis": "Missouri", "Kansas City": "Missouri",
        "Nashville": "Tennessee", "Memphis": "Tennessee",
        "New Orleans": "Louisiana", "Baton Rouge": "Louisiana",
        "Oklahoma City": "Oklahoma", "Tulsa": "Oklahoma",
        "Omaha": "Nebraska", "Lincoln": "Nebraska",
        "Des Moines": "Iowa", "Cedar Rapids": "Iowa",
        "Wichita": "Kansas",
        "Little Rock": "Arkansas",
        "Jackson": "Mississippi",
        "Birmingham (USA)": "Alabama",
        "Fargo": "North Dakota",
        "Sioux Falls": "South Dakota",
        "Denver": "Colorado", "Colorado Springs": "Colorado", "Aurora": "Colorado",
        "Boulder": "Colorado",
        "Salt Lake City": "Utah", "Provo": "Utah",
        "Phoenix": "Arizona", "Tucson": "Arizona", "Mesa": "Arizona",
        "Chandler": "Arizona", "Scottsdale": "Arizona",
        "Albuquerque": "New Mexico", "Santa Fe": "New Mexico",
        "Boise": "Idaho", "Billings": "Montana", "Cheyenne": "Wyoming",
        "Los Angeles": "California", "San Francisco": "California",
        "San Diego": "California", "San Jose": "California",
        "Sacramento": "California", "Oakland": "California",
        "Fremont": "California", "Sunnyvale": "California",
        "Santa Clara": "California", "Irvine": "California",
        "Long Beach": "California", "Fresno": "California",
        "Bakersfield": "California", "Anaheim": "California",
        "Riverside": "California",
        "Seattle": "Washington", "Bellevue": "Washington", "Redmond": "Washington",
        "Tacoma": "Washington", "Spokane": "Washington",
        "Portland (Oregon)": "Oregon", "Eugene": "Oregon",
        "Salem (Oregon)": "Oregon",
        "Las Vegas": "Nevada", "Reno": "Nevada", "Henderson": "Nevada",
        "Anchorage": "Alaska", "Fairbanks": "Alaska", "Juneau": "Alaska",
        "Honolulu": "Hawaii", "Maui (Kahului)": "Hawaii",
    },
    "Canada": {
        "Toronto": "Ontario", "Mississauga": "Ontario", "Brampton": "Ontario",
        "Ottawa": "Ontario", "Hamilton": "Ontario", "Kitchener": "Ontario",
        "London (Canada)": "Ontario",
        "Montreal": "Quebec", "Quebec City": "Quebec", "Laval": "Quebec",
        "Vancouver": "British Columbia", "Surrey": "British Columbia",
        "Burnaby": "British Columbia", "Victoria": "British Columbia",
        "Calgary": "Alberta", "Edmonton": "Alberta",
        "Winnipeg": "Manitoba",
        "Saskatoon": "Saskatchewan", "Regina": "Saskatchewan",
        "Halifax": "Nova Scotia",
        "St. John's": "Newfoundland and Labrador",
    },
    "UK": {
        "London": "England", "Birmingham": "England", "Manchester": "England",
        "Leeds": "England", "Liverpool": "England", "Bristol": "England",
        "Sheffield": "England", "Newcastle upon Tyne": "England",
        "Nottingham": "England", "Leicester": "England",
        "Glasgow": "Scotland", "Edinburgh": "Scotland",
        "Cardiff": "Wales",
        "Belfast": "Northern Ireland",
    },
    "Ireland": {
        "Dublin": "Dublin", "Cork": "Cork", "Galway": "Galway",
    },
    "Australia": {
        "Sydney": "New South Wales", "Newcastle (Australia)": "New South Wales",
        "Wollongong": "New South Wales",
        "Melbourne": "Victoria",
        "Brisbane": "Queensland", "Gold Coast": "Queensland",
        "Perth": "Western Australia",
        "Adelaide": "South Australia",
        "Canberra": "Australian Capital Territory",
        "Hobart": "Tasmania",
        "Darwin": "Northern Territory",
    },
    "New Zealand": {
        "Auckland": "Auckland", "Wellington": "Wellington",
        "Christchurch": "Canterbury", "Hamilton (NZ)": "Waikato",
    },
    "UAE": {
        "Dubai": "Dubai", "Sharjah": "Sharjah", "Ajman": "Ajman",
        "Ras Al Khaimah": "Ras Al Khaimah",
        "Abu Dhabi": "Abu Dhabi", "Al Ain": "Abu Dhabi",
    },
    "Saudi Arabia": {
        "Riyadh": "Riyadh Province", "Jeddah": "Mecca Province",
        "Mecca": "Mecca Province", "Medina": "Medina Province",
        "Dammam": "Eastern Province", "Khobar": "Eastern Province",
    },
    "Qatar": {
        "Doha": "Doha", "Al Rayyan": "Al Rayyan",
    },
    "Kuwait": {
        "Kuwait City": "Capital Governorate",
    },
    "Bahrain": {
        "Manama": "Capital Governorate",
    },
    "Oman": {
        "Muscat": "Muscat Governorate", "Salalah": "Dhofar",
    },
    "Jordan": {
        "Amman": "Amman Governorate",
    },
    "Lebanon": {
        "Beirut": "Beirut Governorate",
    },
    "Israel": {
        "Tel Aviv": "Tel Aviv District", "Jerusalem": "Jerusalem District",
    },
    "Iraq": {
        "Baghdad": "Baghdad Governorate", "Erbil": "Erbil Governorate",
    },
    "Iran": {
        "Tehran": "Tehran Province", "Isfahan": "Isfahan Province",
    },
    "Turkey": {
        "Istanbul": "Istanbul Province", "Ankara": "Ankara Province",
        "Izmir": "Izmir Province",
    },
    "France": {
        "Paris": "Île-de-France",
        "Marseille": "Provence-Alpes-Côte d'Azur",
        "Nice": "Provence-Alpes-Côte d'Azur",
        "Lyon": "Auvergne-Rhône-Alpes",
        "Toulouse": "Occitanie",
    },
    "Germany": {
        "Berlin": "Berlin", "Hamburg": "Hamburg",
        "Munich": "Bavaria", "Stuttgart": "Baden-Württemberg",
        "Frankfurt": "Hesse",
        "Cologne": "North Rhine-Westphalia", "Dusseldorf": "North Rhine-Westphalia",
    },
    "Italy": {
        "Rome": "Lazio", "Milan": "Lombardy", "Naples": "Campania",
        "Turin": "Piedmont", "Florence": "Tuscany",
    },
    "Spain": {
        "Madrid": "Community of Madrid", "Barcelona": "Catalonia",
        "Valencia": "Valencian Community", "Seville": "Andalusia",
    },
    "Portugal": {
        "Lisbon": "Lisbon", "Porto": "Porto",
    },
    "Netherlands": {
        "Amsterdam": "North Holland", "Rotterdam": "South Holland",
        "The Hague": "South Holland",
    },
    "Belgium": {
        "Brussels": "Brussels-Capital Region", "Antwerp": "Flanders",
    },
    "Austria": {
        "Vienna": "Vienna", "Salzburg": "Salzburg",
    },
    "Switzerland": {
        "Zurich": "Zurich", "Geneva": "Geneva",
        "Basel": "Basel-Stadt", "Bern": "Bern",
    },
    "Sweden": {
        "Stockholm": "Stockholm County", "Gothenburg": "Västra Götaland",
    },
    "Norway": {
        "Oslo": "Oslo", "Bergen": "Vestland",
    },
    "Denmark": {
        "Copenhagen": "Capital Region of Denmark",
    },
    "Finland": {
        "Helsinki": "Uusimaa",
    },
    "Poland": {
        "Warsaw": "Masovian", "Krakow": "Lesser Poland",
    },
    "Czech Republic": {
        "Prague": "Prague",
    },
    "Hungary": {
        "Budapest": "Budapest",
    },
    "Greece": {
        "Athens": "Attica",
    },
    "Russia": {
        "Moscow": "Moscow", "Saint Petersburg": "Saint Petersburg",
    },
    "Japan": {
        "Tokyo": "Tokyo", "Yokohama": "Kanagawa", "Osaka": "Osaka",
        "Nagoya": "Aichi", "Sapporo": "Hokkaido", "Kobe": "Hyogo",
        "Kyoto": "Kyoto", "Fukuoka": "Fukuoka",
    },
    "South Korea": {
        "Seoul": "Seoul", "Busan": "Busan", "Incheon": "Incheon",
        "Daegu": "Daegu",
    },
    "China": {
        "Beijing": "Beijing", "Shanghai": "Shanghai", "Hong Kong": "Hong Kong",
        "Guangzhou": "Guangdong", "Shenzhen": "Guangdong",
        "Lhasa": "Tibet",
    },
    "Taiwan": {
        "Taipei": "Taipei", "Kaohsiung": "Kaohsiung",
    },
    "Singapore": {
        "Singapore": "Singapore",
    },
    "Malaysia": {
        "Kuala Lumpur": "Kuala Lumpur", "Penang (George Town)": "Penang",
        "Johor Bahru": "Johor",
    },
    "Thailand": {
        "Bangkok": "Bangkok", "Chiang Mai": "Chiang Mai", "Phuket": "Phuket",
    },
    "Indonesia": {
        "Jakarta": "Jakarta", "Surabaya": "East Java",
        "Bali (Denpasar)": "Bali",
    },
    "Philippines": {
        "Manila": "Metro Manila", "Cebu City": "Central Visayas",
    },
    "Vietnam": {
        "Ho Chi Minh City": "Ho Chi Minh City", "Hanoi": "Hanoi",
    },
    "Myanmar": {
        "Yangon": "Yangon Region", "Mandalay": "Mandalay Region",
    },
    "Bangladesh": {
        "Dhaka": "Dhaka Division", "Chittagong": "Chittagong Division",
        "Sylhet": "Sylhet Division",
    },
    "Pakistan": {
        "Karachi": "Sindh", "Lahore": "Punjab",
        "Islamabad": "Islamabad Capital Territory",
    },
    "Sri Lanka": {
        "Colombo": "Western Province", "Kandy": "Central Province",
    },
    "Bhutan": {
        "Thimphu": "Thimphu District",
    },
    "Mexico": {
        "Mexico City": "Mexico City", "Guadalajara": "Jalisco",
        "Monterrey": "Nuevo León",
    },
    "Brazil": {
        "Sao Paulo": "São Paulo", "Rio de Janeiro": "Rio de Janeiro",
        "Brasilia": "Distrito Federal",
    },
    "Argentina": {
        "Buenos Aires": "Buenos Aires", "Cordoba": "Córdoba",
    },
    "Chile": {
        "Santiago": "Santiago Metropolitan Region",
    },
    "Peru": {
        "Lima": "Lima",
    },
    "Colombia": {
        "Bogota": "Bogotá", "Medellin": "Antioquia",
    },
    "Egypt": {
        "Cairo": "Cairo Governorate", "Alexandria": "Alexandria Governorate",
    },
    "Kenya": {
        "Nairobi": "Nairobi County", "Mombasa": "Mombasa County",
    },
    "South Africa": {
        "Johannesburg": "Gauteng", "Cape Town": "Western Cape",
        "Durban": "KwaZulu-Natal",
    },
    "Nigeria": {
        "Lagos": "Lagos State",
    },
    "Ethiopia": {
        "Addis Ababa": "Addis Ababa",
    },
    "Morocco": {
        "Casablanca": "Casablanca-Settat",
    },
}


def _city_region(mapping: dict[str, str], name: str) -> Optional[str]:
    """Resolve a city's region, honoring exact names and alternate aliases."""
    if not mapping or not name:
        return None
    if name in mapping:
        return mapping[name]
    base = name.split("(", 1)[0].strip()
    if base and base in mapping:
        return mapping[base]
    return None


def province_for_district(district: Optional[str]) -> Optional[str]:
    if not district:
        return None
    for province, districts in NEPAL_PROVINCES.items():
        if district in districts:
            return province
    return None


# Build district metadata after the hierarchy helper is available.
NEPAL_DISTRICT_META = {
    name: {
        "name": name, "name_ne": name_ne, "country": "Nepal",
        "region": province_for_district(name), "district": name,
        "lat": lat, "lon": lon, "tz": 5.75,
        "timezone_id": "Asia/Kathmandu", "source": "web_district_preset",
    }
    for name, name_ne, lat, lon in _NEPAL_DISTRICT_ROWS
}


def district_metadata(country: Optional[str], district: Optional[str]) -> Optional[dict]:
    """Return a copy of a known district reference point, when available."""
    if country != "Nepal" or not district:
        return None
    metadata = NEPAL_DISTRICT_META.get(district)
    return dict(metadata) if metadata else None


def bilingual_district_label(district: str) -> str:
    metadata = NEPAL_DISTRICT_META.get(district) or {}
    translated = metadata.get("name_ne")
    return f"{district} / {translated}" if translated else district


_LOCATION_INDEX_CACHE: dict[int, tuple[list[dict], dict, dict, dict]] = {}


def enrich_cities(cities: Iterable[dict]) -> list[dict]:
    """Add normalized region/district metadata without mutating source records."""
    enriched = []
    for source in cities:
        city = dict(source)
        country = city.get("country") or ""
        name = city.get("name") or ""
        if country == "Nepal":
            district = _city_region(NEPAL_CITY_DISTRICTS, name)
            city["district"] = district
            city["region"] = province_for_district(district)
        elif country == "India":
            city["region"] = _city_region(INDIA_CITY_REGIONS, name)
            city["district"] = None
        else:
            city["region"] = _city_region(WORLD_CITY_REGIONS.get(country, {}), name)
            city["district"] = None
        enriched.append(city)
    return enriched


def _location_indexes(cities: Iterable[dict]) -> tuple[list[dict], dict, dict, dict]:
    """Build reusable country/region/district indexes for a stable city list."""
    if not isinstance(cities, list):
        cities = list(cities)
    cache_key = id(cities)
    cached = _LOCATION_INDEX_CACHE.get(cache_key)
    if cached is not None and cached[0] is cities:
        return cached

    by_country: dict[str, list[dict]] = {}
    by_region: dict[tuple[str, str], list[dict]] = {}
    by_district: dict[tuple[str, str, str], list[dict]] = {}
    for city in cities:
        country = city.get("country")
        region = city.get("region")
        district = city.get("district")
        if country:
            by_country.setdefault(country, []).append(city)
        if country and region:
            by_region.setdefault((country, region), []).append(city)
        if country and region and district:
            by_district.setdefault((country, region, district), []).append(city)

    result = (cities, by_country, by_region, by_district)
    _LOCATION_INDEX_CACHE[cache_key] = result
    return result


def countries(cities: Iterable[dict]) -> list[str]:
    values = sorted({city.get("country") for city in cities if city.get("country")})
    if "Nepal" in values:
        values.remove("Nepal")
        values.insert(0, "Nepal")
    return values


def regions_for_country(country: str, cities: Iterable[dict]) -> list[str]:
    if country == "Nepal":
        return list(NEPAL_PROVINCES)
    _, by_country, _, _ = _location_indexes(cities)
    return sorted({city.get("region") for city in by_country.get(country, []) if city.get("region")})


def districts_for_region(country: str, region: Optional[str], cities: Iterable[dict]) -> list[str]:
    if country == "Nepal" and region:
        return list(NEPAL_PROVINCES.get(region, []))
    _, by_country, by_region, _ = _location_indexes(cities)
    source = by_region.get((country, region), []) if region else by_country.get(country, [])
    return sorted({city.get("district") for city in source if city.get("district")})


def filtered_cities(
    cities: Iterable[dict], country: str, region: Optional[str] = None,
    district: Optional[str] = None,
) -> list[dict]:
    _, by_country, by_region, by_district = _location_indexes(cities)
    if district and region:
        result = by_district.get((country, region, district), [])
    elif region:
        result = by_region.get((country, region), [])
    else:
        result = by_country.get(country, [])
    return sorted(result, key=lambda item: (item.get("name") or "").casefold())
