#!/usr/bin/env python
# coding: utf-8

import numpy as np
import pandas as pd
import cv2
import pytesseract
from glob import glob
import spacy
import re
import string
import warnings
warnings.filterwarnings('ignore')
import json

from PIL import Image

### Load NER model
model_ner = spacy.load('./models/model-best/')


def cleanText(txt):
    whitespace = string.whitespace
    punctuation = "!#$%&\'()*+:;<=>?[\\]^`{|}~"
    tableWhitespace = str.maketrans('','',whitespace)
    tablePunctuation = str.maketrans('','',punctuation)
    text = str(txt)
    #text = text.lower()
    removewhitespace = text.translate(tableWhitespace)
    removepunctuation = removewhitespace.translate(tablePunctuation)
    
    return str(removepunctuation)

# group the label
class groupgen():
    def __init__(self):
        self.id = 0
        self.text = ''
        
    def getgroup(self,text):
        if self.text == text:
            return self.id
        else:
            self.id +=1
            self.text = text
            return self.id
        


def parser(text,label):
    if label == 'PHONE':
        text = text.lower()
        text = re.sub(r'\D','',text)
        
    elif label == 'EMAIL':
        text = text.lower()
        allow_special_char = '@_.\-'
        text = re.sub(r'[^A-Za-z0-9{} ]'.format(allow_special_char),'',text)
        
    elif label == 'WEB':
        text = text.lower()
        allow_special_char = ':/.%#\-'
        text = re.sub(r'[^A-Za-z0-9{} ]'.format(allow_special_char),'',text)
        
    elif label in ('NAME', 'DES'):
        text = text.lower()
        text = re.sub(r'[^a-z ]','',text)
        text = text.title()
        
    elif label == 'ORG':
        text = text.lower()
        text = re.sub(r'[^a-z0-9 ]','',text)
        text = text.title()
        
    return text



grp_gen = groupgen()

def getPredictions(image):
    try:
        # extract data using Pytesseract 
        tessData = pytesseract.image_to_data(image)
        # convert into dataframe
        tessList = list(map(lambda x:x.split('\t'), tessData.split('\n')))
        df = pd.DataFrame(tessList[1:],columns=tessList[0])
        df.dropna(inplace=True) # drop missing values
        df['text'] = df['text'].apply(cleanText)

        # convet data into content
        df_clean = df.query('text != "" ')
        content = " ".join([w for w in df_clean['text']])
        print(content)
        # get prediction from NER model
        doc = model_ner(content)

        # converting doc in json
        docjson = doc.to_json()
        doc_text = docjson['text']

        # creating tokens
        datafram_tokens = pd.DataFrame(docjson['tokens'])
        
        # Check if there are any tokens
        if len(datafram_tokens) == 0:
            return image.copy(), {"ERROR": "No text detected in the image"}

        datafram_tokens['token'] = datafram_tokens[['start','end']].apply(
            lambda x:doc_text[x[0]:x[1]] , axis = 1)

        # Check if there are any entities detected
        if 'ents' not in docjson or len(docjson['ents']) == 0:
            return image.copy(), {"ERROR": "No entities detected in the image"}
            
        # Safely create the right table with entities
        try:
            right_table = pd.DataFrame(docjson['ents'])[['start','label']]
            datafram_tokens = pd.merge(datafram_tokens, right_table, how='left', on='start')
            datafram_tokens.fillna('O', inplace=True)
        except KeyError as e:
            # Handle missing columns in ents dataframe
            print(f"KeyError in entities processing: {str(e)}")
            return image.copy(), {"ERROR": f"Missing data in entity extraction: {str(e)}"}

        # join lable to df_clean dataframe
        df_clean['end'] = df_clean['text'].apply(lambda x: len(x)+1).cumsum() - 1 
        df_clean['start'] = df_clean[['text','end']].apply(lambda x: x[1] - len(x[0]),axis=1)

        # inner join with start 
        try:
            dataframe_info = pd.merge(df_clean, datafram_tokens[['start','token','label']], how='inner', on='start')
        except KeyError as e:
            # Handle missing columns in tokens dataframe
            print(f"KeyError in dataframe merge: {str(e)}")
            return image.copy(), {"ERROR": f"Failed to merge data: {str(e)}"}

        # Bounding Box
        bb_df = dataframe_info.query("label != 'O' ")
        
        # If no entities with bounding boxes were found
        if len(bb_df) == 0:
            return image.copy(), {"ERROR": "No entities with bounding boxes detected"}

        bb_df['label'] = bb_df['label'].apply(lambda x: x[2:])
        bb_df['group'] = bb_df['label'].apply(grp_gen.getgroup)

        # right and bottom of bounding box
        try:
            bb_df[['left','top','width','height']] = bb_df[['left','top','width','height']].astype(int)
            bb_df['right'] = bb_df['left'] + bb_df['width']
            bb_df['bottom'] = bb_df['top'] + bb_df['height']
        except KeyError as e:
            # Handle missing columns in bb_df
            print(f"KeyError in bounding box processing: {str(e)}")
            return image.copy(), {"ERROR": f"Missing bounding box data: {str(e)}"}

        # tagging: groupby group
        col_group = ['left','top','right','bottom','label','token','group']
        group_tag_img = bb_df[col_group].groupby(by='group')
        img_tagging = group_tag_img.agg({
            'left':min,
            'right':max,
            'top':min,
            'bottom':max,
            'label':np.unique,
            'token':lambda x: " ".join(x)
        })

        img_bb = image.copy()
        for l,r,t,b,label,token in img_tagging.values:
            cv2.rectangle(img_bb,(l,t),(r,b),(0,255,0),2)
            # Convert label to string and ensure it's not None
            label_str = str(label) if label is not None else ""
            cv2.putText(img_bb, label_str, (l,t), cv2.FONT_HERSHEY_PLAIN, 1, (255,0,255), 2)

        # Entities
        info_array = dataframe_info[['token','label']].values
        entities = dict(NAME=[],ORG=[],DES=[],PHONE=[],EMAIL=[],WEB=[])
        previous = 'O'

        for token, label in info_array:
            bio_tag = label[0]
            label_tag = label[2:]

            # step -1 parse the token
            text = parser(token,label_tag)

            if bio_tag in ('B','I'):
                if previous != label_tag:
                    entities[label_tag].append(text)
                else:
                    if bio_tag == "B":
                        entities[label_tag].append(text)
                    else:
                        if label_tag in ("NAME",'ORG','DES'):
                            entities[label_tag][-1] = entities[label_tag][-1] + " " + text
                        else:
                            entities[label_tag][-1] = entities[label_tag][-1] + text
            previous = label_tag
            
        return img_bb, entities
        
    except KeyError as e:
        # Catch any other KeyError that might occur
        print(f"KeyError in getPredictions: {str(e)}")
        return image.copy(), {"ERROR": f"Data extraction error: {str(e)}"}
    except Exception as e:
        # Catch any other exceptions
        print(f"Exception in getPredictions: {str(e)}")
        return image.copy(), {"ERROR": f"Processing error: {str(e)}"}


def extract_json_response(input_text):
    """
    Extracts the JSON object from the assistant response and formats it
    with arrays on single lines.
    """
    # Pattern to match JSON object in the assistant's response
    pattern = r'assistant\s*\n\s*(\{[\s\S]*?\})'
    
    # Find the match
    match = re.search(pattern, input_text)
    
    if match:
        json_str = match.group(1)
        
        # Clean up the extracted JSON string
        json_str = json_str.strip()
        
        # Parse the JSON
        try:
            parsed_json = json.loads(json_str)
            
            # Create a custom formatted output
            result = "{\n"
            keys = list(parsed_json.keys())
            
            for i, key in enumerate(keys):
                values = parsed_json[key]
                
                # Format the array of values on a single line
                values_str = json.dumps(values)
                
                # Add to the result
                result += f'  "{key}": {values_str}'
                
                # Add comma if not the last item
                if i < len(keys) - 1:
                    result += ","
                
                result += "\n"
            
            result += "}"
            
            return result
            
        except json.JSONDecodeError:
            return json_str
    else:
        return "No JSON found in the assistant response"