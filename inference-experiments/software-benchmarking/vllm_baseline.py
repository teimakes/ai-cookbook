import sys
from time import perf_counter

from transformers import AutoTokenizer
from vllm import LLM, SamplingParams

model_name = sys.argv[1]
tokenizer = AutoTokenizer.from_pretrained(model_name)
token_ids = tokenizer.encode(
    "Explain how inference software processes requests. ",
    add_special_tokens=False,
)
prompt_ids = (token_ids * 512)[:512]
prompts = [{"prompt_token_ids": prompt_ids} for _ in range(8)]

model = LLM(
    model=model_name,
    dtype="bfloat16",
    max_model_len=4096,
    max_num_seqs=8,
    enable_prefix_caching=False,
    language_model_only=True,
)
sampling = SamplingParams(
    temperature=0,
    max_tokens=128,
    ignore_eos=True,
    detokenize=False,
)

for _ in range(2):
    model.generate(prompts, sampling, use_tqdm=False)

print("elapsed_s, output_tokens, output_tokens_per_s")
for _ in range(3):
    start = perf_counter()
    outputs = model.generate(prompts, sampling, use_tqdm=False)
    elapsed = perf_counter() - start
    output_tokens = sum(len(output.outputs[0].token_ids) for output in outputs)
    print(f"{elapsed:.4f}, {output_tokens}, {output_tokens / elapsed:.2f}")
