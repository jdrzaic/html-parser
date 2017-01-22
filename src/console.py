import tree_builder

builder = tree_builder.TreeBuilder("www.index.com", """<!DOCTYPE html>
<html>
<body>

<h1 key='value'=value2>My First Heading</h1>

<p>My first paragraph.</p>
<!-- komentaaar -->

</body>
</html>""")

builder.parse()