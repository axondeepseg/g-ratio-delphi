from pathlib import Path
import pandas as pd
import argparse
import json

def anonymize_expert_names(experts_df):
    # Create a mapping of original names to anonymized names
    name_mapping = {name: f'expert_{i+1}' for i, name in enumerate(experts_df['Username'])}
    
    # Replace the 'Username' column with anonymized names
    experts_df['Username'] = experts_df['Username'].map(name_mapping)
    
    return experts_df,  name_mapping

def main(csv_file):
    df = pd.read_csv(csv_file)
    emails = df["Username"]
    anonymized_df, name_mapping = anonymize_expert_names(df)
    new_csv_path = csv_file.replace('.csv', '_anonymized.csv')
    anonymized_df.to_csv(new_csv_path, index=False)
    mapping_path = Path(csv_file).with_name('anonymization_mapping.json')
    with open(mapping_path, 'w') as f:
        json.dump(name_mapping, f, indent=4)

    print(name_mapping, '\n', anonymized_df["Username"])

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Anonymize expert names in a CSV file.")
    parser.add_argument("csv_file", help="Path to the raw Google Form CSV export.")
    
    args = parser.parse_args()
    
    main(args.csv_file)