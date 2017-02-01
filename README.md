# HTML parser
## Sample usage
### From string:
#### Parser
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

#### Tokenizer
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
t = tokeniser.Tokeniser(util.Reader(html_string))
print(t.tokenise())
```

### from file:
#### Parser
```bash
python src/console_parser.py -f <html file>
```
#### Tokeniser
```bash
python src/console_tokeniser.py -f <html file>
```
