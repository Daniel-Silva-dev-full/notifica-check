import os
import numpy as np
from PIL import Image
import cv2
from skimage.metrics import structural_similarity as ssim
import matplotlib.pyplot as plt
import io
import base64
from fastapi import FastAPI, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
import uvicorn
from tensorflow.keras.applications import VGG16
from tensorflow.keras.applications.vgg16 import preprocess_input
from tensorflow.keras.models import Model
import tensorflow as tf
from pydantic import BaseModel
import shutil

# Suprimir mensagens de aviso do TensorFlow
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'

app = FastAPI(
    title="NotifiCheck API",
    description="API para verificação de notificações do Nubank",
    version="1.0.0"
)

# Configurar CORS para permitir solicitações do frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, especifique os domínios permitidos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Carregar o modelo VGG16 ao iniciar o servidor
model = None


@app.on_event("startup")
async def startup_event():
    global model
    print("Carregando modelo VGG16...")
    base_model = VGG16(weights='imagenet', include_top=False)
    model = Model(inputs=base_model.input, outputs=base_model.output)
    print("Modelo carregado com sucesso!")

# extrair características de uma imagem usando VGG16


def extract_features(img, model):
    img = cv2.resize(img, (224, 224))
    img = np.expand_dims(img, axis=0)
    img = preprocess_input(img)
    features = model.predict(img, verbose=0)  # Desativar saída verbosa
    return features.flatten()

# calcular a similaridade entre duas imagens usando SSIM


def compare_images_ssim(img1, img2):
    # Converter para escala de cinza
    img1_gray = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
    img2_gray = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)

    # Redimensionar imagens para o mesmo tamanho
    img2_gray = cv2.resize(img2_gray, (img1_gray.shape[1], img1_gray.shape[0]))

    # Calcular SSIM
    (score, diff) = ssim(img1_gray, img2_gray, full=True)
    return score

# calcular a similaridade entre características extraídas pelo VGG16


def compare_features(features1, features2):
    return np.dot(features1, features2) / (np.linalg.norm(features1) * np.linalg.norm(features2))

# Criar um gráfico de confiança


def create_confidence_chart(confidence, threshold):
    fig, ax = plt.subplots(figsize=(5, 0.7))
    ax.barh(["Confiança"], [confidence],
            color='blue' if confidence/100 > threshold else 'red')
    ax.axvline(x=threshold*100, color='green', linestyle='--', alpha=0.7)
    ax.set_xlim(0, 100)
    ax.set_xlabel('Porcentagem (%)')
    ax.grid(True, alpha=0.3)

    buf = io.BytesIO()
    fig.savefig(buf, format='png')
    plt.close(fig)
    buf.seek(0)

    return base64.b64encode(buf.getvalue()).decode()


class AnalysisResult(BaseModel):
    is_authentic: bool
    confidence: float
    confidence_chart: str
    combined_score: float
    visual_similarity: float
    semantic_similarity: float
    best_match_file: Optional[str] = None


@app.post("/analyze", response_model=AnalysisResult)
async def analyze_notification(
    file: UploadFile = File(...),
    reference_dir: str = Form(r"C:\proj_notific_fake\data\real")
):
    # Verificar se o diretório de referência existe
    if not os.path.exists(reference_dir):
        return {"error": f"Diretório {reference_dir} não encontrado"}

    # Listar arquivos de imagem no diretório
    image_files = [f for f in os.listdir(reference_dir)
                   if f.lower().endswith(('.png', '.jpg', '.jpeg'))]

    if not image_files:
        return {"error": f"Nenhuma imagem de referência encontrada em {reference_dir}"}

    # Salvar o arquivo enviado temporariamente
    temp_file = f"temp_{file.filename}"
    with open(temp_file, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        # Processar a imagem
        image = Image.open(temp_file)
        img_array = np.array(image)

        # Converter para BGR (formato OpenCV)
        if len(img_array.shape) == 3 and img_array.shape[2] == 3:
            img_array = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
        elif len(img_array.shape) == 2:
            img_array = cv2.cvtColor(img_array, cv2.COLOR_GRAY2BGR)

        # Extrair características da imagem carregada
        features_uploaded = extract_features(img_array, model)

        # Inicializar variáveis para acompanhar a melhor correspondência
        best_match_score = 0
        best_match_file = None
        best_match_image = None
        best_ssim_score = 0
        best_similarity_score = 0

        # Comparar com todas as imagens de referência
        for image_file in image_files:
            file_path = os.path.join(reference_dir, image_file)
            ref_img = cv2.imread(file_path)

            if ref_img is None:
                continue

            # Extrair características da imagem de referência
            features_ref = extract_features(ref_img, model)

            # Calcular similaridade entre características
            similarity_score = compare_features(
                features_uploaded, features_ref)

            # Calcular similaridade estrutural (SSIM)
            ssim_score = compare_images_ssim(img_array, ref_img)

            # Calcular pontuação combinada (média ponderada)
            combined_score = 0.7 * similarity_score + 0.3 * ssim_score

            # Atualizar melhor correspondência
            if combined_score > best_match_score:
                best_match_score = combined_score
                best_match_file = image_file
                best_match_image = ref_img
                best_ssim_score = ssim_score
                best_similarity_score = similarity_score

        # Definir limiar para classificação
        threshold = 0.65

        # Calcular confiança em porcentagem
        confidence = best_match_score * 100

        # Determinar resultado
        is_authentic = best_match_score > threshold

        # Criar gráfico de confiança
        confidence_chart = create_confidence_chart(confidence, threshold)

        # Retornar resultado
        result = {
            "is_authentic": is_authentic,
            "confidence": confidence,
            "confidence_chart": confidence_chart,
            "combined_score": best_match_score,
            "visual_similarity": best_ssim_score,
            "semantic_similarity": best_similarity_score,
            "best_match_file": best_match_file
        }

        return result

    finally:
        # Limpar o arquivo temporário
        if os.path.exists(temp_file):
            os.remove(temp_file)


@app.get("/")
async def root():
    return {"message": "Bem-vindo à API do NotifiCheck. Use o endpoint /analyze para verificar notificações."}

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
