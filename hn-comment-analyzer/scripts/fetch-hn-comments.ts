#!/usr/bin/env -S npx tsx

/**
 * Fetch Hacker News comments for an item URL, ID, or title via HN Search
 * Usage: npx tsx fetch-hn-comments.ts "<url-or-id-or-title>"
 *    or: bun run fetch-hn-comments.ts "<url-or-id-or-title>"
 * Use --title "<title>" to search titles that look like IDs or URLs.
 */

declare const process: {
	argv: string[];
	exit(code?: number): never;
};

export {};

const HTML_TAG_REGEX = /<[^>]*>?/gm;

type HNItem = {
	id: number;
	author: string | null;
	title?: string;
	url?: string;
	text?: string | null;
	points?: number | null;
	deleted?: boolean;
	dead?: boolean;
	children?: (HNItem | null)[] | null;
};

type HNComment = {
	id: number;
	author: string | null;
	points?: number | null;
	text: string;
	children?: HNComment[];
};

type HNResult = {
	id: number;
	title?: string;
	url?: string;
	points?: number | null;
	author: string | null;
	comments: HNComment[];
};

type HNSearchHit = {
	objectID: string;
	title: string | null;
};

function stripHtml(html: string): string {
	if (!html) return "";
	return html.replace(HTML_TAG_REGEX, "");
}

function extractId(input: string): string | null {
	if (/^\d+$/.test(input)) return input;
	if (!/^https?:\/\//i.test(input)) return null;

	const url = new URL(input);
	const id =
		url.hostname === "news.ycombinator.com" && url.pathname === "/item"
			? url.searchParams.get("id")
			: url.hostname === "hn.algolia.com"
				? url.pathname.match(/^\/(?:api\/v1\/)?items\/(\d+)\/?$/)?.[1]
				: null;
	if (id && /^\d+$/.test(id)) return id;
	throw new Error(
		"Use an HN item URL, numeric ID, or a title (use --title for URL-like titles).",
	);
}

function normalizeTitle(title: string): string {
	return title.trim().replace(/\s+/g, " ").toLowerCase();
}

async function searchTitle(title: string): Promise<string> {
	const url = new URL("https://hn.algolia.com/api/v1/search");
	url.search = new URLSearchParams({
		query: title,
		tags: "story",
		restrictSearchableAttributes: "title",
		hitsPerPage: "50",
	}).toString();

	const response = await fetch(url);
	if (!response.ok) {
		throw new Error(`Failed to search HN titles: ${response.statusText}`);
	}
	const data: { hits: HNSearchHit[] } = await response.json();
	const hits = data.hits.filter(
		(hit): hit is HNSearchHit & { title: string } =>
			/^\d+$/.test(hit.objectID) &&
			typeof hit.title === "string" &&
			hit.title.trim().length > 0,
	);
	const match =
		hits.find((hit) => normalizeTitle(hit.title) === normalizeTitle(title)) ??
		hits[0];
	if (!match) {
		throw new Error(`No HN stories found for title: ${JSON.stringify(title)}`);
	}
	console.error(
		`Matched HN story: ${JSON.stringify(match.title)} — https://news.ycombinator.com/item?id=${match.objectID}`,
	);
	return match.objectID;
}

function processComments(item: HNItem | null): HNComment[] {
	if (!item) return [];

	const children = (item.children ?? []).flatMap(processComments);
	const text = stripHtml(item.text ?? "").trim();

	// Promote readable replies instead of dropping a filtered parent's subtree.
	if (item.deleted || item.dead || !text || /^\[(deleted|dead)\]$/i.test(text)) {
		return children;
	}

	const result: HNComment = {
		id: item.id,
		author: item.author,
		points: item.points,
		text,
	};

	if (children.length > 0) {
		result.children = children;
	}

	return [result];
}

async function fetchHnComments(input: string, titleOnly = false): Promise<HNResult> {
	const id = (titleOnly ? null : extractId(input)) ?? (await searchTitle(input));
	const url = `https://hn.algolia.com/api/v1/items/${id}`;

	const response = await fetch(url);
	if (!response.ok) {
		throw new Error(`Failed to fetch HN item: ${response.statusText}`);
	}

	const data: HNItem = await response.json();

	const comments = (data.children ?? []).flatMap(processComments);

	return {
		id: data.id,
		title: data.title,
		url: data.url,
		points: data.points,
		author: data.author,
		comments,
	};
}
// CLI entrypoint
(async () => {
	const titleOnly = process.argv[2] === "--title";
	const input = process.argv[titleOnly ? 3 : 2]?.trim();

	if (!input || process.argv.length > (titleOnly ? 4 : 3)) {
		console.error('Usage: npx tsx fetch-hn-comments.ts "<url-or-id-or-title>"');
		console.error(
			'Example: npx tsx fetch-hn-comments.ts "https://news.ycombinator.com/item?id=46654726"',
		);
		console.error('Example: npx tsx fetch-hn-comments.ts "46654726"');
		console.error(
			'Example: npx tsx fetch-hn-comments.ts "Ask HN: Is it still worth pursuing a software startup?"',
		);
		console.error('Example: npx tsx fetch-hn-comments.ts --title "1984"');
		process.exit(1);
	}

	const result = await fetchHnComments(input, titleOnly);
	console.log(JSON.stringify(result, null, 2));
})().catch((error: unknown) => {
	console.error(error instanceof Error ? error.message : String(error));
	process.exit(1);
});
