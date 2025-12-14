import re

# Read the file
with open(r'c:\Users\chiri\Documents\GitHub\web-application-2025-group-37\app\templates\inventory.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Remove all items_edit links
content = re.sub(
    r'\s*<a href="\{\{ url_for\(\'main\.items_edit\', item_id=i\.item_id\) \}\}">.*?</a>\s*\n',
    '',
    content,
    flags=re.DOTALL
)

# Write back
with open(r'c:\Users\chiri\Documents\GitHub\web-application-2025-group-37\app\templates\inventory.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("Fixed items_edit references")
