from typing import Any
import io
import csv

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
    fieldnames = ['product_name'] + unique_factors
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    
    writer.writeheader()

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
        row_for_csv = {'product_name': product_name}
        for factor_header in unique_factors:
            row_for_csv[factor_header] = factors_dict.get(factor_header, 'Not found')

        writer.writerow(row_for_csv)
        
    return output.getvalue() 