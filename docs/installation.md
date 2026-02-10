# Installation

## Stable release

To install metamaska, run this command in your
terminal:

``` console
$ pip install metamaska
```

This is the preferred method to install metamaska, as it will always install the most recent stable release.

If you don't have [pip][] installed, this [Python installation guide][]
can guide you through the process.

On first use, the ML model is automatically downloaded from HuggingFace and cached locally — no extra setup needed.

## From source

The source for metamaska can be downloaded from
the [Github repo][].

You can either clone the public repository:

``` console
$ git clone git://github.com/happyhackingspace/metamaska
```

Or download the [tarball][]:

``` console
$ curl -OJL https://github.com/happyhackingspace/metamaska/tarball/main
```

Once you have a copy of the source, you can install it with:

``` console
$ pip install .
```

  [pip]: https://pip.pypa.io
  [Python installation guide]: http://docs.python-guide.org/en/latest/starting/installation/
  [Github repo]: https://github.com/happyhackingspace/metamaska
  [tarball]: https://github.com/happyhackingspace/metamaska/tarball/main
