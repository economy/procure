from typing import Any, List, Dict
import io
import csv

def _format_value(value: Any) -> str:
    """
    Formats a given value for CSV output. If the value is a list of dicts,
    it dynamically formats it into a human-readable string.
    Otherwise, it just converts the value to a string.
    """
    if isinstance(value, list):
        # If the list contains dictionaries, extract their values.
        if all(isinstance(i, dict) for i in value):
            # Assumes the dictionaries have a consistent, single value worth showing.
            # This is a simplification based on the desired output.
            processed_items = [str(next(iter(i.values()), '')) for i in value]
            return ", ".join(filter(None, processed_items))
        # Otherwise, join the items of the list directly.
        return ", ".join(map(str, value))
    
    if value is None:
        return "Not found"
    
    return str(value)

def _format_header(header: str, max_length: int = 25) -> str:
    """Capitalizes and replaces underscores in the header."""
    return header.replace('_', ' ').title()

def format_data_as_csv(
    extracted_data: List[Dict[str, Any]],
    comparison_factors: List[str],
) -> str:
    """
    Formats the extracted data into a CSV string, intelligently handling
    complex data structures like lists of pricing tiers.
    """
    unique_factors = sorted(list(set(factor for factor in comparison_factors)))
    
    output = io.StringIO()
    
    fieldnames = ['product_name'] + [_format_header(f) for f in unique_factors]
    writer = csv.writer(output)
    writer.writerow(fieldnames)

    for item in extracted_data:
        product_name = item.get('product_name', 'N/A')
        
        factors_dict = {
            factor['name']: factor['value']
            for factor in item.get('extracted_factors', [])
            if 'name' in factor
        }

        row_for_csv = [product_name]
        for factor_name in unique_factors:
            value = factors_dict.get(factor_name, 'Not found')
            row_for_csv.append(_format_value(value))

        writer.writerow(row_for_csv)
        
    return output.getvalue()
