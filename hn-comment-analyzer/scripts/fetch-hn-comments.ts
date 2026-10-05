#!/usr/bin/env -S npx tsx

/**
 * Fetch Hacker News comments for a given item URL or ID
 * Usage: npx tsx fetch-hn-comments.ts <url-or-id>
 *    or: bun run fetch-hn-comments.ts <url-or-id>
 */

declare const process: {
	argv: string[];
	exit(code?: number): never;
};

export {};

const ID_REGEX = /id=(\d+)/;
const ITEM_ID_REGEX = /item\?id=(\d+)/;
const ITEMS_REGEX = /\/items\/(\d+)/;
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

function stripHtml(html: string): string {
	if (!html) return "";
	return html.replace(HTML_TAG_REGEX, "");
}

function extractId(input: string): string {
	const match =
		input.match(ID_REGEX) ||
		input.match(ITEM_ID_REGEX) ||
		input.match(ITEMS_REGEX);
	return match ? match[1] : input;
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

async function fetchHnComments(input: string): Promise<HNResult> {
	const id = extractId(input);
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
	const input = process.argv[2];

	if (!input) {
		console.error("Usage: npx tsx fetch-hn-comments.ts <url-or-id>");
		console.error(
			'Example: npx tsx fetch-hn-comments.ts "https://news.ycombinator.com/item?id=46654726"',
		);
		console.error('Example: npx tsx fetch-hn-comments.ts "46654726"');
		process.exit(1);
	}

	const result = await fetchHnComments(input);
	console.log(JSON.stringify(result, null, 2));
})();
