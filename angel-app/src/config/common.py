from os import environ, path

home = environ["HOME"]
angelDir = path.join(home, ".angel_app")

rootDir = path.join(angelDir, "repository")

from twisted.python.filepath import FilePath

if not FilePath(rootDir).exists():
    raise "angel-app root directory " + rootDir +" does not exist"
