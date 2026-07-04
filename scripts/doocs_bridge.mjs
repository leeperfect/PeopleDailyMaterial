#!/usr/bin/env node
/**
 * 通过 doocs/md 自带 MCP 服务渲染 Markdown。
 * stdin: {"repo": "...", "markdown": "...", "options": {...}}
 * stdout: doocs/md render_markdown 返回的 JSON。
 */

import process from "node:process";
import path from "node:path";
import { createRequire } from "node:module";
import { pathToFileURL } from "node:url";

async function readStdin() {
  const chunks = [];
  for await (const chunk of process.stdin) chunks.push(chunk);
  return Buffer.concat(chunks).toString("utf8");
}

async function main() {
  const input = JSON.parse(await readStdin());
  const repo = path.resolve(input.repo);
  const mcpDir = path.join(repo, "packages", "mcp-server");
  const localRequire = createRequire(path.join(mcpDir, "package.json"));
  const clientModule = await import(
    pathToFileURL(localRequire.resolve("@modelcontextprotocol/sdk/client/index.js")).href
  );
  const stdioModule = await import(
    pathToFileURL(localRequire.resolve("@modelcontextprotocol/sdk/client/stdio.js")).href
  );

  const client = new clientModule.Client(
    { name: "peopledaily-writing-workflow", version: "1.0.0" },
    { capabilities: {} },
  );
  const transport = new stdioModule.StdioClientTransport({
    command: process.execPath,
    args: ["--import", "tsx/esm", path.join(mcpDir, "run.mjs")],
    cwd: mcpDir,
    stderr: "pipe",
  });

  try {
    await client.connect(transport);
    const result = await client.callTool({
      name: "render_markdown",
      arguments: {
        markdown: input.markdown,
        ...input.options,
      },
    });
    const text = result.content?.find((item) => item.type === "text")?.text;
    if (!text) throw new Error("doocs/md 没有返回 HTML");
    process.stdout.write(text);
  } finally {
    await client.close();
  }
}

main().catch((error) => {
  process.stderr.write(`${error?.stack || error}\n`);
  process.exitCode = 1;
});
