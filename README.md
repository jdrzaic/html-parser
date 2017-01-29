# HTML parser
## Sample usage:
### From code:
```python
html_string = """
<!DOCTYPE html>
<html>
<head>
  <title>My First HTML</title>
</head>
<body>

<p>This is paragraph.</p>
<ul>
<li>
List item
</li>
</ul>
</body>
</html>
"""

html_tag.initialize_tags()  # add known HTML tags
builder = tree_builder.TreeBuilder(html_string)  # create parser
builder.parse()  # create DOM
```

### from file:
```bash
python src/console.py -f <html file>
```

