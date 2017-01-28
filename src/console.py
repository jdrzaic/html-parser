import tree_builder
import html_tag


# fill with existing html tags
html_tag.initialize_tags()


builder = tree_builder.TreeBuilder("www.index.com", """<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN" "http://www.w3.org/TR/html4/strict.dtd">

<html>
<body>

<h1 key='value' key2>My First Heading</h1>
<script></script>
<div><p class="aaa"></p></div>
<p key="value" key2=value2>My first paragraph.</p>
<!-- komentaaar -->

</body>
</html>""")

builder.parse()