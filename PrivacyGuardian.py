import io
import requests
import PyPDF2
from transformers import pipeline, AutoTokenizer, AutoModelForCausalLM
from langchain_huggingface import HuggingFacePipeline

def extract_text_from_local_pdf(file_path: str) -> str:
    try:
        with open(file_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            text = ""
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
            return text
    except Exception as e:
        return f"Error reading local PDF file: {e}"

def extract_text_from_web_pdf(url: str) -> str:
    try:
        response = requests.get(url)
        response.raise_for_status()
        pdf_file = io.BytesIO(response.content)
        reader = PyPDF2.PdfReader(pdf_file)
        text = ""
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
        return text
    except Exception as e:
        return f"Error reading web PDF file: {e}"

def main():
    print("Please specify the source of the PDF file.")
    source_type = input("Local or Web? (Local/Web): ").strip().lower()
    pdf_text = ""
    if source_type.startswith("l"):
        file_path = input("Please enter the local PDF file path (e.g., /path/to/file.pdf): ").strip()
        pdf_text = extract_text_from_local_pdf(file_path)
    elif source_type.startswith("w"):
        pdf_url = input("Please enter the PDF file URL: ").strip()
        pdf_text = extract_text_from_web_pdf(pdf_url)
    else:
        print("Invalid choice! Please specify 'Local' or 'Web'.")
        return
    if pdf_text.startswith("Error"):
        print(pdf_text)
        return
    quant_choice = input("Do you want to use quantization? (No/4bit/8bit): ").strip().lower()
    print("\nWhich Seneca LLM version would you like to use?")
    print("1. AlicanKiraz0/Seneca-x-DeepSeek-R1-Distill-Qwen-32B-v1.3-Safe")
    print("2. AlicanKiraz0/SenecaLLM-x-Llama3.1-8B")
    model_choice = input("Please enter 1 or 2: ").strip()
    if model_choice == "1":
        model_name = "AlicanKiraz0/Seneca-x-DeepSeek-R1-Distill-Qwen-32B-v1.3-Safe"
    elif model_choice == "2":
        model_name = "AlicanKiraz0/SenecaLLM-x-Llama3.1-8B"
    else:
        print("Invalid choice! Defaulting to 'AlicanKiraz0/SenecaLLM-x-Llama3.1-8B'.")
        model_name = "AlicanKiraz0/SenecaLLM-x-Llama3.1-8B"
    print("\nLoading model and tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    try:
        if quant_choice in ["4bit", "4", "fourbit"]:
            model = AutoModelForCausalLM.from_pretrained(model_name, device_map="auto", load_in_4bit=True)
        elif quant_choice in ["8bit", "8", "eightbit"]:
            model = AutoModelForCausalLM.from_pretrained(model_name, device_map="auto", load_in_8bit=True)
        else:
            model = AutoModelForCausalLM.from_pretrained(model_name, device_map="auto")
    except Exception as e:
        print(f"Error loading model: {e}")
        return
    pipe = pipeline(task="text-generation", model=model, tokenizer=tokenizer, max_new_tokens=256, temperature=0.2, repetition_penalty=1.2, no_repeat_ngram_size=2, do_sample=True, top_p=0.9, top_k=40)
    llm = HuggingFacePipeline(pipeline=pipe)
    system_instruction = """[System note]
You are a strict InfoSec auditor. Your task is to analyze the provided text and identify any signs of sensitive data leaks (such as passwords, tokens, API keys, PII, or hardcoded credentials) and determine whether sharing the document with third parties poses any security risks. Do NOT add extra commentary beyond analyzing the text. If there are no vulnerabilities or sensitive data leaks, simply state "No sensitive data leaks found." Provide your analysis in English, clearly and concisely.
[/System note]
"""
    user_message = f"""[User message]
Below is the content of a PDF document:

--- PDF CONTENT START ---
{pdf_text}
--- PDF CONTENT END ---

Perform a thorough security analysis on the above text. Look specifically for any:
- Passwords, tokens, or API keys
- Personal identifiable information (PII)
- Hardcoded credentials
- Other sensitive secrets or data leaks

Also, assess whether sharing this document with third parties poses any security risks.
If you find any issues, explain them and suggest how to remove or mitigate. If none are found, say "No sensitive data leaks found."
[/User message]
"""
    prompt = system_instruction + "\n" + user_message
    response = llm.invoke(prompt)
    print("\n[/User message]\nHere is your analysis result:\n")
    print(response.strip())

if __name__ == "__main__":
    main()
