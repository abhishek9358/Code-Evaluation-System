from flask import Flask, render_template, request, redirect, url_for, session
import pandas as pd
import ast
import astunparse
from difflib import SequenceMatcher

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Replace with your actual secret key

# Load dataset from CSV
df = pd.read_csv(r'C:\desktop_item\Data_Science_Intership\projects\Code evalution System - Copy\Code evalution System - Copy\output_corrected.csv')

def clean_code(code):
    """Clean the code snippet by removing any surrounding backticks and leading/trailing whitespace."""
    return code.strip('`\n ').lstrip('```python').rstrip('```')

def normalize_code(code):
    try:
        if not code:
            return ''  # Return an empty string if the input is empty
        tree = ast.parse(code)
        normalized_code = astunparse.unparse(tree).strip()
        return normalized_code
    except SyntaxError:
        return code.strip()
    except Exception as e:
        print(f"An error occurred during AST parsing or unparse: {e}")
        return None

def calculate_similarity_score(code1, code2):
    matcher = SequenceMatcher(None, code1, code2)
    return matcher.ratio() * 100

@app.route('/', methods=['GET', 'POST'])
def index():
    if 'attempts' not in session or not isinstance(session['attempts'], list):
        session['attempts'] = []
    if 'total_score' not in session:
        session['total_score'] = 0
    
    question_index = int(request.args.get('question_index', 0))
    instruction = df.iloc[question_index]['instruction']
    
    if request.method == 'POST':
        user_code = request.form['user_code']
        expected_output = df.iloc[question_index]['output']

        user_code = clean_code(user_code)
        expected_output = clean_code(expected_output)

        user_code_normalized = normalize_code(user_code)
        expected_output_normalized = normalize_code(expected_output)

        if user_code_normalized is not None and expected_output_normalized is not None:
            score = calculate_similarity_score(user_code_normalized, expected_output_normalized)
            if question_index not in session['attempts']:
                attempts = session['attempts']
                attempts.append(question_index)
                session['attempts'] = attempts
            session['total_score'] = round((session['total_score'] + score) / len(session['attempts']), 2)
            session.modified = True
        else:
            score = 0
        return render_template('index.html', question_index=question_index, instruction=instruction, show_result=True, score=score, expected_output=expected_output, num_questions=len(df), attempts=session['attempts'], total_score=session['total_score'])
    
    return render_template('index.html', question_index=question_index, instruction=instruction, show_result=False, num_questions=len(df), attempts=session['attempts'], total_score=session['total_score'])



@app.route('/next_question', methods=['POST'])
def next_question():
    question_index = int(request.form['question_index'])
    question_index = (question_index + 1) % len(df)
    return redirect(url_for('index', question_index=question_index))

@app.route('/question/<int:question_index>')
def question(question_index):
    return redirect(url_for('index', question_index=question_index))

if __name__ == '__main__':
    app.run(debug=True)
