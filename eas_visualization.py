"""Plotly-Abbildungen. Alle Achsen sind gesperrt (fixedrange), damit Touch-Geräte beim Scrollen nicht am Diagramm hängen bleiben."""

import plotly.graph_objects as go

import eas_constants as C


def lock_axes(fig):
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(fixedrange=True)
    return fig


def _base(fig, height=340):
    fig.update_layout(height=height, margin=dict(l=10, r=10, t=10, b=10), legend=dict(orientation="h", y=-0.25), plot_bgcolor="rgba(0,0,0,0)")
    return lock_axes(fig)


def blocker_cells(stacks) -> set:
    """Container, die über einem früher abzurufenden im selben Stapel liegen (Position (Stapel, Lage))."""
    out = set()
    for i, s in enumerate(stacks):
        lowest = 10 ** 9
        for j, c in enumerate(s):
            if c > lowest:
                out.add((i, j))
            else:
                lowest = c
    return out


def build_bay(stacks, height, target=None):
    """Die Bucht als Säulen: je Lage ein Balken mit der Abrufnummer. Rot: blockiert einen früher abzurufenden, grün: nächster Abruf
    (`target`, eine Abrufnummer oder None), grau-blau: übrige."""
    blockers = blocker_cells(stacks)
    fig = go.Figure()
    xs = list(range(len(stacks)))
    for j in range(height):
        ys, colors, texts = [], [], []
        for i, s in enumerate(stacks):
            if j < len(s):
                c = s[j]
                ys.append(1)
                texts.append(str(c))
                colors.append(C.COLOR_TARGET if c == target else C.COLOR_BLOCK if (i, j) in blockers else C.COLOR_CELL)
            else:
                ys.append(0)
                texts.append("")
                colors.append(C.COLOR_CELL)
        fig.add_trace(go.Bar(x=xs, y=ys, base=j, marker_color=colors, text=texts, textposition="inside", insidetextanchor="middle",
                             textfont=dict(color="#ffffff", size=16), width=0.78, showlegend=False,
                             hovertemplate="Abruf %{text}<extra></extra>", marker_line=dict(width=0)))
    fig.update_layout(barmode="overlay")
    fig.add_hline(y=height, line_dash="dot", line_color="rgba(128,128,128,0.7)", annotation_text="Höchsthöhe", annotation_position="top left")
    fig.update_xaxes(tickvals=xs, ticktext=[f"Stapel {i + 1}" for i in xs], showgrid=False)
    fig.update_yaxes(range=[0, height + 0.35], showticklabels=False, showgrid=False, zeroline=False)
    return _base(fig, height=48 * height + 90)


def _sigma_labels(sigmas):
    return [f"{s:g}".replace(".", ",") for s in sigmas]


def build_closed(cells):
    """Anteil der geschlossenen Lücke (Prozent) gegen den Schätzfehler, je Zelle eine Linie. `cells`: {"s,h,n": sigma_stats}."""
    fig = go.Figure()
    palette = ["#2F6B65", "#d9822b", "#4c78a8", "#b5545a", "#7a8fa6", "#1c4742"]
    for i, k in enumerate(sorted(cells, key=lambda k: tuple(int(x) for x in k.split(",")))):
        s, h, n = k.split(",")
        ys = [100.0 * cells[k]["closed"][f"{sg:g}"] for sg in C.SIGMA_OPTIONS]
        fig.add_trace(go.Scatter(x=_sigma_labels(C.SIGMA_OPTIONS), y=ys, mode="lines+markers", name=f"{s} Stapel, Höhe {h}, {n} Container", line=dict(color=palette[i % len(palette)]),
                                 hovertemplate="Schätzfehler %{x}: %{y:.0f} %<extra>%{fullData.name}</extra>"))
    fig.update_xaxes(type="category", title_text="Streuung des Schätzfehlers (in Vielfachen der Containerzahl)")
    fig.update_yaxes(title_text="geschlossener Anteil der Lücke (%)")
    return _base(fig, height=380)


def build_cost(stats):
    """Umlagerungen gegen den Schätzfehler für eine Zelle mit Untergrenze: Regel mit Schätzung, exaktes Optimum nach der Ablage, dazu als waagerechte Spuren niedrigster Stapel, zufälliger Stapel
    und Untergrenze. `stats`: lb_stats."""
    xs = _sigma_labels(C.LB_SIGMAS)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=xs, y=[stats["greedy"][f"{sg:g}"] for sg in C.LB_SIGMAS], mode="lines+markers", name="engste Passung nach Schätzung", line=dict(color=C.COLOR_RULES["tight"]),
                             hovertemplate="Schätzfehler %{x}: %{y:.2f}<extra>%{fullData.name}</extra>"))
    fig.add_trace(go.Scatter(x=xs, y=[stats["exact"][f"{sg:g}"] for sg in C.LB_SIGMAS], mode="lines+markers", name="exaktes Optimum nach der Ablage", line=dict(color=C.COLOR_RULES["full"], dash="dot"),
                             hovertemplate="Schätzfehler %{x}: %{y:.2f}<extra>%{fullData.name}</extra>"))
    for name, field, color in (("niedrigster Stapel", "lowest", C.COLOR_RULES["lowest"]), ("zufälliger Stapel", "random", C.COLOR_RULES["random"]), ("Untergrenze der besten Ablage", "lb", C.COLOR_LB)):
        fig.add_trace(go.Scatter(x=xs, y=[stats[field]] * len(xs), mode="lines", name=name, line=dict(color=color, dash="dash"), hovertemplate="%{y:.2f}<extra>%{fullData.name}</extra>"))
    fig.update_xaxes(type="category", title_text="Streuung des Schätzfehlers (in Vielfachen der Containerzahl)")
    fig.update_yaxes(title_text="Umlagerungen beim Abruf (Mittel)", rangemode="tozero")
    return _base(fig, height=380)


def build_rules(stats):
    """Mittlere Umlagerungen je Einlege-Regel (Balken), dazu die Untergrenze, wenn gerechnet. `stats`: sample_stats."""
    names, values, colors = [], [], []
    if "lb" in stats:
        names.append("Untergrenze"); values.append(stats["lb"]); colors.append(C.COLOR_LB)
    names += ["volles Wissen", "mit Schätzung", "niedrigster Stapel", "zufälliger Stapel"]
    values += [stats["full"], stats["tight"], stats["lowest"], stats["random"]]
    colors += [C.COLOR_RULES["full"], C.COLOR_RULES["tight"], C.COLOR_RULES["lowest"], C.COLOR_RULES["random"]]
    fig = go.Figure(go.Bar(x=names, y=values, marker_color=colors, text=[f"{v:.2f}".replace(".", ",") for v in values], textposition="outside", cliponaxis=False,
                           hovertemplate="%{x}: %{y:.2f}<extra></extra>"))
    fig.update_xaxes(type="category")
    fig.update_yaxes(title_text="Umlagerungen beim Abruf (Mittel)", rangemode="tozero")
    return _base(fig, height=320)
