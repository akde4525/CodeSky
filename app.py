# import requests
# import json
# import gradio as gr

# url="http://localhost:11434/api/generate"

# headers={
#     'Content-Type':'application/json'
# }

# history=[]

# def generate_response(prompt):
#     history.append(prompt)
#     final_prompt="\n".join(history)

#     data={
#         "model":"CodeSky",
#         "prompt":final_prompt,
#         "stream":False
#     }
#     response=requests.post(url,headers=headers,data=json.dumps(data))

#     if response.status_code==200:
#         response=response.text
#         data=json.loads(response)
#         actual_response=data['response']
#         return actual_response
#     else:
#         print("error:",response.text)

# # frontend
# interface=gr.Interface(
#     fn=generate_response,
#     inputs=gr.Textbox(lines=4,placeholder="Enter Your Prompt"),
#     outputs="text"
# )
# interface.launch()

import requests
import json
import gradio as gr

# ================= CONFIG =================
URL = "http://localhost:11434/api/generate"
HEADERS = {"Content-Type": "application/json"}
MODEL_NAME = "CodeSky"
MAX_HISTORY = 6

# Keep-alive session (faster)
session = requests.Session()


# ============== HISTORY HANDLER ============
def build_context(history):
    """
    Handles BOTH Gradio history formats:
    1) [(user, bot), ...]
    2) [{'role': 'user', 'content': '...'}, ...]
    """
    turns = []

    if not history:
        return ""

    # Old format
    if isinstance(history[0], (list, tuple)):
        for user, bot in history:
            turns.append(("User", user))
            turns.append(("Assistant", bot))
    else:
        # New Gradio format
        for msg in history:
            role = msg.get("role")
            content = msg.get("content")
            if role and content:
                turns.append((role.capitalize(), content))

    # Limit context
    context = ""
    for role, content in turns[-MAX_HISTORY * 2:]:
        context += f"{role}: {content}\n"

    return context


# ============== MODEL CALL =================
def generate_response(message, history):
    context = build_context(history)
    prompt = context + f"User: {message}\nAssistant:"

    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": True
    }

    response = session.post(
        URL,
        headers=HEADERS,
        json=payload,
        stream=True,
        timeout=300
    )

    full_response = ""

    for line in response.iter_lines(decode_unicode=True):
        if not line:
            continue

        try:
            data = json.loads(line)
        except json.JSONDecodeError:
            continue

        # Ollama end signal
        if data.get("done", False):
            break

        token = data.get("response", "")
        full_response += token
        yield full_response


# ============== UI =========================
with gr.Blocks() as demo:
    gr.Markdown(
        """
        # 🌌 CodeSky  
        ### Your Personal AI Code Assistant  
        **Fast • Local • Stable**
        """
    )

    gr.ChatInterface(
        fn=generate_response,
        chatbot=gr.Chatbot(height=450),
        textbox=gr.Textbox(
            placeholder="Ask CodeSky anything about coding...",
            scale=7
        )
    )

# Theme must be passed here in Gradio 6+
demo.launch(theme=gr.themes.Soft())
