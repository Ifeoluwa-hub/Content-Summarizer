import numpy as np
import pandas as pd
from flask import Flask, jsonify, request, flash, redirect, _request_ctx_stack
from flask import request
import PyPDF2
import re
import requests
from bs4 import BeautifulSoup
import tiktoken
import openai
import tempfile
from getpass import getpass
import os
import urllib.request

# BeautifulSoupWebReader = download_loader("BeautifulSoupWebReader", custom_path='.')

os.environ["OPENAI_API_KEY"] = "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"
# openai_api_key = os.getenv("OPENAI_API_KEY")
app = Flask("content_based_summarizer")

# Set the secret key
app.secret_key = 'summarizer_123'

ALLOWED_EXTENSIONS = {'pdf', 'txt', 'docx'}

@app.route('/healthz', methods = ['GET'])
def health():
    return jsonify(
      application='Web-based Content Summarizer API',
      version='1.0.0',
      message= "endpoint working"
    )

@app.route("/get-summary", methods=["POST", "GET"])
def process():
    document = request.files.getlist('file')
    urls = request.form.getlist('url')

    temp_dir = tempfile.TemporaryDirectory()
    for doc in document:
        if doc:
            filename = doc.filename
            file_path = os.path.join(temp_dir.name, filename)
            doc.save(file_path)
            text=''
            # get content from pdf docs
            if doc.filename.rsplit('.', 1)[1].lower() == 'pdf':
                # creating a pdf file object
                pdfFileObj = open(file_path, 'rb')

                # creating a pdf reader object
                pdfReader = PyPDF2.PdfReader(pdfFileObj)

                start_page = 1
                for i in range(1,len(pdfReader.pages)):
                    pageObj = pdfReader.pages[i]
                    # extracting text from page
                    text=text+pageObj.extract_text()
                    text = re.sub('\n\n', ' ',  re.sub('\t', ' ' ,text))
                pdfFileObj.close()

            # get content from txt docs
            elif doc.filename.rsplit('.', 1)[1].lower() == 'txt':
                with open(file_path) as f:
                    contents = f.readlines()
                    text = ' '.join([str(elem) for elem in contents])
            
            enc = tiktoken.encoding_for_model("gpt-3.5-turbo")
            model_context_size = 15500
            text_max_length = model_context_size - len(enc.encode(text))
            full_text = enc.decode(enc.encode(text)[:text_max_length])

            instructPrompt = """
                        You are an expert content summarizer who is responsible for summarizing the content of documents. You just got the content from a document and want to share a
                        summary with your users. Please write a summary making sure to cover important aspects that were discussed and please keep it concise and friendly.
                        The content of the document is provided below.
                        """
            input = instructPrompt + full_text
            chatOutput = openai.ChatCompletion.create(model="gpt-3.5-turbo-16k",
                                            messages=[{"role": "system", "content": "You are a helpful assistant."},
                                                      {"role": "user", "content": input}
                                                      ], max_tokens=512
                                            )
            summary = chatOutput.choices[0].message.content   
            output = {'statusCode': 200,'summary': summary}
            print(output)
            return jsonify(output)
        else:
            print("A valid document is required")

# get content from web pages
    if urls != "":  
        # Send an HTTP GET request to the website
       for url in urls:
            response = requests.get(url)

            # Check if the request was successful (status code 200)
            if response.status_code == 200:
                # Parse the HTML content of the page
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Find and print the text content of all <p> tags on the page
                text = ''
                for paragraph in soup.find_all('p'):
                    text += paragraph.text 
            else:
                # If the request was not successful, print an error message
                print('Failed to retrieve the website content. Status code:', response.status_code)
                text = None
            text = re.sub('\n', ' ',  re.sub('\xa0', ' ' ,text))  

            enc = tiktoken.encoding_for_model("gpt-3.5-turbo")
            model_context_size = 15500
            text_max_length = model_context_size - len(enc.encode(text))
            full_text = enc.decode(enc.encode(text)[:text_max_length])

            instructPrompt = """
                        You are an expert content summarizer who is responsible for summarizing the content of documents. You just got the content from a document and want to share a
                        summary with your users. Please write a summary making sure to cover important aspects that were discussed and please keep it concise and friendly.
                        The content of the document is provided below.
                        """
            input = instructPrompt + full_text
            chatOutput = openai.ChatCompletion.create(model="gpt-3.5-turbo-16k",
                                            messages=[{"role": "system", "content": "You are a helpful assistant."},
                                                        {"role": "user", "content": input}
                                                        ], max_tokens=512
                                            )
            summary = chatOutput.choices[0].message.content   
            output = {'statusCode': 200,'summary': summary}
            print(output)
            return jsonify(output)
    else:
        pass

if __name__ == "__main__":
    print("starting app")
    app.debug = True
    app.run()