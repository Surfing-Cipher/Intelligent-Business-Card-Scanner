from flask import Flask, request, jsonify
from flask import render_template
import config.settings as settings
import utils.utils as utils
import numpy as np
import cv2
import services.predictions as pred
import os
from flask import session
import json
from datetime import timedelta
import requests
import services.azureform as azureform
import services.qwenform as qwenform
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'document_scanner_app'
# Set session to be permanent with longer timeout
app.permanent_session_lifetime = timedelta(hours=1)

docscan = utils.DocumentScan()

# Initialize models
qwen_model_loaded = False
azure_model_loaded = False

@app.route('/load_qwen_model', methods=['POST'])
def load_qwen_model():
    global qwen_model_loaded
    try:
        if not qwen_model_loaded:
            print("Loading Qwen model...")
            qwen_result = qwenform.load_qwen_model()
            if qwen_result["status"] == "success":
                qwen_model_loaded = True
                print("Qwen model loaded successfully")
                return jsonify({"status": "success", "message": "Qwen model loaded successfully"})
            else:
                return jsonify({"status": "error", "message": qwen_result["message"]}), 500
        else:
            return jsonify({"status": "success", "message": "Qwen model already loaded"})
    except Exception as e:
        print(f"Error loading Qwen model: {str(e)}")
        return jsonify({"status": "error", "message": f"Failed to load Qwen model: {str(e)}"}), 500

@app.route('/',methods=['GET','POST'])
def scandoc():
    if request.method == 'POST':
        file = request.files['image_name']
        ocr_model = request.form.get('ocr_model', 'pytesseract')
        
        # Make session permanent and set OCR model
        session.permanent = True
        session['ocr_model'] = ocr_model
        
        upload_image_path = utils.save_upload_image(file)
        print('Image saved in = ',upload_image_path)
        # predict the coordination of the document
        four_points, size = docscan.document_scanner(upload_image_path)
        print(four_points,size)
        if four_points is None:
            message ='UNABLE TO LOCATE THE COORDINATES OF DOCUMENT: points displayed are random'
            points = [
                {'x':10 , 'y': 10},
                {'x':120 , 'y': 10},
                {'x':120 , 'y': 120},
                {'x':10 , 'y': 120}
            ]
            return render_template('scanner.html',
                                   points=points,
                                   fileupload=True,
                                   ocr_model=ocr_model,
                                   message=message)
        else:
            points = utils.array_to_json_format(four_points)
            message ='Located the Cooridinates of Document using OpenCV'
            return render_template('scanner.html',
                                   points=points,
                                   fileupload=True,
                                   ocr_model=ocr_model,
                                   message=message)
    
    # For GET requests, get the OCR model from session if available, default to pytesseract
    ocr_model = session.get('ocr_model', 'pytesseract')
    return render_template('scanner.html', ocr_model=ocr_model)

@app.route('/transform',methods=['POST'])
def transform():
    try:
        # Keep the model selection from the session
        if 'ocr_model' not in session:
            session['ocr_model'] = 'pytesseract'
            
        points = request.json['data']
        array = np.array(points)
        magic_color = docscan.calibrate_to_original_size(array)
        filename = 'magic_color.jpg'
        magic_image_path = settings.join_path(settings.MEDIA_DIR,filename)
        cv2.imwrite(magic_image_path,magic_color)
        
        return 'success'
    except:
        return 'fail'

@app.route('/prediction')
def prediction():
    # Get the selected OCR model from session
    ocr_model = session.get('ocr_model', 'pytesseract')
    print(f"OCR model from session: {ocr_model}")
    
    if ocr_model == 'qwen2':
        # Check if Qwen model is loaded
        if not qwen_model_loaded:
            return render_template('qwen_prediction.html', 
                                  results={"ERROR": "Qwen2 model not loaded. Please load the model first."})
        
        # Use Qwen2 model for entity extraction
        upload_image_path = settings.join_path(settings.MEDIA_DIR, 'upload.jpg')
        
        # Check if the image exists
        if not os.path.exists(upload_image_path):
            return render_template('qwen_prediction.html', 
                                  results={"ERROR": "Image file not found. Please upload an image first."})
        
        # Save a copy for display as bounding box image
        bb_filename = settings.join_path(settings.MEDIA_DIR, 'bounding_box.jpg')
        image = cv2.imread(upload_image_path)
        
        if image is None:
            return render_template('qwen_prediction.html', 
                                  results={"ERROR": "Failed to read image file. The file may be corrupted."})
        
        cv2.imwrite(bb_filename, image)
        
        # Process document using qwenform
        results = qwenform.process_document(upload_image_path)
        return render_template('qwen_prediction.html', results=results)
        
    elif ocr_model == 'azure':
        try:
            # Use the uploaded image path
            upload_image_path = settings.join_path(settings.MEDIA_DIR, 'upload.jpg')
            if not os.path.exists(upload_image_path):
                return render_template('azure_prediction.html', 
                                      results={"error": "Image file not found. Please upload an image first."})

            results = azureform.process_business_card(upload_image_path)
            print(results)
            return render_template('azure_prediction.html', results=results)
        except Exception as e:
            return render_template('azure_prediction.html', results={"error": f"Azure processing error: {str(e)}"})
    else:
        try:
            # load the wrap image for Pytesseract/Spacy processing
            wrap_image_filepath = settings.join_path(settings.MEDIA_DIR,'magic_color.jpg')
            
            # Check if the wrapped image exists
            if not os.path.exists(wrap_image_filepath):
                return render_template('predictions.html', 
                                      results={"ERROR": "Wrapped image not found. Please process the document first."})
                
            image = cv2.imread(wrap_image_filepath)
            
            if image is None:
                return render_template('predictions.html', 
                                      results={"ERROR": "Failed to read wrapped image. The file may be corrupted."})
                
            # Use the original Pytesseract + SpaCy NER method
            image_bb, results = pred.getPredictions(image)
            
            bb_filename = settings.join_path(settings.MEDIA_DIR,'bounding_box.jpg') 
            cv2.imwrite(bb_filename, image_bb)
            
            # If results contain an ERROR key, it means the prediction failed
            if "ERROR" in results:
                print(f"Error in Pytesseract processing: {results['ERROR']}")
                
            return render_template('predictions.html', results=results)
        except Exception as e:
            print(f"Unhandled exception in Pytesseract processing: {str(e)}")
            return render_template('predictions.html', 
                                  results={"ERROR": f"Error in document processing: {str(e)}"})

@app.route('/about')
def about():
    return render_template('about.html')

if __name__ == "__main__":
    app.run(debug=True)