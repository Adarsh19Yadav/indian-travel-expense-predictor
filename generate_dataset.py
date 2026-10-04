import csv
import random
import math

random.seed(42)

# ── Destinations with fixed type, base distance range, and seasonal peak ──────
DESTINATIONS = [
    # (name, type, dist_range, peak_season_hint)
    ("Delhi",          "City",      (200,  1800), "Winter"),
    ("Mumbai",         "City",      (100,  2000), "Winter"),
    ("Bengaluru",      "City",      (150,  2500), "Winter"),
    ("Hyderabad",      "City",      (200,  2000), "Winter"),
    ("Chennai",        "City",      (150,  2500), "Winter"),
    ("Kolkata",        "City",      (100,  2200), "Winter"),
    ("Pune",           "City",      (100,  1800), "Winter"),
    ("Ahmedabad",      "City",      (100,  1500), "Winter"),
    ("Surat",          "City",      (80,   1400), "Winter"),
    ("Jaipur",         "Heritage",  (150,  1200), "Winter"),
    ("Udaipur",        "Heritage",  (300,  1400), "Winter"),
    ("Jodhpur",        "Heritage",  (350,  1500), "Winter"),
    ("Jaisalmer",      "Heritage",  (500,  1700), "Winter"),
    ("Agra",           "Heritage",  (100,  1500), "Winter"),
    ("Varanasi",       "Religious", (200,  2000), "Winter"),
    ("Amritsar",       "Religious", (300,  2000), "Winter"),
    ("Lucknow",        "Heritage",  (200,  1800), "Winter"),
    ("Rishikesh",      "Adventure", (150,  1600), "Summer"),
    ("Haridwar",       "Religious", (140,  1600), "Spring"),
    ("Dehradun",       "Nature",    (180,  1700), "Summer"),
    ("Nainital",       "Nature",    (200,  1800), "Summer"),
    ("Shimla",         "Mountain",  (350,  1800), "Summer"),
    ("Manali",         "Mountain",  (450,  2000), "Summer"),
    ("Srinagar",       "Nature",    (600,  2500), "Summer"),
    ("Leh",            "Adventure", (900,  3000), "Summer"),
    ("Dharamshala",    "Mountain",  (500,  2200), "Summer"),
    ("Goa",            "Beach",     (400,  2500), "Winter"),
    ("Nashik",         "Religious", (150,  1600), "Monsoon"),
    ("Bhopal",         "Heritage",  (200,  1500), "Winter"),
    ("Indore",         "City",      (150,  1400), "Winter"),
    ("Gwalior",        "Heritage",  (200,  1400), "Winter"),
    ("Khajuraho",      "Heritage",  (400,  1800), "Winter"),
    ("Pachmarhi",      "Nature",    (350,  1600), "Summer"),
    ("Nagpur",         "City",      (200,  1500), "Winter"),
    ("Aurangabad",     "Heritage",  (250,  1700), "Winter"),
    ("Kochi",          "Beach",     (300,  2800), "Winter"),
    ("Munnar",         "Nature",    (500,  2800), "Summer"),
    ("Ooty",           "Nature",    (400,  2500), "Summer"),
    ("Mysuru",         "Heritage",  (350,  2500), "Winter"),
    ("Coorg",          "Nature",    (400,  2600), "Monsoon"),
    ("Visakhapatnam",  "Beach",     (300,  2200), "Winter"),
    ("Bhubaneswar",    "Religious", (250,  2000), "Winter"),
    ("Darjeeling",     "Mountain",  (600,  2500), "Summer"),
    ("Guwahati",       "City",      (500,  2800), "Winter"),
    ("Shillong",       "Nature",    (600,  2900), "Summer"),
    ("Gangtok",        "Mountain",  (700,  2800), "Summer"),
    ("Port Blair",     "Beach",     (1800, 3000), "Winter"),
    ("Puducherry",     "Beach",     (200,  2600), "Winter"),
    ("Ranthambore",    "Wildlife",  (200,  1500), "Winter"),
    ("Mount Abu",      "Nature",    (300,  1600), "Summer"),
    ("Hampi",          "Heritage",  (400,  2500), "Winter"),
    ("Madurai",        "Religious", (300,  2700), "Winter"),
    ("Tirupati",       "Religious", (200,  2500), "Winter"),
    ("Kodaikanal",     "Nature",    (450,  2600), "Summer"),
    ("Puri",           "Beach",     (300,  2200), "Winter"),
    ("Diu",            "Beach",     (400,  1800), "Winter"),
    ("Mahabaleshwar",  "Nature",    (150,  1600), "Summer"),
]

DESTINATION_NAMES = [d[0] for d in DESTINATIONS]
DEST_MAP = {d[0]: d for d in DESTINATIONS}

TRANSPORT_MODES = ["Flight", "Train", "Bus", "Car"]
ACCOMMODATION_TYPES = ["Budget", "2-Star", "3-Star", "4-Star", "5-Star"]
MEAL_PLANS = ["Room Only", "Breakfast", "Half Board", "Full Board"]
SEASONS = ["Peak", "Off-Peak", "Shoulder"]

# ── Cost lookup tables (per-person per-day INR base rates) ────────────────────
ACCOMMODATION_COST = {
    "Budget":  700,
    "2-Star":  1400,
    "3-Star":  2800,
    "4-Star":  5500,
    "5-Star":  12000,
}

MEAL_COST_PER_PERSON_PER_DAY = {
    "Room Only":  0,
    "Breakfast":  300,
    "Half Board": 700,
    "Full Board": 1400,
}

ACTIVITY_COST_PER_PERSON = 800   # average per activity per person

# Transport cost ~ distance-based, per person one-way
def transport_cost_per_person(mode, distance_km):
    if mode == "Flight":
        base = 2500 + distance_km * 3.8
    elif mode == "Train":
        base = 400  + distance_km * 1.2
    elif mode == "Bus":
        base = 200  + distance_km * 0.7
    else:  # Car
        base = 300  + distance_km * 1.8
    return base

# Season multiplier on accommodation + activities
SEASON_MULTIPLIER = {"Peak": 1.35, "Shoulder": 1.0, "Off-Peak": 0.80}

# Accommodation multiplier for meal plans is already in meal_cost

# ── Booking-advance discount on transport (early = cheaper, but noisy) ────────
def booking_discount_factor(booking_days):
    # Max 18% discount for booking 120+ days early; noisy
    discount = min(0.18, booking_days / 700)
    noise = random.uniform(-0.04, 0.04)
    return max(0.82, 1.0 - discount + noise)

# ── Season assignment based on destination hint ───────────────────────────────
def assign_season(dest_hint):
    """Convert destination's peak hint into a season label with probability."""
    # We'll randomly pick from seasons, biasing toward 'correct' peak
    roll = random.random()
    if roll < 0.45:
        return "Peak"
    elif roll < 0.75:
        return "Shoulder"
    else:
        return "Off-Peak"

# ── Generate a single row ─────────────────────────────────────────────────────
def generate_row(dest_name):
    dest = DEST_MAP[dest_name]
    _, dest_type, dist_range, season_hint = dest

    # Core features
    travelers        = random.choices([1,2,3,4,5,6,7,8],
                                      weights=[12,22,18,16,12,8,7,5])[0]
    trip_days        = random.choices(range(2,16),
                                      weights=[5,10,16,18,16,12,8,6,4,3,2,2,1,1])[0]
    distance_km      = random.randint(dist_range[0], dist_range[1])

    # Transport mode: correlated with distance
    if distance_km >= 1200:
        transport_weights = [55, 30, 5, 10]
    elif distance_km >= 600:
        transport_weights = [30, 45, 10, 15]
    elif distance_km >= 300:
        transport_weights = [15, 35, 20, 30]
    else:
        transport_weights = [8,  20, 30, 42]
    transport_mode = random.choices(TRANSPORT_MODES, weights=transport_weights)[0]

    # Accommodation: slight city/beach/mountain bias
    if dest_type in ("City", "Beach"):
        acc_weights = [10, 18, 28, 26, 18]
    elif dest_type in ("Heritage", "Religious"):
        acc_weights = [18, 22, 30, 20, 10]
    elif dest_type in ("Adventure", "Mountain", "Nature"):
        acc_weights = [20, 25, 30, 18, 7]
    else:  # Wildlife
        acc_weights = [12, 18, 28, 26, 16]
    accommodation_type = random.choices(ACCOMMODATION_TYPES, weights=acc_weights)[0]

    meal_plan        = random.choices(MEAL_PLANS, weights=[20, 35, 25, 20])[0]

    # Activities: correlated loosely with trip_days
    max_act = min(10, int(trip_days * 1.2))
    activities_count = random.randint(0, max_act)

    travel_season    = assign_season(season_hint)
    booking_advance  = random.randint(1, 180)

    # ── Compute actual_trip_expense ───────────────────────────────────────────
    season_mult   = SEASON_MULTIPLIER[travel_season]
    book_discount = booking_discount_factor(booking_advance)

    # 1. Transportation (round-trip, per person, booking-discounted)
    transport_pp   = transport_cost_per_person(transport_mode, distance_km)
    transport_cost = transport_pp * travelers * 2 * book_discount

    # 2. Accommodation (per room logic: ~1 room per 2 travelers, rounded up)
    rooms            = math.ceil(travelers / 2)
    acc_cost_per_room = ACCOMMODATION_COST[accommodation_type] * season_mult
    accommodation_cost = acc_cost_per_room * rooms * trip_days

    # 3. Meals
    meal_cost = (MEAL_COST_PER_PERSON_PER_DAY[meal_plan]
                 * travelers * trip_days * season_mult)

    # 4. Activities
    activity_cost = (ACTIVITY_COST_PER_PERSON * travelers
                     * activities_count * season_mult)

    # 5. Miscellaneous (local transport, shopping, tips, etc.) — ~8-18% of sub-total
    sub_total = transport_cost + accommodation_cost + meal_cost + activity_cost
    misc_pct  = random.uniform(0.08, 0.18)
    misc_cost = sub_total * misc_pct

    total = sub_total + misc_cost

    # 6. Destination premium: some destinations command higher costs
    dest_premium = {
        "Leh": 1.25, "Srinagar": 1.15, "Port Blair": 1.30,
        "Manali": 1.10, "Shimla": 1.05, "Gangtok": 1.10,
        "Goa": 1.12, "Darjeeling": 1.08, "Coorg": 1.05,
    }.get(dest_name, 1.0)
    total *= dest_premium

    # 7. Realistic noise ±15 %
    noise = random.uniform(0.87, 1.15)
    total *= noise

    # 8. Clamp to realistic INR range
    total = max(5000, min(300000, total))

    return [
        dest_name,
        dest_type,
        travelers,
        trip_days,
        transport_mode,
        accommodation_type,
        meal_plan,
        activities_count,
        travel_season,
        booking_advance,
        distance_km,
        round(total, 2),
    ]

# ── Main: generate 5200 rows distributed across all destinations ──────────────
def main():
    total_rows   = 5200
    n_dests      = len(DESTINATIONS)
    base_per_dest = total_rows // n_dests          # floor
    remainder     = total_rows - base_per_dest * n_dests

    rows = []
    for i, dest in enumerate(DESTINATIONS):
        count = base_per_dest + (1 if i < remainder else 0)
        for _ in range(count):
            rows.append(generate_row(dest[0]))

    # Shuffle so destinations aren't in blocks
    random.shuffle(rows)

    output_path = "indian_travel_expense_dataset.csv"
    header = [
        "destination", "destination_type", "travelers", "trip_days",
        "transport_mode", "accommodation_type", "meal_plan",
        "activities_count", "travel_season", "booking_advance_days",
        "distance_km", "actual_trip_expense",
    ]

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(rows)

    # ── Quick verification ────────────────────────────────────────────────────
    print(f"Rows written     : {len(rows)}")
    print(f"Unique dests     : {len(set(r[0] for r in rows))}")
    print(f"Columns per row  : {len(header)}")
    print(f"Missing values   : {sum(1 for r in rows for v in r if v == '' or v is None)}")
    expenses = [r[11] for r in rows]
    print(f"Expense min/max  : INR {min(expenses):,.0f} / INR {max(expenses):,.0f}")
    print(f"Expense mean     : INR {sum(expenses)/len(expenses):,.0f}")

    # Categorical value check
    allowed = {
        "transport_mode":      set(TRANSPORT_MODES),
        "accommodation_type":  set(ACCOMMODATION_TYPES),
        "meal_plan":           set(MEAL_PLANS),
        "travel_season":       set(SEASONS),
        "destination":         set(DESTINATION_NAMES),
    }
    col_idx = {h: i for i, h in enumerate(header)}
    violations = 0
    for r in rows:
        for col, allowed_vals in allowed.items():
            if r[col_idx[col]] not in allowed_vals:
                violations += 1
    print(f"Category violations: {violations}")
    print(f"Output file      : {output_path}")

if __name__ == "__main__":
    main()
