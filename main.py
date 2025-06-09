
# LAST WORKING

import requests
from bs4 import BeautifulSoup
import json
import html
import re

# Removed parse_sx_prop_string and parse_jsx_element as they are not needed
# when scraping rendered HTML directly for AssociatedClasses and InferredProps.

def infer_props_from_classes(component_name, class_list):
    """
    Infers common Material UI component props (variant, color, disabled, size)
    based on the presence of specific CSS classes. This function is
    extensible for different component types.

    Args:
        component_name (str): The name of the Material UI component (e.g., 'Button').
        class_list (list): A list of CSS class names found on the rendered element.

    Returns:
        dict: A dictionary of inferred properties.
    """
    inferred_props = {}
    class_str = " ".join(class_list) # Convert list to string for easier searching

    if component_name.lower() == "button":
        # Infer variant
        if "MuiButton-contained" in class_str:
            inferred_props["variant"] = "contained"
        elif "MuiButton-outlined" in class_str:
            inferred_props["variant"] = "outlined"
        else: # Default is text if neither contained nor outlined
            inferred_props["variant"] = "text"

        # Infer color
        if "MuiButton-colorPrimary" in class_str:
            inferred_props["color"] = "primary"
        elif "MuiButton-colorSecondary" in class_str:
            inferred_props["color"] = "secondary"
        elif "MuiButton-colorError" in class_str:
            inferred_props["color"] = "error"
        elif "MuiButton-colorInfo" in class_str:
            inferred_props["color"] = "info"
        elif "MuiButton-colorSuccess" in class_str:
            inferred_props["color"] = "success"
        elif "MuiButton-colorWarning" in class_str:
            inferred_props["color"] = "warning"
        elif "MuiButton-colorInherit" in class_str:
            inferred_props["color"] = "inherit"

        # Infer size
        if "MuiButton-sizeSmall" in class_str:
            inferred_props["size"] = "small"
        elif "MuiButton-sizeLarge" in class_str:
            inferred_props["size"] = "large"
        else: # Default is medium
            inferred_props["size"] = "medium"

        # Infer disabled state
        if "Mui-disabled" in class_str:
            inferred_props["disabled"] = "true" # Store as string for consistency with other props
    
    # Add similar blocks for other components as needed (e.g., if component_name.lower() == "card":)
    # elif component_name.lower() == "card":
    #     if "MuiCard-elevation1" in class_str: inferred_props["elevation"] = "1"
    #     if "MuiCard-elevation8" in class_str: inferred_props["elevation"] = "8"

    return inferred_props

def scrape_mui_demo_variations(component_name):
    """
    Scrapes the Material UI demo page for a given component
    and extracts rendered component variations, their classes,
    and inferred properties. This version focuses on directly
    scraping the rendered HTML elements.

    Args:
        component_name (str): The name of the Material UI component
                              (e.g., 'button', 'card').

    Returns:
        list: A list of dictionaries, each representing a component variation.
              Returns an empty list on error or if no variations are found.
    """
    demo_url = f"https://mui.com/material-ui/react-{component_name.lower()}/"
    print(f"\nAttempting to scrape demo page: {demo_url}")

    try:
        response = requests.get(demo_url)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching demo page {demo_url}: {e}")
        return []

    soup = BeautifulSoup(response.text, 'html.parser')
    component_variations = []

    # General approach: Find elements with the root Material UI class for the component.
    # E.g., for "Button", look for elements with class "MuiButton-root".
    generic_mui_root_class = f"Mui{component_name}-root"
    
    # Find all elements on the page that have this root class.
    # This will capture all instances of the component rendered in the demos.
    rendered_elements_in_demos = soup.find_all(class_=lambda x: x and generic_mui_root_class in x)
    
    if not rendered_elements_in_demos:
        print(f"No rendered '{component_name}' elements with class '{generic_mui_root_class}' found on the demo page.")
        return []

    print(f"Found {len(rendered_elements_in_demos)} rendered '{component_name}' elements. Processing...")

    for i, element in enumerate(rendered_elements_in_demos):
        class_names = element.get('class', [])
        variation_text = element.get_text(strip=True)

        if not variation_text:
            # Attempt to get text from potential child spans/labels common in MUI
            inner_label_span = element.find('span', class_=lambda x: x and ('MuiButton-label' in x or 'MuiTypography-root' in x))
            if inner_label_span:
                variation_text = inner_label_span.get_text(strip=True)

        if not variation_text and "MuiIconButton-root" in class_names:
            # For icon buttons, text might be empty, use a placeholder or icon name
            variation_text = "Icon Button"
        elif not variation_text: # Generic fallback if still no text
            variation_text = f"{component_name} Demo {i+1}"


        # Infer props from the collected class names
        inferred_props = infer_props_from_classes(component_name, class_names)
        
        # Add any direct HTML attributes as props (e.g., 'variant', 'color', 'size' might be direct on some elements)
        # These override inferred props if present, as they are explicit.
        if element.get('variant'):
            inferred_props['variant'] = element.get('variant')
        if element.get('color'):
            inferred_props['color'] = element.get('color')
        if element.get('size'):
            inferred_props['size'] = element.get('size')
        if element.get('disabled') is not None: # Check if 'disabled' attribute exists
             inferred_props['disabled'] = str(element.get('disabled')).lower()


        variation_data = {
            "VariationName": variation_text,
            "RawJSXCode": "", # Not available when scraping rendered HTML directly
            "AssociatedClasses": class_names,
            "InferredProps": inferred_props,
            "ParsedComponent": { # This will be basic as we're not parsing JSX from textareas
                "ComponentName": component_name,
                "Props": {}, # We cannot infer specific JSX props here like 'sx'
                "InnerText": variation_text,
                "Children": [], # Not inferring complex children hierarchy from rendered HTML
                "RawInlineStyleRules": {} # Not extracting raw inline styles from HTML 'style' attribute here
            }
        }
        component_variations.append(variation_data)
            
    return component_variations

def scrape_mui_component_api(component_name):
    """
    Scrapes the Material UI API documentation page for a given component
    and extracts its properties (props), types, default values, and CSS classes,
    and also gathers demo variations.

    Args:
        component_name (str): The name of the Material UI component
                              (e.g., 'button', 'card', 'typography').

    Returns:
        dict: A dictionary mimicking the MaterialComponentDefinition structure,
              populated with scraped data. Returns None on error.
    """
    # Construct the API documentation URL for the specific component's API page
    # Example: https://mui.com/material-ui/api/button/
    api_url = f"https://mui.com/material-ui/api/{component_name.lower()}/"
    print(f"Attempting to scrape API page: {api_url}")

    try:
        response = requests.get(api_url)
        response.raise_for_status() # Raise an exception for HTTP errors (4xx or 5xx)
    except requests.exceptions.RequestException as e:
        print(f"Error fetching API page {api_url}: {e}")
        return None

    soup = BeautifulSoup(response.text, 'html.parser')

    # --- 1. Extract Component Name ---
    # The h1 tag typically contains the component name followed by " API"
    title_tag = soup.find('h1')
    extracted_component_name = component_name # Default to input name
    if title_tag and " API" in title_tag.get_text():
        # Clean the title to get just the component name
        extracted_component_name = title_tag.get_text().replace(" API", "").strip()
    print(f"Extracted Component Name: {extracted_component_name}")

    # --- 2. Extract Properties (Props Table) using specific 'id' pattern ---
    props = {}
    # The IDs for prop rows follow a pattern: [component-name]-prop-[prop-name]
    # For example, for "Button", we look for "button-prop-"
    prop_id_prefix = f"{extracted_component_name.lower()}-prop-"

    print(f"\nSearching for prop rows with ID prefix: '{prop_id_prefix}'")
    prop_rows = soup.find_all('tr', id=lambda x: x and x.startswith(prop_id_prefix))

    if prop_rows:
        print(f"Found {len(prop_rows)} prop rows. Extracting data...")
        for row in prop_rows:
            prop_name = row['id'].replace(prop_id_prefix, '')
            cols = row.find_all(['th', 'td']) # Use th for name and td for others

            if len(cols) >= 4:
                prop_type = cols[1].get_text(strip=True)
                prop_default = cols[2].get_text(strip=True)
                prop_description = cols[3].get_text(strip=True)

                props[prop_name] = {
                    "type": prop_type,
                    "default": prop_default,
                    "description": prop_description
                }
            else:
                print(f"Skipping malformed prop row (not enough columns): {row.get_text(strip=True)}")
    else:
        print(f"Could not find any prop rows with ID prefix '{prop_id_prefix}' on the API page.")

    # --- 3. Extract CSS Classes using specific 'id' pattern ---
    css_classes = []
    # The IDs for class rows follow a pattern: [component-name]-classes-[class-name]
    # For example, for "Button", we look for "button-classes-"
    class_id_prefix = f"{extracted_component_name.lower()}-classes-"

    print(f"\nSearching for CSS class rows with ID prefix: '{class_id_prefix}'")
    class_rows = soup.find_all('tr', id=lambda x: x and x.startswith(class_id_prefix))

    if class_rows:
        print(f"Found {len(class_rows)} CSS class rows. Extracting data...")
        for row in class_rows:
            cols = row.find_all('td')

            if len(cols) >= 3: # Expect at least Class name, Rule name, and Description
                full_class_name_td = cols[0]
                rule_name_td = cols[1]
                description_td = cols[2]

                full_class_name = full_class_name_td.get_text(strip=True)

                rule_name_span = rule_name_td.find('span')
                rule_name = rule_name_span.get_text(strip=True) if rule_name_span else ""

                description = description_td.get_text(strip=True)

                css_classes.append({
                    "className": full_class_name,
                    "ruleName": rule_name,
                    "description": description
                })
            else:
                print(f"Skipping malformed CSS class row (not enough columns): {row.get_text(strip=True)}")
    else:
        print(f"Could not find any CSS class rows with ID prefix '{class_id_prefix}' on the API page.")

    # --- 4. Scrape Demo Variations ---
    # Call the new function to scrape the demo page
    component_variations = scrape_mui_demo_variations(extracted_component_name)


    # --- Construct the MaterialComponentDefinition JSON ---
    # RawInlineStyleRules is now handled within ComponentVariations->InferredProps (from CSS classes)
    # Children and InnerText are only inferred for the demo variations now, not a general component property.
    material_component_definition = {
        "ComponentName": extracted_component_name,
        "Properties": props,
        "CssClasses": css_classes,
        "ComponentVariations": component_variations, # Populated with AssociatedClasses and InferredProps
        "Children": [], # This refers to general nesting rules, not scraped from specific demos
        "RawInlineStyleRules": {}, # Placeholder, actual raw styles are now within InferredProps or from JSX if we re-introduce that level of parsing.
        "InnerText": "" # General inner text for the component type, not specific demo text
    }

    return material_component_definition

# --- Example Usage ---
# Scrape the Material UI Button component API page and its demo variations
# To scrape a different component, just change the string here!
component_to_scrape = "Button" # Example: "Card", "Typography", "Switch", etc.

full_component_json_ast = scrape_mui_component_api(component_to_scrape)

if full_component_json_ast:
    print(f"\n--- Generated JSON AST for {component_to_scrape} Component ---")
    print(json.dumps(full_component_json_ast, indent=2))

    # --- Save to JSON file ---
    output_filename = f"{component_to_scrape.lower()}_full_details.json"
    try:
        with open(output_filename, 'w', encoding='utf-8') as f:
            json.dump(full_component_json_ast, f, indent=2, ensure_ascii=False)
        print(f"\nSuccessfully saved scraped data to {output_filename}")
    except IOError as e:
        print(f"Error saving data to file {output_filename}: {e}")


# LAST WORKING ENDS HERE