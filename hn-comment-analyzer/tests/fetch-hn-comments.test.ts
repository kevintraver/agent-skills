import { afterAll, expect, test } from "bun:test";
import { mkdtempSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, resolve } from "node:path";

const cli = resolve(import.meta.dir, "../scripts/fetch-hn-comments.ts");
const temp = mkdtempSync(join(tmpdir(), "hn-comments-test-"));
const preload = join(temp, "fetch.ts");
writeFileSync(preload, `
const fixture = JSON.parse(process.env.HN_TEST_CASE!);
globalThis.fetch = async (input) => {
  const url = new URL(String(input));
  if (url.origin !== "https://hn.algolia.com") throw new Error("Unexpected origin");
  if (url.pathname === "/api/v1/search") {
    if (fixture.query === undefined || url.searchParams.get("query") !== fixture.query ||
        url.searchParams.get("tags") !== "story" ||
        url.searchParams.get("restrictSearchableAttributes") !== "title" ||
        url.searchParams.get("hitsPerPage") !== "50") throw new Error("Unexpected title search");
    return new Response(JSON.stringify({ hits: fixture.hits ?? [] }), {
      status: fixture.searchStatus ?? 200, statusText: "Search error",
    });
  }
  if (url.pathname !== "/api/v1/items/" + fixture.id) throw new Error("Wrong thread fetched");
  return new Response(JSON.stringify(fixture.story), {
    status: fixture.itemStatus ?? 200, statusText: "Item error",
  });
};
`);
afterAll(() => rmSync(temp, { recursive: true, force: true }));

const comment = (id: number, extra: Record<string, unknown> = {}) => ({
  id, author: `user${id}`, text: `<p>Comment ${id}</p>`, points: null, ...extra,
});
const story = (id = 123, children: unknown = [comment(1)]) => ({
  id, title: "Story", author: "op", points: 42, children,
});
function run(args: string[], fixture: Record<string, unknown> = {}) {
  const result = Bun.spawnSync({
    cmd: [process.execPath, "--preload", preload, cli, ...args],
    env: { ...process.env, HN_TEST_CASE: JSON.stringify({ id: 123, story: story(), ...fixture }) },
  });
  return { code: result.exitCode, stdout: result.stdout.toString(), stderr: result.stderr.toString() };
}
function getComments(children: unknown) {
  const result = run(["123"], { story: story(123, children) });
  expect(result.code).toBe(0);
  return JSON.parse(result.stdout).comments;
}

for (const input of ["123", " 123 ", "https://news.ycombinator.com/item?id=123", "https://news.ycombinator.com/item?foo=bar&id=123#reply", "https://hn.algolia.com/api/v1/items/123"]) {
  test(`direct input bypasses search: ${input}`, () => {
    const result = run([input]);
    expect(result.code).toBe(0);
    expect(result.stderr).toBe("");
    expect(JSON.parse(result.stdout)).toEqual({ id: 123, title: "Story", author: "op", points: 42, comments: [{ id: 1, author: "user1", points: null, text: "Comment 1" }] });
  });
}

test("exact title beats a higher-ranked partial match and prints the chosen HN link", () => {
  const result = run(["Ask HN: Startup advice"], {
    query: "Ask HN: Startup advice",
    hits: [{ objectID: "99", title: "Ask HN: Startup advice for founders" }, { objectID: "123", title: "ASK HN:  Startup advice" }],
  });
  expect(result.code).toBe(0);
  expect(JSON.parse(result.stdout).id).toBe(123);
  expect(result.stderr).toContain('"ASK HN:  Startup advice"');
  expect(result.stderr).toContain("https://news.ycombinator.com/item?id=123");
});

test("title fragment uses HN Search's first ranked match", () => {
  const result = run(["Startup advice"], {
    query: "Startup advice",
    hits: [{ objectID: "123", title: "Ask HN: Startup advice" }, { objectID: "99", title: "Startup advice for founders" }],
  });
  expect(result.code).toBe(0);
  expect(JSON.parse(result.stdout).id).toBe(123);
});

test("duplicate exact titles retain HN Search ordering", () => {
  const result = run(["Story"], { query: "Story", hits: [{ objectID: "123", title: "Story" }, { objectID: "99", title: "Story" }] });
  expect(result.code).toBe(0);
  expect(JSON.parse(result.stdout).id).toBe(123);
});

test("invalid hits are skipped before choosing a title match", () => {
  const result = run(["Story"], { query: "Story", hits: [{ objectID: "99", title: null }, { objectID: "oops", title: "Story" }, { objectID: "88", title: " " }, { objectID: "123", title: "Story" }] });
  expect(result.code).toBe(0);
});

for (const title of ["C++ & C# — 日本語?", "Understanding id=999 in URLs", "Startup advice"]) {
  test(`title query is encoded and searched literally: ${title}`, () => {
    const result = run([` ${title} `], { query: title, hits: [{ objectID: "123", title }] });
    expect(result.code).toBe(0);
    expect(JSON.parse(result.stdout).id).toBe(123);
  });
}

for (const title of ["1984", "https://example.com/article"]) {
  test(`--title forces title search: ${title}`, () => {
    const result = run(["--title", title], { query: title, hits: [{ objectID: "123", title }] });
    expect(result.code).toBe(0);
  });
}

test("empty search results produce a clear error without fetching a thread", () => {
  const result = run(["Missing story"], { query: "Missing story", hits: [] });
  expect(result.code).toBe(1);
  expect(result.stdout).toBe("");
  expect(result.stderr).toContain('No HN stories found for title: "Missing story"');
});

test("search failures are reported separately from item failures", () => {
  const result = run(["Story"], { query: "Story", searchStatus: 503 });
  expect(result.code).toBe(1);
  expect(result.stderr).toContain("Failed to search HN titles: Search error");
});

test("item fetch failures remain nonzero", () => {
  const result = run(["123"], { itemStatus: 503 });
  expect(result.code).toBe(1);
  expect(result.stderr).toContain("Failed to fetch HN item: Item error");
});

for (const input of ["https://example.com/?id=123", "https://news.ycombinator.com/item?id=123abc"]) {
  test(`invalid item URL does not fetch an unrelated ID: ${input}`, () => {
    const result = run([input]);
    expect(result.code).toBe(1);
    expect(result.stdout).toBe("");
    expect(result.stderr).toContain("Use an HN item URL");
  });
}

for (const args of [[], [" "], ["--title"], ["unquoted", "title"]]) {
  test(`missing, blank, or unquoted input shows usage: ${JSON.stringify(args)}`, () => {
    const result = run(args);
    expect(result.code).toBe(1);
    expect(result.stderr).toContain("Usage:");
  });
}

test("moderation flags and placeholders preserve descendant order and nesting", () => {
  const actual = getComments([comment(1, { children: [
    comment(2),
    comment(3, { deleted: true, children: [
      comment(4, { dead: true, children: [comment(5, { text: "<p>[deleted]</p>", children: [comment(6)] })] }),
      comment(7, { text: " [DEAD] ", children: [comment(8)] }),
    ] }),
    comment(9),
  ] })]);
  expect(actual.map((c: any) => c.id)).toEqual([1]);
  expect(actual[0].children.map((c: any) => c.id)).toEqual([2, 6, 8, 9]);
});

test("null and unusable comments preserve surviving children", () => {
  expect(getComments([null, comment(1, { text: null, children: [comment(2)] }),
    { id: 3, author: null, children: [comment(4)] },
    comment(5, { text: " \n\t ", children: [comment(6)] }),
    comment(7, { text: "<p> </p>", children: [comment(8)] }),
  ]).map((c: any) => c.id)).toEqual([2, 4, 6, 8]);
});

test("null/missing scores and readable anonymous comments are retained", () => {
  const actual = getComments([comment(1), comment(2, { points: undefined }), comment(3, { points: 7, author: null }), comment(4, { points: 0, dead: false, deleted: false })]);
  expect(actual[0].points).toBeNull();
  expect("points" in actual[1]).toBe(false);
  expect(actual[2]).toEqual({ id: 3, author: null, points: 7, text: "Comment 3" });
  expect(actual[3].points).toBe(0);
});

test("missing, null and empty child lists yield no comments", () => {
  for (const children of [null, []]) expect(getComments(children)).toEqual([]);
  const { children, ...withoutChildren } = story();
  const result = run(["123"], { story: withoutChildren });
  expect(result.code).toBe(0);
  expect(JSON.parse(result.stdout).comments).toEqual([]);
});
