# Image sizes in tokens for Gemini 1.5 Flash:
# An image input in Gemini is always exactly 258 tokens regardless of resolution.
# For each comparison, we send:
# 1. Prompt text (~100 tokens)
# 2. Reference image (258 tokens)
# 3. Rendered image (258 tokens)
# Total input tokens per image comparison: 100 + 258 + 258 = 616 tokens.
# Output is very short (e.g. "YES" or "NO"), approx. 5 tokens.

TOTAL_IMAGES = 13341

# Gemini 1.5 Flash Pricing (Pay-as-you-go):
# Input: $0.075 per 1M tokens
# Output: $0.30 per 1M tokens
input_tokens_per_img = 616
output_tokens_per_img = 5

total_input_tokens = TOTAL_IMAGES * input_tokens_per_img
total_output_tokens = TOTAL_IMAGES * output_tokens_per_img

input_cost = (total_input_tokens / 1_000_000) * 0.075
output_cost = (total_output_tokens / 1_000_000) * 0.30
total_flash_cost = input_cost + output_cost

# Gemini 2.5 Flash Pricing (Pay-as-you-go):
# Input: $0.30 per 1M tokens
# Output: $2.50 per 1M tokens
input_cost_2_5 = (total_input_tokens / 1_000_000) * 0.30
output_cost_2_5 = (total_output_tokens / 1_000_000) * 2.50
total_flash_2_5_cost = input_cost_2_5 + output_cost_2_5

print("=== Gemini API Cost Estimate for 13,341 Images ===")
print(f"Total input tokens: {total_input_tokens:,}")
print(f"Total output tokens: {total_output_tokens:,}")
print(f"\nOption A: Gemini 1.5 Flash")
print(f"  Input cost:  ${input_cost:.4f}")
print(f"  Output cost: ${output_cost:.4f}")
print(f"  Total cost:  ${total_flash_cost:.2f}")

print(f"\nOption B: Gemini 2.5 Flash")
print(f"  Input cost:  ${input_cost_2_5:.4f}")
print(f"  Output cost: ${output_cost_2_5:.4f}")
print(f"  Total cost:  ${total_flash_2_5_cost:.2f}")
