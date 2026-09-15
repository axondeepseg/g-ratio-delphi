from pathlib import Path
import pandas as pd
import argparse
import json

def anonymize_expert_names(experts_df, name_mapping=None):
    if name_mapping is None:
        name_mapping = {
            name: f'expert_{i+1}'
            for i, name in enumerate(experts_df['Username'])
        }
    
    # Replace the 'Username' column with anonymized names
    experts_df['Username'] = experts_df['Username'].map(name_mapping)
    
    return experts_df,  name_mapping

def main(csv_file, mapping_file=None):
    df = pd.read_csv(csv_file)
    if mapping_file is not None:
        with open(mapping_file) as f:
            name_mapping = json.load(f)
    else:
        name_mapping = None

    anonymized_df, name_mapping = anonymize_expert_names(df, name_mapping)
    new_csv_path = csv_file.replace('.csv', '_anonymized.csv')
    anonymized_df.to_csv(new_csv_path, index=False)
    if mapping_file is None:
        mapping_path = Path(csv_file).with_name('anonymization_mapping.json')
        with open(mapping_path, 'w') as f:
            json.dump(name_mapping, f, indent=4)

    print(name_mapping, '\n', anonymized_df["Username"])

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Anonymize expert names in a CSV file.")
    parser.add_argument("csv_file", help="Path to the raw Google Form CSV export.")
    parser.add_argument(
        "-m", "--mapping-file",
        help="Path to an existing JSON mapping of usernames to anonymized names.",
    )
    
    args = parser.parse_args()
    
    main(args.csv_file, args.mapping_file)