# NotifiCheck – Verificador de Notificações do  

O **NotifiCheck** é um app simples e direto, criado para ajudar você a verificar se aquela notificação que apareceu no seu celular é real ou pode ser uma tentativa de golpe. Usamos inteligência artificial para analisar imagens e dizer se são verdadeiras, aqueles prints dos ganhos do tigrinho mesmo, uque deve costumar ver no seu Instagram.

## Como funciona?

O projeto foi desenvolvido separando o back e o front.

- **Backend (FastAPI)**: é a parte que processa as imagens e faz a verificação de autenticidade.
- **Frontend (Flet)**: é a interface onde você interage, envia a imagem e recebe o resultado de forma rápida e simples.

## O que você precisa para rodar

### Backend (API)
- Python 3.8 ou superior
- FastAPI
- Uvicorn
- TensorFlow
- OpenCV
- scikit-image
- NumPy
- Matplotlib
- Pillow

### Frontend
- Python 3.8 ou superior
- Flet
- Pillow
- Requests

## Como instalar e rodar

### Configurando o Backend

1. **(Opcional, mas recomendado)** Crie e ative um ambiente virtual:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Para Linux/Mac
   venv\Scripts\activate     # Para Windows
   ```

2. **Instale as dependências**:
   ```bash
   pip install fastapi uvicorn python-multipart tensorflow opencv-python scikit-image numpy matplotlib pillow
   ```

3. **Crie a pasta para imagens reais**:
   ```bash
   mkdir -p ./data/real
   ```

4. **Adicione imagens reais de notificações do  ** na pasta `./data/real`.

### Configurando o Frontend

1. **Instale o Flet e outras bibliotecas necessárias**:
   ```bash
   pip install flet pillow requests
   ```

2. **Salve o código do frontend** em um arquivo chamado `appcheck_app.py`.

## Rodando o projeto

### Iniciar o Backend (API)

1. Salve o código da API em um arquivo chamado `api_check.py`.
2. Rode o servidor com o comando:
   ```bash
   uvicorn api_check:app --reload
   ```
3. A API estará disponível em `http://localhost:8000`.

### Iniciar o Frontend

1. Rode o aplicativo Flet com:
   ```bash
   python appcheck_app.py
   ```

## Licença

Este projeto foi feito com fins educacionais e pode servir como base para estudos sobre IA, segurança digital e desenvolvimento de aplicações com Python.
