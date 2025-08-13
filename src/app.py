import os
from flask import Flask, request, render_template, redirect, url_for

# --- Configuration ---
# Create the Flask application
app = Flask(__name__)

# Configure the upload folder and allowed extensions
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# --- Helper Functions ---
def allowed_file(filename):
    """Checks if the file extension is allowed."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# --- Routes ---
@app.route('/', methods=['GET', 'POST'])
def upload_file():
    """Handles the file upload and displays the form."""
    if request.method == 'POST':
        # Check if the post request has the file part
        if 'file' not in request.files:
            # Optional: Add a flash message for user feedback
            return redirect(request.url)
        
        file = request.files['file']
        
        # If the user does not select a file, the browser submits an empty file
        if file.filename == '':
            # Optional: Add a flash message
            return redirect(request.url)
            
        if file and allowed_file(file.filename):
            # In a real app, you would secure the filename
            # For now, we save it directly
            # Ensure the upload folder exists
            if not os.path.exists(app.config['UPLOAD_FOLDER']):
                os.makedirs(app.config['UPLOAD_FOLDER'])
            
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(filepath)
            
            # Redirect to the analysis page after upload
            return redirect(url_for('analyze_image', filename=file.filename))

    # For a GET request, show the upload form
    return render_template('upload.html')

@app.route('/analyze/<filename>')
def analyze_image(filename):
    """Displays the analysis result (placeholder)."""
    # This is where the AI model will be called in the future.
    # For now, we just display the filename and a placeholder message.
    image_url = url_for('static', filename=os.path.join('uploads', filename))
    
    # Placeholder analysis data
    analysis_result = {
        "soil_type": "Placeholder: Loamy Soil",
        "pest_detected": "Placeholder: No Pests Detected",
        "recommendation": "Placeholder: Water requirements are normal. Monitor for changes."
    }
    
    return render_template('analysis.html', image_name=filename, analysis=analysis_result)

# --- Main Execution ---
if __name__ == '__main__':
    # The host='0.0.0.0' makes the server accessible on your local network
    app.run(host='0.0.0.0', port=5000, debug=True)