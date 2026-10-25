"""Fixed public metadata-only fetch; never requests tensor/checkpoint content."""
from hashlib import sha256
import json
from pathlib import Path
import ssl
import urllib.request

HERE = Path(__file__).resolve().parent / "metadata"
PINS = (
    ("qwen3-1.7b-base", "Qwen/Qwen3-1.7B-Base", "ea980cb0a6c2ae4b936e82123acc929f1cec04c1"),
    ("qwen3-4b-base", "Qwen/Qwen3-4B-Base", "906bfd4b4dc7f14ee4320094d8b41684abff8539"),
    ("qwen3-8b-base", "Qwen/Qwen3-8B-Base", "49e3418fbbbca6ecbdf9608b4d22e5a407081db4"),
)
ALLOWED = {"config.json", "generation_config.json", "tokenizer.json", "tokenizer_config.json",
           "merges.txt", "vocab.json", "model.safetensors.index.json"}
CONTEXT = ssl.create_default_context(cafile="/etc/ssl/cert.pem")
CACHE = {}


def fetch(url, maximum):
    request = urllib.request.Request(url, headers={"User-Agent": "Hydra-P6-metadata-only/1"})
    with urllib.request.urlopen(request, timeout=20, context=CONTEXT) as response:
        if not response.url.startswith("https://huggingface.co/"):
            raise ValueError("Metadata redirect escaped the allowed HTTPS host.")
        raw = response.read(maximum + 1)
        if len(raw) > maximum:
            raise ValueError("Metadata exceeded the fixed byte ceiling.")
        return raw


def main():
    HERE.mkdir(parents=True, exist_ok=True)
    result = {"schema": "hydra-qwen3-metadata-observation-v1", "weight_bytes_downloaded": 0,
              "models": []}
    for key, model_id, revision in PINS:
        directory = HERE / key
        directory.mkdir(exist_ok=False)
        api_url = f"https://huggingface.co/api/models/{model_id}/revision/{revision}?blobs=true"
        api_raw = fetch(api_url, 512 * 1024)
        api = json.loads(api_raw)
        assert api["sha"] == revision and api["modelId"] == model_id
        (directory / "api.json").write_bytes(api_raw)
        files = {}
        weights = {}
        for item in api["siblings"]:
            name = item["rfilename"]
            if name.endswith(".safetensors"):
                assert "/" not in name and item["lfs"]["size"] == item["size"]
                weights[name] = {"bytes": item["size"], "sha256": item["lfs"]["sha256"]}
            if name not in ALLOWED:
                continue
            assert "/" not in name and 0 < item["size"] <= 12 * 1024**2
            url = f"https://huggingface.co/{model_id}/resolve/{revision}/{name}"
            blob = item["blobId"]
            raw = CACHE.get(blob)
            if raw is None:
                raw = fetch(url, item["size"])
                CACHE[blob] = raw
            assert len(raw) == item["size"]
            (directory / name).write_bytes(raw)
            files[name] = {"bytes": len(raw), "sha256": sha256(raw).hexdigest()}
        assert {"config.json", "tokenizer.json", "tokenizer_config.json"} <= files.keys()
        assert weights
        record = {"key": key, "model_id": model_id, "revision": revision,
                  "metadata_url": api_url, "metadata_sha256": sha256(api_raw).hexdigest(),
                  "metadata_files": files, "weight_files": weights,
                  "config": json.loads((directory / "config.json").read_text())}
        result["models"].append(record)
        print(json.dumps({"key": key, "revision": revision, "metadata_files": len(files),
                          "weights_downloaded": False, "config": record["config"]}), flush=True)
    with (HERE / "observation.json").open("x") as stream:
        json.dump(result, stream, indent=2)
        stream.write("\n")


if __name__ == "__main__":
    main()
