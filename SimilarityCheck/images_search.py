import os
import requests
from typing import List
from datetime import datetime, timedelta, timezone
from azure.storage.blob import generate_blob_sas, BlobSasPermissions
from urllib.parse import quote
from dotenv import load_dotenv

load_dotenv()

# Convert an image to vector
def vectorize_image(image_path: str) -> List[float]:
    api = f"{os.getenv('VISION_ENDPOINT')}/computervision/retrieval:vectorizeImage"  
    with open(image_path, "rb") as f:
        image_data = f.read()
    headers = {
        "Ocp-Apim-Subscription-Key": os.getenv("VISION_KEY"),
        "Content-Type": "application/octet-stream",
    }
    params = {"api-version": os.getenv("API_VISION"), "model-version": os.getenv("MODEL_VERSION")}
    resp = requests.post(
        api,
        params=params,
        headers=headers,
        data=image_data,
        timeout=30,
    )
    resp.raise_for_status()
    vec = resp.json()["vector"]
    if len(vec) != 1024:
        raise ValueError("Vector dimension is not 1024, model and index mismatch")
    return vec

# Search for similar images through vector similarity
def search_similar(vec: List[float]) -> list:
    url = (
        f"https://{os.getenv('SEARCH_SERVICE')}.search.windows.net/"
        f"indexes/{os.getenv('SEARCH_INDEX')}/docs/search?api-version={os.getenv('API_SEARCH')}"
    )
    headers = {
        "Content-Type": "application/json",
        "api-key": os.getenv("SEARCH_ADMIN_KEY"),
    }
    body = {
        "vectorQueries": [
            {
                "kind": "vector",
                "vector": vec,
                "fields": os.getenv("VECTOR_FIELD"),
                "k": int(os.getenv("TOP_K", "3")),
            }
        ],
        "select": "title"
    }
    resp = requests.post(url, headers=headers, json=body, timeout=30)
    resp.raise_for_status()
    return resp.json()["value"]

# Generate url for images in blob
def generate_blob_url(blob_name: str, expiry_hours: int = 1) -> str:
    parts = os.getenv("STORAGE_CONNECTION_STRING").split(';')
    account_name = None
    account_key = None
    for part in parts:
        if part.startswith('AccountName='):
            account_name = part.split('=', 1)[1]
        elif part.startswith('AccountKey='):
            account_key = part.split('=', 1)[1]
    expiry = datetime.now(timezone.utc) + timedelta(hours=expiry_hours)
    sas_token = generate_blob_sas(
        account_name=account_name,
        container_name=os.getenv("CONTAINER_NAME"),
        blob_name=blob_name,
        account_key=account_key,
        permission=BlobSasPermissions(read=True),
        expiry=expiry
    )
    encoded_blob_name = quote(blob_name, safe='')
    base_url = f"https://{account_name}.blob.core.windows.net/{os.getenv('CONTAINER_NAME')}/{encoded_blob_name}"
    return f"{base_url}?{sas_token}"

# Main function
if __name__ == "__main__":
    try:
        qvec = vectorize_image(os.getenv("QUERY_IMAGE_PATH"))
        results = search_similar(qvec)
        print(f"\nTop {int(os.getenv('TOP_K', '3'))} matches")
        for i, doc in enumerate(results, 1):
            score = doc["@search.score"]
            title = doc.get("title", "[no title]")
            image_url = generate_blob_url(title)
            print(f"{i:>2}. score={score:.3f}")
            print(f"    title: {title}")
            print(f"    url: {image_url}")
            print()
    except requests.HTTPError as e:
        print("HTTP error:", e.response.status_code)
        print(e.response.text)
    except Exception as e:
        print("error", e)