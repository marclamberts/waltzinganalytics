"""
Delivery technique, post target, and data-driven routine clusters
======================================================================

``restart_routines`` tags every corner/free-kick delivery with a
``delivery_technique`` ("inswinger"/"outswinger", from Opta qualifiers
223/224) and a ``post_target`` ("near_post"/"far_post"/"central", relative
to which flank the restart was taken from), alongside the existing
rule-based ``routine_type`` taxonomy.

``cluster_routines`` offers a data-driven alternative to that fixed
taxonomy: k-means over delivery geometry, surfacing whatever patterns a
team actually repeats rather than only the hand-picked named buckets.
Requires the optional ``ml`` extra (scikit-learn).
"""

from pathlib import Path

from wa_setpieces import load_matches
from wa_setpieces.core.routines import cluster_routines, restart_routines
from wa_setpieces.viz.plots import plot_routine_clusters

try:
    _here = Path(__file__).resolve().parent
except NameError:
    _here = Path.cwd()
DATA = _here.parent / "tests" / "data" / "sample_match.json"

events = load_matches(DATA)

# %%
# Delivery technique and post target, alongside the existing taxonomy:
detail = restart_routines(events, "corner")
detail[["eventId", "routine_type", "delivery_technique", "post_target"]]

# %%
# Data-driven clusters, as an alternative to ``routine_type``'s hand-picked
# buckets -- each cluster's label is an auto-generated summary of its own
# average geometry:
clustered = cluster_routines(events, "corner", n_clusters=3, random_state=0)
clustered[["eventId", "cluster", "cluster_label"]]

# %%
fig, ax = plot_routine_clusters(clustered, title="Corner delivery clusters")
