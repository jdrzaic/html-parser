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

ex12 = """
<!DOCTYPE html>
<html>
<body>

<p>I am normal</p>
<p style="color:red;">I am red</p>
<p style="color:blue;">I am blue</p>
<p style="font-size:36px;">I am big</p>

</body>
</html>

"""

ex13 = """
<!DOCTYPE html>
<html>
<body style="background-color:powderblue;">

<h1>This is a heading</h1>
<p>This is a paragraph.</p>

</body>
</html>
"""

ex14 = """
<!DOCTYPE html>
<html>
<body>

<h1 style="text-align:center;">Centered Heading</h1>
<p style="text-align:center;">Centered paragraph.</p>

</body>
</html>
"""

ex15 = """
<!DOCTYPE html>
<html>
<body>

<p>This text is normal.</p>

<p><b>This text is bold.</b>gshadhwhr<b>hsfhswhahd</b></p>

</body>
</html>
"""

ex16 = """
<!DOCTYPE html>
<html>
<body>

<p>This text is normal.</p>

<p><em>This text is emphasized.</em></p>
<p><b>This text is bold.</b>gshadhwhr<b>hsfhswhahd</b></p>

</body>
</html>
"""

ex17 = """
<!DOCTYPE html>
<html>
<body>

<p>This is <sup>superscripted</sup> text.</p>

</body>
</html>
"""

ex18 = """
<!DOCTYPE html>
<html>
<body>

<p>The <abbr title="World Health Organization">WHO</abbr> was founded in 1948.</p>

<p>Marking up abbreviations can give useful information to browsers, translation systems and search-engines.</p>

</body>
</html>
"""

ex19 = """
<!DOCTYPE html>
<html>
<body>

<!-- This is a comment -->
<p>This is a paragraph.</p>
<!-- Comments are not displayed in the browser -->

</body>
</html>
"""

ex20 = """
<!DOCTYPE html>
<html>
<head>
<style>
body {background-color: powderblue;}
h1   {color: blue;}
p    {color: red;}
</style>
</head>
<body>

<h1>This is a heading</h1>
<p>This is a paragraph.</p>

</body>
</html>
"""

ex21 = """
<!DOCTYPE html>
<html>
<body>

<p><a href="html_images.asp">HTML Images</a> is a link to a page on this website.</p>

<p><a href="http://www.w3.org/">W3C</a> is a link to a website on the World Wide Web.</p>

</body>
</html>
"""

ex22 = """
<!DOCTYPE html>
<html>
<body>

<img src="html5.gif" alt="HTML5 Icon" width="128" height="128">

</body>
</html>
"""

ex23 = """
<!DOCTYPE html>
<html>
<body>

<h2>HTML Tables</h2>

<p>HTML tables start with a table tag.</p>
<p>Table rows start with a tr tag.</p>
<p>Table data start with a td tag.</p>

<hr>
<h2>1 Column:</h2>

<table>
  <tr>
    <td>100</td>
  </tr>
</table>

<hr>
<h2>1 Row and 3 Columns:</h2>
<table>
  <tr>
    <td>100</td>
    <td>200</td>
    <td>300</td>
  </tr>
</table>

<hr>
<h2>3 Rows and 3 Columns:</h2>
<table>
  <tr>
    <td>100</td>
    <td>200</td>
    <td>300</td>
  </tr>
  <tr>
    <td>400</td>
    <td>500</td>
    <td>600</td>
  </tr>
  <tr>
    <td>700</td>
    <td>800</td>
    <td>900</td>
  </tr>
</table>

<hr>

</body>
</html>
"""

ex24 = """
<!DOCTYPE html>
<html>
<head>
<style>
table, th, td {
    border: 1px solid black;
    border-collapse: collapse;
}
th, td {
    padding: 5px;
}
</style>
</head>
<body>

<table style="width:100%">
  <tr>
    <th>Firstname</th>
    <th>Lastname</th>
    <th>Age</th>
  </tr>
  <tr>
    <td>Jill</td>
    <td>Smith</td>
    <td>50</td>
  </tr>
  <tr>
    <td>Eve</td>
    <td>Jackson</td>
    <td>94</td>
  </tr>
  <tr>
    <td>John</td>
    <td>Doe</td>
    <td>80</td>
  </tr>
</table>

</body>
</html>
"""

ex25 = """
<!DOCTYPE html>
<html>
<body>

<h2>An ordered HTML list</h2>

<ol>
  <li>Coffee</li>
  <li>Tea</li>
  <li>Milk</li>
</ol>

</body>
</html>
"""

ex26 = """
<!DOCTYPE html>
<html>
<body>

<h2>A Nested List</h2>

<ul>
  <li>Coffee</li>
  <li>Tea
    <ul>
    <li>Black tea</li>
    <li>Green tea</li>
    </ul>
  </li>
  <li>Milk</li>
</ul>

</body>
</html>
"""


def main():
    html_string = ex26
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