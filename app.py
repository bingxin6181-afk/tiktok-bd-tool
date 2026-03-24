import os
import csv
import uuid
from flask import Flask, render_template, request, send_file, flash, redirect, url_for
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'your-secret-key-change-this')

UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'output'
ALLOWED_EXTENSIONS = {'csv', 'xlsx', 'xls'}

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    try:
        # 检查是否是前端转换后的CSV数据
        csv_data = request.form.get('csv_data')
        filename = request.form.get('filename', 'data.csv')
        
        if csv_data:
            # 前端已经转换好了（Excel→CSV），直接保存
            unique_id = str(uuid.uuid4())[:8]
            input_filename = f"{unique_id}_{filename}"
            input_path = os.path.join(UPLOAD_FOLDER, input_filename)
            
            with open(input_path, 'w', encoding='utf-8') as f:
                f.write(csv_data)
                
            print(f"前端转换的CSV已保存: {input_filename}")
        else:
            # 传统文件上传方式（兼容旧版CSV上传）
            if 'file' not in request.files:
                flash('No file part', 'error')
                return redirect(request.url)
            
            file = request.files['file']
            if file.filename == '':
                flash('No selected file', 'error')
                return redirect(request.url)
            
            if not allowed_file(file.filename):
                flash('Invalid file type', 'error')
                return redirect(request.url)
            
            filename = secure_filename(file.filename)
            unique_id = str(uuid.uuid4())[:8]
            input_filename = f"{unique_id}_{filename}"
            input_path = os.path.join(UPLOAD_FOLDER, input_filename)
            file.save(input_path)
        
        # 用标准库csv处理（不依赖pandas）
        input_data = []
        with open(input_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames
            
            for row in reader:
                nickname = row.get('nickname', '')
                followers = row.get('followers', '0')
                
                # 生成3种话术（模板版）
                row['friendly_message'] = f"Hi {nickname}! Love your content 💖 We want to send you a FREE jewelry mystery box + 20% commission. Interested?"
                row['direct_message'] = f"Partnership offer for {nickname}: Free $50 product + 20% commission + exclusive discount code. {followers} followers qualify for premium tier. Reply YES to start."
                row['curious_message'] = f"What if you could 3x your accessory game this month? 🎁 {nickname}, we have a mystery box collab that matches your vibe perfectly..."
                row['ai_recommendation'] = 'friendly'
                
                input_data.append(row)
        
        # 添加新列名
        new_fieldnames = fieldnames + ['friendly_message', 'direct_message', 'curious_message', 'ai_recommendation']
        
        # 写入新CSV
        output_filename = f"processed_{input_filename}"
        output_path = os.path.join(OUTPUT_FOLDER, output_filename)
        
        with open(output_path, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=new_fieldnames)
            writer.writeheader()
            writer.writerows(input_data)
        
        flash(f'Success! Processed {len(input_data)} creators', 'success')
        return render_template('index.html', download_link=output_filename, message=f'Processed {len(input_data)} creators')
            
    except Exception as e:
        print(f"Error: {str(e)}")
        flash(f'Error: {str(e)}', 'error')
        return redirect(url_for('index'))

@app.route('/download/<filename>')
def download(filename):
    return send_file(os.path.join(OUTPUT_FOLDER, filename), as_attachment=True)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
