from typing import List, Dict, Union
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field
from pymongo import MongoClient
import requests
import csv
import os

app = FastAPI()

# MongoDB setup
client = MongoClient("mongodb://localhost:27017/")
db = client["inventory_db"]
collection = db["products"]

# Load CSV data into MongoDB
def load_csv_to_mongodb(csv_file_path: str):
    if not os.path.exists(csv_file_path):
        raise FileNotFoundError(f"CSV file not found: {csv_file_path}")
    with open(csv_file_path, mode="r") as file:
        reader = csv.DictReader(file)
        products = []
        for row in reader:
            row["id"] = int(row["id"])
            row["price"] = float(row["price"])
            row["quantity"] = int(row["quantity"])
            products.append(row)
        collection.insert_many(products)

# Uncomment the line below to load data from a CSV file (run once)
# load_csv_to_mongodb("path/to/your/csvfile.csv")

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
    product = collection.find_one({"id": product_id})
    if product:
        return product
    raise HTTPException(status_code=404, detail="Product not found")

@app.get("/getAll")
def get_all():
    return list(collection.find({}, {"_id": 0}))

@app.post("/addNew")
def add_new(product: ProductInput):
    if collection.find_one({"id": product.id}):
        raise HTTPException(status_code=400, detail="Product with this ID already exists")
    collection.insert_one(product.dict())
    return {"message": "Product added successfully", "product": product.dict()}

@app.delete("/deleteOne")
def delete_one(product_id: int = Query(..., ge=0)):
    result = collection.delete_one({"id": product_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Product not found")
    return {"message": "Product deleted successfully"}

@app.get("/startsWith")
def starts_with(letter: str = Query(..., min_length=1, max_length=1)):
    filtered_products = list(collection.find({"name": {"$regex": f"^{letter}", "$options": "i"}}, {"_id": 0}))
    return filtered_products

@app.get("/paginate")
def paginate(pagination: PaginateInput):
    paginated_products = list(collection.find(
        {"id": {"$gte": pagination.start_id, "$lte": pagination.end_id}},
        {"_id": 0}
    ).limit(10))
    return paginated_products

@app.get("/convert")
def convert(data: ConvertInput):
    product = collection.find_one({"id": data.product_id})
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    response = requests.get("https://api.exchangerate-api.com/v4/latest/USD")
    if response.status_code == 200:
        exchange_rate = response.json()["rates"]["EUR"]
        price_in_euro = product["price"] * exchange_rate
        return {"id": data.product_id, "price_in_euro": price_in_euro}
    else:
        raise HTTPException(status_code=500, detail="Failed to fetch exchange rate")
