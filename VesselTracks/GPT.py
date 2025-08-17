import os
import json
from datasets import load_dataset, DatasetDict
from transformers import (
    GPT2LMHeadModel,
    GPT2Tokenizer,
    DataCollatorForLanguageModeling,
    Trainer,
    TrainingArguments,
    pipeline,
)

# === שלב 1: טוקניזר ומודל ===
model_name = "gpt2"
tokenizer = GPT2Tokenizer.from_pretrained(model_name)
model = GPT2LMHeadModel.from_pretrained(model_name)

tokenizer.add_special_tokens({'additional_special_tokens': ['<|endofroute|>']})
tokenizer.pad_token = tokenizer.eos_token
model.resize_token_embeddings(len(tokenizer))

# === שלב 2: טעינת הקובץ ===
file_path = "/mnt/new_home/idan7/data_mining/ais_tracks_export/cleaned_data/vessel_tracks.txt"
dataset = load_dataset("text", data_files={"data": file_path})["data"]

# === שלב 3: פיצול ל-train ו-validation בלבד ===
split = dataset.train_test_split(test_size=0.1, seed=42)
train_dataset = split["train"]
val_dataset = split["test"]

# === שלב 4: טוקניזציה (רק 10K ל-train, 1K ל-val) ===
def tokenize_function(examples):
    return tokenizer(examples["text"], truncation=True, padding="max_length", max_length=512)

tokenized_train = train_dataset.select(range(10000)).map(tokenize_function, batched=True, remove_columns=["text"])
tokenized_val = val_dataset.select(range(1000)).map(tokenize_function, batched=True, remove_columns=["text"])

# === שלב 5: פרמטרים לאימון מהיר ===
data_collator = DataCollatorForLanguageModeling(tokenizer=tokenizer, mlm=False)

training_args = TrainingArguments(
    output_dir="./gpt-vessel",
    overwrite_output_dir=True,
    max_steps=1000,  # מגביל את מספר הסטפים
    per_device_train_batch_size=8,
    per_device_eval_batch_size=8,
    save_steps=500,
    save_total_limit=1,
    logging_dir="./logs",
    logging_steps=50,
    do_eval=True,
)

# === שלב 6: אימון ===
trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=tokenized_train,
    eval_dataset=tokenized_val,
    tokenizer=tokenizer,
    data_collator=data_collator,
)

print("[INFO] Training started...")
train_result = trainer.train()
print("[INFO] Training completed.")

# === שלב 7: שמירת המודל והתוצאות ===
trainer.save_model("/mnt/new_home/idan7/data_mining/ais_tracks_export/")
tokenizer.save_pretrained("/mnt/new_home/idan7/data_mining/ais_tracks_export/")

with open("/mnt/new_home/idan7/data_mining/ais_tracks_export/training_metrics.json", "w") as f:
    json.dump(train_result.metrics, f, indent=4)

# === שלב 8: בדיקה של פרומפט לדוגמה ===
generator = pipeline("text-generation", model="./gpt-vessel", tokenizer="./gpt-vessel")

def predict_next_coordinate(prompt: str):
    output = generator(
        prompt,
        max_length=60,
        num_return_sequences=1,
        eos_token_id=tokenizer.eos_token_id
    )
    generated_text = output[0]['generated_text']
    if "OUTPUT:" in generated_text:
        return generated_text.split("OUTPUT:", 1)[-1].strip().split("|")[0].strip()
    return generated_text

# דוגמה לבדיקה
example_prompt = "INPUT: LAT:18.3234 LON:-64.8056 SPD:5.1064 BRG:278.3201 ΔT:158 | OUTPUT:"
prediction = predict_next_coordinate(example_prompt)
print(f"[Predicted Coordinates]: {prediction}")
