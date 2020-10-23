let data = ((% data %));
var infoboxTimer;

window.addEventListener('mouseover', (e) => {
    if (data[e.target.id]) {
        infobox = document.getElementById("infobox");
        maxY = window.innerHeight - infobox.offsetHeight;
        infobox.style.top = Math.min(e.clientY, maxY) + "px";
        infobox.style.left = e.clientX + 12 + "px";

        hash = document.getElementById("hash");
        type = document.getElementById("type");
        scope = document.getElementById("scope");
        title = document.getElementById("title");
        message = document.getElementById("message");
        author = document.getElementById("author");
        authored_date = document.getElementById("authored-date");
        committer = document.getElementById("committer");
        committed_date = document.getElementById("committed-date");

        document.getElementById("infobox").style.visibility = "visible";
        document.getElementById("infobox").style.opacity = "100%";

        commit = data[e.target.id]
        hash.innerHTML = commit.hash;
        if (commit.message.type) {
            type.style.display = "inline";
            type.innerHTML = commit.message.type;
        } else {
            type.style.display = "none";
        }
        if (commit.message.scope) {
            scope.style.display = "inline";
            scope.innerHTML = commit.message.scope;
        } else {
            scope.style.display = "none";
        }
        title.innerHTML = commit.message.title;
        message.innerHTML = commit.message.body;
        author.innerHTML = commit.author
        committer.innerHTML = commit.committer
        authored_date.innerHTML = commit.authored_date_delta
        authored_date.setAttribute("title", commit.authored_date)
        committed_date.innerHTML = commit.committed_date_delta
        committed_date.setAttribute("title", commit.committed_date)
    }

    if (!e.target.id.includes("railway")) {
        if (infoboxTimer != null) {
            clearTimeout(infoboxTimer);
            infoboxTimer = null;
        }
    } else {
        if (infoboxTimer == null) {
            infoboxTimer = setTimeout(
                function () {
                    document.getElementById("infobox").style.opacity = "0%";
                    document.getElementById("infobox").style.visibility = "hidden";
                    infoboxTimer = null;
                },
                200
            );
        }
    }
})
