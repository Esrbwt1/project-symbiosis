import os
import torch
import timm
from PIL import Image
from flask import Flask, request, render_template, redirect, url_for, g
from timm.data import resolve_data_config
from timm.data.transforms_factory import create_transform

# --- Configuration ---
app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# --- AI Model Setup ---
def get_model():
    """Loads and returns the AI model, caching it in the application context."""
    if 'model' not in g:
        # Load a pre-trained model from timm. 
        # 'efficientnet_b0' is a good balance of size and accuracy.
        g.model = timm.create_model('efficientnet_b0', pretrained=True)
        g.model.eval() # Set the model to evaluation mode
    return g.model

def run_model_inference(image_path):
    """Runs the uploaded image through the AI model and returns the top prediction."""
    try:
        model = get_model()
        
        # Get the model-specific transformations
        config = resolve_data_config({}, model=model)
        transform = create_transform(**config)

        # Open and transform the image
        image = Image.open(image_path).convert('RGB')
        tensor = transform(image).unsqueeze(0) # Add a batch dimension

        # Get model predictions
        with torch.no_grad():
            out = model(tensor)
        
        # Get probabilities and the top class index
        probabilities = torch.nn.functional.softmax(out[0], dim=0)
        top_class_index = torch.argmax(probabilities).item()

        # Get the human-readable class name
        # Note: This requires the model's class map. For now, we get the raw index.
        # In a real app, we'd map this index to a name like "leaf_blight" or "healthy_plant".
        # For this MVP, the prediction itself is the demonstration.
        
        # Let's get the class name from the model's meta info if available
        class_map_file = os.path.join(os.path.dirname(__file__), 'imagenet_classes.txt')
        with open(class_map_file, 'r') as f:
            class_labels = [line.strip() for line in f.readlines()]
        
        predicted_class = class_labels[top_class_index]
        confidence = probabilities[top_class_index].item() * 100

        return f"Most likely class: '{predicted_class}' with {confidence:.2f}% confidence."

    except Exception as e:
        return f"Error during analysis: {e}"

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
        if 'file' not in request.files:
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            return redirect(request.url)
        if file and allowed_file(file.filename):
            if not os.path.exists(app.config['UPLOAD_FOLDER']):
                os.makedirs(app.config['UPLOAD_FOLDER'])
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(filepath)
            return redirect(url_for('analyze_image', filename=file.filename))
    return render_template('upload.html')

@app.route('/analyze/<filename>')
def analyze_image(filename):
    """Performs AI analysis and displays the result."""
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    
    # Run the AI model on the uploaded image
    ai_prediction = run_model_inference(filepath)
    
    # Our new analysis result includes the AI's output
    analysis_result = {
        "ai_finding": ai_prediction,
        "soil_type": "Placeholder: Loamy Soil",
        "pest_detected": "Placeholder: No Pests Detected",
        "recommendation": "Placeholder: Based on AI finding, further action may be required."
    }
    
    return render_template('analysis.html', image_name=filename, analysis=analysis_result)

# --- Main Execution ---
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)