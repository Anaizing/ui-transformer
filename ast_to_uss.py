import json
import os
import sys # Import the sys module to access command-line arguments

def generate_uss_from_mui_json(json_data):
    """
    Generates a Unity Style Sheet (USS) string from the Material UI component JSON data.
    This function translates Material UI concepts (classes, inferred props) into USS rules.

    Args:
        json_data (dict): The parsed JSON data of a Material UI component,
                          including ComponentVariations.

    Returns:
        str: A string containing the generated USS rules.
    """
    uss_output = []
    
    # --- Define common USS variables (Unity Custom Properties) ---
    # These mimic Material UI's theming concepts for colors and spacing.
    # You would expand and fine-tune these based on your Unity project's theme.
    uss_output.append(":root {")
    uss_output.append("    --primary-color: #1976d2;") # Material UI default primary blue
    uss_output.append("    --secondary-color: #9c27b0;") # Material UI default secondary purple
    uss_output.append("    --error-color: #d32f2f;")
    uss_output.append("    --info-color: #0288d1;")
    uss_output.append("    --success-color: #2e7d32;")
    uss_output.append("    --warning-color: #ed6c02;")
    uss_output.append("    --text-color-light: #ffffff;")
    uss_output.append("    --text-color-dark: rgba(0, 0, 0, 0.87);")
    uss_output.append("    --disabled-opacity: 0.38;")
    uss_output.append("    --spacing-1: 4px;") # Roughly 1 unit in MUI (8px base * 0.5)
    uss_output.append("    --spacing-2: 8px;") # Material UI default 8px spacing
    uss_output.append("    --spacing-3: 12px;")
    uss_output.append("    --spacing-4: 16px;")
    uss_output.append("    --font-size-small: 13px;")
    uss_output.append("    --font-size-medium: 14px;")
    uss_output.append("    --font-size-large: 15px;")
    uss_output.append("}")
    uss_output.append("\n")

    component_name = json_data.get("ComponentName", "Component")
    uss_output.append(f"/* USS Rules for {component_name} Component */\n")

    # --- Common base styles for the component ---
    # These are derived from Mui[ComponentName]-root classes
    # This acts as a foundation for all variations of the component.
    base_selector = f".Mui{component_name}-root"
    uss_output.append(f"{base_selector} {{")
    uss_output.append("    -unity-font-definition: var(--unity-font-regular);") # Assuming a default font
    uss_output.append("    -unity-font-style: normal;")
    uss_output.append("    -unity-text-align: middle-center;")
    uss_output.append("    border-radius: 4px;")
    uss_output.append("    cursor: pointer;")
    uss_output.append("    transition-property: background-color, border-color, color, opacity, shadow-color, shadow-offset, shadow-blur, shadow-width;") # Added shadow transitions
    uss_output.append("    transition-duration: 0.15s;")
    uss_output.append("    transition-timing-function: ease-out;")
    uss_output.append("    flex-direction: row;") # Most Material UI components are horizontal by default
    uss_output.append("    align-items: center;")
    uss_output.append("    justify-content: center;")
    uss_output.append("    min-width: 64px;") # Min width for buttons
    uss_output.append("    min-height: 36px;") # Min height for buttons
    uss_output.append("}\n")


    # --- Iterate through each ComponentVariation to generate specific rules ---
    for variation in json_data.get("ComponentVariations", []):
        variation_name = variation.get("VariationName", "UnnamedVariation").replace(" ", "-").replace("_", "-")
        associated_classes = variation.get("AssociatedClasses", [])
        inferred_props = variation.get("InferredProps", {})
        parsed_component_data = variation.get("ParsedComponent", {}) # Get parsed component data

        # Filter out common base classes to create specific selectors for variations
        specific_classes = [
            cls for cls in associated_classes 
            if cls != f"Mui{component_name}-root" and cls != "MuiButtonBase-root" 
        ]
        
        # Create a unique USS selector for this variation
        # Combine generic root class with specific classes for strong specificity
        selector = f".Mui{component_name}-root"
        for cls in specific_classes:
            # For utility classes like 'css-xxxxxx', don't add them directly to selector
            if not cls.startswith('css-'):
                selector += f".{cls}"
        
        # If no specific classes other than root, add a descriptive class based on inferred props
        # This is a fallback and might create less readable selectors, but ensures uniqueness
        if not specific_classes and inferred_props:
            prop_suffix = []
            if inferred_props.get("variant"): prop_suffix.append(f"variant-{inferred_props['variant']}")
            if inferred_props.get("color"): prop_suffix.append(f"color-{inferred_props['color']}")
            if inferred_props.get("size"): prop_suffix.append(f"size-{inferred_props['size']}")
            if prop_suffix:
                selector += f".{'-'.join(prop_suffix)}"
        
        # Ensure selector is valid USS (no leading dots for combined selectors)
        if selector.startswith(".."):
            selector = selector[1:]

        uss_output.append(f"/* {variation_name} */")
        uss_output.append(f"{selector} {{")

        # --- Apply styles based on inferred properties ---
        variant = inferred_props.get("variant")
        color = inferred_props.get("color")
        size = inferred_props.get("size")
        disabled = inferred_props.get("disabled") == "true"
        loading = inferred_props.get("loading") == "true"
        
        # Determine elevation from ParsedComponent.Props if available
        # Material UI default elevation values for buttons are typically low (0-8)
        elevation = parsed_component_data.get("Props", {}).get("elevation")
        if elevation:
            try:
                elevation_level = int(elevation)
                # Simplified mapping for common shadows in Unity UI
                # You'd need a more precise lookup for full Material UI shadow fidelity
                if elevation_level > 0:
                    uss_output.append("    shadow-color: rgba(0, 0, 0, 0.2);")
                    uss_output.append(f"    shadow-offset: {elevation_level * 0.5}px {elevation_level * 0.5}px;")
                    uss_output.append(f"    shadow-blur: {elevation_level * 1.5}px;")
                    uss_output.append("    shadow-width: 0px;") # Typically no spread in Material UI shadows
                else:
                    uss_output.append("    shadow-color: rgba(0, 0, 0, 0);") # No shadow
            except ValueError:
                pass # Ignore if elevation is not a valid number

        # Variant specific styles
        if variant == "contained":
            uss_output.append(f"    background-color: var(--{color}-color, var(--primary-color));")
            uss_output.append("    color: var(--text-color-light);")
            uss_output.append("    border-width: 0px;")
            uss_output.append("    -unity-background-image-tint-color: rgba(255, 255, 255, 0);") # Clear tint for solid color
            # Close rule block temporarily to add pseudo-states
            uss_output.append(f"}}")
            uss_output.append(f"{selector}:hover {{")
            uss_output.append(f"    background-color: color-mix(in srgb, var(--{color}-color, var(--primary-color)) 90%, black);") # Darken on hover
            if elevation:
                uss_output.append("    shadow-offset: 1px 1px;") # Example hover shadow
                uss_output.append("    shadow-blur: 3px;")
            uss_output.append(f"}}")
            uss_output.append(f"{selector}:active {{")
            uss_output.append(f"    background-color: color-mix(in srgb, var(--{color}-color, var(--primary-color)) 80%, black);") # Darken more on active
            uss_output.append(f"}}")
            uss_output.append(f"{selector} {{") # Re-open for other styles
        elif variant == "outlined":
            uss_output.append("    background-color: rgba(0, 0, 0, 0);") # Transparent background
            uss_output.append(f"    color: var(--{color}-color, var(--primary-color));")
            uss_output.append(f"    border-color: var(--{color}-color, var(--primary-color));")
            uss_output.append("    border-width: 1px;")
            uss_output.append("    -unity-background-image-tint-color: rgba(255, 255, 255, 0);") # Clear tint for transparent background
            # Close rule block temporarily to add pseudo-states
            uss_output.append(f"}}")
            uss_output.append(f"{selector}:hover {{")
            uss_output.append(f"    background-color: color-mix(in srgb, var(--{color}-color, var(--primary-color)) 10%, transparent);") # Light tint on hover
            uss_output.append(f"}}")
            uss_output.append(f"{selector}:active {{")
            uss_output.append(f"    background-color: color-mix(in srgb, var(--{color}-color, var(--primary-color)) 20%, transparent);") # Stronger tint on active
            uss_output.append(f"}}")
            uss_output.append(f"{selector} {{") # Re-open for other styles
        elif variant == "text": # Default Material UI Button variant
            uss_output.append("    background-color: rgba(0, 0, 0, 0);") # Transparent background
            uss_output.append(f"    color: var(--{color}-color, var(--primary-color));")
            uss_output.append("    border-width: 0px;")
            uss_output.append("    -unity-background-image-tint-color: rgba(255, 255, 255, 0);") # Clear tint for transparent background
            # Close rule block temporarily to add pseudo-states
            uss_output.append(f"}}")
            uss_output.append(f"{selector}:hover {{")
            uss_output.append(f"    background-color: color-mix(in srgb, var(--{color}-color, var(--primary-color)) 10%, transparent);") # Light tint on hover
            uss_output.append(f"}}")
            uss_output.append(f"{selector}:active {{")
            uss_output.append(f"    background-color: color-mix(in srgb, var(--{color}-color, var(--primary-color)) 20%, transparent);") # Stronger tint on active
            uss_output.append(f"}}")
            uss_output.append(f"{selector} {{") # Re-open for other styles
        
        # Size specific styles
        if size == "small":
            uss_output.append("    padding: var(--spacing-1) var(--spacing-2);")
            uss_output.append("    -unity-font-size: var(--font-size-small);")
        elif size == "large":
            uss_output.append("    padding: var(--spacing-2) var(--spacing-3);")
            uss_output.append("    -unity-font-size: var(--font-size-large);")
        else: # Medium (default)
            uss_output.append("    padding: var(--spacing-2) var(--spacing-2);")
            uss_output.append("    -unity-font-size: var(--font-size-medium);")

        # Disabled state
        if disabled:
            uss_output.append("    -unity-pointer-events: none;")
            uss_output.append("    opacity: var(--disabled-opacity);")
            if variant == "contained":
                uss_output.append("    background-color: rgba(0, 0, 0, 0.12);") # Lighter disabled background
            elif variant == "outlined":
                uss_output.append("    border-color: rgba(0, 0, 0, 0.26);")
                uss_output.append("    color: rgba(0, 0, 0, 0.26);")
            else: # text
                uss_output.append("    color: rgba(0, 0, 0, 0.26);")

        # Loading state (example for LoadingButton)
        if loading:
            # For USS, this might involve styling a child element or changing opacity.
            uss_output.append("    opacity: 0.7;") # Dim button when loading
            # In UXML, you'd likely have a specific child VisualElement (e.g., a spinner).
            # We would define styles for that child here if we knew its class/name.
            # E.g., uss_output.append(f"{selector} .MuiCircularProgress-root {{ display: flex; }}")
            # uss_output.append(f"{selector} Label {{ display: none; }}") # Hide text label

        # Apply RawInlineStyleRules directly from ParsedComponent's sx prop
        # These are expected to be simple CSS property-value pairs
        raw_inline_styles = parsed_component_data.get("RawInlineStyleRules")
        if raw_inline_styles:
            uss_output.append("    /* Raw inline styles from sx prop */")
            for prop, value in raw_inline_styles.items():
                # Unity USS might not support all CSS properties directly or might have different names.
                # A more advanced solution would map these to USS equivalents.
                # For now, a direct paste is used.
                uss_output.append(f"    {prop}: {value};")


        uss_output.append("}\n")

    return "\n".join(uss_output)

# --- Example Usage ---
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python ast_to_uss.py <ComponentName>")
        print("Example: python ast_to_uss.py Button")
        sys.exit(1)

    component_to_generate = sys.argv[1]
    json_filename = f"{component_to_generate.lower()}_full_details.json"
    output_uss_directory = "GeneratedUSS" # Define a directory for USS files
    
    # Ensure the output directory exists
    if not os.path.exists(output_uss_directory):
        os.makedirs(output_uss_directory)

    if os.path.exists(json_filename):
        with open(json_filename, 'r', encoding='utf-8') as f:
            mui_data = json.load(f)
        
        uss_rules = generate_uss_from_mui_json(mui_data)
        
        output_uss_filename = os.path.join(output_uss_directory, f"{mui_data['ComponentName'].lower()}_styles.uss")
        try:
            with open(output_uss_filename, 'w', encoding='utf-8') as f:
                f.write(uss_rules)
            print(f"\nSuccessfully generated USS rules to {output_uss_filename}")
            print("\n--- Generated USS Content ---")
            print(uss_rules)
        except IOError as e:
            print(f"Error saving USS data to file {output_uss_filename}: {e}")
    else:
        print(f"Error: JSON file '{json_filename}' not found. Please ensure it has been generated by docs_to_json_ast.py for '{component_to_generate}'.")

