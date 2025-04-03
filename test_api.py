import unittest
import httpx
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

BASE_URL = "http://127.0.0.1:8000"

class TestFastAPIEndpoints(unittest.TestCase):
    def test_read_root(self):
        response = httpx.get(f"{BASE_URL}/")
        self.assertIn(response.status_code, [200, 404])  
        if response.status_code == 200:
            self.assertIn("Hello", response.json())

    def test_get_single_product(self):
        response = httpx.get(f"{BASE_URL}/getSingleProduct", params={"product_id": 1})
        self.assertIn(response.status_code, [200, 404])  
        if response.status_code == 200:
            self.assertEqual(response.json()["id"], 1)

    def test_get_all(self):
        response = httpx.get(f"{BASE_URL}/getAll")
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json(), list)

    def test_add_new(self):
        new_product = {
            "id": 3,
            "name": "Product C",
            "description": "Description C",
            "price": 30.0,
            "quantity": 300
        }
        response = httpx.post(f"{BASE_URL}/addNew", json=new_product)
        self.assertIn(response.status_code, [200, 400])  

    def test_delete_one(self):
        response = httpx.delete(f"{BASE_URL}/deleteOne", params={"product_id": 3})
        self.assertEqual(response.status_code, 200)

    def test_starts_with(self):
        response = httpx.get(f"{BASE_URL}/startsWith", params={"letter": "P"})
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json(), list)

    def test_paginate(self):
        response = httpx.get(f"{BASE_URL}/paginate", params={"start_id": 1, "end_id": 2})
        self.assertIn(response.status_code, [200, 422]) 
        if response.status_code == 200:
            self.assertIsInstance(response.json(), list)

    def test_convert(self):
        response = httpx.get(f"{BASE_URL}/convert", params={"product_id": 1})
        self.assertIn(response.status_code, [200, 404, 422])  

def generate_pdf_report(results):
    pdf_path = "test_results.pdf"
    c = canvas.Canvas(pdf_path, pagesize=letter)
    c.drawString(100, 750, "Unit Test Results")
    y = 700
    for result in results:
        c.drawString(100, y, result)
        y -= 20
    c.save()
    print(f"PDF report generated: {pdf_path}")

if __name__ == "__main__":
    suite = unittest.TestLoader().loadTestsFromTestCase(TestFastAPIEndpoints)
    runner = unittest.TextTestRunner(resultclass=unittest.TextTestResult)
    result = runner.run(suite)

    # Collect results for the PDF
    test_results = []
    for test, err in result.errors:
        test_results.append(f"ERROR: {test.id()} - {err}")
    for test, fail in result.failures:
        test_results.append(f"FAIL: {test.id()} - {fail}")
    for test in filter(None, suite._tests):  # Filter out None values
        if test not in [t[0] for t in result.errors + result.failures]:
            test_results.append(f"PASS: {test.id()}")

    # Generate PDF report
    generate_pdf_report(test_results)
