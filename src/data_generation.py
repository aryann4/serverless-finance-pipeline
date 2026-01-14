import pandas as pd
import random
import uuid
from datetime import datetime, timedelta
import os

# --- CONFIGURATION ---
NUM_ROWS = 200  # More rows for better analytics
START_DATE = datetime(2025, 10, 1)  # Start from a few months ago

# 1. Realistic Merchants with fixed or range-based pricing
MERCHANTS = {
    "Food & Drink": [
        ("Starbucks", 4.50, 8.50), ("Dunkin", 3.00, 12.00),
        ("Chipotle", 11.00, 18.00), ("UberEats", 25.00, 60.00),
        ("Local Bar", 15.00, 80.00), ("Vending Machine", 1.50, 3.50)
    ],
    "Grocery": [
        ("Trader Joes", 30.00, 120.00), ("Whole Foods", 50.00, 200.00),
        ("Wegmans", 40.00, 150.00), ("7-Eleven", 5.00, 25.00)
    ],
    "Utilities": [
        ("Spotify", 11.99, 11.99), ("Netflix", 15.49, 15.49),
        ("ConEd Electric", 80.00, 140.00), ("Verizon Fios", 79.99, 79.99),
        ("AWS Cloud Bill", 0.50, 15.00)  # Realistic for a student project!
    ],
    "Transportation": [
        ("Uber Trip", 12.00, 45.00), ("MTA Subway", 2.90, 2.90),
        ("Shell Station", 30.00, 60.00)
    ],
    "Rent": [
        ("Luxury Apartments LLC", 1450.00, 1450.00)  # Fixed rent
    ],
    "Income": [
        ("Tech Internship Pay", 2500.00, 2500.00),
        ("Zelle from Mom", 50.00, 200.00)
    ]
}

# 2. Locations to make map analytics possible later
LOCATIONS = [
    ("New Brunswick", "NJ"), ("Piscataway", "NJ"),
    ("New York", "NY"), ("Princeton", "NJ"), ("Philadelphia", "PA")
]


def generate_transactions(num_rows):
    data = []

    # We want mostly small purchases, fewer big ones
    categories = ["Food & Drink", "Grocery", "Utilities", "Transportation", "Rent", "Income"]
    weights = [0.40, 0.15, 0.15, 0.15, 0.05, 0.10]

    current_date = START_DATE

    for _ in range(num_rows):
        # 1. Pick a Category based on weights
        cat = random.choices(categories, weights=weights, k=1)[0]

        # 2. Pick a Merchant
        merchant_options = MERCHANTS[cat]
        merchant_name, min_price, max_price = random.choice(merchant_options)

        # 3. Calculate Exact Amount
        if min_price == max_price:
            amount = min_price  # Fixed price (like Netflix)
        else:
            amount = round(random.uniform(min_price, max_price), 2)

        # 4. Determine Transaction Type (Debit vs Credit)
        if cat == "Income":
            txn_type = "Credit"
            description = f"DEPOSIT: {merchant_name}"
        else:
            txn_type = "Debit"
            description = f"POS PURCHASE: {merchant_name}"

        # 5. Generate Time & Location
        # Move forward 0-2 days per transaction to simulate time passing
        current_date += timedelta(hours=random.randint(4, 48))
        city, state = random.choice(LOCATIONS)

        data.append({
            "Transaction ID": str(uuid.uuid4()),  # Completely unique ID
            "Date": current_date.strftime("%Y-%m-%d"),
            "Description": description,
            "Category": cat,
            "Amount": amount,
            "Type": txn_type,
            "City": city,
            "State": state
        })

    # Create DataFrame
    df = pd.DataFrame(data)

    # 6. Calculate "Running Balance"
    # Start with $3,000 in the bank
    starting_balance = 3000.00

    # Apply logic: Credits add money, Debits subtract money
    df['Signed_Amount'] = df.apply(lambda x: x['Amount'] if x['Type'] == 'Credit' else -x['Amount'], axis=1)
    df['Running Balance'] = starting_balance + df['Signed_Amount'].cumsum()

    # Drop the helper column
    df = df.drop(columns=['Signed_Amount'])
    df['Running Balance'] = df['Running Balance'].round(2)

    return df


if __name__ == "__main__":
    df = generate_transactions(NUM_ROWS)

    output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "transactions.csv")

    df.to_csv(output_path, index=False)

    print(f"Generated {len(df)} realistic transactions.")
    print(f"   - Includes columns: {list(df.columns)}")
    print(f"   - Saved to: {output_path}")
    print("\nSample Data:")
    print(df[['Date', 'Description', 'Amount', 'Running Balance']].head())