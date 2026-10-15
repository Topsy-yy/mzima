import { writeFile, readFile } from 'node:fs/promises';
import { resolve } from 'node:path';

type Credit = {
  key: string;
  query: string;
  src: string;
  photographer: string;
  photoPage: string;
};

const searches: { key: string; query: string }[] = [
  { key: 'hero', query: 'medical equipment soft light' },
  { key: 'problem', query: 'empty hospital corridor' },
  { key: 'problem-desk', query: 'clipboard desk clinic' },
  { key: 'walkin', query: 'waiting room chairs empty' },
  { key: 'triage', query: 'pastel medicine bottles' },
  { key: 'appointments', query: 'calendar desk minimal' },
  { key: 'story', query: 'plant window clinic' },
  { key: 'signup', query: 'clinic hallway light' },
];

const CREDITS_PATH = resolve(process.cwd(), 'src/data/photo-credits.json');
const SEARCH_URL = (q: string) =>
  `https://unsplash.com/s/photos/${encodeURIComponent(q.replace(/\s+/g, '-'))}`;

async function scrapeOne(key: string, query: string): Promise<Credit | null> {
  try {
    const response = await fetch(SEARCH_URL(query), {
      headers: { 'User-Agent': 'Mozilla/5.0 (compatible; MzimaImageFetcher/1.0)' },
    });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const html = await response.text();
    const imageMatch = html.match(/https:\/\/images\.unsplash\.com\/photo-[A-Za-z0-9_-]+\?[^"'\s]*/);
    if (!imageMatch) throw new Error('no image url found');
    // Normalise to a stable landscape delivery URL.
    const base = imageMatch[0].split('?')[0];
    const src = `${base}?auto=format&fit=crop&w=1600&q=80`;
    const nameMatch = html.match(/by\s+([A-Za-z .'-]+)\s+on\s+Unsplash/i);
    const photographer = nameMatch ? nameMatch[1].trim() : 'Unsplash contributor';
    return { key, query, src, photographer, photoPage: SEARCH_URL(query) };
  } catch (error) {
    console.warn(`[fetch-unsplash] "${query}" failed:`, (error as Error).message);
    return null;
  }
}

async function main() {
  let existing: Credit[] = [];
  try {
    existing = JSON.parse(await readFile(CREDITS_PATH, 'utf8')) as Credit[];
  } catch {
    existing = [];
  }
  const byKey = new Map(existing.map((c) => [c.key, c]));
  for (const item of searches) {
    const found = await scrapeOne(item.key, item.query);
    if (found) byKey.set(item.key, found);
    else if (!byKey.has(item.key))
      byKey.set(item.key, {
        key: item.key,
        query: item.query,
        src: '',
        photographer: 'Unsplash contributor',
        photoPage: SEARCH_URL(item.query),
      });
  }

  const credits = searches.map((s) => byKey.get(s.key)!);
  await writeFile(CREDITS_PATH, JSON.stringify(credits, null, 2) + '\n', 'utf8');
  console.log(`[fetch-unsplash] wrote ${credits.length} entries to ${CREDITS_PATH}`);
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});