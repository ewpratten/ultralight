
// Set the buildsystem snippets
function setActiveVersionExample(group, artifact, version) {

    // Determine the current host
    var this_domain = getDomain();

    // Set gradle snippet
    var gradle_repo_block = document.getElementById("gradle-snippet-repositories");
    var gradle_deps_block = document.getElementById("gradle-snippet-deps");
    gradle_repo_block.innerText = gradle_repo_block.innerText.replace("\{domain\}", this_domain);
    gradle_deps_block.innerText = gradle_deps_block.innerText.replace("\{groupID\}", group)
        .replace("\{artifactID\}", artifact)
        .replace("\{version\}", version);

    // Set Bazel snippet
    var bazel_block = document.getElementById("bazel-snippet");
    bazel_block.innerHTML = bazel_block.innerHTML.replace("\{domain\}", this_domain)
        .replace("\{groupID\}", group)
        .replace("\{artifactID\}", artifact)
        .replace("\{version\}", version);

    // Set maven snippet
    var maven_repo_block = document.getElementById("maven-snippet-repositories");
    var maven_deps_block = document.getElementById("maven-snippet-deps");
    maven_repo_block.innerHTML = maven_repo_block.innerHTML.replace("\{host\}", window.location.hostname)
        .replace("\{domain\}", this_domain);
    maven_deps_block.innerHTML = maven_deps_block.innerHTML.replace("\{groupID\}", group)
        .replace("\{artifactID\}", artifact)
        .replace("\{version\}", version);
    
    // Set Sbt snippet
    var sbt_repo_block = document.getElementById("sbt-snippet-repositories");
    var sbt_deps_block = document.getElementById("sbt-snippet-deps");
    sbt_repo_block.innerText = sbt_repo_block.innerText.replace("\{domain\}", this_domain);
    sbt_deps_block.innerText = sbt_deps_block.innerText.replace("\{groupID\}", group)
        .replace("\{artifactID\}", artifact)
        .replace("\{version\}", version);

    // Set Leiningen snippet
    var leiningen_repo_block = document.getElementById("leiningen-snippet-repositories");
    var leiningen_deps_block = document.getElementById("leiningen-snippet-deps");
    leiningen_repo_block.innerText = leiningen_repo_block.innerText.replace("\{domain\}", this_domain);
    leiningen_deps_block.innerText = leiningen_deps_block.innerText.replace("\{groupID\}", group)
        .replace("\{artifactID\}", artifact)
        .replace("\{version\}", version);

    // document.getElementById("maven-snippet").innerText = "<repositories>\n    <repository>\n        <id>" + window.location.hostname + "</id>\n        <url>" + this_domain + "</url>\n    </repository>\n</repositories>\n\n<dependency>\n    <groupId>" + group + "</groupId>\n    <artifactId>" + artifact + "</artifactId>\n    <version>" + version + "</version>\n</dependency>";

}

function loadArtifactPage(group, artifact) {

    // Hide main page
    document.getElementById("listing").classList.add("hidden");

    // Unhide artifact loader
    document.getElementById("artifact-loader").classList.remove("hidden");

    // Set the shield
    document.getElementById("shield").innerHTML = "<img src='" + window.location.protocol + "//" + window.location.hostname + ":" + window.location.port + "/api/artifact/" + group + "/" + artifact + "/shield?d=" + window.location.hostname + "' />"
    document.getElementById("mdSnippet").innerText = "[![Maven Repository](" + window.location.protocol + "//" + window.location.hostname + ":" + window.location.port + "/api/artifact/" + group + "/" + artifact + "/shield?d=" + window.location.hostname + ")](" + window.location + ")";

    // Make an HTTP request
    const Http = new XMLHttpRequest();
    const url = "/api/artifact/" + group + "/" + artifact + "/versions";
    Http.open("GET", url);
    Http.send();

    // Handle response
    Http.onreadystatechange = (e) => {
        // Get response data
        var response;
        try {
            response = JSON.parse(Http.response);
        } catch (error) {
            return;
        }

        // Set all data
        if (response.success) {

            // Hide loader
            document.getElementById("artifact-loader").classList.add("hidden");

            // Clear the version listing
            document.getElementById("artifact-versions").innerHTML = "";

            // Show the artifact page
            document.getElementById("artifact").classList.remove("hidden");

            // Set the title
            document.getElementById("package-name").innerText = group + "." + artifact;

            // Iter each version
            response.versions.forEach((version) => {
                document.getElementById("artifact-versions").innerHTML += "<li><a href=\"#\" onclick=\"setActiveVersionExample('" + group + "','" + artifact + "','" + version.code + "');\">" + version.code + "</a></li>";
            })

            // Make a call to display the latest set of snippets
            setActiveVersionExample(group, artifact, response.versions[0].code);
        }
    };


}

