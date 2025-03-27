from typing import List, Dict, Union
from fastapi import FastAPI, HTTPException, Query
import requests
from pydantic import BaseModel, Field

app = FastAPI()



@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.get("/items/{item_id}")
def read_item(item_id: int, q: Union[str, None] = None):
    return {"item_id": item_id, "q": q}

class ProductInput(BaseModel):
    id: int
    name: str
    description: str
    price: float
    quantity: int

class PaginateInput(BaseModel):
    start_id: int = Field(..., ge=0)
    end_id: int = Field(..., ge=0)

class ConvertInput(BaseModel):
    product_id: int = Field(..., ge=0)

@app.get("/getSingleProduct")
def get_single_product(product_id: int):
    for product in inventory:
        if product["id"] == product_id:
            return product
    raise HTTPException(status_code=404, detail="Product not found")

@app.get("/getAll")
def get_all():
    return inventory

@app.post("/addNew")
def add_new(product: ProductInput):
    if any(p["id"] == product.id for p in inventory):
        raise HTTPException(status_code=400, detail="Product with this ID already exists")
    new_product = product.dict()
    inventory.append(new_product)
    return {"message": "Product added successfully", "product": new_product}

@app.delete("/deleteOne")
def delete_one(product_id: int = Query(..., ge=0)):
    global inventory
    inventory = [product for product in inventory if product["id"] != product_id]
    return {"message": "Product deleted successfully"}

@app.get("/startsWith")
def starts_with(letter: str = Query(..., min_length=1, max_length=1)):
    filtered_products = [product for product in inventory if product["name"].startswith(letter)]
    return filtered_products

@app.get("/paginate")
def paginate(pagination: PaginateInput):
    paginated_products = [product for product in inventory if pagination.start_id <= product["id"] <= pagination.end_id][:10]
    return paginated_products

@app.get("/convert")
def convert(data: ConvertInput):
    for product in inventory:
        if product["id"] == data.product_id:
            response = requests.get("https://api.exchangerate-api.com/v4/latest/USD")
            if response.status_code == 200:
                exchange_rate = response.json()["rates"]["EUR"]
                price_in_euro = product["price"] * exchange_rate
                return {"id": data.product_id, "price_in_euro": price_in_euro}
            else:
                raise HTTPException(status_code=500, detail="Failed to fetch exchange rate")
    raise HTTPException(status_code=404, detail="Product not found")

#here/scripts/activate
