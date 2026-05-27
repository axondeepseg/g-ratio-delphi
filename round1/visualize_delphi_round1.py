'''
This script visualizes the results of the first round of the Delphi project. It 
reads the data from a CSV export of the Google Form answers, processes it, and 
plots Likert scale agreement to help understand the distribution of responses 
and the consensus among experts.
'''

import pandas as pd
import plotly.express as px
import plotly.offline as pyo

import argparse
from pathlib import Path
from bs4 import BeautifulSoup

# --- 1. SETTINGS & MAPPING ---
# Ensure these match your Google Form exactly
LIKERT_ORDER = ['Strongly disagree', 'Disagree', 'Neutral', 'Agree', 'Strongly agree']
LIKERT_COLORS = {
    'Strongly disagree': "#ff0004", 
    'Disagree': "#ff9429", 
    'Neutral': '#ffffbf', 
    'Agree': "#74ff86", 
    'Strongly agree': "#1dac00"
}

STYLESHEET_PATH = Path(__file__).parent / "round1_style.css"
with open(str(STYLESHEET_PATH), "r") as f:
    STYLESHEET = f.read()

def render_comments(df, col, username_col, anonymize=True, likert_col=None):
    """
    Render comments as HTML divs with styling.
    
    Args:
        df: DataFrame
        col: Column name containing comments
        username_col: Column name with usernames
        anonymize: Whether to anonymize usernames
        likert_col: Optional column name for Likert responses to determine color
    
    Returns:
        HTML string with rendered comments
    """
    comments_html = ""
    comment_indices = df[col].dropna().index.tolist()
    
    for comment_idx in comment_indices:
        # Determine color
        if likert_col:
            response = df[likert_col].iloc[comment_idx]
            color = LIKERT_COLORS.get(response, '#cccccc')
            border_style = f'border: 4px solid {color};'
        else:
            border_style = 'border: 4px solid #95a5a6;'
        
        # Get username for tooltip if not anonymized
        username = df[username_col].iloc[comment_idx] if not anonymize else "Anonymous"
        title_attr = f'title="{username}"' if not anonymize else ""
        
        comment = df[col].iloc[comment_idx]
        comments_html += f'<div class="comment-item" style="{border_style} padding: 10px; border-radius: 5px; margin-bottom: 10px;" {title_attr}>{comment}</div>'
    
    return comments_html

def generate_report(csv_path, questions_html_path, output_filename="survey_report.html", anonymize=False):
    df = pd.read_csv(csv_path)
    with open(questions_html_path, "r", encoding="utf-8") as f:
        questions_html = f.read()
    question_soup = BeautifulSoup(questions_html, "html.parser")
    # some questions had "Strongly Disagree" with a capital D
    for col in df.columns:
        df[col] = df[col].str.replace("Strongly Disagree", "Strongly disagree", regex=False)
    
    html_content = f"""
    <html>
    <head>
        <title>Survey Results Report</title>
        <style>{STYLESHEET}</style>
    </head>
    <body>
        <div class="container">
            <h1>Delphi Survey Round 1 Report</h1>
            <p> <i>Note: "Top 2 Score" represents the percentage of respondents who selected either "Agree" or "Strongly agree". </i></p>
    """

    timestamp_col = df.columns[0]
    username_col = df.columns[1]
    primary_expertise_col = df.columns[2]
    secondary_expertise_col = df.columns[3]

    missing_stuff_col = df.columns[-2]
    concerns_col = df.columns[-1]

    question_nb = 0
    comments_found = True

    # first, we plot the distribution of primary and secondary expertise
    expertise_df = df[
         [username_col, primary_expertise_col, secondary_expertise_col]
    ].melt(
         id_vars=username_col, 
         value_vars=[primary_expertise_col, secondary_expertise_col], 
         var_name='Expertise Type', 
         value_name='Expertise'
    ).dropna(subset=['Expertise'])
    expertise_df['Expertise Type'] = expertise_df['Expertise Type'].map({
         primary_expertise_col: 'Primary Expertise', 
         secondary_expertise_col: 'Secondary Expertise'
    })
    fig = px.bar(expertise_df, x='Expertise', color='Expertise Type', title="Distribution of Primary and Secondary Expertises",
                 color_discrete_map={'Primary Expertise': '#2980b9', 'Secondary Expertise': '#8e44ad'})
    fig.update_layout(xaxis_title="Expertise Area", yaxis_title="Number of Respondents", legend_title="")
    expertise_chart_html = pyo.plot(fig, include_plotlyjs='cdn', output_type='div')

    html_content += f"""
    <div class="question-block">
        <h2>Expertise Distribution</h2>
        {expertise_chart_html}
    </div>
    """

    # Identify Likert vs Text columns
    for col in df.columns[4:-2]:        
        # Check if the column is Likert based on unique values
        unique_vals = [v for v in df[col].dropna().unique()]
        is_likert = any(val in LIKERT_ORDER for val in unique_vals)

        if is_likert:
            # at this point we found a new question, but we may need to close the previous block
            if not comments_found:
                html_content += "</div>"
            question_nb += 1
            comments_found = False

            question_id = f"q{question_nb}"
            question_html = str(question_soup.find(id=question_id))

            # --- PROCESS LIKERT DATA ---
            counts = df[col].value_counts().reindex(LIKERT_ORDER, fill_value=0)
            total = counts.sum()
            
            # Calculate Top 2 (Agree + Strongly Agree)
            top2_count = counts.get('Agree', 0) + counts.get('Strongly agree', 0)
            top2_pct = (top2_count / total) * 100 if total > 0 else 0
            top2_badge_color = "#27ae60" if top2_pct > 80 else "#95a5a6"
            
            # Create Plotly Chart
            fig_df = counts.reset_index()
            fig_df.columns = ['Response', 'Count']
            fig = px.bar(fig_df, x='Count', y=[col]*len(fig_df), color='Response', 
                         orientation='h',
                         color_discrete_map=LIKERT_COLORS,
                         category_orders={"Response": LIKERT_ORDER})
            fig.update_traces(hovertemplate='<b>%{fullData.name}</b><br>Count: %{x}<extra></extra>')
            
            fig.update_layout(
                showlegend=True, height=250, margin=dict(l=20, r=20, t=20, b=20),
                xaxis_title="Number of Respondents", yaxis_title="",
                legend_title="", yaxis=dict(showticklabels=False)
            )
            
            chart_html = pyo.plot(fig, include_plotlyjs='cdn', output_type='div')

            # Append to HTML
            html_content += f"""
            <div class="question-block">
                {question_html}
                <br>
                <div class="top2-badge" style="background-color: {top2_badge_color};">Top 2 Score (Agreement): {top2_pct:.1f}%</div>
                {chart_html}
            """
            
        else:
            # --- PROCESS TEXT DATA ---
            comments_found = True
            comments = df[col].dropna().tolist()
            prev_col = df.columns[df.columns.get_loc(col) - 1]
            html_content += f"""
            <details>
                <summary>Additional comments ({len(comments)})</summary>
                <div class="comments-box">
                    {render_comments(df, col, username_col, anonymize, likert_col=prev_col)}
                </div>
            </details>
            """
            html_content += "</div>" # Close question-block

    # Close last question-block if necessary
    if not comments_found:
        html_content += "</div>"

    # finally, add last two short-answer questions (missing_stuff_col and concerns_col)
    html_content += f"""
    <div class="question-block">
    <h2>Q{question_nb+1}: {missing_stuff_col}</h2>
    <i>Number of responses: {df[missing_stuff_col].dropna().shape[0]}</i><br><br>
        <div class="comments-box">
            {render_comments(df, missing_stuff_col, username_col, anonymize)}
        </div>
    </div> <!-- Close question-block -->
    <div class="question-block">
    <h2>Q{question_nb+2}: {concerns_col}</h2>
    <i>Number of responses: {df[concerns_col].dropna().shape[0]}</i><br><br>
        <div class="comments-box">
            {render_comments(df, concerns_col, username_col, anonymize)}
        </div>
    """

    html_content += "</div></body></html>" # Close container and body 
    
    with open(output_filename, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"Report generated: {output_filename}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate a HTML survey report from a CSV file.")
    parser.add_argument("csv_path", help="Path to the CSV file containing survey results.")
    parser.add_argument("questions_html", help="Path to the master_questions.html file with the question text and formatting.")
    parser.add_argument("--output", default="survey_report.html", help="Output HTML file name (default: survey_report.html)")
    parser.add_argument("--hide-names", default=False, action="store_true", help="Show respondent names on hover")

    
    args = parser.parse_args()
    anonymize = not args.hide_names
    generate_report(args.csv_path, args.questions_html, args.output, anonymize)
    print("Note that you may want to rename some column headers in the CSV for better readability in the report.")