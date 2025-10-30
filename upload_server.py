from flask import Flask, request, jsonify
from flask_cors import CORS
import boto3
from botocore.client import Config
import uuid
import os
from datetime import datetime, timedelta

app = Flask(__name__)
CORS(app)

# S3 клиент
s3 = boto3.client(
    's3',
    endpoint_url='https://s3.ru-1.storage.selcloud.ru',
    aws_access_key_id='9a671cbbc3b04cbcaa693de1ad0c7f7d',
    aws_secret_access_key='5ad4ea67fbfb4d5d826d7d827b752576',
    config=Config(signature_version='s3v4'),
    verify=False
)

BUCKET_NAME = 'meow-test'

@app.route('/')
def home():
    return jsonify({'status': 'ok', 'message': 'Vkalgane Upload Server'})

@app.route('/upload', methods=['POST'])
def upload_file():
    try:
        file = request.files['file']
        file_extension = file.filename.split('.')[-1] if '.' in file.filename else 'jpg'
        s3_filename = f"posts/{uuid.uuid4().hex}.{file_extension}"
        
        # Загружаем файл в S3
        s3.upload_fileobj(
            file,
            BUCKET_NAME,
            s3_filename,
            ExtraArgs={'ContentType': file.content_type}
        )
        
        # Генерируем подписанный URL для доступа к файлу (действителен 1 час)
        file_url = s3.generate_presigned_url(
            'get_object',
            Params={
                'Bucket': BUCKET_NAME,
                'Key': s3_filename
            },
            ExpiresIn=3600
        )
        
        return jsonify({
            'success': True,
            'url': file_url,
            'filename': file.filename,
            's3_key': s3_filename
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/get-signed-url/<path:s3_key>')
def get_signed_url(s3_key):
    """Генерирует новый подписанный URL для файла"""
    try:
        file_url = s3.generate_presigned_url(
            'get_object',
            Params={
                'Bucket': BUCKET_NAME,
                'Key': s3_key
            },
            ExpiresIn=3600
        )
        return jsonify({'success': True, 'url': file_url})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)