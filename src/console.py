import tree_builder
import html_tag
import sys


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

ex3 = """
<!DOCTYPE html>
<html>
<body>

<p>This is a paragraph.</p>
<p>This is a paragraph.</p>
<p>This is a paragraph.</p>

</body>
</html>
"""

ex4 = """
<!DOCTYPE html>
<html>
<body>

<a href="http://www.w3schools.com">This is a link</a>

</body>
</html>
"""

ex5 = """
<!DOCTYPE html>
<html>
<body>

<img src="w3schools.jpg" alt="W3Schools.com" width="104" height="142">

</body>
</html>
"""

# check <p> attributes, not printed
ex6 = """
<!DOCTYPE html>
<html>
<body>

<h2>The title attribute</h2>

<p title="I'm a tooltip">
Mouse over this paragraph, to display the title attribute as a tooltip.
</p>

</body>
</html>
"""

ex7 = """
<!DOCTYPE html>
<html>
<body>

<a href="http://www.w3schools.com">This is a link</a>

</body>
</html>
"""

ex8 = """
<!DOCTYPE html>
<html>
<body>

<a href=http://www.w3schools.com>This is a link</a>

</body>
</html>
"""

ex9 = """
<!DOCTYPE html>
<html>
<body>

<h1>About W3Schools</h1>

<p title=About W3Schools>
You cannot omit quotes around an attribute value
if the value contains spaces.
</p>

<p><b>
If you move the mouse over the paragraph above,
your browser will only display the first word from the title.
</b></p>

</body>
</html>
"""

ex10 = """
<!DOCTYPE html>
<html>
<body>

<h1>This is heading 1</h1>
<p>This is some text.</p>
<hr>

<h2>This is heading 2</h2>
<p>This is some other text.</p>
<hr>

<h2>This is heading 2</h2>
<p>This is some other text.</p>

</body>
</html>
"""

# check what happend in head section
ex11 = """
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


def main():
    html_string = ex11
    args = sys.argv[1:]
    if len(args) == 2 and args[0] == "-f":
        filename = args[1]
        with open(filename, 'r') as f:
            html_string = f.read()
    html_tag.initialize_tags()
    builder = tree_builder.TreeBuilder(html_string)
    builder.parse()


if __name__ == "__main__":
    main()