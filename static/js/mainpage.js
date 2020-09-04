
// Handler for the main page
function loadMainPageArtifacts() {
    // Make an HTTP request
    const Http = new XMLHttpRequest();
    const url = "/api/sources";
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
            document.getElementById("listing-loader").classList.add("hidden");

            // Clear the artifact listing
            document.getElementById("artifact-listing").innerHTML = "";

            // Iter each artifact
            response.sources.forEach((source) => {
                var name = source.groupID + "." + source.artifactID;

                // Build artifact element
                document.getElementById("artifact-listing").innerHTML += "<li class='list-group-item'><a href='/?a=" + source.artifactID + "&g=" + source.groupID + "'>" + name + "</a></li>";
            })

        }
    };
}