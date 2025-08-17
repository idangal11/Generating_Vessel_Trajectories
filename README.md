# Generating Vessel Trajectories Using GPT and AIS Data

## 📌 Overview

This project explores the use of **Generative Pre-trained Transformers (GPT)** to model and generate maritime vessel trajectories based on **Automatic Identification System (AIS)** data.
The goal is to leverage **sequence modeling** techniques, commonly applied in Natural Language Processing (NLP), to capture vessel movement patterns and generate realistic predictions of future routes.

---

## 🚢 Motivation

AIS data provides detailed records of vessel positions, including latitude, longitude, speed, and bearing. However, AIS datasets are often incomplete due to transmission gaps, noise, or missing records.
By treating vessel trajectories as sequential data (similar to sentences in language), GPT can be adapted to:

* **Predict missing trajectory segments**.
* **Generate complete vessel routes** given partial inputs.
* **Model maritime movement patterns** for traffic simulation and risk assessment.

---

## 🔧 Methodology

1. **Data Preprocessing**

   * Extracted vessel tracks from raw AIS `.gpkg` files.
   * Converted `MULTILINESTRING` geometries into sequences of consecutive latitude–longitude pairs.
   * Added contextual features: speed (SPD), bearing (BRG), and time delta (ΔT).

2. **Modeling with GPT**

   * Fine-tuned a **GPT-2 model** on AIS sequences.
   * Special token `<|endofroute|>` used to indicate the end of a vessel trajectory.
   * Input: partial trajectory → Output: predicted continuation.

3. **Evaluation**

   * Calculated the **average geodesic distance** between generated points and real AIS positions.
   * Compared reconstruction accuracy across vessel types and regions.

---

## 📊 Results

* The GPT-based model was able to **generate realistic continuation of vessel tracks**.
* Prediction quality varied by vessel type (cargo, tanker, fishing).
* Demonstrated that NLP-inspired models can successfully adapt to geospatial sequence prediction.

---

## 🌍 Applications

* **Maritime navigation support**: filling missing AIS gaps.
* **Traffic simulation**: generating realistic shipping lane movements.
* **Risk & safety analysis**: predicting potential vessel encounters.
* **Environmental studies**: modeling ship emissions along synthetic trajectories.

---

## 📂 Repository Structure

```
.
├── data/                 # AIS samples (preprocessed)
├── preprocessing/        # Scripts for data cleaning & formatting
├── models/               # GPT training and fine-tuning code
├── experiments/          # Evaluation scripts & results
├── notebooks/            # Jupyter notebooks for exploration
└── README.md             # Project description
```

---

## 🚀 Getting Started

### Prerequisites

* Python 3.9+
* PyTorch
* Hugging Face Transformers
* Geopandas / Shapely (for AIS preprocessing)

### Installation

```bash
git clone https://github.com/<your-username>/<repo-name>.git
cd <repo-name>
pip install -r requirements.txt
```

### Training

```bash
python train_gpt.py --data data/ais_sequences.txt --epochs 10
```

### Inference

```bash
python generate.py --input "LAT:25.8 LON:-82.7 SPD:8.1 BRG:356 ΔT:120"
```

---

## ✨ Example Output

**Input (partial track):**

```
LAT:25.7919 LON:-82.7374 SPD:8.1 BRG:356 ΔT:0 |
LAT:25.8160 LON:-82.7387 SPD:3.2 BRG:358 ΔT:938 |
```

**Generated continuation:**

```
LAT:25.8178 LON:-82.7387 SPD:14.9 BRG:358 ΔT:120 |
LAT:25.8261 LON:-82.7391 SPD:3.1 BRG:358 ΔT:120 |
...
<|endofroute|>
```

---

## 📝 License

This project is released under the **MIT License**.

---

## 🙌 Acknowledgements

* AIS data courtesy of [Marine Cadastre](https://marinecadastre.gov/).
* GPT-2 architecture from [Hugging Face Transformers](https://huggingface.co/transformers/).
* Research inspired by maritime data modeling and NLP adaptation.
