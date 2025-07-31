from typing import Any, List, Dict
import io
import csv
import ast

def _format_value(value: Any) -> str:
    """
    Formats a given value for CSV output. This function is hardened to handle
    cases where a list has been incorrectly converted to its string representation.
    """
    # Defensive check: if value is a string that LOOKS like a list, parse it back into one.
    if isinstance(value, str) and value.strip().startswith('[') and value.strip().endswith(']'):
        try:
            # Use ast.literal_eval for safely evaluating a string containing a Python literal.
            value = ast.literal_eval(value)
        except (ValueError, SyntaxError):
            # If parsing fails, fall back to returning the original string.
            return value

    if isinstance(value, list):
        if not value:
            return "Not Found"
        
        # Handle lists of dictionaries (like pricing tiers)
        if all(isinstance(item, dict) for item in value):
            formatted_items = []
            for item in value:
                item_str = ", ".join(
                    f"{k.replace('_', ' ').title()}: {v}" for k, v in item.items() if v
                )
                if item_str:
                    formatted_items.append(f"({item_str})")
            return " | ".join(formatted_items) if formatted_items else "Not Found"
        
        # Handle simple lists
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
