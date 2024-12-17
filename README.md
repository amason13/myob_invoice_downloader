# MYOB Invoice PDF Downloader

This script downloads PDF attachments from MYOB purchase invoices using the MYOB API.

## Setup

Install the required dependencies:
```bash
pip install -r requirements.txt
```

You will need:
1. MYOB Client ID - available in your MYOB developer portal
2. MYOB Access Token - obtained through the OAuth2 authentication process

## Usage

Run the script by providing your MYOB credentials and date range:
```bash
python app.py --myob-client-id YOUR_CLIENT_ID --myob-access-token YOUR_ACCESS_TOKEN --start-date 2024-01-01 --end-date 2024-12-31
```

Required arguments:
- `--myob-client-id`: Your MYOB client ID
- `--myob-access-token`: Your MYOB access token
- `--start-date`: Start date in YYYY-MM-DD format
- `--end-date`: End date in YYYY-MM-DD format

The script will:
1. Connect to MYOB using your credentials
2. Fetch all invoices between the specified dates
3. For each invoice:
   - Get attachment information
   - Download attachments using direct S3 URLs
   - Save to the `invoice_pdfs` directory
4. Provide a summary of downloaded attachments

Files are saved using the format:
`invoice_[YYYYMMDD]_[invoice_number]_[original_filename]`

For example:
`invoice_20241204_00006905_invoice-3405.pdf`

## Features

- Downloads attachments for invoices within specified date range
- Direct download of attachments using S3 pre-signed URLs
- Organized file naming with date prefixes
- Preservation of original filenames
- Detailed logging of the download process
- Summary statistics of found and downloaded attachments

## Logging

The script provides detailed logging information:
- Number of invoices found in the date range
- Attachments found per invoice
- Download status for each attachment
- Final summary of total attachments found and downloaded
- Any errors that occur during the process

## Troubleshooting

If you encounter issues:
1. Check that your access token is valid
2. Verify that there are invoices in the specified date range
3. Ensure you have write permissions in the output directory
4. Check the logs for detailed error messages

Common issues:
- "Authentication failed" - Your access token may be invalid
- "No invoices found" - Check the date range
- "Failed to download attachment" - The S3 URL may have expired (they typically expire after 30 minutes)
- "Dates must be in YYYY-MM-DD format" - Ensure dates are properly formatted

## MYOB API Documentation

For more information about the MYOB API and obtaining credentials, visit:
https://developer.myob.com/api/myob-business-api/api-overview/
