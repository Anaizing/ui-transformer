import requests
from bs4 import BeautifulSoup
import json
import html
import re
import sys # Import the sys module to access command-line arguments

def parse_sx_prop_string(sx_prop_raw_value):
    """
    Attempts to parse a simple JavaScript object string from an 'sx' prop
    into a Python dictionary of CSS-like rules.
    This is a highly simplified parser and will NOT handle:
    - Nested objects (e.g., '&:hover: { ... }')
    - Theme functions (e.g., theme => ({ ... }))
    - Arrays (e.g., [{...}, {...}])
    - Shorthand CSS properties (e.g., 'p' for padding)

    It expects a simple object literal like: "{ color: 'red', margin: '8px' }"

    Args:
        sx_prop_raw_value (str): The raw string content of the 'sx' prop (e.g., "{ color: 'red', mb: 2 }").

    Returns:
        dict: A dictionary of parsed CSS properties.
    """
    styles = {}
    if not sx_prop_raw_value or not sx_prop_raw_value.strip().startswith('{'):
        return styles

    # Remove outer braces and strip whitespace
    content = sx_prop_raw_value.strip()[1:-1].strip()
    
    # Regex to find key-value pairs:
    # Captures: key (alphanumeric, $, _, -), value (quoted string OR non-curly, non-comma, non-brace sequence)
    # The `(?!\s*\{)` negative lookahead prevents matching nested object keys as top-level.
    prop_value_pattern = re.compile(r'\s*([a-zA-Z0-9$_-]+)\s*:\s*(["\']?(?:(?!\s*\{)[^"\'{,}]*?)["\']?)\s*(?:,|$|\n)')

    # Iterate through potential key-value pairs
    for match in prop_value_pattern.finditer(content):
        prop_name = match.group(1).strip()
        prop_value = match.group(2).strip().strip("'\"") # Remove quotes if present

        styles[prop_name] = prop_value
    
    return styles


def parse_jsx_element(jsx_string):
    """
    Parses a single top-level JSX element string to extract its component name,
    props, inner text, and immediate children (recursively parsed).
    This is still a simplified regex-based parser, not a full AST parser.
    It attempts to handle basic nesting for children.

    Args:
        jsx_string (str): A string containing a single JSX component (e.g., '<Button variant="contained">Click Me</Button>').

    Returns:
        dict: A dictionary representing the parsed component, including:
            - ComponentName (str)
            - Props (dict)
            - InnerText (str)
            - Children (list of parsed component dicts)
            - RawInlineStyleRules (dict, for parsed 'sx' prop)
    """
    props = {}
    children = []
    raw_inline_style_rules = {}

    # Regex to find attributes:
    # Group 1: prop name (word characters, including hyphens for style props like 'aria-label')
    # Group 2: quoted string value (double)
    # Group 3: quoted string value (single)
    # Group 4: curly brace content that might contain nested braces (complex JS object or expression)
    # Group 5: simple unquoted value
    attr_pattern = re.compile(r'([\w-]+)=(?:"([^"]*)"|\'([^\']*)\'|{((?:[^}{]*\{[^}{]*\})+[^}]*|[^}]*)}|([^\s>]+))')


    # Find the main component tag, e.g., <Button ...>
    # Group 1: Component name, Group 2: Attributes string, Group 3: Inner content (for non-self-closing tags)
    match = re.search(r'<\s*(\w+)([^>]*?)(?:/>|>([\s\S]*?)<\/\1>)?', jsx_string, re.DOTALL)

    if not match:
        return {
            "ComponentName": None,
            "Props": {},
            "InnerText": "",
            "Children": [],
            "RawInlineStyleRules": {}
        }

    component_tag_name = match.group(1)
    attributes_str = match.group(2)
    inner_content = match.group(3)

    props['componentTag'] = component_tag_name # Store the actual tag name

    # Extract props from attributes string
    for prop_match in attr_pattern.finditer(attributes_str):
        prop_name = prop_match.group(1)
        # Prioritize double quotes, then single quotes, then complex curly (group 4), then simple curly (group 5), then direct value
        prop_value = (prop_match.group(2) or
                      prop_match.group(3) or
                      prop_match.group(4) or # For { ... } or { { ... } }
                      prop_match.group(5) or
                      prop_match.group(6))
        
        if prop_name and prop_value is not None:
            # Clean up boolean props
            if prop_value.lower() == 'true':
                props[prop_name] = 'true'
            elif prop_value.lower() == 'false':
                props[prop_name] = 'false'
            elif prop_name == 'sx':
                # Attempt to parse the sx prop content
                parsed_sx = parse_sx_prop_string(prop_value.strip())
                raw_inline_style_rules.update(parsed_sx)
            elif prop_name == 'style': # Direct HTML style attribute (less common in MUI JSX demos)
                style_pairs = prop_value.strip().split(';')
                for pair in style_pairs:
                    if ':' in pair:
                        style_prop, style_val = pair.split(':', 1)
                        raw_inline_style_rules[style_prop.strip()] = style_val.strip()
            else:
                props[prop_name] = prop_value.strip() # Remove any whitespace

    # Extract inner text content or immediate children JSX
    if inner_content:
        inner_content = inner_content.strip()
        # Heuristic to distinguish between plain text and child JSX
        # If it contains an opening JSX tag, assume it has children components
        if re.search(r'<\s*\w+', inner_content):
            # Try to split into top-level child JSX components. This is still
            # a major simplification and won't handle deeply nested or complex JSX.
            # It looks for patterns like <Tag ...> or <Tag .../>
            # This regex is an attempt to find top-level JSX tags and their content.
            # It's highly sensitive to content within curly braces if they contain JSX.
            child_jsx_matches = re.finditer(r'(<\s*\w+[^>]*?\/>|<\s*\w+[^>]*?>[\s\S]*?<\/\s*\w+\s*>)', inner_content, re.DOTALL)
            
            last_end = 0
            has_jsx_children = False
            for child_match in child_jsx_matches:
                has_jsx_children = True
                # Capture text before this child JSX element
                pre_text = inner_content[last_end:child_match.start()].strip()
                if pre_text:
                    children.append({"ComponentName": "#text", "Props": {"innerText": pre_text}, "Children": [], "RawInlineStyleRules": {}})
                
                # Recursively parse the child JSX
                parsed_child = parse_jsx_element(child_match.group(0))
                if parsed_child['ComponentName']: # Only add if successfully parsed
                    children.append(parsed_child)
                last_end = child_match.end()
            
            # Capture any remaining text after the last child JSX element
            post_text = inner_content[last_end:].strip()
            if post_text:
                children.append({"ComponentName": "#text", "Props": {"innerText": post_text}, "Children": [], "RawInlineStyleRules": {}})

            # If no JSX children were found by regex, but inner content exists, treat as innerText
            if not has_jsx_children and inner_content: # Only if regex failed to find any JSX children
                 props['innerText'] = inner_content
        else:
            props['innerText'] = inner_content # It's plain text

    # Special handling for components like IconButton which might have no direct text but an icon child
    if component_tag_name == "IconButton" and not props.get('innerText') and not children:
        props['innerText'] = "Icon" # Placeholder for icon component

    return {
        "ComponentName": component_tag_name,
        "Props": props,
        "InnerText": props.pop('innerText', "") , # Move innerText from props to top-level
        "Children": children,
        "RawInlineStyleRules": raw_inline_style_rules
    }

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
        
        # Infer loading state (e.g., from a 'loading' class or explicit loading indicator child)
        # This is a heuristic and might need to be refined for specific components.
        if "MuiLoadingButton-loading" in class_str: # Common for LoadingButton
            inferred_props["loading"] = "true"

    # Add similar blocks for other components as needed (e.g., if component_name.lower() == "card":)
    # elif component_name.lower() == "card":
    #     if "MuiCard-elevation1" in class_str: inferred_props["elevation"] = "1"
    #     if "MuiCard-elevation8" in class_str: inferred_props["elevation"] = "8"

    return inferred_props

def scrape_mui_demo_variations(component_name):
    """
    Scrapes the Material UI demo page for a given component
    and extracts rendered component variations, their raw JSX code,
    parsed properties (including 'sx' styles), and associated CSS classes.

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

    # Find all main demo sections. These often have IDs starting with "demo-"
    demo_sections = soup.select('div[id^="demo-"]')

    if not demo_sections:
        print(f"No specific 'demo-' sections found on {demo_url}. Cannot extract detailed variations.")
        print("Please ensure the demo page structure contains div elements with IDs starting with 'demo-'.")
        return []


    print(f"Found {len(demo_sections)} demo sections. Processing...")

    for i, demo_section in enumerate(demo_sections):
        textarea = demo_section.find('textarea', class_='npm__react-simple-code-editor__textarea')
        
        if not textarea:
            print(f"No textarea (JSX code) found in demo section {i+1}. Skipping this section for detailed parsing.")
            # We can still try to get basic info from rendered elements if no JSX is available
            generic_mui_root_class = f"Mui{component_name}-root"
            rendered_elements_in_section = demo_section.find_all(class_=lambda x: x and generic_mui_root_class in x)
            for k, element in enumerate(rendered_elements_in_section):
                class_names = element.get('class', [])
                variation_text = element.get_text(strip=True) or f"{component_name} Demo {i+1}-{k+1}"
                inferred_props_from_classes_obj = infer_props_from_classes(component_name, class_names)
                component_variations.append({
                    "VariationName": f"{component_name}-{variation_text.replace(' ', '')}_RenderedOnly_{i+1}-{k+1}",
                    "RawJSXCode": "", # Not available
                    "AssociatedClasses": class_names,
                    "InferredProps": inferred_props_from_classes_obj,
                    "ParsedComponent": { # Basic placeholder
                        "ComponentName": component_name, "Props": {}, "InnerText": variation_text, "Children": [], "RawInlineStyleRules": {}
                    }
                })
            continue # Move to next demo section

        raw_jsx_code_escaped = textarea.get_text(strip=True)
        raw_jsx_code = html.unescape(raw_jsx_code_escaped)

        # Split multiple components if they exist within one textarea.
        jsx_snippets = re.findall(r'(<\s*\w+[^>]*?\/>|<\s*\w+[^>]*?>[\s\S]*?<\/\s*\w+\s*>)', raw_jsx_code, re.DOTALL)
        
        if not jsx_snippets and raw_jsx_code.strip():
             jsx_snippets = [raw_jsx_code.strip()]
        
        # Get all relevant rendered elements within this specific demo_section
        generic_mui_root_class = f"Mui{component_name}-root"
        all_rendered_elements_in_section = demo_section.find_all(class_=lambda x: x and generic_mui_root_class in x)
        
        # Process each JSX snippet from the textarea
        for j, snippet in enumerate(jsx_snippets):
            parsed_component_data = parse_jsx_element(snippet)
            
            associated_classes = []
            inferred_props_from_classes_obj = {}
            matched_element = None

            # --- HEURISTIC MATCHING FOR RENDERED ELEMENT ---
            # 1. Try to match by inner text content (most reliable for unique text)
            parsed_inner_text = parsed_component_data.get('InnerText', '').strip()
            if parsed_inner_text:
                for rendered_el in all_rendered_elements_in_section:
                    rendered_text = rendered_el.get_text(strip=True)
                    if rendered_text and parsed_inner_text == rendered_text:
                        matched_element = rendered_el
                        break
            
            # 2. Fallback: Try to match by explicit props from JSX
            # This is key for elements with no unique inner text (e.g., icon buttons, loading buttons)
            if not matched_element:
                jsx_props = parsed_component_data.get('Props', {})
                
                # Collect relevant props from JSX for matching
                match_props = {}
                if 'variant' in jsx_props: match_props['variant'] = jsx_props['variant']
                if 'color' in jsx_props: match_props['color'] = jsx_props['color']
                if 'size' in jsx_props: match_props['size'] = jsx_props['size']
                if 'loading' in jsx_props: match_props['loading'] = jsx_props['loading'] # Match for loading state
                if 'loadingPosition' in jsx_props: match_props['loadingPosition'] = jsx_props['loadingPosition'] # Match for loadingPosition

                if match_props:
                    for rendered_el in all_rendered_elements_in_section:
                        # Infer props from this rendered element's classes
                        inferred_from_rendered = infer_props_from_classes(component_name, rendered_el.get('class', []))
                        
                        # Check if all key match_props from JSX are present and match in inferred props
                        all_match = True
                        for prop_key, prop_val in match_props.items():
                            if prop_key not in inferred_from_rendered or inferred_from_rendered[prop_key] != prop_val:
                                all_match = False
                                break
                        if all_match:
                            matched_element = rendered_el
                            break
            
            # 3. Fallback: Positional match if text/prop match failed
            if not matched_element and j < len(all_rendered_elements_in_section):
                matched_element = all_rendered_elements_in_section[j]
            elif not matched_element and all_rendered_elements_in_section: # Fallback to first element if all else fails
                matched_element = all_rendered_elements_in_section[0] # Changed from [-1] to [0] for consistent fallback


            if matched_element:
                associated_classes = matched_element.get('class', [])
                inferred_props_from_classes_obj = infer_props_from_classes(component_name, associated_classes)
            else:
                print(f"Warning: Could not find corresponding rendered element for JSX snippet {j+1} in demo section {i+1}. AssociatedClasses and InferredProps will be empty.")


            # Create descriptive VariationName: ComponentName-TextContent_Props_Index
            variation_text_for_name = parsed_component_data.get('InnerText', '').strip()
            if not variation_text_for_name and parsed_component_data['ComponentName'] == "IconButton":
                variation_text_for_name = "Icon" # Simpler for icon buttons
            elif not variation_text_for_name:
                variation_text_for_name = parsed_component_data['ComponentName'] # Default to component name if no specific text

            # Add key props to name for uniqueness and description
            props_for_name = []
            jsx_props = parsed_component_data.get('Props', {})
            for p_key in ['variant', 'color', 'size', 'loading', 'loadingPosition']:
                if p_key in jsx_props and p_key != 'componentTag':
                    props_for_name.append(f"{p_key}-{jsx_props[p_key]}")
            
            props_suffix = "_" + "_".join(props_for_name) if props_for_name else ""
            
            final_variation_name = f"{parsed_component_data['ComponentName']}-{variation_text_for_name.replace(' ', '')}{props_suffix}"
            if len(jsx_snippets) > 1: # Add snippet index if multiple in one textarea
                 final_variation_name += f"_{j+1}"
            
            final_variation_name = final_variation_name.replace('__', '_').strip('_') # Clean up double underscores
            if not final_variation_name: # Final fallback for name
                final_variation_name = f"Unnamed-{parsed_component_data['ComponentName']}-Demo-{i+1}-{j+1}"


            variation_data = {
                "VariationName": final_variation_name,
                "RawJSXCode": snippet, # Store the individual JSX snippet
                "AssociatedClasses": associated_classes, # Classes from the *rendered* HTML element (best effort)
                "InferredProps": inferred_props_from_classes_obj, # Inferred from associated classes
                "ParsedComponent": parsed_component_data # Fully parsed JSX component data
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
    material_component_definition = {
        "ComponentName": extracted_component_name,
        "Properties": props,
        "CssClasses": css_classes,
        "ComponentVariations": component_variations, # Populated with AssociatedClasses, InferredProps, RawJSXCode, and ParsedComponent
        "Children": [], # This refers to general nesting rules, not scraped from specific demos yet
        "RawInlineStyleRules": {}, # Placeholder, actual raw styles now within ComponentVariations->ParsedComponent
        "InnerText": "" # General inner text for the component type, not specific demo text
    }

    return material_component_definition

# --- Example Usage ---
if __name__ == "__main__":
    if len(sys.argv) < 2:
        # Corrected script name in usage message
        print("Usage: python docs_to_json_ast.py <ComponentName>")
        print("Example: python docs_to_json_ast.py Button")
        sys.exit(1)

    component_to_scrape = sys.argv[1]
    # Define output_filename here to ensure it's always in scope
    output_filename = f"{component_to_scrape.lower()}_full_details.json" 
    
    full_component_json_ast = scrape_mui_component_api(component_to_scrape)

    if full_component_json_ast:
        print(f"\n--- Generated JSON AST for {component_to_scrape} Component ---")
        print(json.dumps(full_component_json_ast, indent=2))

        # --- Save to JSON file ---
        try:
            # output_filename is correctly defined in this scope
            with open(output_filename, 'w', encoding='utf-8') as f:
                json.dump(full_component_json_ast, f, indent=2, ensure_ascii=False)
            print(f"\nSuccessfully saved scraped data to {output_filename}")
        except IOError as e:
            print(f"Error saving data to file {output_filename}: {e}")








# import requests
# from bs4 import BeautifulSoup
# import json
# import html
# import re

# # Removed parse_sx_prop_string and parse_jsx_element as they are not needed
# # when scraping rendered HTML directly for AssociatedClasses and InferredProps.

# def infer_props_from_classes(component_name, class_list):
#     """
#     Infers common Material UI component props (variant, color, disabled, size)
#     based on the presence of specific CSS classes. This function is
#     extensible for different component types.

#     Args:
#         component_name (str): The name of the Material UI component (e.g., 'Button').
#         class_list (list): A list of CSS class names found on the rendered element.

#     Returns:
#         dict: A dictionary of inferred properties.
#     """
#     inferred_props = {}
#     class_str = " ".join(class_list) # Convert list to string for easier searching

#     if component_name.lower() == "button":
#         # Infer variant
#         if "MuiButton-contained" in class_str:
#             inferred_props["variant"] = "contained"
#         elif "MuiButton-outlined" in class_str:
#             inferred_props["variant"] = "outlined"
#         else: # Default is text if neither contained nor outlined
#             inferred_props["variant"] = "text"

#         # Infer color
#         if "MuiButton-colorPrimary" in class_str:
#             inferred_props["color"] = "primary"
#         elif "MuiButton-colorSecondary" in class_str:
#             inferred_props["color"] = "secondary"
#         elif "MuiButton-colorError" in class_str:
#             inferred_props["color"] = "error"
#         elif "MuiButton-colorInfo" in class_str:
#             inferred_props["color"] = "info"
#         elif "MuiButton-colorSuccess" in class_str:
#             inferred_props["color"] = "success"
#         elif "MuiButton-colorWarning" in class_str:
#             inferred_props["color"] = "warning"
#         elif "MuiButton-colorInherit" in class_str:
#             inferred_props["color"] = "inherit"

#         # Infer size
#         if "MuiButton-sizeSmall" in class_str:
#             inferred_props["size"] = "small"
#         elif "MuiButton-sizeLarge" in class_str:
#             inferred_props["size"] = "large"
#         else: # Default is medium
#             inferred_props["size"] = "medium"

#         # Infer disabled state
#         if "Mui-disabled" in class_str:
#             inferred_props["disabled"] = "true" # Store as string for consistency with other props
    
#     # Add similar blocks for other components as needed (e.g., if component_name.lower() == "card":)
#     # elif component_name.lower() == "card":
#     #     if "MuiCard-elevation1" in class_str: inferred_props["elevation"] = "1"
#     #     if "MuiCard-elevation8" in class_str: inferred_props["elevation"] = "8"

#     return inferred_props

# def scrape_mui_demo_variations(component_name):
#     """
#     Scrapes the Material UI demo page for a given component
#     and extracts rendered component variations, their classes,
#     and inferred properties. This version focuses on directly
#     scraping the rendered HTML elements.

#     Args:
#         component_name (str): The name of the Material UI component
#                               (e.g., 'button', 'card').

#     Returns:
#         list: A list of dictionaries, each representing a component variation.
#               Returns an empty list on error or if no variations are found.
#     """
#     demo_url = f"https://mui.com/material-ui/react-{component_name.lower()}/"
#     print(f"\nAttempting to scrape demo page: {demo_url}")

#     try:
#         response = requests.get(demo_url)
#         response.raise_for_status()
#     except requests.exceptions.RequestException as e:
#         print(f"Error fetching demo page {demo_url}: {e}")
#         return []

#     soup = BeautifulSoup(response.text, 'html.parser')
#     component_variations = []

#     # General approach: Find elements with the root Material UI class for the component.
#     # E.g., for "Button", look for elements with class "MuiButton-root".
#     generic_mui_root_class = f"Mui{component_name}-root"
    
#     # Find all elements on the page that have this root class.
#     # This will capture all instances of the component rendered in the demos.
#     rendered_elements_in_demos = soup.find_all(class_=lambda x: x and generic_mui_root_class in x)
    
#     if not rendered_elements_in_demos:
#         print(f"No rendered '{component_name}' elements with class '{generic_mui_root_class}' found on the demo page.")
#         return []

#     print(f"Found {len(rendered_elements_in_demos)} rendered '{component_name}' elements. Processing...")

#     for i, element in enumerate(rendered_elements_in_demos):
#         class_names = element.get('class', [])
#         variation_text = element.get_text(strip=True)

#         if not variation_text:
#             # Attempt to get text from potential child spans/labels common in MUI
#             inner_label_span = element.find('span', class_=lambda x: x and ('MuiButton-label' in x or 'MuiTypography-root' in x))
#             if inner_label_span:
#                 variation_text = inner_label_span.get_text(strip=True)

#         if not variation_text and "MuiIconButton-root" in class_names:
#             # For icon buttons, text might be empty, use a placeholder or icon name
#             variation_text = "Icon Button"
#         elif not variation_text: # Generic fallback if still no text
#             variation_text = f"{component_name} Demo {i+1}"


#         # Infer props from the collected class names
#         inferred_props = infer_props_from_classes(component_name, class_names)
        
#         # Add any direct HTML attributes as props (e.g., 'variant', 'color', 'size' might be direct on some elements)
#         # These override inferred props if present, as they are explicit.
#         if element.get('variant'):
#             inferred_props['variant'] = element.get('variant')
#         if element.get('color'):
#             inferred_props['color'] = element.get('color')
#         if element.get('size'):
#             inferred_props['size'] = element.get('size')
#         if element.get('disabled') is not None: # Check if 'disabled' attribute exists
#              inferred_props['disabled'] = str(element.get('disabled')).lower()


#         variation_data = {
#             "VariationName": variation_text,
#             "RawJSXCode": "", # Not available when scraping rendered HTML directly
#             "AssociatedClasses": class_names,
#             "InferredProps": inferred_props,
#             "ParsedComponent": { # This will be basic as we're not parsing JSX from textareas
#                 "ComponentName": component_name,
#                 "Props": {}, # We cannot infer specific JSX props here like 'sx'
#                 "InnerText": variation_text,
#                 "Children": [], # Not inferring complex children hierarchy from rendered HTML
#                 "RawInlineStyleRules": {} # Not extracting raw inline styles from HTML 'style' attribute here
#             }
#         }
#         component_variations.append(variation_data)
            
#     return component_variations

# def scrape_mui_component_api(component_name):
#     """
#     Scrapes the Material UI API documentation page for a given component
#     and extracts its properties (props), types, default values, and CSS classes,
#     and also gathers demo variations.

#     Args:
#         component_name (str): The name of the Material UI component
#                               (e.g., 'button', 'card', 'typography').

#     Returns:
#         dict: A dictionary mimicking the MaterialComponentDefinition structure,
#               populated with scraped data. Returns None on error.
#     """
#     # Construct the API documentation URL for the specific component's API page
#     # Example: https://mui.com/material-ui/api/button/
#     api_url = f"https://mui.com/material-ui/api/{component_name.lower()}/"
#     print(f"Attempting to scrape API page: {api_url}")

#     try:
#         response = requests.get(api_url)
#         response.raise_for_status() # Raise an exception for HTTP errors (4xx or 5xx)
#     except requests.exceptions.RequestException as e:
#         print(f"Error fetching API page {api_url}: {e}")
#         return None

#     soup = BeautifulSoup(response.text, 'html.parser')

#     # --- 1. Extract Component Name ---
#     # The h1 tag typically contains the component name followed by " API"
#     title_tag = soup.find('h1')
#     extracted_component_name = component_name # Default to input name
#     if title_tag and " API" in title_tag.get_text():
#         # Clean the title to get just the component name
#         extracted_component_name = title_tag.get_text().replace(" API", "").strip()
#     print(f"Extracted Component Name: {extracted_component_name}")

#     # --- 2. Extract Properties (Props Table) using specific 'id' pattern ---
#     props = {}
#     # The IDs for prop rows follow a pattern: [component-name]-prop-[prop-name]
#     # For example, for "Button", we look for "button-prop-"
#     prop_id_prefix = f"{extracted_component_name.lower()}-prop-"

#     print(f"\nSearching for prop rows with ID prefix: '{prop_id_prefix}'")
#     prop_rows = soup.find_all('tr', id=lambda x: x and x.startswith(prop_id_prefix))

#     if prop_rows:
#         print(f"Found {len(prop_rows)} prop rows. Extracting data...")
#         for row in prop_rows:
#             prop_name = row['id'].replace(prop_id_prefix, '')
#             cols = row.find_all(['th', 'td']) # Use th for name and td for others

#             if len(cols) >= 4:
#                 prop_type = cols[1].get_text(strip=True)
#                 prop_default = cols[2].get_text(strip=True)
#                 prop_description = cols[3].get_text(strip=True)

#                 props[prop_name] = {
#                     "type": prop_type,
#                     "default": prop_default,
#                     "description": prop_description
#                 }
#             else:
#                 print(f"Skipping malformed prop row (not enough columns): {row.get_text(strip=True)}")
#     else:
#         print(f"Could not find any prop rows with ID prefix '{prop_id_prefix}' on the API page.")

#     # --- 3. Extract CSS Classes using specific 'id' pattern ---
#     css_classes = []
#     # The IDs for class rows follow a pattern: [component-name]-classes-[class-name]
#     # For example, for "Button", we look for "button-classes-"
#     class_id_prefix = f"{extracted_component_name.lower()}-classes-"

#     print(f"\nSearching for CSS class rows with ID prefix: '{class_id_prefix}'")
#     class_rows = soup.find_all('tr', id=lambda x: x and x.startswith(class_id_prefix))

#     if class_rows:
#         print(f"Found {len(class_rows)} CSS class rows. Extracting data...")
#         for row in class_rows:
#             cols = row.find_all('td')

#             if len(cols) >= 3: # Expect at least Class name, Rule name, and Description
#                 full_class_name_td = cols[0]
#                 rule_name_td = cols[1]
#                 description_td = cols[2]

#                 full_class_name = full_class_name_td.get_text(strip=True)

#                 rule_name_span = rule_name_td.find('span')
#                 rule_name = rule_name_span.get_text(strip=True) if rule_name_span else ""

#                 description = description_td.get_text(strip=True)

#                 css_classes.append({
#                     "className": full_class_name,
#                     "ruleName": rule_name,
#                     "description": description
#                 })
#             else:
#                 print(f"Skipping malformed CSS class row (not enough columns): {row.get_text(strip=True)}")
#     else:
#         print(f"Could not find any CSS class rows with ID prefix '{class_id_prefix}' on the API page.")

#     # --- 4. Scrape Demo Variations ---
#     # Call the new function to scrape the demo page
#     component_variations = scrape_mui_demo_variations(extracted_component_name)


#     # --- Construct the MaterialComponentDefinition JSON ---
#     # RawInlineStyleRules is now handled within ComponentVariations->InferredProps (from CSS classes)
#     # Children and InnerText are only inferred for the demo variations now, not a general component property.
#     material_component_definition = {
#         "ComponentName": extracted_component_name,
#         "Properties": props,
#         "CssClasses": css_classes,
#         "ComponentVariations": component_variations, # Populated with AssociatedClasses and InferredProps
#         "Children": [], # This refers to general nesting rules, not scraped from specific demos
#         "RawInlineStyleRules": {}, # Placeholder, actual raw styles are now within InferredProps or from JSX if we re-introduce that level of parsing.
#         "InnerText": "" # General inner text for the component type, not specific demo text
#     }

#     return material_component_definition

# # --- Example Usage ---
# # Scrape the Material UI Button component API page and its demo variations
# # To scrape a different component, just change the string here!
# component_to_scrape = "Button" # Example: "Card", "Typography", "Switch", etc.

# full_component_json_ast = scrape_mui_component_api(component_to_scrape)

# if full_component_json_ast:
#     print(f"\n--- Generated JSON AST for {component_to_scrape} Component ---")
#     print(json.dumps(full_component_json_ast, indent=2))

#     # --- Save to JSON file ---
#     output_filename = f"{component_to_scrape.lower()}_full_details.json"
#     try:
#         with open(output_filename, 'w', encoding='utf-8') as f:
#             json.dump(full_component_json_ast, f, indent=2, ensure_ascii=False)
#         print(f"\nSuccessfully saved scraped data to {output_filename}")
#     except IOError as e:
#         print(f"Error saving data to file {output_filename}: {e}")

