import json
import time
import requests
from pathlib import Path
import os
from dotenv import load_dotenv
load_dotenv()

def process_business_card(image_path):
    # Azure Form Recognizer configuration
    endpoint = os.getenv('AZURE_FORM_RECOGNIZER_ENDPOINT')
    api_key = os.getenv('AZURE_FORM_RECOGNIZER_KEY')
    
    if not endpoint or not api_key:
        return {"error": "Azure Form Recognizer configuration is missing. Please set AZURE_FORM_RECOGNIZER_ENDPOINT and AZURE_FORM_RECOGNIZER_KEY environment variables."}
    
    analyze_url = f"{endpoint}/formrecognizer/v2.1/prebuilt/businessCard/analyze"
    
    # Prepare headers and parameters
    headers = {
        'Content-Type': 'image/jpeg',
        'Ocp-Apim-Subscription-Key': api_key,
    }
    params = {
        "includeTextDetails": True
    }
    
    # Read image data
    try:
        with open(image_path, "rb") as image_file:
            image_data = image_file.read()
    except Exception as e:
        return {"error": f"Failed to read image file: {str(e)}"}
    
    # Submit the image for analysis
    try:
        response = requests.post(analyze_url, data=image_data, headers=headers, params=params)
        response.raise_for_status()  # Raise exception for HTTP errors
        
        # Get the operation URL to check status
        operation_url = response.headers["operation-location"]
        print(f"Analysis operation started. Waiting for results...")
        
        # Define a more efficient wait strategy
        max_retries = 5  # Reduced number of retries
        initial_wait = 2  # seconds - longer initial wait
        
        # Wait for the analysis to complete with exponential backoff
        for i in range(max_retries):
            # Calculate wait time with exponential backoff (10, 15, 22.5, 33.75, 50.6)
            wait_time = initial_wait * (1.5 ** i)
            
            print(f"Waiting {wait_time:.1f} seconds before checking status...")
            time.sleep(wait_time)
            
            # Check the status of the analysis
            status_response = requests.get(operation_url, headers={'Ocp-Apim-Subscription-Key': api_key})
            status_response.raise_for_status()
            
            result = status_response.json()
            status = result["status"]
            
            print(f"Analysis status: {status} (attempt {i+1}/{max_retries})")
            
            if status == "succeeded":
                return extract_business_card_data(result)
            elif status == "failed":
                raise Exception(f"Analysis failed: {result}")
        
        # If we've exhausted retries, return the raw result for debugging
        return {"error": "Analysis timed out after maximum retries", "raw_result": result}
        
    except requests.exceptions.RequestException as e:
        return {"error": f"Azure Form Recognizer API request failed: {str(e)}"}
    except Exception as e:
        return {"error": f"Unexpected error during Azure processing: {str(e)}"}

def extract_business_card_data(result):
    """
    Extract relevant business card data from Form Recognizer results
    
    Args:
        result (dict): Form Recognizer analysis result
    
    Returns:
        dict: Structured business card data with empty fields removed
    """
    try:
        # Get document results
        doc_results = result["analyzeResult"]["documentResults"][0]["fields"]
        
        # Prepare output structure
        business_card = {
            "entities": {
                "name": {},
                "jobTitle": [],
                "company": [],
                "address": [],
                "phone": [],
                "fax": [],
                "email": [],
                "website": []
            }
        }
        
        # Add raw text only if it exists and is not empty
        raw_text = result.get("analyzeResult", {}).get("readResults", [{}])[0].get("text", "")
        if raw_text.strip():
            business_card["raw_text"] = raw_text
        
        # Helper function to safely extract values
        def extract_value(field_obj):
            if "valueString" in field_obj:
                return field_obj["valueString"]
            elif "text" in field_obj:
                return field_obj["text"]
            elif "value" in field_obj:
                return field_obj["value"]
            return None
        
        # Extract contact name
        if "ContactNames" in doc_results and doc_results["ContactNames"].get("valueArray"):
            for contact in doc_results["ContactNames"]["valueArray"]:
                if "valueObject" in contact:
                    contact_obj = contact["valueObject"]
                    name_parts = {}
                    
                    if "FirstName" in contact_obj:
                        first_name = extract_value(contact_obj["FirstName"])
                        if first_name:
                            name_parts["firstName"] = first_name
                    
                    if "LastName" in contact_obj:
                        last_name = extract_value(contact_obj["LastName"])
                        if last_name:
                            name_parts["lastName"] = last_name
                    
                    if name_parts:  # Only add name if it has content
                        business_card["entities"]["name"] = name_parts
        
        # Extract job title
        if "JobTitles" in doc_results and doc_results["JobTitles"].get("valueArray"):
            for job in doc_results["JobTitles"]["valueArray"]:
                job_title = extract_value(job)
                if job_title:
                    business_card["entities"]["jobTitle"].append(job_title)
        
        # Extract company name
        if "CompanyNames" in doc_results and doc_results["CompanyNames"].get("valueArray"):
            for company in doc_results["CompanyNames"]["valueArray"]:
                company_name = extract_value(company)
                if company_name:
                    business_card["entities"]["company"].append(company_name)
        
        # Extract address
        if "Addresses" in doc_results and doc_results["Addresses"].get("valueArray"):
            for address in doc_results["Addresses"]["valueArray"]:
                address_text = extract_value(address)
                if address_text:
                    business_card["entities"]["address"].append(address_text)
        
        # Extract phone numbers
        if "OtherPhones" in doc_results and doc_results["OtherPhones"].get("valueArray"):
            for phone in doc_results["OtherPhones"]["valueArray"]:
                phone_number = extract_value(phone)
                if phone_number:
                    business_card["entities"]["phone"].append(phone_number)
        
        # Extract fax numbers
        if "Faxes" in doc_results and doc_results["Faxes"].get("valueArray"):
            for fax in doc_results["Faxes"]["valueArray"]:
                fax_number = extract_value(fax)
                if fax_number:
                    business_card["entities"]["fax"].append(fax_number)
        
        # Extract emails
        if "Emails" in doc_results and doc_results["Emails"].get("valueArray"):
            for email in doc_results["Emails"]["valueArray"]:
                email_address = extract_value(email)
                if email_address:
                    business_card["entities"]["email"].append(email_address)
        
        # Extract websites
        if "Websites" in doc_results and doc_results["Websites"].get("valueArray"):
            for website in doc_results["Websites"]["valueArray"]:
                website_url = extract_value(website)
                if website_url:
                    business_card["entities"]["website"].append(website_url)
        
        # Remove empty fields from entities
        business_card["entities"] = {
            k: v for k, v in business_card["entities"].items()
            if (isinstance(v, list) and v) or (isinstance(v, dict) and v)
        }
        
        # If entities is empty, remove it
        if not business_card["entities"]:
            del business_card["entities"]
        
        return business_card
    
    except Exception as e:
        # If there's an error in extraction, return the error and the raw result for debugging
        return {
            "error": str(e),
            "raw_result": result
        }
