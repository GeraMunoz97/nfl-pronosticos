import os
t=open("page_template.html").read(); os.makedirs("docs",exist_ok=True)
open("docs/index.html","w").write(t.replace("__DATA__",open("week.json").read()).replace("__HIST__",open("history.json").read()).replace("__LOG__",open("state/log.json").read()).replace("__PICKS__",open("state/picks.json").read()))
open("docs/.nojekyll","w").write(""); print("pagina ok -> docs/index.html")
