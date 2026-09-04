import json
import urllib.request
import urllib.parse
import uuid
import websocket
import os
import sys
import time
from pathlib import Path

class ComfyClient:
    def __init__(self, server_address="127.0.0.1:8188"):
        self.server_address = server_address
        self.client_id = str(uuid.uuid4())

    def check_server_status(self) -> bool:
        """
        Check if the ComfyUI server is up and listening.
        """
        try:
            url = f"http://{self.server_address}/system_stats"
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=5) as response:
                if response.status == 200:
                    return True
        except Exception:
            pass
        return False

    def get_node_id_by_title(self, workflow: dict, title: str) -> str:
        """
        Finds a node's ID dynamically by matching its user-defined title.
        This prevents breakage when ComfyUI node IDs shift on workflow exports.
        """
        for node_id, node_data in workflow.items():
            meta = node_data.get("_meta", {})
            if meta.get("title") == title:
                return node_id
        # Fallback search if _meta is missing: check node type or title key in values
        for node_id, node_data in workflow.items():
            if node_data.get("title") == title:
                return node_id
        return None

    def queue_prompt(self, prompt_workflow: dict) -> dict:
        """
        Submits the workflow prompt JSON to ComfyUI.
        """
        p = {"prompt": prompt_workflow, "client_id": self.client_id}
        data = json.dumps(p).encode('utf-8')
        
        url = f"http://{self.server_address}/prompt"
        req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode('utf-8'))

    def get_image(self, filename: str, subfolder: str, folder_type: str) -> bytes:
        """
        Downloads a generated image from ComfyUI.
        """
        data = {"filename": filename, "subfolder": subfolder, "type": folder_type}
        query_values = urllib.parse.urlencode(data)
        url = f"http://{self.server_address}/view?{query_values}"
        with urllib.request.urlopen(url) as response:
            return response.read()

    def get_history(self, prompt_id: str) -> dict:
        """
        Fetches the execution history for a prompt ID.
        """
        url = f"http://{self.server_address}/history/{prompt_id}"
        with urllib.request.urlopen(url) as response:
            return json.loads(response.read().decode('utf-8'))

    def run_workflow(self, workflow_path: Path, input_image_path: Path, output_image_path: Path, parameters: dict = None) -> bool:
        """
        Loads a workflow JSON, patches the parameters dynamically, runs it, and saves the output.
        """
        if not self.check_server_status():
            raise ConnectionError(f"ComfyUI server at {self.server_address} is down or unresponsive.")

        # 1. Load the workflow JSON
        with open(workflow_path, 'r', encoding='utf-8') as f:
            workflow = json.load(f)

        # 2. Resolve input and output nodes dynamically by title
        input_node_id = self.get_node_id_by_title(workflow, "INPUT_IMAGE")
        output_node_id = self.get_node_id_by_title(workflow, "OUTPUT_IMAGE")

        if not input_node_id:
            raise ValueError(f"Could not find a node titled 'INPUT_IMAGE' in ComfyUI workflow {workflow_path.name}")
        if not output_node_id:
            raise ValueError(f"Could not find a node titled 'OUTPUT_IMAGE' in ComfyUI workflow {workflow_path.name}")

        # 3. Patch inputs
        # Copy input image to ComfyUI's input directory or pass absolute path if supported by node
        comfy_input_dir = Path(r"C:\Users\AndronikLindgren\ComfyUI\input")
        comfy_input_dir.mkdir(parents=True, exist_ok=True)
        
        # Copy file to ComfyUI input folder to avoid path resolution issues
        temp_input_name = f"reforma_temp_{uuid.uuid4().hex}_{input_image_path.name}"
        shutil_dest = comfy_input_dir / temp_input_name
        import shutil
        shutil.copy2(input_image_path, shutil_dest)

        workflow[input_node_id]["inputs"]["image"] = temp_input_name

        # Patch custom parameters if provided (e.g. threshold, blur, etc.)
        if parameters:
            for node_title, params in parameters.items():
                node_id = self.get_node_id_by_title(workflow, node_title)
                if node_id:
                    for key, val in params.items():
                        workflow[node_id]["inputs"][key] = val

        # 4. Connect to websocket and queue prompt
        ws_url = f"ws://{self.server_address}/ws?clientId={self.client_id}"
        ws = websocket.WebSocket()
        ws.connect(ws_url)

        try:
            prompt_res = self.queue_prompt(workflow)
            prompt_id = prompt_res.get("prompt_id")
            if not prompt_id:
                raise RuntimeError("Failed to queue prompt: missing prompt_id in response.")

            # 5. Poll websocket for completion or errors
            output_images = []
            while True:
                out = ws.recv()
                if isinstance(out, str):
                    message = json.loads(out)
                    if message['type'] == 'executing':
                        data = message['data']
                        if data['node'] is None and data['prompt_id'] == prompt_id:
                            break  # Execution finished!
                    elif message['type'] == 'execution_error':
                        data = message['data']
                        if data['prompt_id'] == prompt_id:
                            raise RuntimeError(f"ComfyUI Execution Error: {data.get('exception_message')}")
                else:
                    continue  # Binary data

            # 6. Fetch results from history
            history = self.get_history(prompt_id).get(prompt_id, {})
            outputs = history.get("outputs", {})
            
            # Find output files in the output node
            node_output = outputs.get(output_node_id, {})
            if "images" in node_output:
                for img_info in node_output["images"]:
                    output_images.append(img_info)

            # Cleanup temp input file
            try:
                os.remove(shutil_dest)
            except Exception:
                pass

            if not output_images:
                raise FileNotFoundError("ComfyUI finished execution but returned no output images.")

            # 7. Download output image and save to target path
            first_image = output_images[0]
            image_data = self.get_image(
                first_image["filename"],
                first_image["subfolder"],
                first_image["type"]
            )
            
            output_image_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_image_path, "wb") as f:
                f.write(image_data)
                
            return True

        finally:
            ws.close()

if __name__ == "__main__":
    # Small test loop
    client = ComfyClient()
    print("Server online:", client.check_server_status())
