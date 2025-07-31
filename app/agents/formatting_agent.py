from typing import Any, List, Dict
import io
import csv
import ast

def _format_value(value: Any) -> str:
    """
    Formats a given value for CSV output. This function is hardened to handle
    cases where a list has been incorrectly converted to its string representation,
    and it now formats lists of dictionaries with line breaks for readability.
    """
    if isinstance(value, str) and value.strip().startswith('[') and value.strip().endswith(']'):
        try:
            value = ast.literal_eval(value)
        except (ValueError, SyntaxError):
            return value

    if isinstance(value, list):
        if not value:
            return "Not Found"
        
        if all(isinstance(item, dict) for item in value):
            formatted_items = []
            for item in value:
                # Use a consistent tier name key, default to 'Name'
                tier_name = item.pop('tier_name', item.pop('name', 'Tier'))
                # Format remaining key-value pairs
                details = ", ".join(
                    f"{k.replace('_', ' ').title()}: {v}" for k, v in item.items() if v
                )
                formatted_items.append(f"**{tier_name}**: {details}")
            # Join with newlines for clear, readable table cells
            return "\n".join(formatted_items) if formatted_items else "Not Found"
        
        return ", ".join(map(str, value))
    
    if value is None:
        return "Not Found"
    
    return str(value)

def _format_header(header: str) -> str:
    """Formats headers for display."""
    if header.lower() == 'product_name':
        return 'Name'
    return header.replace('_', ' ').title()

def format_data_as_csv(
    extracted_data: List[Dict[str, Any]],
    comparison_factors: List[str],
) -> str:
    """
    Formats the refined data into a CSV string.
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
