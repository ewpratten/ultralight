import requests
import flask
import json
import yaml

# Flask app configuration
app = flask.Flask(__name__)
app.config['JSON_SORT_KEYS'] = False

# Function to load the sources yml
def loadSourcesYML() -> dict:
    return yaml.load(open("sources.yml"))

# Index route
@app.route("/")
def handleIndex():

    # Load the index
    index = open("index.html", "r").read()

    # Build a flask response
    res = flask.make_response(index)

    # Add a caching header for Vercel
    res.headers.set('Cache-Control', 's-maxage=1, stale-while-revalidate')

    return res

# Sources route
@app.route("/sources.yml")
def handleSources():

    # Load the sources file
    sources = open("sources.yml", "r").read()

    # Build a flask response
    res = flask.make_response(sources)

    # Add a caching header for Vercel
    res.headers.set('Cache-Control', 's-maxage=1, stale-while-revalidate')

    # Set the content type
    res.headers.set('content-type', 'application/yaml')

    return res

# Sources api
@app.route("/api/sources")
def handleSourcesAPI():

    # Get the YML config
    sources = loadSourcesYML()["sources"]
    output = []

    # Parse config
    for source in sources:
        output.append(source)

    # Build a flask response
    res = flask.make_response(flask.jsonify(
        {
            "success": True,
            "sources": output
        }
    ))

    # Add a caching header for Vercel
    res.headers.set('Cache-Control', 's-maxage=1, stale-while-revalidate')

    # Set the content type
    res.headers.set('content-type', 'application/json')

    return res

# Generates a fake .pom file for input data
def generatePOMForPackage(group, artifact, version) -> str:
    return f"""
<?xml version="1.0" encoding="UTF-8"?>
<project xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 http://maven.apache.org/xsd/maven-4.0.0.xsd" xmlns="http://maven.apache.org/POM/4.0.0" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <modelVersion>4.0.0</modelVersion>
  <groupId>{group}</groupId>
  <artifactId>{artifact}</artifactId>
  <version>{version}</version>
</project>
"""

# Fetches a list of valid versions for a repository
def getAllValidVersions(repocode) -> dict:
    # Read from the GitHub API
    data = requests.get(f"https://api.github.com/repos/{repocode}/releases").json()

    # Build version list
    output = {}
    for entry in data:
        output[entry["tag_name"].strip("v")] = entry["assets_url"]

    return output


# Fetches a JAR through GitHub
def fetchJAR(url, fmt):
    # Read from the GitHub API
    data = requests.get(url).json()

    # Look for an entry in data with a matching filename
    for entry in data:
        if entry["name"] == fmt:
            res = flask.make_response(flask.jsonify({
                "success": True,
                "redirect": True
            }))
            res.headers.set("content-type", "application/x-maven-pom+xml")
            res.headers.set("Location", entry["browser_download_url"])
            return res, 302

    return "Not found", 404

# Maven handler
@app.route("/maven/<path:path>")
def handleMaven(path):

    # Parse filepath
    pathComponents = path.split("/")

    # If there are less than 4 elements, throw an error
    if len(pathComponents) < 4:
        return "Artifact not found (parse error)", 404

    # Get the requested filename
    filename = pathComponents[-1]
    file_ext = filename.split(".")[-1]

    # Get the version
    version = pathComponents[-2]

    # Get the artifactID
    artifact = pathComponents[-3]

    # Get the groupID
    group = ".".join(pathComponents[:-3])

    # Check that the artifact exists
    repocode = ""
    fmt = ""
    for source in loadSourcesYML()["sources"]:
        if source["groupID"] == group and source["artifactID"] == artifact:
            repocode = source["github"]["owner"] + "/" + source["github"]["repository"]
            fmt = source["github"]["assetFormat"]
            break
    else:
        return "Artifact not on this server", 404

    # Make sure the requested version exists
    allAssetVersions = getAllValidVersions(repocode)
    if version not in allAssetVersions.keys():
        return "Artifact does not have this version (yet?)", 404

    # If the request is for a pom file, generate one
    if file_ext == "pom":
        res = generatePOMForPackage(group, artifact, version)
        res.headers.set('Cache-Control', 's-maxage=1, stale-while-revalidate')
        return res

    if file_ext == "jar":

        # Get the asset URL for this version
        assetURL = allAssetVersions[version]

        res = flask.make_response(fetchJAR(assetURL, fmt.replace("{version}", version)))
        res.headers.set("content-type", "application/java-archive")
        res.headers.set('Cache-Control', 's-maxage=1, stale-while-revalidate')
        return res

    return "Artifact not found", 404

# Runner for local development
if __name__ == "__main__":
    app.run(debug=True)