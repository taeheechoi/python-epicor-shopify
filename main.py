import os
from datetime import datetime

import requests
from dotenv import load_dotenv
from requests.auth import HTTPBasicAuth

load_dotenv()

shopify_api_url = os.getenv('SHOPIFY_API_URL')
shopify_access_token = os.getenv('SHOPIFY_ACCESS_TOKEN')

epicor_company = os.getenv('EPICOR_COMPANY')
epicor_web_customer = os.getenv('EPICOR_WEB_CUSTOMER')
epicor_api_url = os.getenv('EPICOR_API_URL')
epicor_user_id = os.getenv('EPICOR_USER_ID')
epicor_password = os.getenv('EPICOR_PASSWORD')

def get_data_from_shopify(endpoint):
    url = f'{shopify_api_url}/{endpoint}'

    headers = {
        'X-Shopify-Access-Token': shopify_access_token,
        'Content-Type': 'application/json'
    }
    
    response = requests.get(url, headers=headers)
    
    response.raise_for_status()
    
    return response.json()

def get_orders_from_shopify():
    created_at_min = datetime.now().strftime("%Y-%m-%d")
    
    endpoint = f'orders.json?created_at_min={created_at_min}'

    return get_data_from_shopify(endpoint)

def create_data_to_epicor(endpoint, data):
    url = f'{epicor_api_url}/{endpoint}'
    
    headers = {
        'Content-Type': 'application/json'
    }

    response = requests.post(url, auth=HTTPBasicAuth(epicor_user_id, epicor_password), json=data, headers=headers)
    
    response.raise_for_status()
    
    return response.json()

def create_order_header(data):
    url = 'Erp.BO.SalesOrderSvc/SalesOrders'

    order_header = {
        'Company': epicor_company,
        'CustNum': epicor_web_customer,    
        'ReadyToCalc': True,
        'UseOTS': True,
        'NeedByDate': data['created_at'],
        'OTSName': data['shipping_address']['name'],
        'OTSAddress1': data['shipping_address']['address1'],
        'OTSAddress2': data['shipping_address']['address2'],
        'OTSCity': data['shipping_address']['city'],
        'OTSZIP': data['shipping_address']['zip'],
        'OTSState': data['shipping_address']['province']
    }

    response = create_data_to_epicor(url, order_header)

    return response['OrderNum']

def create_order_detail(orderNum, data):
    url = f'Erp.BO.SalesOrderSvc/OrderDtls'
    
    order_detail = []
    
    for line_item in data['line_items']:
        detail = {
            'Company': epicor_company,
            'OrderNum': orderNum,
            'PartNum': line_item['sku'],
            'LineDesc': line_item['name'],
            'SellingQuantity': str(line_item['quantity']),
            'DocUnitPrice': line_item['price']

        }
        order_detail.append(detail)
    
    for detail in order_detail:
        create_data_to_epicor(url, detail)

if __name__ == '__main__':
    orders = get_orders_from_shopify()['orders']
    
    if orders:
        for order in orders:
            orderNum = create_order_header(order)
            
            if orderNum:
                create_order_detail(orderNum, order)
   

