# Module 03 — Obsidian vault (knowledge base)

**Goal:** an atomic, wiki-linked knowledge base — the concept graph the book renders linearly. Every
key notion is one note; notes link liberally with `[[wikilinks]]`. Lecture MOCs (Maps of Content) tie
them together. Openable directly in Obsidian; also readable as plain Markdown on GitHub.

## Structure
```
vault/
  .obsidian/            (minimal config: graph, hotkeys)
  moc/00-index.md       (top-level MOC → the 6 lecture MOCs)
  moc/l1..l6.md         (one MOC per lecture)
  concepts/*.md         (atomic notes: lambda-term, beta-reduction, curry-howard, dependent-type, ...)
  lectures/*.md         (per-lecture running notes, linking concepts)
```

## Subtasks
- [x] `.obsidian` config + top-level MOC + 6 lecture MOCs.
- [x] Seed concept notes for Lectures 1–3 with wikilinks and a "see also" tail.
- [ ] Grow concept notes for Lectures 4–6 (tactics, typeclasses, autoformalization, EML).
- [ ] Backlink concepts to the book chapters and artifacts.

## Acceptance criteria
- Vault opens in Obsidian with a connected graph (no orphan MOCs).
- Every concept note has ≥1 inbound and ≥1 outbound link.
