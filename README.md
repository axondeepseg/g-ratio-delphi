[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.23772601.svg)](https://doi.org/10.5281/zenodo.23772601)

# Overview
This utility parses a CSV export of a Google Form Delphi survey and outputs a
HTML report for convenient visualization of respondents' answers.

# Dependencies
The dependencies required for this tool are:
```
pandas
beautifulsoup4
```

# How to build
First, export the Google Form results as a CSV. Then, anonymize the file with:

```
python code/anonymize.py PATH/TO/RAW/CSV/FILE
```

<details><summary>Provide an existing mapping</summary>
To reuse an existing anonymization mapping, pass it with `--mapping-file`:

```
python code/anonymize.py PATH/TO/RAW/CSV/FILE --mapping-file PATH/TO/anonymization_mapping.json
```

</details>


> [!NOTE]
> The anonymized CSV file of the round 1 results is available for download here: https://github.com/axondeepseg/g-ratio-delphi/releases/download/r20260529/round1_anonymized.csv

Navigate to the `docs` directory (this is where github pages deploys from). Run 
the report generation script with:

```
python ../code/visualize_delphi_round1.py PATH/TO/ANONYMIZED/CSV master_questions_r1.html
python ../code/visualize_delphi_round2.py PATH/TO/ANONYMIZED/CSV master_questions_r2.html
```

The _index.html_ file will then link to a menu to select either round 1 or 2. 
