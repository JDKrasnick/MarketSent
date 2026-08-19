import { mkdir, readFile, rename, stat, writeFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

import { pipeline, env } from "@huggingface/transformers";


const projectRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../..");
const defaultModel = "mikeysharma/finance-sentiment-analysis";
const configuredModel = process.env.SENTIMENT_MODEL || defaultModel;
const configuredDtype = process.env.SENTIMENT_DTYPE || "fp32";
const localModelName = "marketsent-finance-sentiment";
const modelCacheRoot = process.env.SENTIMENT_CACHE_DIR || path.join(projectRoot, ".cache", "models");
const localModelRoot = path.join(modelCacheRoot, localModelName);

const modelFiles = [
    ["config.json", "config.json"],
    ["tokenizer.json", "tokenizer.json"],
    ["tokenizer_config.json", "tokenizer_config.json"],
    ["special_tokens_map.json", "special_tokens_map.json"],
    ["vocab.txt", "vocab.txt"],
    ["model.onnx", "onnx/model.onnx"],
];


async function downloadFile(source, destination) {
    try {
        await stat(destination);
        return;
    } catch {
        // The cache is populated below.
    }

    await mkdir(path.dirname(destination), { recursive: true });
    const response = await fetch(
        `https://huggingface.co/${defaultModel}/resolve/main/${source}?download=true`
    );
    if (!response.ok) {
        throw new Error(`Unable to download ${source}: HTTP ${response.status}`);
    }
    const temporary = `${destination}.${process.pid}.tmp`;
    await writeFile(temporary, Buffer.from(await response.arrayBuffer()));
    await rename(temporary, destination);
}


async function prepareCompactModel() {
    await Promise.all(
        modelFiles.map(([source, target]) =>
            downloadFile(source, path.join(localModelRoot, target))
        )
    );

    const configPath = path.join(localModelRoot, "config.json");
    const config = JSON.parse(await readFile(configPath, "utf8"));
    config.id2label = { 0: "negative", 1: "neutral", 2: "positive" };
    config.label2id = { negative: 0, neutral: 1, positive: 2 };
    await writeFile(configPath, `${JSON.stringify(config, null, 2)}\n`);

    env.localModelPath = modelCacheRoot;
    env.allowLocalModels = true;
    env.allowRemoteModels = false;
    return { model: localModelName, dtype: "fp32" };
}


async function getClassifier() {
    const selected = configuredModel === defaultModel
        ? await prepareCompactModel()
        : { model: configuredModel, dtype: configuredDtype };

    if (configuredModel !== defaultModel) {
        env.allowLocalModels = true;
        env.allowRemoteModels = true;
    }
    return {
        classifier: await pipeline("text-classification", selected.model, {
            dtype: selected.dtype,
        }),
        selected,
    };
}


function normalizeOutput(output, inputCount) {
    const grouped = inputCount === 1 && !Array.isArray(output[0]) ? [output] : output;
    return grouped.map((labels) => {
        const scores = { positive: 0, negative: 0, neutral: 0 };
        for (const item of labels) {
            const label = String(item.label).toLowerCase();
            if (Object.hasOwn(scores, label)) {
                scores[label] = Number(item.score);
            }
        }
        return scores;
    });
}


async function main() {
    const { classifier, selected } = await getClassifier();
    if (process.argv.includes("--warm")) {
        process.stdout.write(JSON.stringify({
            status: "ready",
            model: configuredModel,
            runtimeModel: selected.model,
            dtype: selected.dtype,
        }));
        return;
    }

    let input = "";
    for await (const chunk of process.stdin) {
        input += chunk;
    }

    const payload = JSON.parse(input);
    if (!Array.isArray(payload.texts) || payload.texts.length === 0) {
        throw new Error("texts must be a non-empty array");
    }

    const texts = payload.texts.map((text) => String(text));
    const batchSize = Math.max(1, Math.min(Number(payload.batchSize) || 16, 64));
    const scores = [];
    for (let start = 0; start < texts.length; start += batchSize) {
        const batch = texts.slice(start, start + batchSize);
        const output = await classifier(batch, { top_k: null });
        scores.push(...normalizeOutput(output, batch.length));
    }
    process.stdout.write(JSON.stringify({ scores }));
}


main().catch((error) => {
    process.stderr.write(`${error.stack || error.message}\n`);
    process.exitCode = 1;
});
