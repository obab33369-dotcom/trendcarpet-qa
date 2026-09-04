import json
import os

path = r"C:\Users\AndronikLindgren\.claude\projects\C--Users-AndronikLindgren--gemini-antigravity-scratch-Projects-REFORMA\86f49241-b28b-4af9-91a1-fc1aa5f61a2b.jsonl"
out_path = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA\scratch\task-439-full-chat.md"

with open(path, "r", encoding="utf-8") as f, open(out_path, "w", encoding="utf-8") as out:
    for line in f:
        data = json.loads(line)
        m_type = data.get("type")
        if m_type in ["user", "assistant"]:
            msg = data.get("message", {})
            role = msg.get("role", m_type)
            timestamp = data.get("timestamp", "")
            
            # Extract text from content list
            text_blocks = []
            content_list = msg.get("content", [])
            if isinstance(content_list, list):
                for item in content_list:
                    if isinstance(item, dict) and item.get("type") == "text":
                        text_blocks.append(item.get("text", ""))
                    elif isinstance(item, dict) and item.get("type") == "thinking":
                        # Include thinking process if present
                        thinking = item.get("thinking", "")
                        if thinking:
                            text_blocks.append(f"> [Thinking]\n> {thinking.replace('\n', '\n> ')}")
            
            if text_blocks:
                full_text = "\n\n".join(text_blocks)
                out.write(f"### TYPE: {role.upper()} ({timestamp})\n\n{full_text}\n\n---\n\n")

print("Successfully extracted parsed chat history!")
