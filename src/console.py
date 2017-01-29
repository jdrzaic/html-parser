import tree_builder
import html_tag


# fill with existing html tags
html_tag.initialize_tags()

ex1 = """<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN" "http://www.w3.org/TR/html4/strict.dtd">

<html>
<body>

<h1 key='value' key2>My FirstampHeading</h1>
<script></script><a href="wwww">fdgdhs</a>
<div><p class="aaa"></p></div>
<p key="value" key2=value2>My first paragraph.</p>
<!-- komentaaar -->

</body>
</html>"""

ex2 = """
<!DOCTYPE html>
<html>
<head>
<title>gdshsh</title>
</head>
<body>

<h1>This is heading 1</h1>
<h2>This is heading 2</h2>
<h3>This is heading 3</h3>
<h4>This is heading 4</h4>
<h5>This is heading 5</h5>
<h6>This is heading 6</h6>

</body>
</html>
"""
builder = tree_builder.TreeBuilder("www.index.com", ex2)

builder.parse()