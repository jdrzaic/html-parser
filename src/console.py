import tree_builder

builder = tree_builder.TreeBuilder("www.index.com", """<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN" "http://www.w3.org/TR/html4/strict.dtd">

<html>
<body>

<h1 key='value' key2>My First Heading</h1>
<script></script>
<p>My first paragraph.</p>
<!-- komentaaar -->

</body>
</html>""")

builder.parse()