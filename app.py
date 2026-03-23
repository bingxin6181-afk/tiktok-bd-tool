import os
import uuid
from flask import Flask, render_template, request, send_file, flash, redirect, url_for
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this'

UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'output'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() == 'csv'

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        flash('No file part', 'error')
        return redirect(request.url)
    
    file = request.files['file']
    if file.filename == '':
        flash('No selected file', 'error')
        return redirect(request.url)
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        unique_id = str(uuid.uuid4())[:8]
        input_filename = f"{unique_id}_{filename}"
        input_path = os.path.join(UPLOAD_FOLDER, input_filename)
        
        file.save(input_path)
        
        try:
            # 简单处理：读取CSV并添加示例话术
            import pandas as pd
            df = pd.read_csv(input_path)
            
            # 为每个达人生成3种话术（简化版）
            df['friendly_message'] = 'Hi ' + df['nickname'] + '! Love your content 💖 We want to send you a FREE jewelry mystery box + 20% commission. Interested?'
            df['direct_message'] = 'Partnership offer for ' + df['nickname'] + ': Free $50 product + 20% commission + exclusive discount code. 12k followers qualify for premium tier. Reply YES to start.'
            df['curious_message'] = 'What if you could 3x your accessory game this month? 🎁 ' + df['nickname'] + ', we have a mystery box collab that matches your vibe perfectly...'
            df['ai_recommendation'] = 'friendly'
            
            output_filename = f"processed_{input_filename}"
            output_path = os.path.join(OUTPUT_FOLDER, output_filename)
            df.to_csv(output_path, index=False, encoding='utf-8-sig')
            
            flash(f'Success! Processed {len(df)} creators', 'success')
            return render_template('index.html', download_link=output_filename, message=f'Processed {len(df)} creators')
            
        except Exception as e:
            flash(f'Error: {str(e)}', 'error')
            return redirect(url_for('index'))
    
    flash('Invalid file type', 'error')
    return redirect(url_for('index'))

@app.route('/download/<filename>')
def download(filename):
    return send_file(os.path.join(OUTPUT_FOLDER, filename), as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)