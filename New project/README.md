# Next Word Prediction

This workspace has been rebuilt to match the project described in your report: a next-word prediction system with a Flask backend, a polished frontend, and a corrected LSTM training pipeline.

## Project Motive

The report's abstract and introduction consistently describe the same goal:

- help users type faster by suggesting the next likely word
- use an LSTM model to learn word order and context from text data
- expose the predictions through a simple web interface

## What Was Wrong In The Report Code

The code shown in the Word document is a good starting idea, but it is not reliable enough to claim accurate training yet. The main issues are:

- it "saves" the tokenizer by opening `tokenizer.pkl` in read mode and loading it instead of writing it
- it compiles the model twice with conflicting losses; `categorical_crossentropy` is incorrect for integer labels unless `y` is one-hot encoded
- it only reports training accuracy and does not use a validation split, so the result can look better than it really is
- it slices the sequence list to `8000` items without explanation, which can throw away a lot of useful training data
- the debug line `y.argmax().max()` is not meaningful for the 1D label array being used
- inference quietly falls back to demo words if the model is missing, which hides deployment problems

## Project Structure

- `app.py`: Flask server and API routes
- `backend/predictor.py`: LSTM artifact loader plus fallback predictor selection
- `backend/project_profile.py`: report-aligned project summary exposed to the frontend
- `backend/ngram_fallback.py`: local fallback predictor that works without TensorFlow
- `training/train_lstm.py`: corrected training script with validation metrics and artifact saving
- `data/sample_corpus.txt`: demo corpus so the app works immediately
- `frontend/index.html`, `frontend/style.css`, `frontend/script.js`: frontend
- `tests/smoke_test.py`: simple integration check for the main routes

## Run Locally

### 1. Create a virtual environment

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### 2. Install the runtime dependencies

```powershell
pip install -r requirements.txt
```

### 3. Start the app in development

```powershell
python app.py
```

or:

```powershell
.\run_local.ps1
```

### 4. Open the app

Visit [http://localhost:5000](http://localhost:5000)

The app will run immediately using the fallback predictor. Once you train and save LSTM artifacts into `artifacts/`, the API will switch to LSTM mode automatically.

## Train The LSTM Model

TensorFlow is not installed in the current local environment yet. The official pip guide currently lists Python `3.9–3.12` for TensorFlow, so your current Python `3.13` environment is not the right place to train the LSTM. Create a Python `3.11` virtual environment for the smoothest setup. This project uses `tensorflow-cpu` by default. Native Windows GPU support ended after TensorFlow `2.10`, so use WSL2 and TensorFlow's CUDA install path if you want GPU acceleration.

### 1. Install the training dependencies

```powershell
pip install -r requirements-lstm.txt
```

### 2. Replace the sample corpus if you have your real dataset

Put your text dataset in `data/` and update the `--corpus` path if needed.

### 3. Run training

```powershell
python training\train_lstm.py --corpus data\sample_corpus.txt
```

or:

```powershell
.\train_model.ps1
```

### 4. Check the generated files

The script writes these files into `artifacts/`:

- `next_word_model.keras`
- `tokenizer.pkl`
- `metadata.json`
- `metrics.json`
- `history.json`

Use `metrics.json` to judge actual model quality. The most important values are:

- `loss`
- `accuracy`
- `top3_accuracy`
- `perplexity`

## Deployment Steps

### Option 1: Deploy With Docker

1. Install Docker.
2. Build the image:

```powershell
docker build -t next-word-predictor .
```

3. Run it locally first:

```powershell
docker run -p 5000:5000 next-word-predictor
```

4. Push the image to a container registry like Docker Hub or GitHub Container Registry.
5. Deploy that image to any host that supports Docker.

### Option 2: Deploy As A Single Flask Service

1. Use Python 3.11 on the hosting platform.
2. Upload this project.
3. Set the production start command to:

```bash
waitress-serve --listen="*:$PORT" app:app
```

4. Make sure the platform exposes the `PORT` environment variable.
5. If you want real LSTM predictions in production, deploy with the trained files already present in `artifacts/`.

## Accuracy Guidance

Without your real dataset and without running TensorFlow training in a supported Python version, nobody can honestly claim that the original training is already accurate. What we can say from the report code review is:

- the original code was not reliable enough for a fair accuracy claim
- the new training script is set up to measure validation quality correctly
- the final verdict should come from the generated validation metrics after training on your actual corpus
