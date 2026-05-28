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
    'Strongly disagree': "#dc3246", 
    'Disagree': "#ff9328", 
    'Neutral': "#ffff94", 
    'Agree': "#bcff79", 
    'Strongly agree': "#28aa00"
}

STYLESHEET_PATH = Path(__file__).parent / "round1_style.css"
with open(str(STYLESHEET_PATH), "r") as f:
    STYLESHEET = f.read()

def get_contrast_color(hex_color):
    """
    Determine if text should be white or dark based on background color brightness.
    
    Args:
        hex_color: Hex color string (e.g., "#ffffbf")
    
    Returns:
        "white" or "#333333" (dark gray)
    """
    # Remove '#' and convert to RGB
    hex_color = hex_color.lstrip('#')
    r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    # Calculate perceived brightness using the luminance formula
    luminance = (r * 0.299 + g * 0.587 + b * 0.114) / 255
    
    # Use dark text for light backgrounds, white for dark backgrounds
    return "#333333" if luminance > 0.5 else "white"

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

def create_likert_chart_html(counts, likert_order, likert_colors):
    """
    Create a pure HTML/CSS stacked horizontal bar chart for Likert data.
    
    Args:
        counts: pd.Series with response counts indexed by response type
        likert_order: List of response types in order
        likert_colors: Dict mapping response type to color hex code
    
    Returns:
        HTML string with the chart
    """
    total = counts.sum()
    
    chart_html = '<div class="likert-chart">'
    chart_html += '<div class="likert-stacked-bar">'
    
    for response in likert_order:
        count = counts.get(response, 0)
        if count == 0:  # Skip responses with no answers
            continue
            
        percentage = (count / total * 100) if total > 0 else 0
        color = likert_colors.get(response, '#cccccc')
        text_color = get_contrast_color(color)
        chart_html += f'''
        <div class="likert-segment" style="width: {percentage}%; background-color: {color}; color: {text_color};" title="{response}: {int(count)} respondents">
            <span class="likert-segment-count">{int(count)}</span>
        </div>
        '''
    
    chart_html += '</div>'
    chart_html += '</div>'
    return chart_html

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
            <p> <i>Note: For every question, the "Agreement" badge represents the fraction of respondents who agreed, without considering neutral responses. </i></p>
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
            
            # Calculate agreement ()
            top2_count = counts.get('Agree', 0) + counts.get('Strongly agree', 0)
            bottom2_count = counts.get('Disagree', 0) + counts.get('Strongly disagree', 0)
            agreement_pct = (top2_count / (top2_count + bottom2_count) * 100) if (top2_count + bottom2_count) > 0 else 0
            if agreement_pct >= 75:
                agreement_badge_color = "#27ae60"  # Green for agreement consensus
            elif agreement_pct <= 15:
                agreement_badge_color = "#dc3246"  # Red for disagreement consensus
            else:
                agreement_badge_color = "#95a5a6"  # Gray for no clear consensus
            agreement_tooltip = f"title='{top2_count} agree, {bottom2_count} disagree'"
            
            chart_html = create_likert_chart_html(counts, LIKERT_ORDER, LIKERT_COLORS)

            # Append to HTML
            html_content += f"""
            <div class="question-block">
                {question_html}
                <br>
                <div class="top2-badge" style="background-color: {agreement_badge_color};" {agreement_tooltip}>Agreement: {agreement_pct:.1f}%</div>
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
    parser.add_argument("--hide-names", action="store_true", help="Show respondent names on hover")

    
    args = parser.parse_args()
    generate_report(args.csv_path, args.questions_html, args.output, args.hide_names)