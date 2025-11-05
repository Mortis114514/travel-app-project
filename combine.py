import pandas as pd

try:
    # Read both CSV files
    df1 = pd.read_csv('data/Kyoto_Restaurant_Info_Full.csv', encoding='utf-8-sig')
    df2 = pd.read_csv('data/Kyoto_Restaurant_Info_Rated.csv', encoding='utf-8-sig')

    # Print info about the dataframes before merging
    print("Before merging:")
    print(f"File 1 shape: {df1.shape}")
    print(f"File 2 shape: {df2.shape}")
    
    # Merge the dataframes on Restaurant_ID
    merged_df = pd.merge(
        df1, 
        df2,
        on='Restaurant_ID',
        how='outer',
        suffixes=('_1', '_2')
    )

    # Print info after merging
    print(f"\nAfter merging:")
    print(f"Merged shape: {merged_df.shape}")

    # For columns that appear in both dataframes, keep the non-null values
    for col in merged_df.columns:
        if col.endswith('_1'):
            base_col = col[:-2]
            if f"{base_col}_2" in merged_df.columns:
                merged_df[base_col] = merged_df[f"{base_col}_2"].fillna(merged_df[col])
                # Drop the duplicate columns
                merged_df = merged_df.drop(columns=[col, f"{base_col}_2"])

    # Define the final column order
    final_fields = [
        'Restaurant_ID', 'Name', 'JapaneseName', 'Station', 'FirstCategory', 'SecondCategory',
        'TotalRating', 'Lat', 'Long', 'DinnerPrice', 'LunchPrice', 'Price_Category',
        'DinnerRating', 'LunchRating', 'ReviewNum', 'Rating_Category'
    ]

    # Reorder columns and save to CSV
    merged_df = merged_df[final_fields]
    merged_df.to_csv('data/Combined_Restaurants.csv', index=False, encoding='utf-8-sig')

    print(f"\nSuccessfully merged and saved! Total rows: {len(merged_df)}")
    print("Missing values in final dataset:")
    print(merged_df.isnull().sum())

except FileNotFoundError as e:
    print(f"Error: Could not find file - {e}")
except Exception as e:
    print(f"Error: {e}")