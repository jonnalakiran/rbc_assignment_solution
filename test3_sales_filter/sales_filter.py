import pandas as pd
from pathlib import Path

INPUT_FILE = Path(__file__).resolve().parent / "assignment data (1).csv"
OUTPUT_FILE = Path(__file__).resolve().parent / "filtered_properties_below_avg_price_per_sqft.csv"


def main():
    df = pd.read_csv(INPUT_FILE)

    valid_df = df[df["sq__ft"] > 0].copy()
    valid_df["price_per_sqft"] = valid_df["price"] / valid_df["sq__ft"]

    avg_price_per_sqft = valid_df["price_per_sqft"].mean()

    filtered_df = valid_df[valid_df["price_per_sqft"] < avg_price_per_sqft].copy()
    filtered_df.to_csv(OUTPUT_FILE, index=False)

    print(f"Input rows               : {len(df)}")
    print(f"Valid rows (sq__ft > 0)  : {len(valid_df)}")
    print(f"Average price per sqft   : {avg_price_per_sqft:.4f}")
    print(f"Output rows              : {len(filtered_df)}")
    print(f"Written file             : {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
