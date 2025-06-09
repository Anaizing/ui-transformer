import json
import os
import xml.etree.ElementTree as ET
from xml.dom import minidom
import sys # Import the sys module to access command-line arguments

def prettify_xml(elem):
    """Return a pretty-printed XML string for the Element."""
    rough_string = ET.tostring(elem, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="    ")

def map_mui_component_to_uxml_tag(mui_component_name):
    """
    Maps a Material UI component name to its corresponding Unity UXML tag.
    This mapping can be expanded for more components.
    """
    mui_component_name_lower = mui_component_name.lower()
    if mui_component_name_lower == "button":
        return "ui:Button"
    elif mui_component_name_lower == "typography":
        return "ui:Label" # Typography often translates to a Label for text
    elif mui_component_name_lower == "card":
        return "ui:VisualElement" # Card is a container, VisualElement is appropriate
    elif mui_component_name_lower == "iconbutton":
        return "ui:Button" # IconButton is still a button in Unity, potentially with an icon child
    # Add more mappings here as needed
    return "ui:VisualElement" # Default to VisualElement if no specific mapping

def map_mui_prop_to_uxml_attribute(prop_name, prop_value):
    """
    Maps Material UI props to Unity UXML attributes.
    This is a simplified mapping and should be expanded for more props.
    """
    if prop_name == "text": # Common prop for button/typography text
        return "text", prop_value
    elif prop_name == "variant": # Handled by USS classes, but could be a custom attribute if needed
        return None, None
    elif prop_name == "color": # Handled by USS classes
        return None, None
    elif prop_name == "size": # Handled by USS classes
        return None, None
    elif prop_name == "disabled":
        return "enable-raycast", "false" if prop_value == "true" else "true" # Disabled often means no raycast
    elif prop_name == "loading": # Custom attribute, handled by C#
        return "loading", prop_value # UXML will need a custom trait for this
    elif prop_name == "loadingPosition": # Custom attribute, handled by C#
        return "loading-position", prop_value # UXML will need a custom trait for this
    # Add more direct prop mappings here
    return None, None

def create_uxml_element_from_parsed_component(parsed_component_data):
    """
    Recursively creates UXML elements from the ParsedComponent data.
    """
    component_name = parsed_component_data.get("ComponentName")
    if not component_name:
        return None

    if component_name == "#text":
        # For plain text nodes, create a Label
        label_element = ET.Element("ui:Label")
        label_element.set("text", parsed_component_data.get("InnerText", "").strip())
        return label_element

    uxml_tag = map_mui_component_to_uxml_tag(component_name)
    element = ET.Element(uxml_tag)

    # Set common attributes like name and classes
    # The name is important for C# script to query elements
    # Classes are for USS styling
    
    # Props from ParsedComponent
    for prop_key, prop_val in parsed_component_data.get("Props", {}).items():
        if prop_key == 'componentTag': # Internal prop from parsing, skip
            continue
        uxml_attr, uxml_val = map_mui_prop_to_uxml_attribute(prop_key, prop_val)
        if uxml_attr and uxml_val is not None:
            element.set(uxml_attr, uxml_val)
    
    # Add ParsedComponent.InnerText if available and not set by a specific prop
    if parsed_component_data.get("InnerText") and not element.get("text"):
        if uxml_tag == "ui:Label" or uxml_tag == "ui:Button":
            element.set("text", parsed_component_data["InnerText"].strip())
        else:
            # For other VisualElements, text usually goes into a child Label
            text_label = ET.SubElement(element, "ui:Label")
            text_label.set("text", parsed_component_data["InnerText"].strip())
            text_label.set("name", "inner-text-label") # Name for C# lookup

    # Recursively add children
    for child_data in parsed_component_data.get("Children", []):
        child_element = create_uxml_element_from_parsed_component(child_data)
        if child_element is not None:
            element.append(child_element)
            # Add a specific name for icon children for easier C# manipulation
            if child_data.get("ComponentName") and "Icon" in child_data["ComponentName"]:
                child_element.set("name", f"{child_data['ComponentName'].lower()}-icon")

    # Add a custom attribute for RawInlineStyleRules to possibly pass to C# if direct USS isn't enough
    # This is more for debugging/passing data, as these are meant for USS direct application.
    # if parsed_component_data.get("RawInlineStyleRules"):
    #     element.set("raw-inline-styles", json.dumps(parsed_component_data["RawInlineStyleRules"]))

    return element

def generate_uxml_from_mui_json(json_data, output_dir="UXML"):
    """
    Generates Unity UI Toolkit UXML files from the Material UI component JSON data.

    Args:
        json_data (dict): The parsed JSON data of a Material UI component,
                          including ComponentVariations.
        output_dir (str): The directory to save the generated UXML files.
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    component_name_base = json_data.get("ComponentName", "Component")

    for i, variation in enumerate(json_data.get("ComponentVariations", [])):
        variation_name = variation.get("VariationName", f"UnnamedVariation_{i+1}")
        raw_jsx_code = variation.get("RawJSXCode", "")
        associated_classes = variation.get("AssociatedClasses", [])
        parsed_component_data = variation.get("ParsedComponent", {})

        # Create the root UXML element based on ParsedComponent
        root_uxml_element = create_uxml_element_from_parsed_component(parsed_component_data)
        
        if root_uxml_element is None:
            print(f"Skipping UXML generation for variation '{variation_name}' due to empty ParsedComponent.")
            continue

        # Add classes from AssociatedClasses to the root UXML element
        if associated_classes:
            current_classes = root_uxml_element.get("class", "").split()
            new_classes = " ".join(sorted(list(set(current_classes + associated_classes))))
            root_uxml_element.set("class", new_classes)

        # Set a meaningful name for the UXML element
        root_uxml_element.set("name", variation_name.replace(" ", "-").replace("_", "-"))


        # Create the UXML document structure
        root_ui_document = ET.Element("ui:UXML")
        root_ui_document.set("xmlns:ui", "UnityEngine.UIElements")
        root_ui_document.set("xmlns:uie", "UnityEditor.UIElements")
        # You might also add a custom namespace for your C# components later, e.g.:
        # root_ui_document.set("xmlns:mui", "YourUnityProject.UI.MaterialUI")

        root_ui_document.append(root_uxml_element)

        # Generate the UXML file
        pretty_xml_string = prettify_xml(root_ui_document)
        
        # Sanitize filename for OS compatibility
        filename = f"{variation_name.replace(' ', '_').replace('/', '_').lower()}.uxml"
        output_path = os.path.join(output_dir, filename)

        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(pretty_xml_string)
            print(f"Generated UXML for '{variation_name}' to {output_path}")
        except IOError as e:
            print(f"Error saving UXML to {output_path}: {e}")

# --- Example Usage ---
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python ast_to_uxml.py <ComponentName>")
        print("Example: python ast_to_uxml.py Button")
        sys.exit(1)

    component_to_generate = sys.argv[1]
    json_filename = f"{component_to_generate.lower()}_full_details.json"
    uxml_output_directory = "GeneratedUXML" # Define a directory for UXML files

    # Ensure the output directory exists
    if not os.path.exists(uxml_output_directory):
        os.makedirs(uxml_output_directory)

    if os.path.exists(json_filename):
        with open(json_filename, 'r', encoding='utf-8') as f:
            mui_data = json.load(f)
        
        generate_uxml_from_mui_json(mui_data, uxml_output_directory)
    else:
        print(f"Error: JSON file '{json_filename}' not found. Please ensure it has been generated by docs_to_json_ast.py for '{component_to_generate}'.")
