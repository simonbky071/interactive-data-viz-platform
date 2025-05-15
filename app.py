from flask import Flask, render_template, request, flash, redirect, url_for
import pandas as pd
import plotly.express as px
import plotly
import json
import os

app = Flask(__name__, template_folder='templates')
app.secret_key = 'supersecretkey'
UPLOAD_FOLDER = 'Uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

@app.route('/')
def index():
    print("Template folder:", app.template_folder)  # Debug
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        flash('No file part')
        return redirect(url_for('index'))
    file = request.files['file']
    if file.filename == '':
        flash('No selected file')
        return redirect(url_for('index'))
    if file and (file.filename.endswith('.csv') or file.filename.endswith('.json')):
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        if os.access(app.config['UPLOAD_FOLDER'], os.W_OK):
            print(f"Saving file to {file_path}")  # Debug
            print(f"Write access for {app.config['UPLOAD_FOLDER']}: {os.access(app.config['UPLOAD_FOLDER'], os.W_OK)}")  # Debug
            file.save(file_path)
            try:
                if file.filename.endswith('.csv'):
                    df = pd.read_csv(file_path)
                else:
                    df = pd.read_json(file_path)
                stats = {
                    'rows': len(df),
                    'columns': list(df.columns),
                    'missing': df.isnull().sum().to_dict()
                }
                return render_template('result.html', filename=file.filename, stats=stats)
            except Exception as e:
                flash(f'Error processing file: {str(e)}')
                return redirect(url_for('index'))
        else:
            flash('Cannot save file due to permissions')
            return redirect(url_for('index'))
    else:
        flash('Invalid file format. Please upload a CSV or JSON file.')
        return redirect(url_for('index'))

@app.route('/clean_data', methods=['POST'])
def clean_data():
    filename = request.form.get('filename')
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    try:
        if filename.endswith('.csv'):
            df = pd.read_csv(file_path)
        else:
            df = pd.read_json(file_path)
        df = df.dropna()
        df.to_csv(file_path, index=False) if filename.endswith('.csv') else df.to_json(file_path, orient='records')
        stats = {
            'rows': len(df),
            'columns': list(df.columns),
            'missing': df.isnull().sum().to_dict()
        }
        flash('Missing values removed successfully')
        return render_template('result.html', filename=filename, stats=stats)
    except Exception as e:
        flash(f'Error cleaning data: {str(e)}')
        return redirect(url_for('index'))

@app.route('/visualize', methods=['POST'])
def visualize():
    filename = request.form.get('filename')
    x_axis = request.form.get('x_axis')
    y_axis = request.form.get('y_axis')
    plot_type = request.form.get('plot_type')
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    try:
        if filename.endswith('.csv'):
            df = pd.read_csv(file_path)
        else:
            df = pd.read_json(file_path)
        if plot_type == 'scatter':
            fig = px.scatter(df, x=x_axis, y=y_axis)
        elif plot_type == 'bar':
            fig = px.bar(df, x=x_axis, y=y_axis)
        else:
            fig = px.line(df, x=x_axis, y=y_axis)
        plot_html = plotly.io.to_html(fig, full_html=False)
        stats = {
            'rows': len(df),
            'columns': list(df.columns),
            'missing': df.isnull().sum().to_dict()
        }
        return render_template('result.html', filename=filename, stats=stats, plot_html=plot_html)
    except Exception as e:
        flash(f'Error generating visualization: {str(e)}')
        return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=False)