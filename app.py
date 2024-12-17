import os
import json
import requests
from datetime import datetime, timezone
import logging
import argparse

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class MyobClient:
    def __init__(self, client_id, access_token):
        self.client_id = client_id
        self.access_token = access_token
        
        self.session = requests.session()
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'x-myobapi-key': f'{self.client_id}',
            'x-myobapi-version': 'v2',
            'Content-Type': 'application/json'
        }
        self.session.headers.update(headers)
        self.api_url = self.session.request("GET", "https://api.myob.com/accountright/").json()[0]['Uri']
        logging.info(f"Using API URL: {self.api_url}")

    def _send_request(self, method, url, params={}, body={}):
        if 'filters' in params:
            filter_query_string = "&".join(['filters[{}]={}'.format(k,v) for k,v in params['filters'].items()])
        else: 
            filter_query_string = ""
            
        params.pop('filters', None)
        non_filter_query_string = '&'.join(['{}={}'.format(k,v) for k,v in params.items()])
        
        query_string = "&".join([filter_query_string, non_filter_query_string]).strip('&')

        message = url + query_string
        body_str = ""
        if body:
            body_str = json.dumps(body, separators=(',', ':'))
            message += body_str
            
        if query_string:
            url += '?' + query_string
            
        logging.info(f"Making {method} request to: {url}")
        response = self.session.request(method, url, data=body_str.encode())
        
        # Log response details
        logging.info(f"Response status code: {response.status_code}")
        if response.status_code != 200:
            logging.error(f"Response text: {response.text}")
        else:
            logging.info("Request successful")
            
        return response

    def get_invoices_between_dates(self, start_date, end_date):
        """
        Fetch all invoices between the given dates
        """
        url = f"{self.api_url}/Purchase/Bill"
        params = {
            '$filter': f"Date ge datetime'{start_date}T00:00:00' and Date le datetime'{end_date}T23:59:59'",
            '$orderby': 'Date desc'
        }
        
        logging.info(f"Searching for invoices between {start_date} and {end_date}")
        response = self._send_request("GET", url, params=params)
        
        if response.status_code != 200:
            logging.error("Failed to get invoices")
            return []
            
        data = response.json()
        invoices = data.get('Items', [])
        logging.info(f"Found {len(invoices)} invoices between {start_date} and {end_date}")
        return invoices

    def get_invoice_attachments(self, invoice_uid):
        """
        Get list of attachments for an invoice
        """
        logging.info(f"Getting attachments for invoice UID: {invoice_uid}")
        url = f"{self.api_url}/Purchase/Bill/Service/{invoice_uid}/Attachment"
        response = self._send_request("GET", url)
        
        if response.status_code != 200:
            logging.error("Failed to get attachments")
            return []
            
        data = response.json()
        return data.get('Attachments', [])

    def download_attachment(self, file_uri, save_path):
        """
        Download an attachment using its FileUri
        """
        logging.info(f"Downloading attachment from: {file_uri}")
        response = requests.get(file_uri)  # Using requests directly as no auth needed for S3 URL
        
        if response.status_code != 200:
            raise Exception(f"Failed to download attachment: {response.text}")
            
        # Save the PDF
        with open(save_path, 'wb') as f:
            f.write(response.content)
        logging.info(f"Successfully saved attachment to {save_path}")

def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Download MYOB invoice attachments')
    parser.add_argument('--myob-client-id', required=True, help='MYOB client ID')
    parser.add_argument('--myob-access-token', required=True, help='MYOB access token')
    parser.add_argument('--start-date', required=True, help='Start date in YYYY-MM-DD format')
    parser.add_argument('--end-date', required=True, help='End date in YYYY-MM-DD format')
    
    args = parser.parse_args()
    
    # Validate date formats
    try:
        datetime.strptime(args.start_date, '%Y-%m-%d')
        datetime.strptime(args.end_date, '%Y-%m-%d')
    except ValueError:
        logging.error("Dates must be in YYYY-MM-DD format")
        return
    
    # Create output directory
    output_dir = "invoice_pdfs"
    os.makedirs(output_dir, exist_ok=True)
    
    # Initialize MYOB client
    client = MyobClient(args.myob_client_id, args.myob_access_token)
    
    try:
        # Get all invoices between the specified dates
        invoices = client.get_invoices_between_dates(args.start_date, args.end_date)
        
        total_attachments = 0
        downloaded_attachments = 0
        
        for invoice in invoices:
            invoice_number = invoice.get("Number", "unknown")
            invoice_date = invoice.get("Date", "unknown")
            invoice_uid = invoice["UID"]
            
            logging.info(f"Processing invoice {invoice_number} from {invoice_date}")
            
            # Get attachments for this invoice
            attachments = client.get_invoice_attachments(invoice_uid)
            
            if attachments:
                total_attachments += len(attachments)
                logging.info(f"Found {len(attachments)} attachments for invoice {invoice_number}")
                
                for attachment in attachments:
                    file_uri = attachment.get("FileUri")
                    original_filename = attachment.get("OriginalFileName", "unknown.pdf")
                    
                    if file_uri:
                        # Create a filename that includes invoice date for better organization
                        invoice_date_str = datetime.strptime(invoice_date, "%Y-%m-%dT%H:%M:%S").strftime("%Y%m%d")
                        file_name = f"{output_dir}/invoice_{invoice_date_str}_{invoice_number}_{original_filename}"
                        
                        try:
                            client.download_attachment(file_uri, file_name)
                            downloaded_attachments += 1
                            logging.info(f"Successfully downloaded: {file_name}")
                        except Exception as e:
                            logging.error(f"Failed to download attachment for invoice {invoice_number}: {str(e)}")
                    else:
                        logging.error(f"No FileUri found in attachment data for invoice {invoice_number}")
            else:
                logging.info(f"No attachments found for invoice {invoice_number}")
        
        logging.info(f"Download complete. Found {total_attachments} attachments, successfully downloaded {downloaded_attachments}")
                        
    except Exception as e:
        logging.error(f"Error: {str(e)}")

if __name__ == "__main__":
    main()
