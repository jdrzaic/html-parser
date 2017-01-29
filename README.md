# HTML parser
## Sample usage:

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
