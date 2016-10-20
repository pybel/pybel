![PyBEL Logotype](PyBEL-logotype-1024.png)

#The PyBEL Logo

##Usage Guidelines and Information
Feel free to use the PyBEL logos to represent the use of PyBEL in your projects. The full logotype version is preferred in most contexts, but the square version may be used in locations with limited space. However, please do not use just the bell icon without the "Py" text inside.

The text in the PyBEL logos is set in Optima Bold Italic with manual kerning and adjustments. Some SVG versions of the logos may have the text converted to paths to allow display on a wider variety of systems.

Keep approximately one "bell worth" of space between the logotype and other elements. Approximately 30% whitespace should be left around the square version.

Inverting the colors of the logos may be appropriate to match with the context in which the logo is being displayed. However, please do not recolor, stretch, skew, or otherwise modify the logos when using them to represent the PyBEL project.

When mentioned in text, the project name should be styled as PyBEL, with only the "y" in lowercase. Generally, write the name in plain text instead of embedding the logo inline.

The PyBEL logos were created as vector graphics in Inkscape and rasterized to PNG with Inkscape as well. The PNG versions were then [optimized](https://blog.codinghorror.com/zopfli-optimization-literally-free-bandwidth/) using `optipng` and `advdef`:
```sh
optipng -o2 -nb *.png && advdef -z -4 *.png
```

##License
The PyBEL logos are derivatives of "[Ringing bell](http://game-icons.net/lorc/originals/ringing-bell.html)" by [Lorc](https://lorcblog.blogspot.com/), used under [CC BY 3.0](http://creativecommons.org/licenses/by/3.0/). The PyBEL logos are licensed under [CC BY 3.0](http://creativecommons.org/licenses/by/3.0/) by Scott Colby.
