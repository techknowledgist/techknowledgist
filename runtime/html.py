HTML_PREFIX = """
<html>

<head>
<style>
.header, .section { margin-top: 3pt; }
.header { color: darkred; }
.header:before { content: "TYPE="; }
.section { padding: 3pt; padding-left: 6pt; padding-bottom: 0pt; border: solid darkblue thin }
.offset { color: darkblue; }
.padded { padding: 5pt; }
.bordered { padding: 5pt; border: thin solid black; }
</style>
</head>

<body>

"""

HTML_END = """
</body>
</html>
"""
