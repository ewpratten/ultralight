import requests
import flask
import json
import yaml
from datetime import datetime
import os

# Flask app configuration
app = flask.Flask(__name__, static_folder="static")
app.config['JSON_SORT_KEYS'] = False

# Handle Github tokens
GH_ID = os.environ.get("GH_CLI_ID", "")
GH_PRIV = os.environ.get("GH_CLI_PRIV", "")

# Caching
CACHE_SECONDS = 60

# Function to load the sources yml
def loadSourcesYML() -> dict:
    return yaml.load(open("sources.yml"))

# Index route
@app.route("/")
def handleIndex():

    # Load the index
    index = open("static/index.html", "r").read()

    # Build a flask response
    res = flask.make_response(index)

    # Add a caching header for Vercel
    res.headers.set('Cache-Control', f"s-maxage={CACHE_SECONDS}, stale-while-revalidate")

    return res

# Sources route
@app.route("/sources.yml")
def handleSources():

    # Load the sources file
    sources = open("sources.yml", "r").read()

    # Build a flask response
    res = flask.make_response(sources)

    # Add a caching header for Vercel
    res.headers.set('Cache-Control', f"s-maxage={CACHE_SECONDS}, stale-while-revalidate")

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
    res.headers.set('Cache-Control', f"s-maxage={CACHE_SECONDS}, stale-while-revalidate")

    # Set the content type
    res.headers.set('content-type', 'application/json')

    return res

@app.route("/api/artifact/<group>/<artifact>/versions")
def handleArtifactAPI(group, artifact):

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

    # Get version data
    version_data = []
    raw_versions = getAllValidVersions(repocode)
    for v in raw_versions:
        version_data.append({
            "code": v,
            "timestamp": raw_versions[v]["timestamp"]
        })


    # Build a flask response
    res = flask.make_response(flask.jsonify(
        {
            "success": True,
            "versions": version_data
        }
    ))

    # Add a caching header for Vercel
    res.headers.set('Cache-Control', f"s-maxage={CACHE_SECONDS}, stale-while-revalidate")

    # Set the content type
    res.headers.set('content-type', 'application/json')

    return res

@app.route("/api/artifact/<group>/<artifact>/shield")
def handleArtifactShieldAPI(group, artifact):

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

    # Get version data
    raw_versions = getAllValidVersions(repocode)
    latest_version = list(raw_versions.keys())[0]

    # Select correct title text based on inputs
    title_text = "Ultralight"
    if "d" in flask.request.args:
        title_text = flask.request.args.get("d")
    if title_text == "127.0.0.1":
        title_text = "Ultralight"

    # Create a response
    res = flask.make_response(flask.jsonify({
        "success": True,
        "redirect": True
    }), 302)
    res.headers.set("content-type", "application/x-maven-pom+xml")
    res.headers.set("Location", f"https://img.shields.io/badge/{title_text}-{latest_version}-blue")
    return res


# Generates a fake .pom file for input data
def generatePOMForPackage(group, artifact, version) -> str:
    return f"""
<project xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 http://maven.apache.org/xsd/maven-4.0.0.xsd" xmlns="http://maven.apache.org/POM/4.0.0" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <modelVersion>4.0.0</modelVersion>
  <groupId>{group}</groupId>
  <artifactId>{artifact}</artifactId>
  <version>{version}</version>
</project>
"""

def generateMavenMetadata(group, artifact, versions):

    # Get the latest timestamp
    latest_timestamp = 0
    for version in versions.values():
        if int(version["timestamp"]) > latest_timestamp:
            latest_timestamp = int(version["timestamp"])

    # Build a versions list
    generated_versions = ""
    for version in versions:
        generated_versions += f"<version>{version}</version>\n"

    latest_version = list(versions.keys())[0]

    # Build file
    return f"""
<metadata modelVersion="1.1.0">
  <groupId>{group}</groupId>
  <artifactId>{artifact}</artifactId>
  <version>{latest_version}</version>
  <versioning>
    <latest>{latest_version}</latest>
    <release>{latest_version}</release>
    <versions>
        {generated_versions}
    </versions>
    <lastUpdated>{latest_timestamp}</lastUpdated>
  </versioning>
</metadata>
"""

# Fetches a list of valid versions for a repository
def getAllValidVersions(repocode) -> dict:
    # Read from the GitHub API
    data = requests.get(f"https://api.github.com/repos/{repocode}/releases", auth=(GH_ID, GH_PRIV)).json()

    # Build version list
    output = {}
    for entry in data:
        output[entry["tag_name"].strip("v")] = {
            "url": entry["assets_url"],

            # Make a timestamp
            "timestamp": (datetime.strptime(entry["published_at"], '%Y-%m-%dT%H:%M:%SZ') - datetime(1970, 1, 1)).total_seconds(),
        }

    return output

# Fetches a JAR through GitHub
def fetchJAR(url, fmt):
    # Read from the GitHub API
    data = requests.get(url, auth=(GH_ID, GH_PRIV)).json()

    # Look for an entry in data with a matching filename
    for entry in data:
        if entry["name"] == fmt:
            res = flask.make_response(flask.jsonify({
                "success": True,
                "redirect": True
            }), 302)
            res.headers.set("content-type", "application/x-maven-pom+xml")
            res.headers.set("Location", entry["browser_download_url"])
            return res

    return flask.make_response("Not found", 404)

# Maven handler
@app.route("/maven/<path:path>")
def handleMaven(path):

    # Parse filepath
    pathComponents = path.split("/")

    # Get the requested filename
    filename = pathComponents[-1]
    file_ext = filename.split(".")[-1]

    # Handle non-metadata requests
    version: str
    artifact: str
    group: str
    if len(pathComponents) > 4:
        # Get the version
        version = pathComponents[-2]

        # Get the artifactID
        artifact = pathComponents[-3]

        # Get the groupID
        group = ".".join(pathComponents[:-3])
    if len(pathComponents) == 4 or filename == "maven-metadata.xml":
        # Get the artifactID
        artifact = pathComponents[-2]

        # Get the groupID
        group = ".".join(pathComponents[:-2])
    else:
        return "Artifact not found (parse error)", 404

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

    # Get a list of valid versions
    allAssetVersions = getAllValidVersions(repocode)

    # Handle requests to maven-metadata
    if filename == "maven-metadata.xml":
        res = flask.make_response(generateMavenMetadata(group, artifact, allAssetVersions))
        res.headers.set("content-type", "application/xml")
        res.headers.set('Cache-Control', f"s-maxage={CACHE_SECONDS}, stale-while-revalidate")
        return res

    # Make sure the requested version exists
    if version not in allAssetVersions.keys():
        return "Artifact does not have this version (yet?)", 404

    # If the request is for a pom file, generate one
    if file_ext == "pom":
        res = flask.make_response(generatePOMForPackage(group, artifact, version))
        res.headers.set("content-type", "application/java-archive")
        res.headers.set('Cache-Control', f"s-maxage={CACHE_SECONDS}, stale-while-revalidate")
        return res

    if file_ext == "jar":

        # Get the asset URL for this version
        assetURL = allAssetVersions[version]["url"]

        res = fetchJAR(assetURL, fmt.replace("{version}", version))
        res.headers.set('Cache-Control', f"s-maxage={CACHE_SECONDS}, stale-while-revalidate")
        return res

    return "Artifact not found", 404

# Runner for local development
if __name__ == "__main__":
    app.run(debug=True)