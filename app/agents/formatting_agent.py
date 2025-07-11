from typing import Any
import io
import csv

def _format_header(header: str, max_length: int = 20) -> str:
    """Capitalizes, replaces underscores, and truncates the header."""
    formatted = header.replace('_', ' ').title()
    if len(formatted) > max_length:
        return formatted[:max_length - 3] + '...'
    return formatted

def format_data_as_csv(
    extracted_data: list[dict[str, Any]],
    comparison_factors: list[str],
) -> str:
    """
    Formats the extracted data into a CSV string.

    This is a pure Python function for deterministic and reliable formatting.
    """
    # Use a set for unique, sorted, lower-cased comparison factors for the header
    unique_factors = sorted(list(set(factor.lower() for factor in comparison_factors)))
    
    output = io.StringIO()
    # Format headers for display
    formatted_headers = {f: _format_header(f) for f in unique_factors}
    
    fieldnames = ['product_name'] + [formatted_headers[f] for f in unique_factors]
    writer = csv.writer(output)
    writer.writerow(fieldnames)

    # Create a mapping from original factor name to formatted header
    factor_to_header_map = {f.lower(): formatted_headers[f.lower()] for f in comparison_factors}

    for item in extracted_data:
        # Each 'item' is a dict that looks like:
        # {'product_name': '...', 'extracted_factors': [{'name': '...', 'value': '...'}]}
        
        product_name = item.get('product_name', 'N/A')
        
        # Create a lookup from the list of extracted factors
        factors_dict = {
            factor['name'].lower(): factor['value']
            for factor in item.get('extracted_factors', [])
            if 'name' in factor # Ensure the factor has a name
        }

        # Build the row for the CSV
        row_for_csv = [product_name]
        for factor_header in unique_factors:
             # Get the value using the original, unformatted factor name
            row_for_csv.append(factors_dict.get(factor_header, 'Not found'))

        writer.writerow(row_for_csv)
        
    return output.getvalue() 