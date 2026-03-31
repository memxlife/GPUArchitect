import fs from "node:fs/promises";
import { Codex } from "@openai/codex-sdk";

function normalizeEvents(events) {
  return events.map((event) => JSON.parse(JSON.stringify(event)));
}

async function main() {
  const requestPath = process.argv[2];
  if (!requestPath) {
    console.error("Usage: node codex_runner.mjs <request.json>");
    process.exit(2);
  }

  const rawRequest = await fs.readFile(requestPath, "utf-8");
  const request = JSON.parse(rawRequest);
  const codex = new Codex();
  const thread = codex.startThread({
    model: request.model,
    sandboxMode: request.sandbox_mode,
    workingDirectory: request.working_directory,
    skipGitRepoCheck: Boolean(request.skip_git_repo_check),
    modelReasoningEffort: request.reasoning_effort,
    networkAccessEnabled: true,
    webSearchEnabled: Boolean(request.web_search_enabled),
    approvalPolicy: "never",
  });

  const inputText = [
    `Role: ${request.role}`,
    "",
    request.instructions,
    "",
    "Return only data that matches the required JSON schema.",
    "",
    "Payload:",
    JSON.stringify(request.payload, null, 2),
  ].join("\n");

  let events = [];
  let finalResponse = null;
  let usage = null;

  if (request.stream_mode === "turn") {
    const turn = await thread.run([{ type: "text", text: inputText }], {
      outputSchema: request.output_schema,
    });
    finalResponse = turn.finalResponse;
    usage = turn.usage;
  } else {
    const streamed = await thread.runStreamed([{ type: "text", text: inputText }], {
      outputSchema: request.output_schema,
    });

    for await (const event of streamed.events) {
      events.push(event);
      if (
        (event.type === "item.completed" || event.type === "item.updated") &&
        event.item?.type === "agent_message" &&
        typeof event.item.text === "string"
      ) {
        finalResponse = event.item.text;
      }
      if (event.type === "turn.completed") {
        usage = event.usage;
      }
    }
  }

  if (typeof finalResponse !== "string") {
    throw new Error("Codex runtime did not emit a final agent message.");
  }

  const rawResponse = finalResponse;
  const output = JSON.parse(rawResponse);
  process.stdout.write(
    JSON.stringify(
      {
        backend: "codex_sdk",
        thread_id: thread.id,
        usage,
        events: normalizeEvents(events),
        raw_response: rawResponse,
        output,
      },
      null,
      2,
    ),
  );
}

main().catch((error) => {
  console.error(error instanceof Error ? error.stack || error.message : String(error));
  process.exit(1);
});
