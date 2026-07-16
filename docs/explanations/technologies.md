---
icon: lucide/wrench
---

# Technologiewahl

Trans\*DB ist über die Jahre gewachsen, und somit haben sich auch die Anforderungen an die Codebase verändet.

Früher basierte die Backend-Architektur auf **TypeScript** Code.
Es hatte den Vorteil, dass sich Features schnell prototypen ließen und man eine einheitliche Programmiersprache für Frontend & Backend hatte.

Es stellte sich jedoch heraus, dass das schnelllebige JavaScript Ökosystem für einen enormen Wartungsaufwand sorgt. Die genutzen Frameworks und Libraries wurden deprecated und ein Rewrite musste sowieso gemacht werden.

Die Anforderungen für die Wahl einer neuen Backend-Architektur waren daher klar:
Ein etabliertes Framework mit stabilem Ökosystem und sicherem Support, nicht noch mal "the new shiny thing".
Langweilig und *"Enterprise"* ist für diesen Case besser und sicherer.


Die Wahl viel auf **C#/.NET bzw. ASP.NET Core**.

Zum einen habe ich (die Maintainerin von Trans\*DB) meine Berufsausbildung auf dieser Sprache gemacht, was natürlich für den Rewrite wirklich hilfreich war.

Seit einigen Jahren sind die neueren .NET Versionen sowohl Cross-Platform als auch Open-Source.

Die Objektorientierung und ASP.NET Core bieten eine klare Struktur, was die Wartung und die Mitarbeit anderer Entwickler\*innen vereinfacht.

Da Microsoft hinter dem ganzen steht, kann man sich Sicher sein, dass C# und .NET noch für viele Jahre supported sein werden.

Auch wenn diese Entscheidung sicherlich auf einige Kritik innerhalb technikenthusiastischer Communities stoßen wird, hoffe ich, dass die Gründe nachvollziehbar sind.

Wir arbeiten ehrenamtlich an diesem Projekt und brauchen etwas, dass *einfach funktioniert* und nicht jedes Mal größere Umbauarbeiten nach sich zieht.