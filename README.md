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
python round1/anonymize.py PATH/TO/RAW/CSV/FILE
```

> [!NOTE]
> The anonymized CSV file of the round 1 results is available for download here: https://github.com/axondeepseg/g-ratio-delphi/releases/download/r20260529/round1_anonymized.csv

Navigate to the `docs` directory (this is where github pages deploys from). Run 
the report generation script with:

```
python ../round1/visualize_delphi_round1.py PATH/TO/ANONYMIZED/CSV master_questions_r1.html
```

This will create an _index.html_ file, which gh pages will search for. 