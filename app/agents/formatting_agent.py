from typing import Any, List, Dict
import io
import csv

def _format_value(value: Any) -> str:
    """
    Formats a given value for CSV output. Handles strings, lists, and lists of
    dictionaries in a simple, readable way.
    """
    if isinstance(value, list):
        if not value:
            return ""
        # If the list contains dictionaries, format them cleanly.
        if all(isinstance(i, dict) for i in value):
            return " | ".join(
                ", ".join(f"{k}: {v}" for k, v in item.items() if v)
                for item in value
            )
        # Otherwise, join the items of the list directly.
        return ", ".join(map(str, value))
    
    if value is None:
        return "Not Found"
    
    return str(value)

def _format_header(header: str) -> str:
    """Capitalizes and replaces underscores in the header."""
    return header.replace('_', ' ').title()

def format_data_as_csv(
    extracted_data: List[Dict[str, Any]],
    comparison_factors: List[str],
) -> str:
    """
    Formats the refined data into a CSV string. This agent is now a simple
    presenter of the clean data it receives.
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
            value = factors_dict.get(factor_name, "Not found")
            row_for_csv.append(_format_value(value))

        writer.writerow(row_for_csv)
        
    return output.getvalue()
