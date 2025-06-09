import json
import os
import re
import sys # Import the sys module to access command-line arguments

def generate_csharp_component(component_name, json_data):
    """
    Generates C# code for a Unity UI Toolkit component based on Material UI data.

    Args:
        component_name (str): The name of the Material UI component (e.g., 'Button').
        json_data (dict): The parsed JSON data for the component.

    Returns:
        str: A string containing the generated C# code.
    """
    csharp_output = []

    # Determine base class based on Material UI component name
    base_class = "UnityEngine.UIElements.VisualElement"
    if component_name.lower() == "button" or component_name.lower() == "iconbutton":
        base_class = "UnityEngine.UIElements.Button"
    elif component_name.lower() == "typography":
        base_class = "UnityEngine.UIElements.Label" # Typography often translates to a Label

    # --- Namespace and Usings ---
    csharp_output.append("using UnityEngine;")
    csharp_output.append("using UnityEngine.UIElements;")
    csharp_output.append("using System.Collections.Generic;")
    csharp_output.append("using System.Linq;")
    csharp_output.append("")
    csharp_output.append(f"namespace YourUnityProject.UI.MaterialUI") # Define your Unity project's UI namespace
    csharp_output.append("{")

    # --- Component Class Definition ---
    csharp_output.append(f"    public class Mui{component_name} : {base_class}")
    csharp_output.append("    {")
    csharp_output.append("        // UXML Class Name for this component")
    csharp_output.append(f"        public new static readonly string ussClassName = \"Mui{component_name}-root\";")
    csharp_output.append("")

    # --- Private Fields to hold references to child elements (e.g., for loading state) ---
    if component_name.lower() == "button":
        csharp_output.append("        private VisualElement _loadingSpinner;")
        csharp_output.append("        private Label _innerTextLabel;")
        csharp_output.append("")

    # --- Constructor ---
    csharp_output.append(f"        public Mui{component_name}()")
    csharp_output.append("        {")
    csharp_output.append(f"            AddToClassList(ussClassName);")
    csharp_output.append(f"            // Add any common initial setup here, e.g., default styles, children creation")
    
    if component_name.lower() == "button":
        csharp_output.append("            // Query and store references to child elements (expected in UXML)")
        csharp_output.append("            RegisterCallback<AttachToPanelEvent>(OnAttachToPanel);")
        csharp_output.append("            RegisterCallback<DetachFromPanelEvent>(OnDetachFromPanel);")
    
    csharp_output.append("        }")
    csharp_output.append("")

    if component_name.lower() == "button":
        csharp_output.append("        private void OnAttachToPanel(AttachToPanelEvent evt)")
        csharp_output.append("        {")
        csharp_output.append("            _loadingSpinner = this.Q<VisualElement>(\"loading-spinner\");") # Query for named spinner
        csharp_output.append("            _innerTextLabel = this.Q<Label>(\"inner-text-label\");") # Query for inner text label
        csharp_output.append("            UpdateLoadingState(); // Initial update based on UXML value")
        csharp_output.append("        }")
        csharp_output.append("")
        csharp_output.append("        private void OnDetachFromPanel(DetachToPanelEvent evt)")
        csharp_output.append("        {")
        csharp_output.append("            _loadingSpinner = null;")
        csharp_output.append("            _innerTextLabel = null;")
        csharp_output.append("        }")
        csharp_output.append("")

    # --- Exposed Properties (corresponding to Material UI props) ---
    
    # Generic properties that might be found in JSON data's Properties section
    for prop_name, prop_details in json_data.get("Properties", {}).items():
        # Skipping 'children' and 'sx' as they are handled by UXML hierarchy and USS
        if prop_name.lower() in ["children", "sx", "component", "ref"]:
            continue
        
        csharp_type = "string" # Default type, refine based on 'type' from API doc
        if "bool" in prop_details.get("type", "").lower():
            csharp_type = "bool"
        elif "number" in prop_details.get("type", "").lower():
            csharp_type = "float" # or int

        # Sanitize prop_name for C# (e.g., 'loadingPosition' -> 'LoadingPosition')
        csharp_prop_name = "".join(word.capitalize() for word in re.split(r'([A-Z][a-z0-9]+)', prop_name) if word)
        if csharp_prop_name == "": # Handle cases like 'disabled' already lowercase
            csharp_prop_name = prop_name[0].upper() + prop_name[1:]


        # Implement custom logic for specific props
        if csharp_prop_name == "Disabled":
            csharp_output.append(f"        private {csharp_type} _disabled;")
            csharp_output.append(f"        public {csharp_type} {csharp_prop_name}")
            csharp_output.append("        {")
            csharp_output.append("            get => _disabled;")
            csharp_output.append("            set")
            csharp_output.append("            {")
            csharp_output.append("                if (_disabled == value) return;")
            csharp_output.append("                _disabled = value;")
            csharp_output.append("                SetEnabled(!value);") # Base VisualElement method for disabled state
            csharp_output.append(f"                EnableInClassList(\"Mui-disabled\", value);") # Apply/remove class
            csharp_output.append("            }")
            csharp_output.append("        }")
            csharp_output.append("")
        elif csharp_prop_name == "Loading" and component_name.lower() == "button":
            csharp_output.append("        private bool _loading;")
            csharp_output.append("        public bool Loading")
            csharp_output.append("        {")
            csharp_output.append("            get => _loading;")
            csharp_output.append("            set")
            csharp_output.append("            {")
            csharp_output.append("                if (_loading == value) return;")
            csharp_output.append("                _loading = value;")
            csharp_output.append("                UpdateLoadingState();")
            csharp_output.append("            }")
            csharp_output.append("        }")
            csharp_output.append("")
        elif csharp_prop_name == "LoadingPosition" and component_name.lower() == "button":
            csharp_output.append("        private string _loadingPosition = \"\";") # Default value
            csharp_output.append("        public string LoadingPosition")
            csharp_output.append("        {")
            csharp_output.append("            get => _loadingPosition;")
            csharp_output.append("            set")
            csharp_output.append("            {")
            csharp_output.append("                if (_loadingPosition == value) return;")
            csharp_output.append("                _loadingPosition = value;")
            csharp_output.append("                UpdateLoadingState();")
            csharp_output.append("            }")
            csharp_output.append("        }")
            csharp_output.append("")
        else: # Standard property with simple assignment
            csharp_output.append(f"        private {csharp_type} _{prop_name.lower()};")
            csharp_output.append(f"        public {csharp_type} {csharp_prop_name}")
            csharp_output.append("        {")
            csharp_output.append(f"            get => _{prop_name.lower()};")
            csharp_output.append("            set")
            csharp_output.append("            {")
            csharp_output.append(f"                if (_{prop_name.lower()} == value) return;")
            csharp_output.append(f"                _{prop_name.lower()} = value;")
            csharp_output.append("                // Add logic to update UI based on this prop if necessary")
            csharp_output.append("            }")
            csharp_output.append("        }")
            csharp_output.append("")

    # --- Loading State Update Method (for Button/LoadingButton) ---
    if component_name.lower() == "button":
        csharp_output.append("        private void UpdateLoadingState()")
        csharp_output.append("        {")
        csharp_output.append("            if (_loadingSpinner == null || _innerTextLabel == null) return;")
        csharp_output.append("")
        csharp_output.append("            if (Loading)")
        csharp_output.append("            {")
        csharp_output.append("                _loadingSpinner.style.display = DisplayStyle.Flex;")
        csharp_output.append("                _innerTextLabel.style.display = DisplayStyle.None;")
        csharp_output.append("                // Adjust flex direction and justification based on LoadingPosition")
        csharp_output.append("                if (LoadingPosition == \"start\")")
        csharp_output.append("                {")
        csharp_output.append("                    style.flexDirection = FlexDirection.Row;")
        csharp_output.append("                    style.justifyContent = JustifyContent.FlexStart;")
        csharp_output.append("                }")
        csharp_output.append("                else if (LoadingPosition == \"end\")")
        csharp_output.append("                {")
        csharp_output.append("                    style.flexDirection = FlexDirection.RowReverse;")
        csharp_output.append("                    style.justifyContent = JustifyContent.FlexEnd;")
        csharp_output.append("                }")
        csharp_output.append("                else if (LoadingPosition == \"center\" || LoadingPosition == \"\")")
        csharp_output.append("                {")
        csharp_output.append("                    style.flexDirection = FlexDirection.Row;")
        csharp_output.append("                    style.justifyContent = JustifyContent.Center;")
        csharp_output.append("                }")
        csharp_output.append("            }")
        csharp_output.append("            else")
        csharp_output.append("            {")
        csharp_output.append("                _loadingSpinner.style.display = DisplayStyle.None;")
        csharp_output.append("                _innerTextLabel.style.display = DisplayStyle.Flex;")
        csharp_output.append("                // Reset to default layout if not loading")
        csharp_output.append("                style.flexDirection = FlexDirection.Row;")
        csharp_output.append("                style.justifyContent = JustifyContent.Center;")
        csharp_output.append("            }")
        csharp_output.append("        }")
        csharp_output.append("")

    # --- UXML Factory ---
    # Enables using this component directly in UXML with <mui:MuiButton />
    csharp_output.append(f"        public new class UxmlFactory : UxmlFactory<Mui{component_name}, UxmlTraits> {{}}")
    csharp_output.append("")

    # --- UXML Traits ---
    # Exposes properties to UXML and the UI Builder
    csharp_output.append(f"        public new class UxmlTraits : {base_class}.UxmlTraits")
    csharp_output.append("        {")
    
    # Add UxmlAttributes for all exposed properties
    for prop_name, prop_details in json_data.get("Properties", {}).items():
        if prop_name.lower() in ["children", "sx", "component", "ref"]:
            continue
        
        uxml_type = "string"
        if "bool" in prop_details.get("type", "").lower():
            uxml_type = "bool"
        elif "number" in prop_details.get("type", "").lower():
            uxml_type = "float" # Assuming float for number props in UXML, adjust if int is needed
        
        # Sanitize prop_name for UXML attribute name (kebab-case)
        uxml_attribute_name = ''.join(['-' + c.lower() if c.isupper() else c for c in prop_name]).strip('-')


        csharp_output.append(f"            private Uxml{uxml_type.capitalize()}Attribute _{uxml_attribute_name.replace('-', '_')}Attribute = new Uxml{uxml_type.capitalize()}Attribute {{ name = \"{uxml_attribute_name}\" }};")

    csharp_output.append("")
    csharp_output.append("            public override void Init(VisualElement ve, IUxmlAttributes bag, CreationContext cc)")
    csharp_output.append("            {")
    csharp_output.append("                base.Init(ve, bag, cc);")
    csharp_output.append(f"                var component = ve as Mui{component_name};")
    csharp_output.append("                if (component == null) return;")
    csharp_output.append("")
    
    # Initialize properties from UxmlAttributes
    for prop_name, prop_details in json_data.get("Properties", {}).items():
        if prop_name.lower() in ["children", "sx", "component", "ref"]:
            continue
        
        csharp_prop_name = "".join(word.capitalize() for word in re.split(r'([A-Z][a-z0-9]+)', prop_name) if word)
        if csharp_prop_name == "":
            csharp_prop_name = prop_name[0].upper() + prop_name[1:]
        
        uxml_attribute_name = ''.join(['-' + c.lower() if c.isupper() else c for c in prop_name]).strip('-')


        csharp_output.append(f"                component.{csharp_prop_name} = _{uxml_attribute_name.replace('-', '_')}Attribute.GetValueFromBag(bag);")

    csharp_output.append("            }")
    csharp_output.append("        }")
    csharp_output.append("    }")
    csharp_output.append("}")

    return "\n".join(csharp_output)

# --- Example Usage ---
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python ast_to_csharp.py <ComponentName>")
        print("Example: python ast_to_csharp.py Button")
        sys.exit(1)

    component_to_generate = sys.argv[1]
    json_filename = f"{component_to_generate.lower()}_full_details.json"
    csharp_output_directory = "GeneratedCSharp"

    if os.path.exists(json_filename):
        with open(json_filename, 'r', encoding='utf-8') as f:
            mui_data = json.load(f)
        
        csharp_code = generate_csharp_component(mui_data["ComponentName"], mui_data)
        
        if not os.path.exists(csharp_output_directory):
            os.makedirs(csharp_output_directory)

        output_csharp_filename = os.path.join(csharp_output_directory, f"Mui{mui_data['ComponentName']}.cs")
        try:
            with open(output_csharp_filename, 'w', encoding='utf-8') as f:
                f.write(csharp_code)
            print(f"\nSuccessfully generated C# component to {output_csharp_filename}")
            print("\n--- Generated C# Content ---")
            print(csharp_code)
        except IOError as e:
            print(f"Error saving C# file to {output_csharp_filename}: {e}")
    else:
        print(f"Error: JSON file '{json_filename}' not found. Please run the scraping script (e.g., mui_docs_to_json_ast.py) first for '{component_to_generate}'.")

