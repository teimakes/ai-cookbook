import sys
from time import perf_counter

import torch
from transformers import AutoTokenizer, GenerationConfig, Qwen3_5ForConditionalGeneration

model_name = sys.argv[1]
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = Qwen3_5ForConditionalGeneration.from_pretrained(
    model_name, dtype=torch.bfloat16
).to("cuda").eval()

token_ids = tokenizer.encode(
    "Explain how inference software processes requests. ",
    add_special_tokens=False,
)
prompt_ids = (token_ids * 512)[:512]
inputs = torch.tensor([prompt_ids] * 8, device="cuda")
generation = GenerationConfig(
    do_sample=False,
    max_new_tokens=128,
    min_new_tokens=128,
    pad_token_id=tokenizer.eos_token_id,
)

with torch.inference_mode():
    for _ in range(2):
        model.generate(inputs, generation_config=generation)
    torch.cuda.synchronize()

    print("elapsed_s, output_tokens, output_tokens_per_s")
    for _ in range(3):
        torch.cuda.synchronize()
        start = perf_counter()
        outputs = model.generate(inputs, generation_config=generation)
        torch.cuda.synchronize()
        elapsed = perf_counter() - start
        output_tokens = outputs.shape[0] * (outputs.shape[1] - inputs.shape[1])
        print(f"{elapsed:.4f}, {output_tokens}, {output_tokens / elapsed:.2f}")
