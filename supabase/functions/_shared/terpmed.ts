import { normalizeId, type Tersona } from "./tersonas.ts";

type TerpMedCell = {
  column?: string;
  value?: string;
  query?: string;
  link?: string;
  summary?: string;
};

type TerpMedRow = {
  term?: string;
  cells?: TerpMedCell[];
};

type TerpMedPayload = {
  generated_at?: string;
  rows?: TerpMedRow[];
};

export type TerpMedCitation = {
  pmid: string;
  url: string;
};

export type TerpMedMatch = {
  term: string;
  terpene: string;
  count: number;
  query: string;
  link: string;
  summary?: string;
  citations: TerpMedCitation[];
};

let cachedPayload: { fetchedAt: number; data: TerpMedPayload } | null = null;

const TERPMED_URL = Deno.env.get("TERPMED_RESULTS_URL") || "https://terpmed.terpedia.com/results.json";
const TERPMED_CACHE_MS = 1000 * 60 * 30;

const TERSONA_COLUMN_ALIASES: Record<string, string[]> = {
  pinene: ["alpha-pinene"],
  caryophyllene: ["β-caryophyllene", "beta-caryophyllene", "caryophyllene"],
  myrcene: ["β-myrcene", "beta-myrcene", "myrcene"],
  bisabolol: ["α-bisabolol", "alpha-bisabolol", "bisabolol"],
};

const GENERIC_TERMS = new Set([
  "absorption",
  "analgesic",
  "antibacterial",
  "anti-inflammatory",
  "anti-oxidant",
  "antioxidant",
  "anti-anxiety",
  "sedative",
]);

export async function buildTerpMedContext(
  message: string,
  tersona: Tersona,
  options: { maxMatches?: number; includeGeneric?: boolean } = {},
): Promise<{ matches: TerpMedMatch[]; context: string }> {
  const payload = await loadTerpMedPayload();
  const rows = Array.isArray(payload.rows) ? payload.rows : [];
  const matchedRows = matchRows(message, rows, options.includeGeneric || false);
  if (!matchedRows.length) {
    return { matches: [], context: "" };
  }

  const columnNames = columnAliasesForTersona(tersona);
  const matches: TerpMedMatch[] = [];

  for (const row of matchedRows) {
    const term = String(row.term || "").trim();
    const cell = findCell(row, columnNames);
    if (!term || !cell?.query || !cell.link) continue;
    const count = parseCount(cell.value);
    const citations = await fetchTopPubMedIds(cell.query, 4);
    matches.push({
      term,
      terpene: cell.column || tersona.name,
      count,
      query: cell.query,
      link: cell.link,
      summary: cell.summary || undefined,
      citations,
    });
    if (matches.length >= (options.maxMatches || 3)) break;
  }

  return { matches, context: renderTerpMedContext(matches) };
}

function renderTerpMedContext(matches: TerpMedMatch[]): string {
  if (!matches.length) return "";
  const lines = matches.map((match) => {
    const citationText = match.citations.length
      ? ` Top PMIDs: ${match.citations.map((citation) => citation.pmid).join(", ")}.`
      : "";
    const summaryText = match.summary ? ` Summary: ${match.summary}` : "";
    return `- ${match.terpene} x ${match.term}: ${match.count.toLocaleString()} PubMed hits. Query: ${match.query}. Link: ${match.link}.${citationText}${summaryText}`;
  });

  return `\n\nTERPMED CONTEXT:\nUse this as retrieval context when relevant. Cite PMIDs as [PMID:123456] when using the PMID list, and make it clear these are PubMed search results, not proof of clinical efficacy.\n${lines.join("\n")}`;
}

async function loadTerpMedPayload(): Promise<TerpMedPayload> {
  const now = Date.now();
  if (cachedPayload && now - cachedPayload.fetchedAt < TERPMED_CACHE_MS) {
    return cachedPayload.data;
  }

  const response = await fetch(TERPMED_URL, {
    headers: { Accept: "application/json" },
  });
  if (!response.ok) {
    throw new Error(`TerpMed request failed (${response.status})`);
  }
  const data = await response.json();
  cachedPayload = { fetchedAt: now, data };
  return data;
}

function matchRows(message: string, rows: TerpMedRow[], includeGeneric: boolean): TerpMedRow[] {
  const normalizedMessage = normalizeText(message);
  const scored: Array<{ row: TerpMedRow; score: number }> = [];

  for (const row of rows) {
    const term = String(row.term || "").trim();
    if (!term || term === "compound-only") continue;
    const normalizedTerm = normalizeText(term);
    if (!includeGeneric && GENERIC_TERMS.has(normalizedTerm)) continue;
    if (normalizedMessage.includes(normalizedTerm)) {
      scored.push({ row, score: normalizedTerm.length + 100 });
      continue;
    }
    const tokens = normalizedTerm.split(/\s+/).filter((token) => token.length > 3);
    const hits = tokens.filter((token) => normalizedMessage.includes(token)).length;
    if (hits > 0 && tokens.length > 0) {
      scored.push({ row, score: hits / tokens.length + hits });
    }
  }

  return scored.sort((a, b) => b.score - a.score).map((item) => item.row);
}

function findCell(row: TerpMedRow, aliases: string[]): TerpMedCell | undefined {
  const cells = Array.isArray(row.cells) ? row.cells : [];
  const normalizedAliases = aliases.map(normalizeColumn);
  return cells.find((cell) => normalizedAliases.includes(normalizeColumn(cell.column || "")));
}

function columnAliasesForTersona(tersona: Tersona): string[] {
  const normalized = normalizeId(tersona.id);
  const aliases = TERSONA_COLUMN_ALIASES[normalized] || [];
  return [tersona.id, tersona.name, ...aliases];
}

function parseCount(value: unknown): number {
  const parsed = Number.parseInt(String(value || "0").replace(/,/g, ""), 10);
  return Number.isFinite(parsed) ? parsed : 0;
}

function normalizeColumn(value: string): string {
  return normalizeText(value)
    .replace(/^alpha pinene$/, "alpha-pinene")
    .replace(/^beta pinene$/, "beta-pinene")
    .replace(/^beta caryophyllene$/, "beta-caryophyllene")
    .replace(/^beta myrcene$/, "beta-myrcene")
    .replace(/^alpha bisabolol$/, "alpha-bisabolol");
}

function normalizeText(value: string): string {
  return value
    .toLowerCase()
    .replace(/[α]/g, "alpha")
    .replace(/[β]/g, "beta")
    .replace(/[γ]/g, "gamma")
    .replace(/["']/g, "")
    .replace(/[^a-z0-9]+/g, " ")
    .trim();
}

async function fetchTopPubMedIds(query: string, retmax: number): Promise<TerpMedCitation[]> {
  const params = new URLSearchParams({
    db: "pubmed",
    term: query,
    retmode: "json",
    retmax: String(retmax),
    sort: "relevance",
  });
  const apiKey = Deno.env.get("NCBI_API_KEY");
  if (apiKey) params.set("api_key", apiKey);

  const response = await fetch(`https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?${params}`);
  if (!response.ok) return [];
  const data = await response.json();
  const ids = data?.esearchresult?.idlist;
  if (!Array.isArray(ids)) return [];
  return ids.map((pmid: string) => ({
    pmid,
    url: `https://pubmed.ncbi.nlm.nih.gov/${pmid}/`,
  }));
}
