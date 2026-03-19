import os
import numpy as np
import tensorflow as tf
from PIL import Image

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
_model = None


def get_model():
    global _model
    if _model is None:
        model_path = os.path.join(BASE_DIR, '..', 'models', 'plant_disease_model.h5')
        _model = tf.keras.models.load_model(model_path)
        print('✅ Model loaded.')
    return _model


CLASS_NAMES = [
    'Corn Rust',
    'Corn Healthy',
    'Pepper Bacterial Spot',
    'Pepper Healthy',
    'Potato Early Blight',
    'Potato Late Blight',
    'Potato Healthy',
    'Tomato Early Blight',
    'Tomato Late Blight',
    'Tomato Healthy',
]

TREATMENTS = {
    'Corn Rust': {
        'severity':   'high',
        'immediate':  'Apply propiconazole or trifloxystrobin-based fungicide immediately. Remove and destroy heavily infected leaves.',
        'prevention': 'Plant rust-resistant corn varieties. Avoid overhead irrigation. Ensure wide plant spacing for air circulation.',
        'notes':      'Common rust spreads rapidly in warm, humid weather (16–23°C). Monitor daily once detected.',
    },
    'Corn Healthy': {
        'severity':   'low',
        'immediate':  'No action needed. Plant looks healthy.',
        'prevention': 'Maintain regular fertilisation schedule. Monitor weekly for early signs of pests or disease.',
        'notes':      'Continue current care practices. Ensure soil drainage is adequate.',
    },
    'Pepper Bacterial Spot': {
        'severity':   'high',
        'immediate':  'Apply copper-based bactericide (e.g. copper hydroxide) every 7 days. Remove infected plant parts immediately.',
        'prevention': 'Use disease-free certified seeds. Avoid working in the field when plants are wet. Rotate crops yearly.',
        'notes':      'Bacterial spot is seed-borne. Hot and rainy conditions accelerate spread. No cure — management is key.',
    },
    'Pepper Healthy': {
        'severity':   'low',
        'immediate':  'No action needed. Plant looks healthy.',
        'prevention': 'Continue regular watering at soil level. Avoid wetting foliage. Add mulch to retain moisture.',
        'notes':      'Peppers thrive in well-drained soil with 6–8 hours of sunlight.',
    },
    'Potato Early Blight': {
        'severity':   'medium',
        'immediate':  'Apply chlorothalonil or mancozeb fungicide. Remove lower infected leaves and dispose away from the field.',
        'prevention': 'Avoid overhead watering. Ensure proper plant spacing. Rotate with non-solanaceous crops for 2 years.',
        'notes':      'Early blight (Alternaria solani) is most severe on stressed plants. Improve soil nutrition.',
    },
    'Potato Late Blight': {
        'severity':   'high',
        'immediate':  'Apply metalaxyl + mancozeb fungicide immediately. Destroy infected plants. Do NOT compost them.',
        'prevention': 'Use certified blight-free seed potatoes. Avoid planting near tomatoes. Apply preventive fungicide sprays.',
        'notes':      'Late blight (Phytophthora infestans) caused the Irish Famine. It can destroy a crop in days.',
    },
    'Potato Healthy': {
        'severity':   'low',
        'immediate':  'No action needed. Plant looks healthy.',
        'prevention': 'Hill soil around stems to prevent greening. Ensure consistent watering to avoid hollow heart.',
        'notes':      'Monitor weekly for dark lesions or water-soaked spots — first signs of late blight.',
    },
    'Tomato Early Blight': {
        'severity':   'medium',
        'immediate':  'Remove affected lower leaves. Apply copper-based fungicide or chlorothalonil every 7–10 days.',
        'prevention': 'Mulch soil to prevent spore splash-back. Water at base of plant. Remove crop debris after harvest.',
        'notes':      'Early blight starts on oldest leaves. Consistent management prevents it from reaching the fruit.',
    },
    'Tomato Late Blight': {
        'severity':   'high',
        'immediate':  'Apply cymoxanil + mancozeb fungicide immediately. Remove and bag all infected material. Do NOT compost.',
        'prevention': 'Avoid overhead irrigation. Plant in raised beds with good drainage. Use resistant varieties.',
        'notes':      'Tomato late blight spreads very fast in cool, wet conditions (10–25°C with high humidity).',
    },
    'Tomato Healthy': {
        'severity':   'low',
        'immediate':  'No action needed. Plant looks healthy.',
        'prevention': 'Stake or cage plants for air circulation. Feed with balanced fertiliser.',
        'notes':      'Healthy tomatoes need consistent watering — irregular watering causes blossom end rot.',
    },
}


def predict(img: Image.Image):
    img = img.resize((224, 224)).convert('RGB')
    arr = np.expand_dims(np.array(img) / 255.0, axis=0)
    preds = get_model().predict(arr, verbose=0)
    idx = int(np.argmax(preds))
    disease = CLASS_NAMES[idx]
    confidence = float(np.max(preds)) * 100
    treatment = TREATMENTS.get(disease, {})
    crop = _crop_from_disease(disease)
    return disease, round(confidence, 2), treatment, crop


def _crop_from_disease(disease):
    d = disease.lower()
    if 'corn'   in d: return 'Corn'
    if 'pepper' in d: return 'Pepper'
    if 'potato' in d: return 'Potato'
    if 'tomato' in d: return 'Tomato'
    return 'Unknown'