from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import boto3
from botocore.client import Config
import uuid
import os

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
        
        s3.upload_fileobj(
            file,
            BUCKET_NAME,
            s3_filename,
            ExtraArgs={'ContentType': file.content_type}
        )
        
        file_url = f"https://meow-test.s3.ru-1.storage.selcloud.ru/{s3_filename}"
        
        return jsonify({
            'success': True,
            'url': file_url,
            'filename': file.filename,
            's3_key': s3_filename
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/image/<path:s3_key>')
def get_image(s3_key):
    """Прокси для получения изображений из S3"""
    try:
        print(f"Получаем изображение: {s3_key}")
        
        # Получаем файл из S3
        response = s3.get_object(Bucket=BUCKET_NAME, Key=s3_key)
        image_data = response['Body'].read()
        content_type = response['ContentType']
        
        # Возвращаем изображение через прокси
        return Response(
            image_data,
            content_type=content_type,
            headers={
                'Cache-Control': 'public, max-age=3600',
                'Access-Control-Allow-Origin': '*'
            }
        )
        
    except Exception as e:
        print(f"Ошибка получения изображения {s3_key}: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 404

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)