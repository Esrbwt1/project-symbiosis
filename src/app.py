import os
import torch
import timm
from PIL import Image
from flask import Flask, request, render_template, redirect, url_for, g, jsonify

from timm.data import resolve_data_config
from timm.data.transforms_factory import create_transform

# --- Configuration ---
app = Flask(__name__)
UPLOAD_FOLDER = os.path.join('static', 'uploads') # Storing uploads in static folder for direct access
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# In-memory storage for our DePIN nodes. In a real system, this would be a database or on-chain.
REGISTERED_NODES = set()

# --- AI Model Setup ---
def get_model():
    if 'model' not in g:
        g.model = timm.create_model('efficientnet_b0', pretrained=True)
        g.model.eval()
    return g.model

def run_model_inference(image_path):
    try:
        model = get_model()
        config = resolve_data_config({}, model=model)
        transform = create_transform(**config)
        image = Image.open(image_path).convert('RGB')
        tensor = transform(image).unsqueeze(0)
        with torch.no_grad():
            out = model(tensor)
        probabilities = torch.nn.functional.softmax(out[0], dim=0)
        top_class_index = torch.argmax(probabilities).item()
        
        # Use the class map file
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
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# --- DePIN Routes (NEW) ---
@app.route('/register_node', methods=['POST'])
def register_node():
    """Registers a new compute node to our network."""
    node_address = request.json.get('node_address')
    if not node_address:
        return jsonify({"error": "Invalid request. 'node_address' is required."}), 400
    
    REGISTERED_NODES.add(node_address)
    print(f"Node registered: {node_address}. Total nodes: {len(REGISTERED_NODES)}")
    return jsonify({
        "message": "Node registered successfully.",
        "total_nodes": len(REGISTERED_NODES)
    }), 201

@app.route('/nodes')
def get_nodes():
    """Lists all registered compute nodes."""
    return jsonify({"nodes": list(REGISTERED_NODES)})

# --- AgriAI User Routes ---
@app.route('/', methods=['GET', 'POST'])
def upload_file():
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
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    ai_prediction = run_model_inference(filepath)
    analysis_result = {
        "ai_finding": ai_prediction,
        "soil_type": "Placeholder: Loamy Soil",
        "pest_detected": "Placeholder: No Pests Detected",
        "recommendation": "Placeholder: Based on AI finding, further action may be required."
    }
    image_url = url_for('static', filename=os.path.join('uploads', filename))
    return render_template('analysis.html', image_name=filename, analysis=analysis_result, image_url=image_url)

# --- Main Execution ---
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)