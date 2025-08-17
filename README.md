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
* **Model maritime movement patterns** for traffic simulation.

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

* The GPT-based model was able to **generate approximate vessel tracks**.
* Demonstrated that NLP-inspired models can adapt to geospatial sequence prediction.

---

## 🌍 Applications

* **Maritime navigation support**: filling missing AIS gaps.
* **Traffic simulation**: generating realistic shipping lane movements.
* **Risk & safety analysis**: predicting potential vessel encounters.
* **Environmental studies**: modeling ship emissions along synthetic trajectories.


## 🚀 Getting Started

### Prerequisites

* Python 3.9+
* PyTorch
* Hugging Face Transformers
* Geopandas / Shapely (for AIS preprocessing)

## 🙌 Acknowledgements

* AIS data courtesy of [Marine Cadastre](https://marinecadastre.gov/).
* GPT-2 architecture from [Hugging Face Transformers](https://huggingface.co/transformers/).
* Research inspired by maritime data modeling and NLP adaptation.
