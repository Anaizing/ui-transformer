import pandas
import requests
from bs4 import BeautifulSoup

response = requests.get('https://mui.com/material-ui/react-button/')
if response.status_code != 200:
    print('Could not feth the page')
    exit(1)

print('Successfully fetched the page')

soup = BeautifulSoup(response.content, 'html.parser')
buttons = soup.find_all('button')


# Initialize an empty list to store the class names
button_class_names = []

# Step 1: Select the button elements using a CSS selector
# div[id^="demo"]    -> Selects div elements whose ID starts with "demo"
# > button           -> Selects direct child button elements within those divs
target_buttons = soup.select('div[id^="demo"] > button')

# Step 2: Iterate through the found buttons and extract their class names
for buttons in target_buttons:
    # Check if the button has a 'class' attribute
    if 'class' in buttons.attrs:
        # The 'class' attribute returns a list of class names
        button_class_names.extend(buttons['class'])
    else:
        # Optional: Handle buttons without a class attribute if needed
        # print(f"Button '{button.text}' has no class attribute.")
        pass

# Print the resulting list of class names
print("Extracted button class names:")
print(button_class_names)

# If you want unique class names:
unique_button_class_names = list(set(button_class_names))
print("\nUnique button class names:")
print(unique_button_class_names)



data_frame = pandas.DataFrame({'Button Classes': button_class_names})
data_frame.to_csv('butonclasses.csv', index=False, encoding='utf-8')
