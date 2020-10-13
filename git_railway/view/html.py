# This file is part of "git-railway" which is released under GPL.
#
# See file LICENCE or go to http://www.gnu.org/licenses/ for full license
# details.
#
# git-railway is top-like TUI for Austin.
#
# Copyright (c) 2018-2020 Gabriele N. Tornetta <phoenix1987@gmail.com>.
# All rights reserved.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


# TODO: Split into resource files
import json


TEMPLATE = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>{title} - Git Railway</title>
  <style>
    @import url('https://fonts.googleapis.com/css2?family=Ubuntu+Mono:wght@400;700&display=swap');

    html, body {{
      width: 100%;
      height: 100%;
      margin: 0;
      font-family: "Ubuntu Mono", monospace;
      background-color: #4e545b;
    }}

    #app {{
        display: flex;
        flex-direction: row;
        height: 100%;
        overflow:none;
    }}

    #railway {{
        flex: 1 0 auto;
        overflow-y: auto;
    }}

    #railway_svg {{
        position: relative;
        left: 50%;
        transform: translate(-50%);
    }}

    #info {{
        flex: 1 1 auto;
        height: 100%;
        position: relative;
    }}

    #infobox {{
        color: #dddddd;
        background-color: #323232;
        background-color: rgba(50, 50, 50, 0.9);
        border-radius: 12px;
        padding: 24px;
        width: 100%;
        max-width: 480px;
        height: 320px;
        position: fixed;
        /*top: 50%;
        bottom: 50%;
        left: 50%;
        transform: translate(-50%, -50%);*/
        display: flex;
        flex-direction: column;
        visibility: hidden;
        opacity: 0%;
        transition: opacity 0.1s linear;
        -webkit-box-shadow: 0px 0px 64px -16px rgba(0,0,0,0.75);
        -moz-box-shadow: 0px 0px 64px -16px rgba(0,0,0,0.75);
        box-shadow: 0px 0px 64px -16px rgba(0,0,0,0.75);
        backdrop-filter: blur(8px);
    }}

    #message {{
        padding: 8px 0;
        font-family: "Ubuntu Mono", "monospace";
        font-size: 90%;
        flex: 1 0 0;
        white-space: pre-wrap;
        overflow-y: auto;
        min-height: 0;
        line-height: 1.25;
    }}

    #hash {{
        font-weight: bold;
        color: #d07d49;
        padding-right: .5em;
    }}

    .cc {{
        padding: 2px 8px;
    }}

    #type {{
        background: #282828;
        color: #5ce7f5;
    }}

    #scope {{
        background: #5ce7f5;
        color: #282828;
    }}

    #title {{
        font-weight: bold;
        color: #e8e9a9;
        padding-left: .5em;
        line-height: 1.25;
    }}

    .metadata {{
        font-size: 90%;
        padding: 2px 0;
    }}

    .date {{
        color: #57df6c;
    }}

    #infobox a {{
        color: #5992c1;
        font-weight: bold;
    }}

    .stop:hover {{
        r: 6;
    }}

    #railway::-webkit-scrollbar-track, #railway::-webkit-scrollbar-track {{
      -webkit-box-shadow: inset 0 0 6px rgba(0, 0, 0, 0.3);
      border-radius: 8px;
      background-color: #A5A5A5;
    }}

    #railway::-webkit-scrollbar, #railway::-webkit-scrollbar {{
      width: 8px;
      height: 8px;
      border-radius: 8px;
      background-color: #A5A5A5;
    }}

    #railway::-webkit-scrollbar-thumb, #railway::-webkit-scrollbar-thumb {{
      border-radius: 8px;
      -webkit-box-shadow: inset 0 0 6px rgba(0, 0, 0, 0.3);
      background-color: #555;
    }}
  </style>
</head>

<body>
    <div id="app">
        <div id="railway">{svg}</div>
        <!--<div id="info">-->
            <div id="infobox">
                <div><span id="hash"></span><span id="type" class="cc"></span><span id="scope" class="cc"></span><span id="title"></span></div>
                <pre id="message"></pre>
                <div class="metadata">
                    Authored by <span class="actor" id="author"></span> (<span class="date" id="authored-date"></span>)
                </div>
                <div class="metadata">
                    Committed by <span class="actor" id="committer"></span> (<span class="date" id="committed-date"></span>)
                </div>
            </div>
        <!--</div>-->
    </div>

    <script>
        let data = {data};
        var infoboxTimer;

        window.addEventListener('mouseover', (e) => {{
            if (data[e.target.id]) {{
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
                if (commit.message.type) {{
                    type.style.display = "inline";
                    type.innerHTML = commit.message.type;
                }} else {{
                    type.style.display = "none";
                }}
                if (commit.message.scope) {{
                    scope.style.display = "inline";
                    scope.innerHTML = commit.message.scope;
                }} else {{
                    scope.style.display = "none";
                }}
                title.innerHTML = commit.message.title;
                message.innerHTML = commit.message.body;
                author.innerHTML = commit.author
                committer.innerHTML = commit.committer
                authored_date.innerHTML = commit.authored_date_delta
                authored_date.setAttribute("title", commit.authored_date)
                committed_date.innerHTML = commit.committed_date_delta
                committed_date.setAttribute("title", commit.committed_date)
            }}

            if (!e.target.id.includes("railway")) {{
                if (infoboxTimer != null) {{
                    clearTimeout(infoboxTimer);
                    infoboxTimer = null;
                }}
            }} else {{
                if (infoboxTimer == null) {{
                    infoboxTimer = setTimeout(
                        function () {{
                            document.getElementById("infobox").style.opacity = "0%";
                            document.getElementById("infobox").style.visibility = "hidden";
                            infoboxTimer = null;
                        }},
                        200
                    );
                }}
            }}

        }})
    </script>
</body>
</html>
"""


def write_html(stream, svg: str, commit_data, title: str) -> None:
    stream.write(
        TEMPLATE.format(svg=svg, data=json.dumps(commit_data), title=title).encode(
            "utf-8"
        )
    )
